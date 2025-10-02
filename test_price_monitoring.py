#!/usr/bin/env python3
"""
Test script for price monitoring system
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.services.price_monitor import price_monitor
from bot.services.notification_service import initialize_notification_service
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def test_price_monitoring():
    """Test the price monitoring system"""
    
    print("🔍 Testing Price Monitoring System...")
    print("=" * 60)
    
    # Test 1: Check price changes
    print("\n1. Testing price change detection...")
    print("-" * 40)
    
    try:
        changes = await price_monitor.check_price_changes()
        print(f"   Found {len(changes)} significant price changes")
        
        for change in changes:
            print(f"   - {change.ticker} ({change.name}): {change.change_pct:.2f}%")
            print(f"     User: {change.user_id}, Type: {change.security_type}")
            print(f"     Price: {change.old_price:.2f} → {change.new_price:.2f}")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Test notification formatting (without sending)
    print("\n2. Testing notification formatting...")
    print("-" * 40)
    
    if changes:
        from bot.services.notification_service import NotificationService
        
        # Create a dummy notification service
        dummy_service = NotificationService("dummy_token")
        
        for change in changes[:2]:  # Test first 2 changes
            message = dummy_service._format_price_change_message(change)
            print(f"   Message for {change.ticker}:")
            print(f"   {message}")
            print()
    
    # Test 3: Test user portfolio prices
    print("\n3. Testing user portfolio prices...")
    print("-" * 40)
    
    try:
        from bot.core.db import db_manager
        
        # Get first user with holdings
        users = db_manager.get_all_users_with_holdings()
        if users:
            user = users[0]
            print(f"   Testing with user {user.id} ({user.phone_number})")
            
            prices = await price_monitor.get_user_portfolio_prices(user.id)
            print(f"   Found prices for {len(prices)} securities:")
            
            for ticker, price in list(prices.items())[:5]:  # Show first 5
                print(f"     {ticker}: {price:.2f} RUB")
        else:
            print("   No users with holdings found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n🏁 Price monitoring test completed!")

async def main():
    """Main test function"""
    print("🚀 Starting Price Monitoring Test")
    print("=" * 60)
    
    await test_price_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
