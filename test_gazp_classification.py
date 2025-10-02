#!/usr/bin/env python3
"""
Test script to verify GAZP classification and price loading
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

async def test_gazp_classification():
    """Test GAZP classification and price loading"""
    
    print("🔍 Testing GAZP classification and price loading...")
    print("=" * 60)
    
    # Test queries for GAZP
    test_queries = [
        "GAZP",
        "ГАЗПРОМ",
        "ГАЗПРОМ ПАО",
        "RU0007661625"  # GAZP ISIN
    ]
    
    for query in test_queries:
        print(f"\n📋 Testing query: '{query}'")
        print("-" * 40)
        
        try:
            # Get snapshot from aggregator
            snapshots = await market_aggregator.get_snapshot_for(query)
            
            if not snapshots:
                print("❌ No snapshots found")
                continue
                
            snapshot = snapshots[0]
            
            print(f"✅ Found snapshot:")
            print(f"   Name: {snapshot.name}")
            print(f"   Ticker: {snapshot.ticker}")
            print(f"   ISIN: {snapshot.isin}")
            print(f"   Security Type: {snapshot.security_type}")
            print(f"   Provider: {snapshot.provider}")
            print(f"   Last Price: {snapshot.last_price}")
            print(f"   Change Day %: {snapshot.change_day_pct}")
            print(f"   Currency: {snapshot.currency}")
            print(f"   Trading Status: {snapshot.trading_status}")
            
            # Check if it's correctly classified as share
            if snapshot.security_type == "share":
                print("✅ CORRECTLY classified as SHARE")
            else:
                print(f"❌ INCORRECTLY classified as {snapshot.security_type} (should be 'share')")
            
            # Check if price is loaded
            if snapshot.last_price and snapshot.last_price > 0:
                print("✅ Price data loaded successfully")
            else:
                print("❌ Price data NOT loaded")
                
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")
            logger.error(f"Error testing '{query}': {e}")

async def test_moex_search():
    """Test MOEX search directly"""
    
    print("\n🔍 Testing MOEX search directly...")
    print("=" * 60)
    
    try:
        from bot.providers.moex_bridge import moex_bridge
        
        # Test MOEX search
        resolved = await moex_bridge.resolve_by_name("GAZP")
        
        if resolved:
            print("✅ MOEX resolved GAZP:")
            print(f"   SecID: {resolved.get('secid')}")
            print(f"   Type: {resolved.get('type')}")
            print(f"   Shortname: {resolved.get('shortname')}")
            print(f"   Name: {resolved.get('name')}")
            print(f"   ISIN: {resolved.get('isin')}")
        else:
            print("❌ MOEX could not resolve GAZP")
            
    except Exception as e:
        print(f"❌ Error in MOEX search: {e}")
        logger.error(f"Error in MOEX search: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting GAZP Classification Tests")
    print("=" * 60)
    
    await test_moex_search()
    await test_gazp_classification()
    
    print("\n🏁 Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
