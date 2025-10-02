#!/usr/bin/env python3
"""
Notification service for sending price change alerts to Telegram
"""

import logging
from datetime import datetime
from typing import List, Optional
from telegram import Bot
from telegram.error import TelegramError

from bot.services.price_monitor import PriceChange
from bot.core.logging import get_logger

logger = get_logger(__name__)

class NotificationService:
    """Service for sending price change notifications to Telegram"""
    
    def __init__(self, bot_token: str):
        """
        Initialize notification service
        
        Args:
            bot_token: Telegram bot token
        """
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
    
    async def send_price_change_notification(self, change: PriceChange, user_telegram_id: int) -> bool:
        """
        Send price change notification to user
        
        Args:
            change: PriceChange object
            user_telegram_id: User's Telegram ID
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Format the message
            message = self._format_price_change_message(change)
            
            # Send message
            await self.bot.send_message(
                chat_id=user_telegram_id,
                text=message,
                parse_mode='HTML'
            )
            
            logger.info(f"Price change notification sent to user {user_telegram_id} for {change.ticker}")
            return True
            
        except TelegramError as e:
            logger.error(f"Failed to send notification to user {user_telegram_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending notification: {e}")
            return False
    
    def _format_price_change_message(self, change: PriceChange) -> str:
        """
        Format price change message for Telegram
        
        Args:
            change: PriceChange object
            
        Returns:
            Formatted message string
        """
        # Determine if it's a bond or stock
        security_type_text = "облигации" if change.security_type == "bond" else "акции"
        
        # Format price change with appropriate sign
        change_sign = "+" if change.change_pct >= 0 else ""
        change_text = f"{change_sign}{change.change_pct:.2f}%"
        
        # Format prices
        old_price_text = f"{change.old_price:.2f}" if change.old_price else "N/A"
        new_price_text = f"{change.new_price:.2f}" if change.new_price else "N/A"
        
        # Create message
        message = f"""
📈 <b>Изменение цены {security_type_text}</b>

<b>{change.name}</b> ({change.ticker})
{change_text} к цене закрытия предыдущего дня

💰 <b>Цена:</b> {old_price_text} → {new_price_text} RUB
📊 <b>Изменение:</b> {change_text}

Проверьте, не надо ли предпринять какие-либо срочные действия в отношении данной бумаги.
        """.strip()
        
        return message
    
    async def send_bulk_notifications(self, changes: List[PriceChange]) -> int:
        """
        Send bulk notifications for multiple price changes
        
        Args:
            changes: List of PriceChange objects
            
        Returns:
            Number of successfully sent notifications
        """
        if not changes:
            return 0
        
        # Group changes by user
        user_changes = {}
        for change in changes:
            if change.user_id not in user_changes:
                user_changes[change.user_id] = []
            user_changes[change.user_id].append(change)
        
        sent_count = 0
        
        for user_id, user_change_list in user_changes.items():
            try:
                # Get user's Telegram ID
                from bot.core.db import db_manager
                user = db_manager.get_user_by_id(user_id)
                if not user or not user.telegram_id:
                    logger.warning(f"No Telegram ID found for user {user_id}")
                    continue
                
                # Send individual notifications for each change
                for change in user_change_list:
                    success = await self.send_price_change_notification(change, user.telegram_id)
                    if success:
                        sent_count += 1
                    
                    # Small delay between messages to avoid rate limiting
                    import asyncio
                    await asyncio.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error sending notifications to user {user_id}: {e}")
                continue
        
        logger.info(f"Sent {sent_count} price change notifications")
        return sent_count

# Global notification service instance
notification_service = None

def initialize_notification_service(bot_token: str):
    """Initialize the global notification service"""
    global notification_service
    notification_service = NotificationService(bot_token)
