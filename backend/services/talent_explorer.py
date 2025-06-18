from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List
from backend.db.session import get_db_dep
from backend.db.models import Employee
from sqlalchemy.orm import Session
from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase

router = APIRouter()

# In-memory session context (for demonstration; use Redis/DB for production)
session_memory: Dict[str, dict] = {}

# Lazy initialization of RAG system
_rag_system = None

def get_rag_system():
    """Get or create the RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGQuerySystem(employee_db=EmployeeDatabase())
    return _rag_system

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str

@router.get("/employees")
def get_employees(db: Session = Depends(get_db_dep)):
    employees = db.query(Employee).all()
    return [{"id": str(emp.id), "full_name": emp.full_name} for emp in employees]

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    # Retrieve or initialize session history/context
    session_context = session_memory.setdefault(request.session_id, {})
    try:
        # Get the RAG system (initialized lazily)
        rag_system = get_rag_system()
        
        # Use the RAG system to process the query with context
        rag_result = rag_system.process_complex_query(
            query=request.message,
            context_type="general",
            conversation_id=request.session_id
        )
        response_text = rag_result.get("response", "Sorry, I couldn't generate a response.")
        # Optionally, update session context with new history if needed
        session_context["last_rag_result"] = rag_result
        return ChatResponse(response=response_text, session_id=request.session_id)
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}", session_id=request.session_id) 