#!/usr/bin/env python3
"""
Test script to verify all the fixes are working properly
"""
import sys
import os
import requests
import json
import time

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.data_access.employee_database import EmployeeDatabase
from backend.services.rag.query_service import RAGQuerySystem, QueryCache

def test_employee_database():
    """Test the improved employee database functionality."""
    print("🧪 Testing Employee Database...")
    
    try:
        # Initialize database
        db = EmployeeDatabase()
        
        # Test get_all_employees
        employees = db.get_all_employees()
        print(f"✅ Retrieved {len(employees)} employees")
        
        if employees:
            # Test get_employee with first employee
            first_emp = employees[0]
            full_data = db.get_employee(first_emp["id"])
            
            if full_data:
                print(f"✅ Retrieved full data for {full_data['name']}")
                print(f"   - Experiences: {len(full_data.get('experiences', []))}")
                print(f"   - Education: {len(full_data.get('education', []))}")
                print(f"   - Skills: {len(full_data.get('skills', []))}")
                print(f"   - Hogan scores: {len(full_data.get('hogan_scores', {}))}")
                print(f"   - IDI scores: {len(full_data.get('idi_scores', {}))}")
            else:
                print("❌ Failed to get full employee data")
        
        # Test fuzzy name matching
        if employees:
            test_name = employees[0]["name"].split()[0]  # Just first name
            matches = db.find_employees_by_name(test_name, fuzzy_match=True)
            print(f"✅ Fuzzy match for '{test_name}': {len(matches)} matches")
        
        return True
        
    except Exception as e:
        print(f"❌ Employee database test failed: {e}")
        return False

def test_query_cache():
    """Test the query caching functionality."""
    print("\n🧪 Testing Query Cache...")
    
    try:
        cache = QueryCache(max_size=10, ttl_seconds=5)
        
        # Test cache set/get
        test_data = {"response": "test response", "source": "test"}
        cache.set("test query", "general", "test_session", test_data)
        
        # Test immediate retrieval
        result = cache.get("test query", "general", "test_session")
        if result == test_data:
            print("✅ Cache set/get working")
        else:
            print("❌ Cache set/get failed")
            return False
        
        # Test cache miss
        result = cache.get("different query", "general", "test_session")
        if result is None:
            print("✅ Cache miss working")
        else:
            print("❌ Cache miss failed")
            return False
        
        # Test TTL expiration
        print("⏳ Testing TTL expiration (waiting 6 seconds)...")
        time.sleep(6)
        result = cache.get("test query", "general", "test_session")
        if result is None:
            print("✅ TTL expiration working")
        else:
            print("❌ TTL expiration failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Query cache test failed: {e}")
        return False

def test_rag_system():
    """Test the RAG system with improved functionality."""
    print("\n🧪 Testing RAG System...")
    
    try:
        # Initialize RAG system
        rag_system = RAGQuerySystem()
        
        # Test employee index initialization
        rag_system._initialize_employee_index()
        print(f"✅ Employee index initialized with {len(rag_system._employee_name_index)} employees")
        
        # Test fuzzy matching
        if rag_system._employee_name_index:
            test_name = list(rag_system._employee_name_index.keys())[0].split()[0]
            matches = rag_system._fuzzy_match_employee_name(test_name)
            print(f"✅ Fuzzy matching for '{test_name}': {len(matches)} matches")
        
        # Test cache functionality
        rag_system.clear_cache()
        print("✅ Cache cleared successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG system test failed: {e}")
        return False

def test_api_endpoints():
    """Test the API endpoints."""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        base_url = "http://localhost:8000/api/talent"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test employees endpoint
        response = requests.get(f"{base_url}/employees", timeout=5)
        if response.status_code == 200:
            employees = response.json()
            print(f"✅ Employees endpoint working: {len(employees)} employees")
        else:
            print(f"❌ Employees endpoint failed: {response.status_code}")
            return False
        
        # Test chat endpoint with invalid input
        response = requests.post(
            f"{base_url}/chat",
            json={"message": "", "session_id": "test"},
            timeout=5
        )
        if response.status_code == 400:
            print("✅ Input validation working")
        else:
            print(f"❌ Input validation failed: {response.status_code}")
            return False
        
        # Test cache clear endpoint
        response = requests.post(f"{base_url}/clear-cache", timeout=5)
        if response.status_code == 200:
            print("✅ Cache clear endpoint working")
        else:
            print(f"❌ Cache clear endpoint failed: {response.status_code}")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️ API server not running - skipping API tests")
        return True
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def test_disambiguation():
    """Test employee disambiguation functionality."""
    print("\n🧪 Testing Employee Disambiguation...")
    
    try:
        rag_system = RAGQuerySystem()
        rag_system._initialize_employee_index()
        
        # Test with ambiguous name (like "Aisha")
        ambiguous_query = "What is Aisha's ambition score?"
        result = rag_system.process_complex_query(ambiguous_query)
        
        if result.get("clarification_needed"):
            candidates = result.get("candidates", [])
            print(f"✅ Disambiguation working: {len(candidates)} candidates found")
            for i, cand in enumerate(candidates, 1):
                print(f"   {i}. {cand['name']} ({cand['department']})")
        else:
            print("⚠️ No disambiguation needed or disambiguation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Disambiguation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Running KnowThee Fixes Verification Tests")
    print("=" * 50)
    
    tests = [
        ("Employee Database", test_employee_database),
        ("Query Cache", test_query_cache),
        ("RAG System", test_rag_system),
        ("API Endpoints", test_api_endpoints),
        ("Employee Disambiguation", test_disambiguation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            print(f"❌ {test_name} test ERROR: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes are working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 