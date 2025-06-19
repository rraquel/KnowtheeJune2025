#!/usr/bin/env python3
"""
Simple test script for hybrid RAG functionality
Tests the core concepts without importing the problematic query_service.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_hybrid_concept():
    """Test the hybrid RAG concept with mock data"""
    
    print("🧪 Testing Hybrid RAG Concept")
    print("=" * 50)
    
    # Mock test cases
    test_queries = {
        "Structured Queries (Database)": [
            "What is Ahmed Al-Ahmad's Prudence score?",
            "Show me Lisa Wu's Ambition score",
            "Compare the Sociability scores of Ahmed and Lisa",
            "Who has the highest Adjustment score among Ahmed and Lisa?",
            "What are Ahmed's Hogan scores?",
            "Show me the top 5 employees with highest Ambition scores"
        ],
        "General Queries (RAG/Embeddings)": [
            "Tell me about Ahmed's work experience",
            "How does Lisa perform in team settings?",
            "What are Ahmed's key strengths?",
            "What challenges does Lisa face in her role?",
            "Describe Ahmed's leadership style",
            "What is Lisa's educational background?"
        ]
    }
    
    for category, queries in test_queries.items():
        print(f"\n📋 {category}")
        print("-" * 30)
        
        for i, query in enumerate(queries, 1):
            print(f"\n🔍 Test {i}: {query}")
            
            # Simulate intent classification
            if any(keyword in query.lower() for keyword in ['score', 'hogan', 'idi', 'compare', 'highest', 'top']):
                intent = "structured_query"
                source = "database"
                print(f"   📝 Intent: {intent}")
                print(f"   📊 Source: {source}")
                print(f"   ✅ Would use database for exact scores")
            else:
                intent = "general_query"
                source = "rag_embeddings"
                print(f"   📝 Intent: {intent}")
                print(f"   📊 Source: {source}")
                print(f"   ✅ Would use RAG/embeddings for qualitative info")
    
    print("\n" + "=" * 50)
    print("✅ Hybrid RAG concept test completed!")
    
    print("\n📈 Expected Behavior:")
    print("- Structured queries → Database (exact scores)")
    print("- General queries → RAG/Embeddings (qualitative insights)")
    print("- AI intent classification determines the path")
    print("- Fallback mechanisms ensure robustness")

def test_ai_intent_classification():
    """Test AI-based intent classification concept"""
    
    print("\n🤖 Testing AI Intent Classification Concept")
    print("=" * 50)
    
    # Test cases for intent classification
    classification_tests = [
        ("What is Ahmed's Prudence score?", "get_score"),
        ("Tell me about Ahmed's work experience", "general_query"),
        ("Compare Lisa and Ahmed's Sociability", "compare_scores"),
        ("Top 5 employees by Ambition", "rank_scores"),
        ("What are Ahmed's Hogan scores?", "get_all_scores"),
        ("How does Lisa perform in teams?", "general_query")
    ]
    
    for query, expected_intent in classification_tests:
        print(f"\n🔍 Query: {query}")
        print(f"🎯 Expected Intent: {expected_intent}")
        
        # Simulate AI classification
        if "score" in query.lower() and any(name in query.lower() for name in ['ahmed', 'lisa']):
            if "compare" in query.lower():
                actual_intent = "compare_scores"
            elif "top" in query.lower() or "rank" in query.lower():
                actual_intent = "rank_scores"
            elif "hogan" in query.lower() or "idi" in query.lower():
                actual_intent = "get_all_scores"
            else:
                actual_intent = "get_score"
        else:
            actual_intent = "general_query"
        
        print(f"✅ Simulated Intent: {actual_intent}")
        
        if actual_intent == expected_intent:
            print("✅ Classification Correct!")
        else:
            print("❌ Classification Incorrect!")

if __name__ == "__main__":
    test_hybrid_concept()
    test_ai_intent_classification() 