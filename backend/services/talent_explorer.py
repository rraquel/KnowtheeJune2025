from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from backend.db.session import get_db_dep
from backend.db.models import Employee
from sqlalchemy.orm import Session
from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory session context (for demonstration; use Redis/DB for production)
session_memory: Dict[str, dict] = {}

# Lazy initialization of RAG system
_rag_system = None

def get_rag_system():
    """Get or create the RAG system instance"""
    global _rag_system
    if _rag_system is None:
        logger.info("Initializing new RAG system instance")
        _rag_system = RAGQuerySystem(employee_db=EmployeeDatabase())
    return _rag_system

def clear_rag_system_cache():
    """Clear the cached RAG system instance - useful for testing and debugging"""
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
def get_employees(db: Session = Depends(get_db_dep)):
    employees = db.query(Employee).all()
    return [{"id": str(emp.id), "full_name": emp.full_name} for emp in employees]

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
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
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return ChatResponse(response=f"Error: {str(e)}", session_id=request.session_id)

@router.post("/clear-cache")
def clear_cache():
    """Clear the RAG system cache - useful for debugging"""
    clear_rag_system_cache()
    return {"message": "Cache cleared successfully"} 