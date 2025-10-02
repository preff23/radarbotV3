#!/usr/bin/env python3
"""
Test server debug script
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.core.db import DatabaseManager

def test_server_debug():
    """Test server debug"""
    
    print("🔍 Testing server debug...")
    print("=" * 50)
    
    try:
        db_manager = DatabaseManager()
        summary = db_manager.get_user_portfolio_summary(1)
        
        print('Portfolio summary:')
        print(f'  Accounts: {len(summary["accounts"])}')
        print(f'  Holdings: {len(summary["holdings"])}')
        print(f'  Cash: {len(summary["cash_positions"])}')
        
        print('Holdings:')
        for h in summary["holdings"][:5]:
            print(f'  - {h.get("ticker", "N/A")}: {h.get("security_type", "N/A")}')
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_debug()
