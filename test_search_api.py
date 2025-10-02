#!/usr/bin/env python3
"""
Test search API script
"""

import requests
import json

def test_search_api():
    """Test search API"""
    
    print("🔍 Testing search API...")
    print("=" * 50)
    
    # Test search for Полюс
    print("1. Testing search for 'Полюс'...")
    search_url = "http://130.193.52.12:8000/api/portfolio/search"
    search_params = {"query": "Полюс", "phone": "+79151731545"}
    
    try:
        response = requests.get(search_url, params=search_params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   Found {len(results)} results")
            
            for i, result in enumerate(results[:3]):
                print(f"   Result {i+1}:")
                print(f"     Name: {result.get('name', 'N/A')}")
                print(f"     Ticker: {result.get('ticker', 'N/A')}")
                print(f"     Security Type: {result.get('security_type', 'N/A')}")
                print(f"     Provider: {result.get('provider', 'N/A')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_search_api()
