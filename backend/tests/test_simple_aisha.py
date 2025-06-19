#!/usr/bin/env python3

from backend.services.rag.query_service import RAGQuerySystem

def test_simple_aisha():
    """Test the _execute_get_score method directly."""
    rag_system = RAGQuerySystem()
    
    # Create the exact plan that should trigger clarification
    plan = {
        "intent": "get_score",
        "trait": "ambition", 
        "assessment_type": "Hogan",
        "employees": ["Aisha Ibrahim", "Aisha Hassan", "Aisha Al-Zahra"],
        "query": "what is the ambition score of Aisha"
    }
    
    print("Testing _execute_get_score directly:")
    print(f"Plan: {plan}")
    
    result = rag_system._execute_get_score(plan)
    print(f"Result: {result}")
    print(f"Response: {result['response']}")

if __name__ == "__main__":
    test_simple_aisha() 