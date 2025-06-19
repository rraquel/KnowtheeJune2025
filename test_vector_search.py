#!/usr/bin/env python3
"""
Test script to check vector search for Carlos Garcia
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.rag.vector_store import VectorStore
from backend.services.data_access.employee_database import EmployeeDatabase

def test_carlos_garcia_search():
    """Test if Carlos Garcia can be found in vector search"""
    
    print("=== TESTING VECTOR SEARCH FOR CARLOS GARCIA ===")
    
    # Initialize services
    vector_store = VectorStore()
    employee_db = EmployeeDatabase()
    
    # Get all employees to find Carlos Garcia
    all_employees = employee_db.get_all_employees()
    carlos_garcia = None
    
    for emp in all_employees:
        if "carlos garcia" in emp["name"].lower():
            carlos_garcia = emp
            break
    
    if not carlos_garcia:
        print("❌ Carlos Garcia not found in employee database")
        return
    
    print(f"✅ Found Carlos Garcia in database: {carlos_garcia['name']} (ID: {carlos_garcia['id']})")
    
    # Test vector search
    print("\n=== TESTING VECTOR SEARCH ===")
    search_queries = [
        "Carlos Garcia work background",
        "Carlos Garcia",
        "work background",
        "Full Stack Developer"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        try:
            results = vector_store.search_employees(query, n_results=10)
            print(f"Found {len(results)} results")
            
            # Check if Carlos Garcia is in the results
            carlos_found = False
            for result in results:
                emp_data = employee_db.get_employee(result['employee_id'])
                if emp_data and "carlos garcia" in emp_data['name'].lower():
                    carlos_found = True
                    print(f"✅ Carlos Garcia found in results: {emp_data['name']} (score: {result.get('score', 'N/A')})")
                    break
            
            if not carlos_found:
                print("❌ Carlos Garcia NOT found in search results")
                print("Top results:")
                for i, result in enumerate(results[:5]):
                    emp_data = employee_db.get_employee(result['employee_id'])
                    if emp_data:
                        print(f"  {i+1}. {emp_data['name']} (score: {result.get('score', 'N/A')})")
                        
        except Exception as e:
            print(f"❌ Error in vector search: {e}")
    
    # Test direct employee context
    print(f"\n=== TESTING DIRECT EMPLOYEE CONTEXT ===")
    try:
        from backend.services.rag.query_service import RAGQuerySystem
        rag_system = RAGQuerySystem()
        
        context_chunks = rag_system._get_employee_context(
            carlos_garcia['id'], 
            {"query_type": "individual_profile", "scope": "single_employee"}
        )
        
        print(f"Generated {len(context_chunks)} context chunks for Carlos Garcia:")
        for i, chunk in enumerate(context_chunks[:3]):  # Show first 3 chunks
            print(f"  {i+1}. {chunk[:100]}...")
            
    except Exception as e:
        print(f"❌ Error getting employee context: {e}")

if __name__ == "__main__":
    test_carlos_garcia_search() 