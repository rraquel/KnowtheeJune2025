from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from backend.db.session import get_db_dep, SessionLocal
from backend.db.models import Employee
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase
import logging
import traceback
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session context (for demonstration; use Redis/DB for production)
session_memory: Dict[str, dict] = {}

# Lazy initialization of RAG system
_rag_system = None

def error_handler(func):
    """Decorator for comprehensive error handling."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # Re-raise HTTP exceptions as-is (for validation errors, etc.)
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    return wrapper

def get_rag_system():
    """Get or create the RAG system instance with error handling."""
    global _rag_system
    try:
        if _rag_system is None:
            logger.info("Initializing new RAG system instance")
            _rag_system = RAGQuerySystem(employee_db=EmployeeDatabase())
        return _rag_system
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize RAG system")

def clear_rag_system_cache():
    """Clear the cached RAG system instance - useful for testing and debugging."""
    global _rag_system
    if _rag_system is not None:
        logger.info("Clearing cached RAG system instance")
        _rag_system = None

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    clarification_needed: Optional[bool] = False
    candidates: Optional[List[Dict[str, Any]]] = None

@router.get("/employees")
@error_handler
async def get_employees(db: Session = Depends(get_db_dep)):
    """Get all employees with error handling."""
    try:
        employees = db.query(Employee).all()
        result = [{"id": str(emp.id), "full_name": emp.full_name} for emp in employees]
        logger.info(f"Retrieved {len(result)} employees")
        return result
    except Exception as e:
        logger.error(f"Error retrieving employees: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve employees")

@router.post("/chat", response_model=ChatResponse)
@error_handler
async def chat_endpoint(request: ChatRequest):
    """Process chat requests with comprehensive error handling."""
    
    # Validate input
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    if not request.session_id or not request.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID cannot be empty")
    
    # Retrieve or initialize session history/context
    session_context = session_memory.setdefault(request.session_id, {})
    
    try:
        logger.info(f"Processing chat request: {request.message[:100]}...")
        
        # Get the RAG system (initialized lazily)
        rag_system = get_rag_system()
        
        # Use the RAG system to process the query with context
        rag_result = rag_system.process_complex_query(
            query=request.message,
            context_type="general",
            conversation_id=request.session_id
        )
        
        # Extract response and check for clarification needs
        response_text = rag_result.get("response", "Sorry, I couldn't generate a response.")
        clarification_needed = rag_result.get("clarification_needed", False)
        candidates = rag_result.get("candidates", None)
        
        # Log the response for debugging
        logger.info(f"Generated response: {response_text[:100]}...")
        if clarification_needed:
            logger.info(f"Clarification needed with {len(candidates) if candidates else 0} candidates")
        
        # Optionally, update session context with new history if needed
        session_context["last_rag_result"] = rag_result
        
        # Return full response with clarification data
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            clarification_needed=clarification_needed,
            candidates=candidates
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return a user-friendly error response
        return ChatResponse(
            response="I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists.",
            session_id=request.session_id,
            clarification_needed=False,
            candidates=None
        )

@router.post("/clear-cache")
@error_handler
async def clear_cache():
    """Clear the RAG system cache - useful for debugging."""
    try:
        clear_rag_system_cache()
        logger.info("Cache cleared successfully")
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        # Test RAG system
        rag_system = get_rag_system()
        
        return {
            "status": "healthy",
            "database": "connected",
            "rag_system": "initialized",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy") 