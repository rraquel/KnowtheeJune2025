#!/usr/bin/env python3

import requests
import json

def test_api_flow():
    """Test the complete API flow to debug the Aisha issue."""
    
    # Test 1: Clear cache first
    print("1. Clearing cache...")
    response = requests.post("http://localhost:8000/api/talent/clear-cache")
    print(f"Cache clear response: {response.json()}")
    
    # Test 2: Send Aisha query
    print("\n2. Sending Aisha query...")
    query_data = {
        "message": "what is the ambition score of Aisha",
        "session_id": "debug_session"
    }
    
    response = requests.post(
        "http://localhost:8000/api/talent/chat",
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result['response']}")
        
        # Test 3: Check if the response contains clarification
        if "multiple employees" in result['response'].lower() or "please specify" in result['response'].lower():
            print("✅ SUCCESS: Clarification logic is working!")
        else:
            print("❌ FAILURE: Clarification logic is NOT working!")
            print("Expected clarification message but got direct answer.")
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_api_flow() 