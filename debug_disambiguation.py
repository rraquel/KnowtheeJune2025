#!/usr/bin/env python3

import requests
import json

def debug_disambiguation():
    """Debug the name disambiguation process."""
    
    print("=== DEBUGGING NAME DISAMBIGUATION ===")
    
    # Test 1: Clear cache
    print("\n1. Clearing cache...")
    response = requests.post("http://localhost:8000/api/talent/clear-cache")
    print(f"Cache clear response: {response.json()}")
    
    # Test 2: Send Aisha query
    print("\n2. Sending Aisha query...")
    query_data = {
        "message": "what is Aisha's ambition score?",
        "session_id": "debug_session"
    }
    
    response = requests.post(
        "http://localhost:8000/api/talent/chat",
        json=query_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Full API response: {json.dumps(result, indent=2)}")
        
        # Check if clarification is needed
        if result.get("clarification_needed"):
            print("✅ SUCCESS: Clarification logic is working!")
            candidates = result.get("candidates", [])
            print(f"Found {len(candidates)} candidates:")
            for cand in candidates:
                print(f"  - {cand.get('name')} ({cand.get('department')})")
        else:
            print("❌ FAILURE: Clarification logic is NOT working!")
            print("Expected clarification_needed=True but got:", result.get("clarification_needed"))
    else:
        print(f"❌ API Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_disambiguation() 