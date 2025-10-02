#!/usr/bin/env python3
"""
Debug script to investigate CHMF classification issue
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.providers.aggregator import market_aggregator
from bot.providers.moex_iss.client import MOEXISSClient
from bot.providers.tbank_rest import TBankRestClient
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def debug_chmf():
    """Debug CHMF classification"""
    
    print("🔍 Debugging CHMF (Северсталь) classification...")
    print("=" * 60)
    
    # Test with aggregator
    print("1. Testing with MarketDataAggregator...")
    print("-" * 40)
    
    try:
        snapshots = await market_aggregator.get_snapshot_for("CHMF")
        
        if not snapshots:
            print("❌ No data found for CHMF")
        else:
            snapshot = snapshots[0]
            print(f"   Name: {snapshot.name}")
            print(f"   Ticker: {snapshot.ticker}")
            print(f"   Security Type: {snapshot.security_type}")
            print(f"   Provider: {snapshot.provider}")
            print(f"   Last Price: {snapshot.last_price}")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test MOEX directly
    print("\n2. Testing MOEX directly...")
    print("-" * 40)
    
    moex_client = MOEXISSClient()
    
    try:
        search_results = await moex_client.search_securities("CHMF")
        print(f"   Search results: {len(search_results)}")
        
        if search_results:
            for i, result in enumerate(search_results[:3]):
                print(f"   Result {i+1}:")
                print(f"     Name: {result.name}")
                print(f"     Shortname: {result.shortname}")
                print(f"     Type: {result.type}")
                print(f"     Secid: {result.secid}")
                print(f"     ISIN: {result.isin}")
                print(f"     Board: {result.board}")
                
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test T-Bank directly
    print("\n3. Testing T-Bank directly...")
    print("-" * 40)
    
    tbank_client = TBankRestClient()
    
    try:
        search_results = await tbank_client.find_instrument("CHMF")
        print(f"   Search results: {len(search_results)}")
        
        if search_results:
            for i, result in enumerate(search_results[:3]):
                print(f"   Result {i+1}:")
                print(f"     Name: {result.name}")
                print(f"     Ticker: {result.ticker}")
                print(f"     Type: {result.instrument_type}")
                print(f"     FIGI: {result.figi}")
                print(f"     ISIN: {result.isin}")
                print(f"     Currency: {result.currency}")
                
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test with different queries
    print("\n4. Testing with different queries...")
    print("-" * 40)
    
    queries = ["CHMF", "СЕВЕРСТАЛЬ", "Северсталь", "CHH4"]
    
    for query in queries:
        print(f"\n   Testing '{query}':")
        try:
            snapshots = await market_aggregator.get_snapshot_for(query)
            if snapshots:
                snapshot = snapshots[0]
                print(f"     -> {snapshot.name} ({snapshot.ticker}) - {snapshot.security_type}")
            else:
                print(f"     -> No data found")
        except Exception as e:
            print(f"     -> Error: {e}")

async def main():
    """Main debug function"""
    print("🚀 Starting CHMF Debug")
    print("=" * 60)
    
    await debug_chmf()
    
    print("\n🏁 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main())
