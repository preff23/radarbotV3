#!/usr/bin/env python3
"""
Test portfolio analysis with new prompt v13.7.6
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def test_portfolio_analysis():
    """Test portfolio analysis with new prompt"""
    
    print("🔍 Testing Portfolio Analysis with new prompt v13.7.6...")
    print("=" * 60)
    
    analyzer = PortfolioAnalyzer()
    
    # Test with user ID 1 (assuming it exists)
    user_id = 1
    
    try:
        print(f"📊 Running analysis for user {user_id}...")
        
        # Run full analysis
        result = await analyzer.run_analysis(user_id)
        
        print(f"✅ Analysis completed!")
        print(f"   Result type: {type(result)}")
        
        if isinstance(result, dict):
            if "error" in result:
                print(f"   Error: {result['error']}")
                print(f"   Summary: {result.get('summary', 'No summary')}")
            else:
                print(f"   Keys: {list(result.keys())}")
                if "analysis" in result:
                    print(f"   Analysis length: {len(result['analysis'])} characters")
                    print("\n" + "="*60)
                    print("📋 ANALYSIS RESULT:")
                    print("="*60)
                    print(result['analysis'][:2000] + "..." if len(result['analysis']) > 2000 else result['analysis'])
                else:
                    print(f"   Full result: {result}")
        else:
            print(f"   Result: {result}")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Analysis testing completed!")

async def main():
    """Main function"""
    await test_portfolio_analysis()

if __name__ == "__main__":
    asyncio.run(main())
