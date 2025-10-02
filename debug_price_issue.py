#!/usr/bin/env python3
"""
Debug script to investigate price issues for stocks
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

async def debug_price_issue():
    """Debug price issues for specific stocks"""
    
    print("🔍 Debugging price issues for stocks...")
    print("=" * 60)
    
    # Test stocks with price issues
    test_stocks = [
        {"name": "Сбербанк", "ticker": "SBER", "isin": "RU0009029540"},
        {"name": "Газпром", "ticker": "GAZP", "isin": "RU0007661625"},
        {"name": "Северсталь", "ticker": "CHMF", "isin": "RU0009046510"},
        {"name": "Полюс", "ticker": "PLZL", "isin": "RU000A0JNAA8"},  # This one works
        {"name": "ЛУКОЙЛ", "ticker": "LKOH", "isin": "RU0009024277"}  # This one works
    ]
    
    for stock in test_stocks:
        print(f"\n📋 Debugging {stock['name']} ({stock['ticker']})...")
        print("-" * 50)
        
        try:
            snapshots = await market_aggregator.get_snapshot_for(stock['ticker'])
            
            if not snapshots:
                print(f"❌ No data found for {stock['ticker']}")
                continue
                
            snapshot = snapshots[0]
            
            print(f"   Name: {snapshot.name}")
            print(f"   Ticker: {snapshot.ticker}")
            print(f"   Security Type: {snapshot.security_type}")
            print(f"   Provider: {snapshot.provider}")
            print(f"   Last Price: {snapshot.last_price}")
            print(f"   Currency: {snapshot.currency}")
            print(f"   Change Day %: {snapshot.change_day_pct}")
            print(f"   Trading Status: {snapshot.trading_status}")
            print(f"   Volume: {snapshot.volume}")
            print(f"   Cached At: {snapshot.cached_at}")
            print(f"   Last Update: {snapshot.last_update}")
            
            # Check if price is 0 or None
            if snapshot.last_price is None or snapshot.last_price == 0:
                print("   ⚠️  PRICE ISSUE: last_price is None or 0")
            else:
                print("   ✅ Price looks good")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Main debug function"""
    print("🚀 Starting Price Issue Debug")
    print("=" * 60)
    
    await debug_price_issue()
    
    print("\n🏁 Debug completed!")

if __name__ == "__main__":
    asyncio.run(main())
