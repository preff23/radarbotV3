import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from bot.providers.tbank_rest import TBankRestClient
from bot.providers.moex_bridge import moex_bridge
from bot.providers.moex_iss.models import ShareSnapshot, BondSnapshot
from bot.utils.cache import market_data_cache, cache_key
from bot.utils.normalize import normalize_security_name
from bot.utils.trading_hours import get_trading_status, TradingStatus
from bot.core.config import config
from bot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MarketSnapshot:
    secid: str
    ticker: Optional[str] = None
    isin: Optional[str] = None
    name: Optional[str] = None
    security_type: Optional[str] = None
    
    last_price: Optional[float] = None
    change_day_pct: Optional[float] = None
    trading_status: Optional[str] = None
    currency: Optional[str] = None
    
    ytm: Optional[float] = None
    duration: Optional[float] = None
    aci: Optional[float] = None
    next_coupon_date: Optional[datetime] = None
    maturity_date: Optional[datetime] = None
    coupon_value: Optional[float] = None
    face_value: Optional[float] = None
    
    sector: Optional[str] = None
    next_dividend_date: Optional[datetime] = None
    dividend_value: Optional[float] = None
    
    provider: Optional[str] = None
    cached_at: Optional[datetime] = None
    
    is_trading_open: Optional[bool] = None
    trading_status: Optional[str] = None
    data_freshness: Optional[str] = None
    
    raw_name: Optional[str] = None
    raw_quantity: Optional[float] = None
    volume: Optional[float] = None
    shortname: Optional[str] = None
    board: Optional[str] = None
    last_update: Optional[datetime] = None
    coupon_rate: Optional[float] = None
    coupon_frequency: Optional[int] = None
    issue_date: Optional[datetime] = None
    issue_size: Optional[float] = None
    rating: Optional[str] = None
    rating_agency: Optional[str] = None


class MarketDataAggregator:
    
    def __init__(self):
        self.tbank_client = TBankRestClient()
        self.moex_bridge = moex_bridge
    
    async def get_snapshot_for(self, query_or_ids: Union[str, List[str]]) -> List[MarketSnapshot]:
        """Get market snapshots for securities.

        Args:
            query_or_ids: Security name, ticker, ISIN, or list of them

        Returns:
            List of market snapshots
        """
        if isinstance(query_or_ids, str):
            queries = [query_or_ids]
        else:
            queries = query_or_ids
        
        snapshots = []
        
        tasks = [self._get_single_snapshot(query) for query in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to get snapshot for '{queries[i]}': {result}")
            elif result:
                snapshots.append(result)
        
        return snapshots
    
    async def _get_single_snapshot(self, query: str) -> Optional[MarketSnapshot]:
        cache_key_str = cache_key("snapshot", query)
        cached_snapshot = market_data_cache.get(cache_key_str)
        if cached_snapshot:
            return cached_snapshot
        
        tbank_snapshot = None
        moex_snapshot = None
        
        if config.feature_tbank:
            tbank_snapshot = await self._try_tbank(query)
        
        if config.feature_moex_iss:
            moex_snapshot = await self._try_moex(query)
        
        best_snapshot = self._choose_best_snapshot(tbank_snapshot, moex_snapshot)
        if best_snapshot:
            secondary_snapshot = moex_snapshot if best_snapshot is tbank_snapshot else tbank_snapshot
            best_snapshot = self._merge_snapshot_data(best_snapshot, secondary_snapshot)
        
        if best_snapshot:
            best_snapshot = self._add_trading_hours_info(best_snapshot)
            
            market_data_cache.set(cache_key_str, best_snapshot, ttl=300)
            return best_snapshot
        
        return None
    
    def _choose_best_snapshot(self, tbank_snapshot: Optional[MarketSnapshot], moex_snapshot: Optional[MarketSnapshot]) -> Optional[MarketSnapshot]:
        if not tbank_snapshot and not moex_snapshot:
            return None
        
        if not tbank_snapshot:
            return moex_snapshot
        
        if not moex_snapshot:
            return tbank_snapshot
        
        if tbank_snapshot.security_type != moex_snapshot.security_type:
            if moex_snapshot.security_type == "share" and tbank_snapshot.security_type != "share":
                logger.info(f"Choosing MOEX over T-Bank for '{moex_snapshot.ticker}' (security type mismatch)")
                return moex_snapshot
            if tbank_snapshot.security_type == "share" and moex_snapshot.security_type != "share":
                logger.info(f"Choosing T-Bank over MOEX for '{tbank_snapshot.ticker}' (security type mismatch)")
                return tbank_snapshot

        tbank_has_change = tbank_snapshot.change_day_pct is not None
        moex_has_change = moex_snapshot.change_day_pct is not None
        
        if moex_has_change and not tbank_has_change:
            logger.info(f"Choosing MOEX over T-Bank for '{tbank_snapshot.ticker}' (has daily change)")
            return moex_snapshot
        
        if tbank_has_change and not moex_has_change:
            logger.info(f"Choosing T-Bank over MOEX for '{tbank_snapshot.ticker}' (has daily change)")
            return tbank_snapshot
        
        logger.info(f"Choosing T-Bank over MOEX for '{tbank_snapshot.ticker}' (default priority)")
        return tbank_snapshot

    def _merge_snapshot_data(self, primary: Optional[MarketSnapshot], secondary: Optional[MarketSnapshot]) -> Optional[MarketSnapshot]:
        if not primary or not secondary:
            return primary

        def _merge_field(field: str):
            primary_value = getattr(primary, field, None)
            secondary_value = getattr(secondary, field, None)
            if primary_value in (None, "", 0) and secondary_value not in (None, "", 0):
                setattr(primary, field, secondary_value)

        shared_fields = [
            "currency",
            "face_value",
            "ytm",
            "duration",
            "aci",
            "next_coupon_date",
            "maturity_date",
            "coupon_value",
            "sector",
            "next_dividend_date",
            "dividend_value",
            "coupon_rate",
            "coupon_frequency",
            "issue_date",
            "issue_size",
            "rating",
            "rating_agency",
        ]

        for field in shared_fields:
            _merge_field(field)

        if primary.security_type == "bond":
            if getattr(primary, "data_freshness", None) is None and getattr(secondary, "data_freshness", None):
                primary.data_freshness = secondary.data_freshness

            if getattr(primary, "is_trading_open", None) is None and getattr(secondary, "is_trading_open", None) is not None:
                primary.is_trading_open = secondary.is_trading_open

            if getattr(primary, "volume", None) in (None, 0) and getattr(secondary, "volume", None):
                primary.volume = secondary.volume

            primary_last = getattr(primary, "last_price", None)
            secondary_last = getattr(secondary, "last_price", None)
            if primary_last in (None, 0) and secondary_last not in (None, 0):
                primary.last_price = secondary.last_price

            # Preserve percent price from primary data source but ensure currency fallback
            if primary.currency in (None, "", "None") and secondary.currency not in (None, "", "None"):
                primary.currency = secondary.currency
        
        return primary
    
    def _add_trading_hours_info(self, snapshot: MarketSnapshot) -> MarketSnapshot:
        if not snapshot:
            return snapshot
        
        provider = snapshot.provider.lower() if snapshot.provider else "moex"
        
        trading_info = get_trading_status(provider)
        
        snapshot.is_trading_open = trading_info["is_trading_open"]
        snapshot.trading_status = trading_info["status"].value
        
        if trading_info["status"] == TradingStatus.OPEN:
            snapshot.data_freshness = "live"
        elif trading_info["status"] == TradingStatus.AFTER_HOURS:
            snapshot.data_freshness = "last_close"
        elif trading_info["status"] == TradingStatus.PRE_MARKET:
            snapshot.data_freshness = "last_close"
        else:
            snapshot.data_freshness = "last_close"
        
        return snapshot
    
    async def _try_tbank(self, query: str) -> Optional[MarketSnapshot]:
        try:
            data = await self.tbank_client.get_instrument_data(query)
            if not data:
                return None
            
            instrument = data["instrument"]
            
            security_type = "share"
            if instrument.instrument_type in ["bond", "corporate_bond", "government_bond"]:
                security_type = "bond"
            elif instrument.instrument_type in ["fund", "etf"]:
                security_type = "fund"
            
            next_dividend = None
            if data["dividends"]:
                from datetime import timezone
                now = datetime.now(timezone.utc)
                future_dividends = [d for d in data["dividends"] if d.payment_date and d.payment_date > now]
                if future_dividends:
                    next_dividend = min(future_dividends, key=lambda x: x.payment_date)
            
            return MarketSnapshot(
                secid=instrument.figi,
                ticker=instrument.ticker,
                isin=instrument.isin,
                name=instrument.name,
                security_type=security_type,
                last_price=data["last_price"],
                change_day_pct=data["change_pct"],
                trading_status=data["trading_status"],
                currency=instrument.currency,
                next_coupon_date=data["next_coupon"].coupon_date if data["next_coupon"] else None,
                coupon_value=data["next_coupon"].coupon_value if data["next_coupon"] else None,
                next_dividend_date=next_dividend.payment_date if next_dividend else None,
                dividend_value=next_dividend.dividend_net if next_dividend else None,
                provider="TBANK",
                cached_at=datetime.now(),
                shortname=instrument.ticker,
                last_update=datetime.now(),
                volume=data.get("volume", 0.0)
            )
            
        except Exception as e:
            logger.error(f"T-Bank lookup failed for '{query}': {e}")
            return None
    
    async def _try_moex(self, query: str) -> Optional[MarketSnapshot]:
        try:
            resolved = await self.moex_bridge.resolve_by_name(query)
            if not resolved:
                return None
            
            secid = resolved["secid"]
            security_type = resolved.get("type", "unknown")
            
            if security_type in ["share", "stock", "common_share", "preferred_share"]:
                share_snapshot = await self.moex_bridge.share_snapshot(secid)
                if share_snapshot:
                    return MarketSnapshot(
                        secid=secid,
                        ticker=share_snapshot.shortname,
                        name=resolved.get("name"),
                        security_type="share",
                        last_price=share_snapshot.last,
                        change_day_pct=share_snapshot.change_day_pct,
                        trading_status=share_snapshot.trading_status,
                        currency=share_snapshot.currency,
                        sector=share_snapshot.sector,
                        provider="MOEX",
                        cached_at=datetime.now(),
                        shortname=share_snapshot.shortname,
                        last_update=datetime.now(),
                        volume=share_snapshot.volume
                    )
            
            elif security_type in ["bond", "corporate_bond", "government_bond", "exchange_bond"]:
                bond_snapshot = await self.moex_bridge.bond_snapshot(secid)
                if bond_snapshot:
                    return MarketSnapshot(
                        secid=secid,
                        ticker=bond_snapshot.shortname,
                        name=resolved.get("name"),
                        security_type="bond",
                        last_price=bond_snapshot.last,
                        change_day_pct=bond_snapshot.change_day_pct,
                        trading_status=bond_snapshot.trading_status,
                        currency=bond_snapshot.currency,
                        ytm=bond_snapshot.ytm,
                        duration=bond_snapshot.duration,
                        aci=bond_snapshot.aci,
                        face_value=bond_snapshot.face_value,
                        provider="MOEX",
                        cached_at=datetime.now(),
                        shortname=bond_snapshot.shortname,
                        last_update=datetime.now(),
                        volume=bond_snapshot.volume
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"MOEX lookup failed for '{query}': {e}")
            return None
    
    async def get_bond_calendar(self, secid: str) -> Optional[Dict[str, Any]]:
        try:
            cache_key_str = cache_key("bond_calendar", secid)
            cached_calendar = market_data_cache.get(cache_key_str)
            if cached_calendar:
                return cached_calendar
            
            calendar = await self.moex_bridge.bond_calendar_30d(secid)
            if calendar:
                calendar_data = {
                    "secid": secid,
                    "coupons": [
                        {
                            "date": coupon.coupon_date,
                            "value": coupon.coupon_value,
                            "type": "coupon"
                        }
                        for coupon in calendar.coupons
                    ],
                    "amortizations": [
                        {
                            "date": amort.amort_date,
                            "value": amort.amort_value,
                            "type": "amortization"
                        }
                        for amort in calendar.amortizations
                    ]
                }
                
                market_data_cache.set(cache_key_str, calendar_data, ttl=3600)
                return calendar_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bond calendar for {secid}: {e}")
            return None
    
    async def get_snapshots(self, queries: List[str]) -> List[MarketSnapshot]:
        return await self.get_snapshot_for(queries)
    
    async def get_market_data(self, holdings: List[Dict[str, Any]]) -> List[MarketSnapshot]:
        snapshots = []
        
        for holding in holdings:
            queries = []
            
            if holding.get('isin'):
                queries.append(holding['isin'])
            
            if holding.get('ticker'):
                queries.append(holding['ticker'])
            
            if holding.get('raw_name'):
                queries.append(holding['raw_name'])
            
            snapshot = None
            for query in queries:
                snapshot = await self._get_single_snapshot(query)
                if snapshot:
                    break
            
            if snapshot:
                snapshot.raw_name = holding.get('raw_name')
                snapshot.raw_quantity = holding.get('raw_quantity')
                snapshots.append(snapshot)
            else:
                logger.warning(f"No market data found for {holding.get('raw_name', 'unknown')}")
        
        return snapshots
    
    async def batch_get_snapshots(self, queries: List[str]) -> Dict[str, Optional[MarketSnapshot]]:
        results = {}
        
        batch_size = 10
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            
            tasks = [self._get_single_snapshot(query) for query in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for query, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch snapshot error for '{query}': {result}")
                    results[query] = None
                else:
                    results[query] = result
            
            if i + batch_size < len(queries):
                await asyncio.sleep(0.1)
        
        return results


market_aggregator = MarketDataAggregator()