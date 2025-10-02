#!/usr/bin/env python3
"""
Test adding CHMF position and verify classification
"""

import requests
import json

def test_add_chmf():
    """Test adding CHMF position"""
    
    print("🔍 Testing CHMF addition and classification...")
    print("=" * 50)
    
    # Add CHMF position directly
    print("1. Adding CHMF position...")
    add_url = "http://130.193.52.12:8000/api/portfolio/position"
    add_params = {"phone": "+79151731545"}
    
    position_data = {
        "account_id": "manual",
        "account_name": "Manual Account", 
        "currency": "RUB",
        "name": "Северсталь (ПАО)ао",
        "ticker": "CHMF",
        "security_type": "share",  # Force as share
        "quantity": 2,
        "quantity_unit": "шт",
        "isin": "RU0009046510"
    }
    
    try:
        response = requests.post(add_url, params=add_params, json=position_data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ CHMF position added successfully")
            
            # Check portfolio
            print("\n2. Checking portfolio...")
            portfolio_url = "http://130.193.52.12:8000/api/portfolio"
            portfolio_params = {"phone": "+79151731545"}
            
            response = requests.get(portfolio_url, params=portfolio_params, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                accounts = data.get('accounts', [])
                
                if accounts:
                    account = accounts[0]
                    holdings = account.get('holdings', [])
                    print(f"   Found {len(holdings)} holdings")
                    
                    # Look for CHMF
                    chmf_holdings = [h for h in holdings if h.get('ticker') == 'CHMF']
                    if chmf_holdings:
                        print("   ✅ CHMF found in portfolio:")
                        for holding in chmf_holdings:
                            print(f"   - {holding.get('name', 'N/A')} ({holding.get('ticker', 'N/A')}) - {holding.get('security_type', 'N/A')}")
                    else:
                        print("   ❌ CHMF not found in portfolio")
                        
                    # Show all holdings
                    print("\n   All holdings:")
                    for holding in holdings:
                        print(f"   - {holding.get('ticker', 'N/A')}: {holding.get('security_type', 'N/A')}")
                else:
                    print("   No accounts found")
            else:
                print(f"   Error: {response.text}")
        else:
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_add_chmf()
