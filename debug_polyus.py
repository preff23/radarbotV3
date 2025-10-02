#!/usr/bin/env python3
"""
Debug script to investigate PLZL (Полюс) classification issue
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.providers.aggregator import market_aggregator
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def debug_polyus():
    """Debug PLZL (Полюс) classification"""
    
    print("🔍 Debugging PLZL (Полюс) classification...")
    print("=" * 60)
    
    # Test with aggregator
    print("1. Testing with MarketDataAggregator...")
    print("-" * 40)
    
    queries = ["PLZL", "Полюс", "POLY", "ПОЛЮС"]
    
    for query in queries:
        print(f"\n   Testing '{query}':")
        try:
            snapshots = await market_aggregator.get_snapshot_for(query)
            
            if not snapshots:
                print(f"     ❌ No data found for {query}")
            else:
                snapshot = snapshots[0]
                print(f"     ✅ Found: {snapshot.name}")
                print(f"     Ticker: {snapshot.ticker}")
                print(f"     Security Type: {snapshot.security_type}")
                print(f"     Provider: {snapshot.provider}")
                print(f"     Last Price: {snapshot.last_price}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")

async def main():
    """Main debug function"""
    print("🚀 Starting PLZL Debug")
    print("=" * 60)
    
    await debug_polyus()
    
    print("\n🏁 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main())
