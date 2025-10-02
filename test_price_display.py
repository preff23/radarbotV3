#!/usr/bin/env python3
"""
Test script to check price display for stocks
"""

import requests
import json

def test_price_display():
    """Test price display for various stocks"""
    
    print("🔍 Testing price display for stocks...")
    print("=" * 60)
    
    # Test stocks that should have prices
    test_stocks = [
        {"name": "Полюс", "ticker": "PLZL", "isin": "RU000A0JNAA8"},
        {"name": "Сбербанк", "ticker": "SBER", "isin": "RU0009029540"},
        {"name": "Газпром", "ticker": "GAZP", "isin": "RU0007661625"},
        {"name": "ЛУКОЙЛ", "ticker": "LKOH", "isin": "RU0009024277"},
        {"name": "Северсталь", "ticker": "CHMF", "isin": "RU0009046510"}
    ]
    
    for stock in test_stocks:
        print(f"\n📋 Testing {stock['name']} ({stock['ticker']})...")
        print("-" * 40)
        
        try:
            # Test search API first
            search_url = "http://130.193.52.12:8000/api/portfolio/search"
            search_params = {"query": stock['ticker'], "phone": "+79151731545"}
            
            search_response = requests.get(search_url, params=search_params, timeout=10)
            print(f"   Search API status: {search_response.status_code}")
            
            if search_response.status_code == 200:
                search_data = search_response.json()
                results = search_data.get('results', [])
                if results:
                    result = results[0]
                    print(f"   Found: {result.get('name', 'N/A')}")
                    print(f"   Ticker: {result.get('ticker', 'N/A')}")
                    print(f"   Security Type: {result.get('security_type', 'N/A')}")
                    print(f"   Provider: {result.get('provider', 'N/A')}")
                    
                    # Test details API
                    details_url = f"http://130.193.52.12:8000/api/portfolio/security/{stock['isin']}/details"
                    details_params = {"phone": "+79151731545"}
                    
                    details_response = requests.get(details_url, params=details_params, timeout=10)
                    print(f"   Details API status: {details_response.status_code}")
                    
                    if details_response.status_code == 200:
                        details_data = details_response.json()
                        price_info = details_data.get('price', {})
                        print(f"   Price: {price_info.get('last', 'N/A')}")
                        print(f"   Currency: {price_info.get('currency', 'N/A')}")
                        print(f"   Change: {price_info.get('change_day_pct', 'N/A')}%")
                        print(f"   Security Type: {details_data.get('security_type', 'N/A')}")
                    else:
                        print(f"   Details API error: {details_response.text}")
                else:
                    print("   No search results found")
            else:
                print(f"   Search API error: {search_response.text}")
                
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_price_display()
