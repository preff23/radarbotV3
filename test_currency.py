#!/usr/bin/env python3
"""
Test currency rates parsing from MOEX
"""

import requests
import json

def test_currency_rates():
    """Test currency rates from MOEX"""
    
    print("🔍 Testing Currency Rates from MOEX...")
    print("=" * 50)
    
    try:
        # Test USD/RUB
        print("📊 Testing USD/RUB...")
        usd_response = requests.get("https://iss.moex.com/iss/engines/currency/markets/selt/boards/CETS/securities/USD000UTSTOM.json", timeout=10)
        
        if usd_response.status_code == 200:
            usd_data = usd_response.json()
            print(f"✅ USD Response status: {usd_response.status_code}")
            print(f"📋 USD Data keys: {list(usd_data.keys())}")
            
            if usd_data.get('marketdata', {}).get('data'):
                usd_data_row = usd_data['marketdata']['data'][0]
                print(f"📊 USD Data row: {usd_data_row}")
                print(f"📊 USD Data row length: {len(usd_data_row)}")
                
                # Try different columns for the rate
                for i, value in enumerate(usd_data_row):
                    if value and isinstance(value, (int, float)) and value > 10:  # Reasonable rate
                        print(f"💰 Potential rate at column {i}: {value}")
                
                # Look for the last price (usually near the end)
                usd_rate = None
                for i in range(len(usd_data_row) - 1, -1, -1):
                    if usd_data_row[i] and isinstance(usd_data_row[i], (int, float)) and usd_data_row[i] > 10:
                        usd_rate = usd_data_row[i]
                        print(f"💰 USD/RUB Rate found at column {i}: {usd_rate}")
                        break
            else:
                print("❌ No USD market data found")
        else:
            print(f"❌ USD Response status: {usd_response.status_code}")
        
        print("\n" + "-" * 30 + "\n")
        
        # Test EUR/RUB
        print("📊 Testing EUR/RUB...")
        eur_response = requests.get("https://iss.moex.com/iss/engines/currency/markets/selt/boards/CETS/securities/EUR000UTSTOM.json", timeout=10)
        
        if eur_response.status_code == 200:
            eur_data = eur_response.json()
            print(f"✅ EUR Response status: {eur_response.status_code}")
            print(f"📋 EUR Data keys: {list(eur_data.keys())}")
            
            if eur_data.get('marketdata', {}).get('data'):
                eur_data_row = eur_data['marketdata']['data'][0]
                print(f"📊 EUR Data row: {eur_data_row}")
                eur_rate = eur_data_row[4] if len(eur_data_row) > 4 else None
                print(f"💰 EUR/RUB Rate: {eur_rate}")
            else:
                print("❌ No EUR market data found")
        else:
            print(f"❌ EUR Response status: {eur_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Currency testing completed!")

if __name__ == "__main__":
    test_currency_rates()
