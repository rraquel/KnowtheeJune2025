#!/usr/bin/env python3
"""
Test script for the new AI-driven query planning architecture
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase

def test_ai_query_planning():
    """Test the new AI-driven query planning system"""
    
    print("🧪 Testing AI-Driven Query Planning Architecture")
    print("=" * 60)
    
    # Initialize the query system
    employee_db = EmployeeDatabase()
    query_system = RAGQuerySystem(employee_db=employee_db)
    
    # Test queries
    test_queries = [
        "What is Ahmed Al-Ahmad's Prudence score?",
        "Who has the highest Prudence score among Ahmed and Lisa?",
        "Show me the top 5 employees with highest Ambition scores",
        "Compare the Sociability scores of Ahmed and Lisa",
        "What are Ahmed's Hogan scores?",
        "Show me Lisa's IDI scores",
        "Who has the best Adjustment scores?",
        "What is the lowest Prudence score in the database?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 40)
        
        try:
            # Test the planning step
            plan = query_system._plan_query_with_ai(query)
            print(f"🔍 Query Plan: {plan}")
            
            # Test the execution step
            result = query_system._execute_query_plan(plan)
            print(f"✅ Result: {result['response'][:100]}...")
            print(f"📊 Confidence: {result['confidence']}")
            print(f"👥 Employees: {result.get('employees', [])}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Testing completed!")

if __name__ == "__main__":
    test_ai_query_planning() 