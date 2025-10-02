#!/usr/bin/env python3
"""
Test API debug script
"""

import requests
import json

def test_api_debug():
    """Test API debug"""
    
    print("🔍 Testing API debug...")
    print("=" * 50)
    
    # Test portfolio API
    print("1. Testing portfolio API...")
    portfolio_url = "http://130.193.52.12:8000/api/portfolio"
    portfolio_params = {"phone": "+79151731545"}
    
    try:
        response = requests.get(portfolio_url, params=portfolio_params, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            
            accounts = data.get('accounts', [])
            print(f"   Accounts: {len(accounts)}")
            
            if accounts:
                account = accounts[0]
                print(f"   Account keys: {list(account.keys())}")
                holdings = account.get('holdings', [])
                print(f"   Holdings: {len(holdings)}")
                
                for h in holdings[:3]:
                    print(f"   - {h.get('ticker', 'N/A')}: {h.get('security_type', 'N/A')}")
            else:
                print("   No accounts found")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_api_debug()
