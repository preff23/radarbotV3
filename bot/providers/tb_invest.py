import asyncio
import httpx
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from bot.core.config import config
from bot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TBankShare:
    figi: str
    ticker: str
    name: str
    last_price: Optional[float] = None
    change_day_pct: Optional[float] = None
    trading_status: Optional[str] = None
    currency: Optional[str] = None


@dataclass
class TBankBond:
    figi: str
    ticker: str
    name: str
    isin: Optional[str] = None
    last_price: Optional[float] = None
    change_day_pct: Optional[float] = None
    trading_status: Optional[str] = None
    currency: Optional[str] = None
    ytm: Optional[float] = None
    next_coupon_date: Optional[datetime] = None
    maturity_date: Optional[datetime] = None
    coupon_value: Optional[float] = None


class TBankInvestClient:
    
    BASE_URL = "https://invest-public-api.tinkoff.ru/rest"
    TIMEOUT = 10
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
        self.token = config.tin_token
        self.base_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _get_headers(self) -> Dict[str, str]:
        headers = self.base_headers.copy()
        headers["X-Request-ID"] = str(uuid.uuid4())
        return headers
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def search_instruments(self, query: str) -> List[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.InstrumentsService/SearchByTicker"
            
            payload = {
                "query": query
            }
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            return data.get("instruments", [])
            
        except Exception as e:
            logger.error(f"T-Bank search failed for '{query}': {e}")
            return []
    
    async def get_instruments(self, instrument_type: str = "share") -> List[Dict[str, Any]]:
        try:
            if instrument_type == "share":
                url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares"
            elif instrument_type == "bond":
                url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.InstrumentsService/Bonds"
            else:
                return []
            
            response = await self.client.get(url, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            return data.get("instruments", [])
            
        except Exception as e:
            logger.error(f"T-Bank get instruments failed for '{instrument_type}': {e}")
            return []
    
    async def get_share_by_ticker(self, ticker: str) -> Optional[TBankShare]:
        try:
            instruments = await self.search_instruments(ticker)
            
            for instrument in instruments:
                if instrument.get("ticker") == ticker and instrument.get("instrument_type") == "share":
                    market_data = await self.get_market_data(instrument.get("figi"))
                    
                    return TBankShare(
                        figi=instrument.get("figi", ""),
                        ticker=instrument.get("ticker", ""),
                        name=instrument.get("name", ""),
                        last_price=market_data.get("last_price") if market_data else None,
                        change_day_pct=market_data.get("change_day_pct") if market_data else None,
                        trading_status=market_data.get("trading_status") if market_data else None,
                        currency=instrument.get("currency", "")
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get share by ticker '{ticker}': {e}")
            return None
    
    async def get_bond_by_ticker(self, ticker: str) -> Optional[TBankBond]:
        try:
            instruments = await self.search_instruments(ticker)
            
            for instrument in instruments:
                if instrument.get("ticker") == ticker and instrument.get("instrument_type") == "bond":
                    market_data = await self.get_market_data(instrument.get("figi"))
                    
                    return TBankBond(
                        figi=instrument.get("figi", ""),
                        ticker=instrument.get("ticker", ""),
                        name=instrument.get("name", ""),
                        isin=instrument.get("isin"),
                        last_price=market_data.get("last_price") if market_data else None,
                        change_day_pct=market_data.get("change_day_pct") if market_data else None,
                        trading_status=market_data.get("trading_status") if market_data else None,
                        currency=instrument.get("currency", ""),
                        ytm=market_data.get("ytm") if market_data else None,
                        next_coupon_date=market_data.get("next_coupon_date") if market_data else None,
                        maturity_date=market_data.get("maturity_date") if market_data else None,
                        coupon_value=market_data.get("coupon_value") if market_data else None
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bond by ticker '{ticker}': {e}")
            return None
    
    async def get_bond_by_isin(self, isin: str) -> Optional[TBankBond]:
        try:
            instruments = await self.search_instruments(isin)
            
            for instrument in instruments:
                if instrument.get("isin") == isin and instrument.get("instrument_type") == "bond":
                    market_data = await self.get_market_data(instrument.get("figi"))
                    
                    return TBankBond(
                        figi=instrument.get("figi", ""),
                        ticker=instrument.get("ticker", ""),
                        name=instrument.get("name", ""),
                        isin=instrument.get("isin"),
                        last_price=market_data.get("last_price") if market_data else None,
                        change_day_pct=market_data.get("change_day_pct") if market_data else None,
                        trading_status=market_data.get("trading_status") if market_data else None,
                        currency=instrument.get("currency", ""),
                        ytm=market_data.get("ytm") if market_data else None,
                        next_coupon_date=market_data.get("next_coupon_date") if market_data else None,
                        maturity_date=market_data.get("maturity_date") if market_data else None,
                        coupon_value=market_data.get("coupon_value") if market_data else None
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get bond by ISIN '{isin}': {e}")
            return None
    
    async def get_market_data(self, figi: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices"
            
            payload = {
                "figi": [figi]
            }
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            last_prices = data.get("lastPrices", [])
            
            if last_prices:
                price_data = last_prices[0]
                return {
                    "last_price": price_data.get("price", {}).get("units", 0) + 
                                 price_data.get("price", {}).get("nano", 0) / 1e9,
                    "trading_status": "T" if price_data.get("time") else "N"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get market data for FIGI '{figi}': {e}")
            return None
    
    async def get_coupons(self, figi: str) -> List[Dict[str, Any]]:
        try:
            url = f"{self.BASE_URL}/tinkoff.public.invest.api.contract.v1.InstrumentsService/GetBondCoupons"
            
            payload = {
                "figi": figi
            }
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            return data.get("events", [])
            
        except Exception as e:
            logger.error(f"Failed to get coupons for FIGI '{figi}': {e}")
            return []


tb_client = TBankInvestClient()