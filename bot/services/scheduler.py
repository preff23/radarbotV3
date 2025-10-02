#!/usr/bin/env python3
"""
Scheduler service for periodic price monitoring
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional

from bot.services.price_monitor import price_monitor
from bot.services.notification_service import notification_service
from bot.core.logging import get_logger

logger = get_logger(__name__)

class PriceMonitoringScheduler:
    """Scheduler for periodic price monitoring"""
    
    def __init__(self, check_interval_minutes: int = 60):
        """
        Initialize scheduler
        
        Args:
            check_interval_minutes: Interval between price checks in minutes (default: 60)
        """
        self.check_interval_minutes = check_interval_minutes
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the price monitoring scheduler"""
        if self.is_running:
            logger.warning("Price monitoring scheduler is already running")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Price monitoring scheduler started (interval: {self.check_interval_minutes} minutes)")
    
    async def stop(self):
        """Stop the price monitoring scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Price monitoring scheduler stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                logger.info("Starting scheduled price monitoring...")
                
                # Check for price changes
                changes = await price_monitor.check_price_changes()
                
                if changes:
                    logger.info(f"Found {len(changes)} significant price changes")
                    
                    # Send notifications
                    if notification_service:
                        sent_count = await notification_service.send_bulk_notifications(changes)
                        logger.info(f"Sent {sent_count} notifications")
                    else:
                        logger.warning("Notification service not initialized")
                else:
                    logger.info("No significant price changes detected")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval_minutes * 60)
                
            except asyncio.CancelledError:
                logger.info("Price monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in price monitoring loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(60)
    
    async def run_once(self):
        """Run price monitoring once (for testing or manual execution)"""
        logger.info("Running price monitoring once...")
        
        try:
            changes = await price_monitor.check_price_changes()
            
            if changes:
                logger.info(f"Found {len(changes)} significant price changes")
                
                if notification_service:
                    sent_count = await notification_service.send_bulk_notifications(changes)
                    logger.info(f"Sent {sent_count} notifications")
                    return sent_count
                else:
                    logger.warning("Notification service not initialized")
                    return 0
            else:
                logger.info("No significant price changes detected")
                return 0
                
        except Exception as e:
            logger.error(f"Error in one-time price monitoring: {e}")
            return 0

# Global scheduler instance
scheduler = PriceMonitoringScheduler(check_interval_minutes=60)  # Check every hour
