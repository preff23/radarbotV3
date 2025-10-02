#!/usr/bin/env python3
"""
Test script to verify GAZP classification via API
"""

import requests
import json

def test_gazp_api():
    """Test GAZP classification via API"""
    
    print("🔍 Testing GAZP classification via API...")
    print("=" * 60)
    
    # Test search first
    print("📋 Testing search API...")
    search_url = "http://130.193.52.12:8000/api/portfolio/search"
    search_params = {
        "query": "GAZP",
        "phone": "+79151731545"
    }
    
    try:
        response = requests.get(search_url, params=search_params, verify=False, timeout=10)
        print(f"   Search status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   Found {len(results)} results")
            
            for i, result in enumerate(results[:3]):  # Show first 3 results
                print(f"   {i+1}. {result.get('name')} ({result.get('ticker')}) - {result.get('security_type')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test adding position
    print(f"\n📋 Testing add position API...")
    add_url = "http://130.193.52.12:8000/api/portfolio/position"
    add_params = {
        "phone": "+79151731545"
    }
    
    position_data = {
        "account_id": "manual",
        "account_name": "manual",
        "currency": "RUB",
        "name": "ГАЗПРОМ ПАО АО",
        "ticker": "GAZP",
        "security_type": "акция",  # Explicitly set as акция
        "quantity": 1.0,
        "quantity_unit": "шт",
        "isin": ""
    }
    
    try:
        response = requests.post(add_url, params=add_params, json=position_data, verify=False, timeout=10)
        print(f"   Add position status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('message', 'Position added')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test portfolio retrieval
    print(f"\n📋 Testing portfolio retrieval...")
    portfolio_url = "http://130.193.52.12:8000/api/portfolio"
    portfolio_params = {
        "phone": "+79151731545"
    }
    
    try:
        response = requests.get(portfolio_url, params=portfolio_params, verify=False, timeout=10)
        print(f"   Portfolio status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            accounts = data.get('accounts', [])
            if accounts:
                account = accounts[0]
                holdings = account.get('holdings', [])
                print(f"   Found {len(holdings)} holdings")
                
                for holding in holdings:
                    if holding.get('ticker') == 'GAZP':
                        print(f"   GAZP holding:")
                        print(f"     Name: {holding.get('name')}")
                        print(f"     Ticker: {holding.get('ticker')}")
                        print(f"     Security Type: {holding.get('security_type')}")
                        print(f"     Price: {holding.get('price')}")
                        print(f"     Market Value: {holding.get('market_value')}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_gazp_api()
