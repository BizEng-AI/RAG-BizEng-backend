"""
Test Azure Content Filter Fix
Tests that previously problematic queries now work
"""

import requests
import json

BASE_URL = "http://localhost:8020"

def test_ask_endpoint(query, description):
    """Test the /ask endpoint with a query"""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/ask",
            json={"query": query, "k": 5},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "")
            sources = data.get("sources", [])
            
            print(f"✅ SUCCESS")
            print(f"Answer: {answer[:200]}...")
            print(f"Sources: {len(sources)} sources found")
            return True
        else:
            print(f"❌ FAILED - Status {response.status_code}")
            print(f"Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    print("="*60)
    print("AZURE CONTENT FILTER FIX - TEST SUITE")
    print("="*60)
    
    # Test cases that previously failed
    test_cases = [
        ("yo", "Casual greeting (was blocked)"),
        ("sup", "Informal greeting (was blocked)"),
        ("hey there", "Casual greeting variation"),
        ("What is business English?", "Normal question (should work)"),
        ("How do I write a professional email?", "Professional question"),
        ("u should use formal language", "Informal text speak"),
    ]
    
    results = []
    for query, description in test_cases:
        success = test_ask_endpoint(query, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {description}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Content filter fix is working!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check server logs for details.")


if __name__ == "__main__":
    main()

