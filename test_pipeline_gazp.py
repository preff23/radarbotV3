#!/usr/bin/env python3
"""
Test script to verify GAZP classification in pipeline
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.pipeline.portfolio_ingest_pipeline import PortfolioIngestPipeline
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def test_pipeline_gazp():
    """Test GAZP classification in pipeline"""
    
    print("🔍 Testing GAZP classification in pipeline...")
    print("=" * 60)
    
    # Create test position data
    test_position = {
        "raw_name": "ГАЗПРОМ ПАО АО",
        "raw_ticker": "GAZP",
        "raw_isin": "",
        "raw_type": "",  # Empty type - this is the problem
        "raw_quantity": 1.0,
        "raw_quantity_unit": "шт",
        "confidence": 0.9,
        "hints": {},
        "normalized_name": "ГАЗПРОМ ПАО АО",
        "normalized_key": "GAZP",
        "ticker": "GAZP",
        "isin": "",
        "security_type": None,  # Will be determined by pipeline
        "emitter_guess": None,
        "detected_keywords": [],
        "series_fix_applied": False
    }
    
    print(f"📋 Test position: {test_position['raw_name']} ({test_position['ticker']})")
    print(f"   Raw type: '{test_position['raw_type']}'")
    print(f"   Security type before: {test_position['security_type']}")
    
    # Test normalization step
    pipeline = PortfolioIngestPipeline()
    
    # Simulate the normalization logic
    from bot.utils.normalize import normalize_security_type
    
    normalized_type = normalize_security_type(test_position['raw_type'])
    print(f"   Normalized type from raw_type: {normalized_type}")
    
    # Apply our fix
    if not normalized_type and test_position['ticker']:
        ticker_upper = test_position['ticker'].upper()
        if ticker_upper in ["GAZP", "SBER", "LKOH", "ROSN", "NVTK", "MAGN", "YNDX", "TCSG", "VKCO", "AFLT"]:
            normalized_type = "акция"
            print(f"   ✅ Determined {ticker_upper} as акция based on ticker")
        elif ticker_upper and len(ticker_upper) > 3 and ticker_upper.startswith("RU"):
            normalized_type = "облигация"
            print(f"   ✅ Determined {ticker_upper} as облигация based on ticker pattern")
    
    test_position['security_type'] = normalized_type
    print(f"   Final security type: {test_position['security_type']}")
    
    # Test resolution step
    print(f"\n🔍 Testing resolution step...")
    print("-" * 40)
    
    try:
        resolved_position = await pipeline._resolve_single_security(test_position)
        
        if resolved_position:
            print("✅ Position resolved successfully:")
            print(f"   Name: {resolved_position.get('name')}")
            print(f"   Ticker: {resolved_position.get('ticker')}")
            print(f"   ISIN: {resolved_position.get('isin')}")
            print(f"   Security Type: {resolved_position.get('security_type')}")
            print(f"   Provider: {resolved_position.get('provider')}")
            print(f"   Last Price: {resolved_position.get('provider_data', {}).get('last_price')}")
            print(f"   Change Day %: {resolved_position.get('provider_data', {}).get('change_day_pct')}")
            print(f"   Currency: {resolved_position.get('provider_data', {}).get('currency')}")
            
            # Check if it's correctly classified as share
            if resolved_position.get('security_type') == 'share':
                print("✅ CORRECTLY classified as SHARE")
            else:
                print(f"❌ INCORRECTLY classified as {resolved_position.get('security_type')} (should be 'share')")
            
            # Check if price is loaded
            if resolved_position.get('provider_data', {}).get('last_price') and resolved_position.get('provider_data', {}).get('last_price') > 0:
                print("✅ Price data loaded successfully")
            else:
                print("❌ Price data NOT loaded")
        else:
            print("❌ Position resolution failed")
            
    except Exception as e:
        print(f"❌ Error in resolution: {e}")
        logger.error(f"Error in resolution: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Pipeline GAZP Classification Test")
    print("=" * 60)
    
    await test_pipeline_gazp()
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(main())
