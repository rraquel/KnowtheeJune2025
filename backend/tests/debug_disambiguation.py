#!/usr/bin/env python3

import requests
import json
import sys
import os

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import BACKEND_API_URL

def test_disambiguation():
    """Test the disambiguation logic."""
    
    # Test 1: Clear cache first
    print("1. Clearing cache...")
    response = requests.post(f"{BACKEND_API_URL}/clear-cache")
    print(f"Cache clear response: {response.json()}")
    
    # Test 2: Send ambiguous query
    print("\n2. Sending ambiguous query...")
    query_data = {
        "message": "what is the ambition score of Aisha",
        "session_id": "debug_session"
    }
    
    response = requests.post(
        f"{BACKEND_API_URL}/chat",
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response: {result['response']}")
        
        if result.get("clarification_needed"):
            print("✅ SUCCESS: Disambiguation working!")
            candidates = result.get("candidates", [])
            print(f"Found {len(candidates)} candidates")
        else:
            print("❌ FAILURE: Expected disambiguation but got direct answer")
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_disambiguation() 