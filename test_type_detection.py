#!/usr/bin/env python3
"""
Test script to verify improved type detection based on source data
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

async def test_type_detection():
    """Test type detection for various securities"""
    
    print("🔍 Testing improved type detection...")
    print("=" * 60)
    
    # Test different types of securities
    test_securities = [
        # Known stocks
        ("SBER", "share"),
        ("GAZP", "share"), 
        ("LKOH", "share"),
        ("ROSN", "share"),
        ("NVTK", "share"),
        ("MAGN", "share"),
        ("YNDX", "share"),
        ("VKCO", "share"),
        ("AFLT", "share"),
        ("ROSB", "share"),
        ("MOEX", "share"),
        ("RUAL", "share"),
        ("NLMK", "share"),
        ("CHMF", "share"),
        ("MTSS", "share"),
        ("PHOR", "share"),
        ("TATN", "share"),
        ("SNGS", "share"),
        ("SNGSP", "share"),
        ("GMKN", "share"),
        ("ALRS", "share"),
        ("POLY", "share"),
        ("HYDR", "share"),
        ("IRAO", "share"),
        ("FEES", "share"),
        ("MVID", "share"),
        ("OZON", "share"),
        
        # Known bonds
        ("RU000A10B2M3", "bond"),
        ("RU000A10ATB6", "bond"),
        ("RU000A105SK4", "bond"),
        ("RU000A107GU4", "bond"),
        ("RU000A1082K7", "bond"),
        ("RU000A10C8H9", "bond"),
        ("RU000A10B4T4", "bond"),
        ("RU000A108C17", "bond"),
        ("RU000A10ANT1", "bond"),
        ("RU000A109NM3", "bond"),
        ("RU000A10C9Z9", "bond"),
        ("RU000A1014L8", "bond"),
        ("RU000A10BRN3", "bond"),
        ("RU000A0JXE06", "bond"),
        ("RU000A10C758", "bond"),
        
        # Funds
        ("RU000A0JP799", "fund"),
    ]
    
    results = {}
    
    for ticker, expected_type in test_securities:
        print(f"\n📋 Testing {ticker} (expected: {expected_type})...")
        print("-" * 40)
        
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
            
            # Check if it's correctly classified
            if snapshot.security_type == expected_type:
                print(f"✅ CORRECTLY classified as {snapshot.security_type}")
                results[ticker] = "CORRECT"
            else:
                print(f"❌ INCORRECTLY classified as {snapshot.security_type} (expected: {expected_type})")
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
    print(f"📈 Success rate: {correct}/{len(test_securities)} ({correct/len(test_securities)*100:.1f}%)")
    
    if incorrect > 0:
        print(f"\n❌ Incorrectly classified securities:")
        for ticker, result in results.items():
            if result == "INCORRECT":
                print(f"   - {ticker}")

async def main():
    """Main test function"""
    print("🚀 Starting Improved Type Detection Test")
    print("=" * 60)
    
    await test_type_detection()
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
