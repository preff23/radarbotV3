#!/usr/bin/env python3
"""
Comprehensive test script to check all stocks from T-Bank and MOEX
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

async def test_moex_stocks():
    """Test all stocks from MOEX"""
    
    print("🔍 Testing MOEX stocks...")
    print("=" * 60)
    
    moex_client = MOEXISSClient()
    
    # Test major Russian stocks
    test_stocks = [
        "SBER", "GAZP", "LKOH", "ROSN", "NVTK", "MAGN", "YNDX", "VKCO", "AFLT",
        "ROSB", "MOEX", "RUAL", "NLMK", "CHMF", "MTSS", "PHOR", "TATN", "SNGS",
        "SNGSP", "GMKN", "ALRS", "POLY", "HYDR", "IRAO", "FEES", "MVID", "OZON",
        "PLZL", "QIWI", "DSKY", "FIVE", "LENTA", "MGNT", "MGTSP", "RENI", "RTKM",
        "RTKMP", "SELG", "SELGP", "SMLT", "SMLTP", "TATNP", "TRNFP", "UPRO",
        "UPROP", "VRSB", "VRSBP", "YNDXP", "SBERP", "TATNP", "SNGSP"
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
    
    return results

async def test_tbank_stocks():
    """Test all stocks from T-Bank"""
    
    print("\n🔍 Testing T-Bank stocks...")
    print("=" * 60)
    
    tbank_client = TBankRestClient()
    
    # Test major Russian stocks
    test_stocks = [
        "SBER", "GAZP", "LKOH", "ROSN", "NVTK", "MAGN", "YNDX", "VKCO", "AFLT",
        "ROSB", "MOEX", "RUAL", "NLMK", "CHMF", "MTSS", "PHOR", "TATN", "SNGS",
        "SNGSP", "GMKN", "ALRS", "POLY", "HYDR", "IRAO", "FEES", "MVID", "OZON",
        "PLZL", "QIWI", "DSKY", "FIVE", "LENTA", "MGNT", "MGTSP", "RENI", "RTKM",
        "RTKMP", "SELG", "SELGP", "SMLT", "SMLTP", "TATNP", "TRNFP", "UPRO",
        "UPROP", "VRSB", "VRSBP", "YNDXP", "SBERP", "TATNP", "SNGSP"
    ]
    
    results = {}
    
    for ticker in test_stocks:
        print(f"\n📋 Testing {ticker}...")
        print("-" * 30)
        
        try:
            search_results = await tbank_client.find_instrument(ticker)
            
            if not search_results:
                print(f"❌ No data found for {ticker}")
                results[ticker] = "NO_DATA"
                continue
                
            # Look for stocks (not bonds or futures)
            stocks = [r for r in search_results if r.instrument_type == "share"]
            
            if not stocks:
                print(f"❌ No stocks found for {ticker}")
                results[ticker] = "NO_STOCKS"
                continue
                
            stock = stocks[0]
            print(f"   Name: {stock.name}")
            print(f"   Ticker: {stock.ticker}")
            print(f"   Type: {stock.instrument_type}")
            print(f"   FIGI: {stock.figi}")
            print(f"   ISIN: {stock.isin}")
            
            if stock.instrument_type == "share":
                print("✅ CORRECTLY classified as SHARE")
                results[ticker] = "CORRECT"
            else:
                print(f"❌ INCORRECTLY classified as {stock.instrument_type} (should be 'share')")
                results[ticker] = "INCORRECT"
                
        except Exception as e:
            print(f"❌ Error testing {ticker}: {e}")
            results[ticker] = "ERROR"
    
    return results

async def main():
    """Main test function"""
    print("🚀 Starting Comprehensive Stock Classification Test")
    print("=" * 60)
    
    moex_results = await test_moex_stocks()
    tbank_results = await test_tbank_stocks()
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 60)
    
    print("MOEX Results:")
    correct = sum(1 for r in moex_results.values() if r == "CORRECT")
    incorrect = sum(1 for r in moex_results.values() if r == "INCORRECT")
    errors = sum(1 for r in moex_results.values() if r == "ERROR")
    no_data = sum(1 for r in moex_results.values() if r == "NO_DATA")
    
    print(f"✅ Correctly classified: {correct}")
    print(f"❌ Incorrectly classified: {incorrect}")
    print(f"⚠️  Errors: {errors}")
    print(f"❓ No data: {no_data}")
    print(f"📈 Success rate: {correct}/{len(moex_results)} ({correct/len(moex_results)*100:.1f}%)")
    
    if incorrect > 0:
        print(f"\n❌ Incorrectly classified MOEX stocks:")
        for ticker, result in moex_results.items():
            if result == "INCORRECT":
                print(f"   - {ticker}")
    
    print("\nT-Bank Results:")
    correct = sum(1 for r in tbank_results.values() if r == "CORRECT")
    incorrect = sum(1 for r in tbank_results.values() if r == "INCORRECT")
    errors = sum(1 for r in tbank_results.values() if r == "ERROR")
    no_data = sum(1 for r in tbank_results.values() if r == "NO_DATA")
    
    print(f"✅ Correctly classified: {correct}")
    print(f"❌ Incorrectly classified: {incorrect}")
    print(f"⚠️  Errors: {errors}")
    print(f"❓ No data: {no_data}")
    print(f"📈 Success rate: {correct}/{len(tbank_results)} ({correct/len(tbank_results)*100:.1f}%)")
    
    if incorrect > 0:
        print(f"\n❌ Incorrectly classified T-Bank stocks:")
        for ticker, result in tbank_results.items():
            if result == "INCORRECT":
                print(f"   - {ticker}")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
