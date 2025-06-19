#!/usr/bin/env python3
"""
Comprehensive test script for the hybrid RAG system
Tests both structured queries (database) and general queries (embeddings)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.rag.query_service import RAGQuerySystem
from backend.services.data_access.employee_database import EmployeeDatabase

def test_hybrid_rag_system():
    """Test the hybrid RAG system with various query types"""
    
    print("🧪 Testing Hybrid RAG System - Structured vs General Queries")
    print("=" * 70)
    
    # Initialize the query system
    employee_db = EmployeeDatabase()
    query_system = RAGQuerySystem(employee_db=employee_db)
    
    # Test queries organized by type
    test_cases = {
        "Structured Queries (Database)": [
            "What is Ahmed Al-Ahmad's Prudence score?",
            "Show me Lisa Wu's Ambition score",
            "Compare the Sociability scores of Ahmed and Lisa",
            "Who has the highest Adjustment score among Ahmed and Lisa?",
            "What are Ahmed's Hogan scores?",
            "Show me the top 5 employees with highest Ambition scores",
            "Rank employees by Prudence score"
        ],
        "General Queries (RAG/Embeddings)": [
            "Tell me about Ahmed's work experience",
            "How does Lisa perform in team settings?",
            "What are Ahmed's key strengths?",
            "What challenges does Lisa face in her role?",
            "Describe Ahmed's leadership style",
            "What is Lisa's educational background?",
            "How does Ahmed handle stress and pressure?",
            "What are the main responsibilities in Lisa's current position?"
        ],
        "Mixed/Complex Queries": [
            "What is Ahmed's Prudence score and how does it affect his work?",
            "Compare Lisa and Ahmed's scores and tell me about their work styles",
            "Who has the highest Ambition score and what does that mean for their career?"
        ]
    }
    
    for category, queries in test_cases.items():
        print(f"\n📋 {category}")
        print("-" * 50)
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            print("─" * 40)
            
            try:
                # Test the planning step
                plan = query_system._plan_query_with_ai(query)
                print(f"📝 Query Plan: {plan}")
                
                # Test the execution step
                result = query_system._execute_query_plan(plan)
                print(f"✅ Response: {result['response'][:200]}...")
                print(f"📊 Source: {result['source']}")
                print(f"🎯 Confidence: {result['confidence']}")
                print(f"👥 Employees: {result.get('employees', [])}")
                
                # Test the full pipeline
                full_result = query_system.process_complex_query(query)
                print(f"🔄 Full Pipeline Source: {full_result['source']}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ Comprehensive testing completed!")
    
    # Summary statistics
    print("\n📈 Test Summary:")
    print("- Structured queries should use 'ai_query_plan' source")
    print("- General queries should use 'hybrid_rag' source")
    print("- Mixed queries may use either depending on intent classification")

def test_ai_intent_classification():
    """Test the AI-based intent classification specifically"""
    
    print("\n🤖 Testing AI Intent Classification")
    print("=" * 50)
    
    employee_db = EmployeeDatabase()
    query_system = RAGQuerySystem(employee_db=employee_db)
    
    # Test queries that should be classified differently
    classification_tests = [
        ("What is Ahmed's Prudence score?", "get_score"),
        ("Tell me about Ahmed's work experience", "general_query"),
        ("Compare Lisa and Ahmed's Sociability", "compare_scores"),
        ("Top 5 employees by Ambition", "rank_scores"),
        ("What are Ahmed's Hogan scores?", "get_all_scores"),
        ("How does Lisa perform in teams?", "general_query"),
        ("Who has the highest Adjustment score?", "rank_scores")
    ]
    
    for query, expected_intent in classification_tests:
        print(f"\n🔍 Query: {query}")
        print(f"🎯 Expected Intent: {expected_intent}")
        
        try:
            plan = query_system._plan_query_with_ai(query)
            actual_intent = plan.get("intent", "unknown")
            print(f"✅ Actual Intent: {actual_intent}")
            
            if actual_intent == expected_intent:
                print("✅ Classification Correct!")
            else:
                print("❌ Classification Incorrect!")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_hybrid_rag_system()
    test_ai_intent_classification() 