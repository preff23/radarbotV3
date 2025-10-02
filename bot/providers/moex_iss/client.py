import asyncio
import httpx
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json
from bot.core.config import config
from bot.core.logging import get_logger
from .models import (
    SecurityInfo, ShareSnapshot, BondSnapshot, BondCalendar,
    CouponEvent, AmortizationEvent, SearchResult, MarketData
)

logger = get_logger(__name__)


class MOEXISSClient:
    
    BASE_URL = "https://iss.moex.com/iss"
    TIMEOUT = config.moex_iss_timeout
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def search_securities(self, query: str, limit: int = 50) -> List[SearchResult]:
        """Search securities by query.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of search results
        """
        try:
            url = f"{self.BASE_URL}/securities.json"
            params = {
                "q": query,
                "limit": limit
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            securities = data.get("securities", {}).get("data", [])
            columns = data.get("securities", {}).get("columns", [])
            
            results = []
            for row in securities:
                if len(row) >= len(columns):
                    security_dict = dict(zip(columns, row))
                    
                    result = SearchResult(
                        secid=security_dict.get("secid", ""),
                        shortname=security_dict.get("shortname", ""),
                        name=security_dict.get("name", ""),
                        isin=security_dict.get("isin"),
                        type=security_dict.get("type"),
                        board=security_dict.get("primary_boardid")
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return []
    
    async def get_share_info(self, secid: str) -> Optional[SecurityInfo]:
        try:
            url = f"{self.BASE_URL}/engines/stock/markets/shares/boards/TQBR/securities/{secid}.json"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            securities = data.get("securities", {}).get("data", [])
            columns = data.get("securities", {}).get("columns", [])
            
            if securities and len(securities[0]) >= len(columns):
                security_dict = dict(zip(columns, securities[0]))
                
                return SecurityInfo(
                    secid=security_dict.get("secid", ""),
                    shortname=security_dict.get("shortname", ""),
                    name=security_dict.get("name", ""),
                    isin=security_dict.get("isin"),
                    regnumber=security_dict.get("regnumber"),
                    type=security_dict.get("type"),
                    group=security_dict.get("group"),
                    primary_boardid=security_dict.get("primary_boardid"),
                    marketprice_boardid=security_dict.get("marketprice_boardid")
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get share info for {secid}: {e}")
            return None
    
    async def get_bond_info(self, secid: str) -> Optional[SecurityInfo]:
        try:
            boards = ["TQCB", "TQOB", "TQIR", "TQOD"]
            
            for board in boards:
                url = f"{self.BASE_URL}/engines/stock/markets/bonds/boards/{board}/securities/{secid}.json"
                
                response = await self.client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    securities = data.get("securities", {}).get("data", [])
                    columns = data.get("securities", {}).get("columns", [])
                    
                    if securities and len(securities[0]) >= len(columns):
                        security_dict = dict(zip(columns, securities[0]))
                        
                        return SecurityInfo(
                            secid=security_dict.get("secid", ""),
                            shortname=security_dict.get("shortname", ""),
                            name=security_dict.get("name", ""),
                            isin=security_dict.get("isin"),
                            regnumber=security_dict.get("regnumber"),
                            type=security_dict.get("type"),
                            group=security_dict.get("group"),
                            primary_boardid=security_dict.get("primary_boardid"),
                            marketprice_boardid=security_dict.get("marketprice_boardid")
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bond info for {secid}: {e}")
            return None
    
    async def get_share_marketdata(self, secid: str) -> Optional[ShareSnapshot]:
        try:
            url = f"{self.BASE_URL}/engines/stock/markets/shares/boards/TQBR/securities/{secid}.json"
            params = {"iss.meta": "off", "iss.only": "marketdata,description"}
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            marketdata = data.get("marketdata", {}).get("data", [])
            marketdata_columns = data.get("marketdata", {}).get("columns", [])
            
            description = data.get("description", {}).get("data", [])
            description_columns = data.get("description", {}).get("columns", [])
            
            if marketdata and len(marketdata[0]) >= len(marketdata_columns):
                market_dict = dict(zip(marketdata_columns, marketdata[0]))
                
                desc_dict = {}
                if description and len(description[0]) >= len(description_columns):
                    desc_dict = dict(zip(description_columns, description[0]))
                
                return ShareSnapshot(
                    secid=secid,
                    shortname=desc_dict.get("shortname", market_dict.get("SECID", "")),
                    last=self._parse_float(market_dict.get("LAST")),
                    change_day_pct=self._parse_float(market_dict.get("LASTCHANGEPRCNT")),
                    trading_status=market_dict.get("TRADINGSTATUS"),
                    sector=None,
                    currency=market_dict.get("CURRENCYID"),
                    board="TQBR",
                    market="shares",
                    volume=self._parse_float(market_dict.get("VOLTODAY"))
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get share marketdata for {secid}: {e}")
            return None
    
    async def get_bond_marketdata(self, secid: str) -> Optional[BondSnapshot]:
        try:
            boards = ["TQCB", "TQOB", "TQIR", "TQOD"]
            
            for board in boards:
                url = f"{self.BASE_URL}/engines/stock/markets/bonds/boards/{board}/securities/{secid}.json"
                params = {"iss.meta": "off", "iss.only": "securities,marketdata,description"}
                
                response = await self.client.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    securities = data.get("securities", {}).get("data", [])
                    securities_columns = data.get("securities", {}).get("columns", [])
                    
                    marketdata = data.get("marketdata", {}).get("data", [])
                    marketdata_columns = data.get("marketdata", {}).get("columns", [])
                    
                    description = data.get("description", {}).get("data", [])
                    description_columns = data.get("description", {}).get("columns", [])
                    
                    if marketdata and len(marketdata[0]) >= len(marketdata_columns):
                        market_dict = dict(zip(marketdata_columns, marketdata[0]))
                        
                        securities_dict = {}
                        if securities and len(securities[0]) >= len(securities_columns):
                            securities_dict = dict(zip(securities_columns, securities[0]))
                        
                        desc_dict = {}
                        if description and len(description[0]) >= len(description_columns):
                            desc_dict = dict(zip(description_columns, description[0]))
                        
                        # Get calendar data for coupon and maturity dates
                        calendar_data = await self.get_bond_calendar(secid)
                        
                        # Extract next coupon date and value from calendar
                        next_coupon_date = None
                        coupon_value = None
                        if calendar_data and calendar_data.coupons:
                            # Find the next coupon
                            now = datetime.now()
                            future_coupons = [c for c in calendar_data.coupons if c.coupon_date >= now]
                            if future_coupons:
                                next_coupon = min(future_coupons, key=lambda x: x.coupon_date)
                                next_coupon_date = next_coupon.coupon_date
                                coupon_value = next_coupon.coupon_value
                        
                        # Extract maturity date from amortizations
                        maturity_date = None
                        if calendar_data and calendar_data.amortizations:
                            # Find the last amortization (maturity)
                            if calendar_data.amortizations:
                                last_amort = max(calendar_data.amortizations, key=lambda x: x.amort_date)
                                maturity_date = last_amort.amort_date
                        
                        return BondSnapshot(
                            secid=secid,
                            shortname=desc_dict.get("shortname", market_dict.get("SECID", "")),
                            last=self._parse_float(market_dict.get("LAST")),
                            change_day_pct=self._parse_float(market_dict.get("LASTCHANGEPRCNT")),
                            trading_status=market_dict.get("TRADINGSTATUS"),
                            ytm=self._parse_float(market_dict.get("YIELD")),
                            duration=self._parse_float(market_dict.get("DURATION")),
                            aci=self._parse_float(market_dict.get("ACCRUEDINT")),
                            currency=market_dict.get("CURRENCYID"),
                            board=board,
                            market="bonds",
                            face_value=self._parse_float(securities_dict.get("FACEVALUE")),
                            volume=self._parse_float(market_dict.get("VOLTODAY")),
                            next_coupon_date=next_coupon_date,
                            maturity_date=maturity_date,
                            coupon_value=coupon_value
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bond marketdata for {secid}: {e}")
            return None
    
    async def get_bond_calendar(self, secid: str, days_ahead: int = 30) -> Optional[BondCalendar]:
        try:
            url = f"{self.BASE_URL}/securities/{secid}/bondization.json"
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            coupons = []
            coupon_data = data.get("coupons", {}).get("data", [])
            coupon_columns = data.get("coupons", {}).get("columns", [])
            
            for row in coupon_data:
                if len(row) >= len(coupon_columns):
                    coupon_dict = dict(zip(coupon_columns, row))
                    coupon_date = self._parse_date(coupon_dict.get("coupondate"))
                    # Строгая проверка: только текущий год
                    current_year = datetime.now().year
                    if coupon_date and coupon_date >= datetime.now() and coupon_date <= datetime.now() + timedelta(days=days_ahead) and coupon_date.year == current_year:
                        coupon = CouponEvent(
                            secid=secid,
                            coupon_date=coupon_date,
                            coupon_value=self._parse_float(coupon_dict.get("value")),
                            coupon_type="coupon"
                        )
                        coupons.append(coupon)
            
            amortizations = []
            amort_data = data.get("amortizations", {}).get("data", [])
            amort_columns = data.get("amortizations", {}).get("columns", [])
            
            for row in amort_data:
                if len(row) >= len(amort_columns):
                    amort_dict = dict(zip(amort_columns, row))
                    amort_date = self._parse_date(amort_dict.get("amortdate"))
                    # Строгая проверка: только текущий год
                    current_year = datetime.now().year
                    if amort_date and amort_date >= datetime.now() and amort_date <= datetime.now() + timedelta(days=days_ahead) and amort_date.year == current_year:
                        amort = AmortizationEvent(
                            secid=secid,
                            amort_date=amort_date,
                            amort_value=self._parse_float(amort_dict.get("value")),
                            amort_type="amortization"
                        )
                        amortizations.append(amort)
            
            return BondCalendar(
                secid=secid,
                coupons=coupons,
                amortizations=amortizations
            )
            
        except Exception as e:
            logger.error(f"Failed to get bond calendar for {secid}: {e}")
            return None
    
    async def _get_share_sector(self, secid: str) -> Optional[str]:
        try:
            return None
        except Exception:
            return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_date(self, value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        try:
            if isinstance(value, str):
                return datetime.strptime(value, "%Y-%m-%d")
            return value
        except (ValueError, TypeError):
            return None

    async def get_all_corporate_bonds(self) -> List[Dict[str, Any]]:
        bonds: List[Dict[str, Any]] = []
        start = 0
        page_size = 100

        while True:
            try:
                url = f"{self.BASE_URL}/engines/stock/markets/bonds/securities.json"
                params = {
                    "iss.only": "securities",
                    "iss.meta": "off",
                    "start": start,
                }
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                rows = data.get("securities", {}).get("data", [])
                columns = data.get("securities", {}).get("columns", [])
                if not rows:
                    break

                for row in rows:
                    if len(row) < len(columns):
                        continue
                    record = dict(zip(columns, row))
                    isin = record.get("isin")
                    if isin:
                        bonds.append(record)

                start += page_size
            except Exception as e:
                logger.error(f"Failed to fetch MOEX bonds batch starting {start}: {e}")
                break

        logger.info(f"Fetched {len(bonds)} corporate bonds from MOEX ISS")
        return bonds


moex_client = MOEXISSClient()