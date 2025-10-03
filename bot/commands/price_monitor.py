#!/usr/bin/env python3
"""
CLI command for price monitoring
"""

import asyncio
import argparse
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bot.services.price_monitor import price_monitor
from bot.services.notification_service import initialize_notification_service
from bot.services.scheduler import scheduler
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

async def run_monitoring_once():
    """Run price monitoring once"""
    logger.info("Running price monitoring once...")
    
    try:
        changes = await price_monitor.check_price_changes()
        
        if changes:
            logger.info(f"Found {len(changes)} significant price changes:")
            for change in changes:
                logger.info(f"  - {change.ticker} ({change.name}): {change.change_pct:.2f}%")
        else:
            logger.info("No significant price changes detected")
        
        return len(changes)
        
    except Exception as e:
        logger.error(f"Error in price monitoring: {e}")
        return 0

async def start_scheduler():
    """Start the price monitoring scheduler"""
    logger.info("Starting price monitoring scheduler...")
    
    try:
        await scheduler.start()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping scheduler...")
        await scheduler.stop()
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")

async def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Price monitoring CLI")
    parser.add_argument("--once", action="store_true", help="Run monitoring once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (continuous monitoring)")
    parser.add_argument("--bot-token", help="Telegram bot token for notifications")
    parser.add_argument("--threshold", type=float, default=0.01, help="Price change threshold in percent")  
    
    args = parser.parse_args()
    
    # Initialize notification service if bot token provided
    if args.bot_token:
        initialize_notification_service(args.bot_token)
        logger.info("Notification service initialized")
    
    # Set price change threshold
    price_monitor.change_threshold = args.threshold
    logger.info(f"Price change threshold set to {args.threshold}%")
    
    if args.once:
        # Run once
        changes_count = await run_monitoring_once()
        sys.exit(0 if changes_count == 0 else 1)
    elif args.daemon:
        # Run as daemon
        await start_scheduler()
    else:
        # Default: run once
        changes_count = await run_monitoring_once()
        sys.exit(0 if changes_count == 0 else 1)

if __name__ == "__main__":
    asyncio.run(main())
