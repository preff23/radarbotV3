#!/usr/bin/env python3
"""
Price monitoring service for tracking significant price changes
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from bot.core.db import db_manager
from bot.providers.aggregator import market_aggregator
from bot.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class PriceChange:
    """Represents a significant price change for a security"""
    user_id: int
    ticker: str
    name: str
    security_type: str
    old_price: float
    new_price: float
    change_pct: float
    isin: Optional[str] = None
    provider: Optional[str] = None

class PriceMonitor:
    """Monitors price changes and detects significant movements"""
    
    def __init__(self, change_threshold: float = 1.0):
        """
        Initialize price monitor
        
        Args:
            change_threshold: Minimum percentage change to trigger notification (default: 1.0%)
        """
        self.change_threshold = change_threshold
        self.price_history: Dict[str, Dict[int, float]] = {}  # {ticker: {user_id: last_price}}
    
    async def check_price_changes(self) -> List[PriceChange]:
        """
        Check for significant price changes across all user portfolios
        
        Returns:
            List of PriceChange objects for significant changes
        """
        logger.info("Starting price change monitoring...")
        significant_changes = []
        
        try:
            # Get all active users with holdings
            users = db_manager.get_all_users_with_holdings()
            logger.info(f"Found {len(users)} users with holdings")
            
            for user in users:
                user_id = user.id
                logger.info(f"Checking price changes for user {user_id}")
                
                # Get user's holdings
                holdings = db_manager.get_user_holdings(user_id, active_only=True)
                logger.info(f"User {user_id} has {len(holdings)} holdings")
                
                for holding in holdings:
                    if not holding.ticker:
                        continue
                    
                    try:
                        # Get current market data
                        snapshots = await market_aggregator.get_snapshot_for(holding.ticker)
                        if not snapshots:
                            logger.warning(f"No market data found for {holding.ticker}")
                            continue
                        
                        snapshot = snapshots[0]
                        current_price = snapshot.last_price
                        
                        if current_price is None or current_price <= 0:
                            logger.warning(f"Invalid price for {holding.ticker}: {current_price}")
                            continue
                        
                        # Check if we have previous price
                        ticker_key = f"{holding.ticker}_{holding.isin or ''}"
                        if ticker_key in self.price_history and user_id in self.price_history[ticker_key]:
                            old_price = self.price_history[ticker_key][user_id]
                            
                            # Calculate percentage change
                            change_pct = ((current_price - old_price) / old_price) * 100
                            
                            # Check if change is significant
                            if abs(change_pct) >= self.change_threshold:
                                logger.info(f"Significant price change detected for {holding.ticker}: {change_pct:.2f}%")
                                
                                change = PriceChange(
                                    user_id=user_id,
                                    ticker=holding.ticker,
                                    name=holding.normalized_name or holding.raw_name,
                                    security_type=holding.security_type,
                                    old_price=old_price,
                                    new_price=current_price,
                                    change_pct=change_pct,
                                    isin=holding.isin,
                                    provider=snapshot.provider
                                )
                                significant_changes.append(change)
                        
                        # Update price history
                        if ticker_key not in self.price_history:
                            self.price_history[ticker_key] = {}
                        self.price_history[ticker_key][user_id] = current_price
                        
                    except Exception as e:
                        logger.error(f"Error checking price for {holding.ticker}: {e}")
                        continue
            
            logger.info(f"Found {len(significant_changes)} significant price changes")
            return significant_changes
            
        except Exception as e:
            logger.error(f"Error in price monitoring: {e}")
            return []
    
    async def get_user_portfolio_prices(self, user_id: int) -> Dict[str, float]:
        """
        Get current prices for all securities in user's portfolio
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary mapping ticker to current price
        """
        prices = {}
        
        try:
            holdings = db_manager.get_user_holdings(user_id, active_only=True)
            
            for holding in holdings:
                if not holding.ticker:
                    continue
                
                try:
                    snapshots = await market_aggregator.get_snapshot_for(holding.ticker)
                    if snapshots and snapshots[0].last_price:
                        prices[holding.ticker] = snapshots[0].last_price
                except Exception as e:
                    logger.warning(f"Error getting price for {holding.ticker}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting portfolio prices for user {user_id}: {e}")
        
        return prices

# Global price monitor instance
price_monitor = PriceMonitor(change_threshold=0.01)  # 0.01% threshold (minimal)
