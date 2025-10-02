#!/usr/bin/env python3
"""
Debug script to investigate what data sources return about security types
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.providers.moex_iss.client import MOEXISSClient
from bot.providers.tbank_rest import TBankRestClient
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def debug_moex_data():
    """Debug what MOEX returns for different securities"""
    
    print("🔍 Debugging MOEX data...")
    print("=" * 60)
    
    moex_client = MOEXISSClient()
    
    # Test different types of securities
    test_securities = [
        "SBER",      # Known stock
        "GAZP",      # Known stock  
        "LKOH",      # Known stock
        "ROSN",      # Known stock
        "RU000A10B2M3",  # Bond ISIN
        "RU000A10ATB6",  # Bond ISIN
        "RU000A0JP799",  # Fund ISIN
    ]
    
    for security in test_securities:
        print(f"\n📋 Testing {security}...")
        print("-" * 40)
        
        try:
            # Test search
            search_results = await moex_client.search_securities(security)
            print(f"   Search results: {len(search_results)}")
            
            if search_results:
                for i, result in enumerate(search_results[:2]):  # Show first 2 results
                    print(f"   Result {i+1}:")
                    print(f"     Name: {result.name}")
                    print(f"     Shortname: {result.shortname}")
                    print(f"     Type: {result.type}")
                    print(f"     Secid: {result.secid}")
                    print(f"     ISIN: {result.isin}")
                    print(f"     Board: {result.board}")
                    
                    # Test market data if we have secid
                    secid = result.secid
                    if secid:
                        print(f"     Testing market data for {secid}...")
                        try:
                            market_data = await moex_client.get_security_marketdata(secid)
                            if market_data:
                                print(f"       Market data type: {getattr(market_data, 'type', 'N/A')}")
                                print(f"       Market data name: {getattr(market_data, 'name', 'N/A')}")
                        except Exception as e:
                            print(f"       Market data error: {e}")
                            
        except Exception as e:
            print(f"   Error: {e}")

async def debug_tbank_data():
    """Debug what T-Bank returns for different securities"""
    
    print("\n🔍 Debugging T-Bank data...")
    print("=" * 60)
    
    tbank_client = TBankRestClient()
    
    # Test different types of securities
    test_securities = [
        "SBER",      # Known stock
        "GAZP",      # Known stock
        "LKOH",      # Known stock
        "ROSN",      # Known stock
        "RU000A10B2M3",  # Bond ISIN
        "RU000A10ATB6",  # Bond ISIN
    ]
    
    for security in test_securities:
        print(f"\n📋 Testing {security}...")
        print("-" * 40)
        
        try:
            # Test search
            search_results = await tbank_client.find_instrument(security)
            print(f"   Search results: {len(search_results)}")
            
            if search_results:
                for i, result in enumerate(search_results[:2]):  # Show first 2 results
                    print(f"   Result {i+1}:")
                    print(f"     Name: {result.name}")
                    print(f"     Ticker: {result.ticker}")
                    print(f"     Type: {result.instrument_type}")
                    print(f"     FIGI: {result.figi}")
                    print(f"     ISIN: {result.isin}")
                    print(f"     Currency: {result.currency}")
                    
        except Exception as e:
            print(f"   Error: {e}")

async def main():
    """Main debug function"""
    print("🚀 Starting Data Sources Debug")
    print("=" * 60)
    
    await debug_moex_data()
    await debug_tbank_data()
    
    print("\n🏁 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main())
