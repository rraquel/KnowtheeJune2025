#!/usr/bin/env python3

from backend.services.rag.query_service import RAGQuerySystem

def test_aisha_query():
    """Test the fix for finding Aisha's ambition score."""
    rag_system = RAGQuerySystem()
    
    # Test the query
    query = "what is the ambition score of Aisha"
    print(f"Testing query: {query}")
    
    # Test the AI query planning
    plan = rag_system._plan_query_with_ai(query)
    print(f"AI Query Plan: {plan}")
    
    # Test employee extraction
    employees = rag_system._extract_employee_names_from_query(query)
    print(f"Extracted employees: {employees}")
    
    # Test employee lookup
    if employees:
        employee_data = rag_system._get_employee_by_name(employees[0])
        if employee_data:
            print(f"Found employee: {employee_data['name']}")
            
            # Test getting the specific score
            score = rag_system._get_specific_score(employee_data, "ambition", "Hogan")
            print(f"Ambition score: {score}")
        else:
            print("Employee not found in database")
    else:
        print("No employees extracted from query")
    
    # Test the full query execution
    result = rag_system.query(query)
    print(f"\nFull query result:\n{result}")

if __name__ == "__main__":
    test_aisha_query() 