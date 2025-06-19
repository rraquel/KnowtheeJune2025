#!/usr/bin/env python3
"""
Debug script to test Carlos query specifically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase

def test_carlos_query():
    """Test the Carlos query step by step."""
    print("🔍 Testing Carlos query step by step...")
    
    try:
        # Step 1: Initialize RAG system
        print("Step 1: Initializing RAG system...")
        rag_system = RAGQuerySystem()
        print("✅ RAG system initialized")
        
        # Step 2: Test employee database
        print("\nStep 2: Testing employee database...")
        all_employees = rag_system.employee_db.get_all_employees()
        print(f"✅ Retrieved {len(all_employees)} employees")
        
        # Step 3: Test employee name extraction
        print("\nStep 3: Testing employee name extraction...")
        query = "What are Carlos Hogan scores?"
        employees = rag_system._extract_employee_names_from_query(query)
        print(f"✅ Extracted employees: {employees}")
        
        # Step 4: Test query planning
        print("\nStep 4: Testing query planning...")
        plan = rag_system._plan_query_with_rules(query)
        print(f"✅ Query plan: {plan}")
        
        # Step 5: Test query execution
        print("\nStep 5: Testing query execution...")
        result = rag_system._execute_query_plan(plan)
        print(f"✅ Query result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_carlos_query()
    if success:
        print("\n🎉 Carlos query test completed successfully!")
    else:
        print("\n💥 Carlos query test failed!") 