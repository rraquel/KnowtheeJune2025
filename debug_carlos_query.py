#!/usr/bin/env python3
"""
Debug script to trace Carlos Garcia query processing
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase

def debug_carlos_query():
    """Debug the Carlos Garcia query step by step"""
    
    print("=== DEBUGGING CARLOS GARCIA QUERY ===")
    
    # Initialize the RAG system
    rag_system = RAGQuerySystem()
    
    # Test query
    query = "What is Carlos Garcia work background?"
    
    print(f"\n1. ORIGINAL QUERY: {query}")
    
    # Step 1: Extract employee names
    print(f"\n2. EXTRACTING EMPLOYEE NAMES...")
    employee_names = rag_system._extract_employee_names_from_query(query)
    print(f"   Extracted employees: {employee_names}")
    
    # Step 2: Check if Carlos Garcia exists in database
    print(f"\n3. CHECKING DATABASE...")
    all_employees = rag_system.employee_db.get_all_employees()
    carlos_employees = [emp for emp in all_employees if "carlos" in emp["name"].lower()]
    print(f"   All Carlos employees in DB: {[emp['name'] for emp in carlos_employees]}")
    
    # Step 3: Test direct employee lookup
    print(f"\n4. TESTING DIRECT EMPLOYEE LOOKUP...")
    carlos_data = rag_system._get_employee_by_name("Carlos Garcia")
    if carlos_data:
        print(f"   Found Carlos Garcia data: {carlos_data.get('name', 'Unknown')}")
        print(f"   Department: {carlos_data.get('department', 'Not found')}")
        print(f"   Position: {carlos_data.get('current_position', 'Not found')}")
        print(f"   Experiences: {len(carlos_data.get('experiences', []))} entries")
    else:
        print(f"   Carlos Garcia NOT found in database")
    
    # Step 4: Test query planning
    print(f"\n5. TESTING QUERY PLANNING...")
    plan = rag_system._plan_query_with_ai(query)
    print(f"   AI Plan: {plan}")
    
    # Step 5: Test query execution
    print(f"\n6. TESTING QUERY EXECUTION...")
    result = rag_system._execute_query_plan(plan)
    print(f"   Execution Result: {result}")
    
    # Step 6: Test full process
    print(f"\n7. TESTING FULL PROCESS...")
    full_result = rag_system.process_complex_query(query)
    print(f"   Full Result: {full_result}")
    
    # Step 7: Check vector store
    print(f"\n8. TESTING VECTOR STORE...")
    try:
        search_results = rag_system.vector_store.search_employees("Carlos Garcia", n_results=5)
        print(f"   Vector search results: {len(search_results)} found")
        for result in search_results:
            print(f"     - {result}")
    except Exception as e:
        print(f"   Vector search error: {e}")
    
    # Step 8: Check hybrid service
    print(f"\n9. TESTING HYBRID SERVICE...")
    try:
        hybrid_service = rag_system._get_hybrid_query_service()
        if hybrid_service:
            search_results = hybrid_service.search_employees("Carlos Garcia", n_results=5)
            print(f"   Hybrid search results: {search_results}")
        else:
            print(f"   Hybrid service not available")
    except Exception as e:
        print(f"   Hybrid service error: {e}")

if __name__ == "__main__":
    debug_carlos_query() 