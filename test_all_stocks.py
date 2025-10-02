#!/usr/bin/env python3
"""
Test script to verify all major Russian stocks classification
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

async def test_stock_classification():
    """Test classification of major Russian stocks"""
    
    print("🔍 Testing major Russian stocks classification...")
    print("=" * 60)
    
    # Major Russian stocks to test
    test_stocks = [
        "GAZP", "SBER", "LKOH", "ROSN", "NVTK", "MAGN", "YNDX", "TCSG", "VKCO", "AFLT",
        "ROSB", "MOEX", "RUAL", "NLMK", "CHMF", "MTSS", "PHOR", "RSTI", "SBERP", "TATN",
        "SNGS", "SNGSP", "GMKN", "ALRS", "POLY", "HYDR", "IRAO", "FEES", "MVID", "OZON"
    ]
    
    results = {}
    
    for ticker in test_stocks:
        print(f"\n📋 Testing {ticker}...")
        print("-" * 30)
        
        try:
            snapshots = await market_aggregator.get_snapshot_for(ticker)
            
            if not snapshots:
                print(f"❌ No data found for {ticker}")
                results[ticker] = "NO_DATA"
                continue
                
            snapshot = snapshots[0]
            
            print(f"   Name: {snapshot.name}")
            print(f"   Ticker: {snapshot.ticker}")
            print(f"   Security Type: {snapshot.security_type}")
            print(f"   Provider: {snapshot.provider}")
            print(f"   Last Price: {snapshot.last_price}")
            
            # Check if it's correctly classified as share
            if snapshot.security_type == "share":
                print("✅ CORRECTLY classified as SHARE")
                results[ticker] = "CORRECT"
            else:
                print(f"❌ INCORRECTLY classified as {snapshot.security_type} (should be 'share')")
                results[ticker] = "INCORRECT"
                
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            results[ticker] = "ERROR"
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 60)
    correct = sum(1 for r in results.values() if r == "CORRECT")
    incorrect = sum(1 for r in results.values() if r == "INCORRECT")
    errors = sum(1 for r in results.values() if r == "ERROR")
    no_data = sum(1 for r in results.values() if r == "NO_DATA")
    
    print(f"✅ Correctly classified: {correct}")
    print(f"❌ Incorrectly classified: {incorrect}")
    print(f"⚠️  Errors: {errors}")
    print(f"❓ No data: {no_data}")
    print(f"📈 Success rate: {correct}/{len(test_stocks)} ({correct/len(test_stocks)*100:.1f}%)")
    
    if incorrect > 0:
        print(f"\n❌ Incorrectly classified stocks:")
        for ticker, result in results.items():
            if result == "INCORRECT":
                print(f"   - {ticker}")

async def main():
    """Main test function"""
    print("🚀 Starting Major Russian Stocks Classification Test")
    print("=" * 60)
    
    await test_stock_classification()
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
