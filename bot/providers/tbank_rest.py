import asyncio
import httpx
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from bot.core.config import config
from bot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TBankInstrument:
    figi: str
    ticker: str
    isin: Optional[str]
    name: str
    instrument_type: str
    currency: str
    lot: int = 1
    min_price_increment: Optional[float] = None


@dataclass
class TBankPrice:
    figi: str
    price: float
    time: Optional[datetime] = None


@dataclass
class TBankClosePrice:
    figi: str
    price: float


@dataclass
class TBankTradingStatus:
    figi: str
    trading_status: str
    time: Optional[datetime] = None


@dataclass
class TBankDividend:
    figi: str
    payment_date: datetime
    declared_date: Optional[datetime]
    dividend_net: float
    currency: str


@dataclass
class TBankCoupon:
    figi: str
    coupon_date: datetime
    coupon_value: float
    coupon_number: int
    fix_date: Optional[datetime]
    currency: str


class TBankRestClient:
    
    def __init__(self):
        self.base_url = config.tin_api_base
        self.token = config.tin_token
        self.client = httpx.AsyncClient(timeout=10.0)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        headers = self.headers.copy()
        headers["X-Request-ID"] = str(uuid.uuid4())
        return headers
    
    async def find_instrument(self, query: str) -> List[TBankInstrument]:
        """Find instruments by query.

        Args:
            query: Search query (name, ticker, ISIN)

        Returns:
            List of matching instruments
        """
        try:
            url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.InstrumentsService/FindInstrument"
            
            payload = {
                "query": query,
                "instrumentKind": "INSTRUMENT_TYPE_UNSPECIFIED"
            }
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            instruments = data.get("instruments", [])
            
            result = []
            for instrument in instruments:
                result.append(TBankInstrument(
                    figi=instrument.get("figi", ""),
                    ticker=instrument.get("ticker", ""),
                    isin=instrument.get("isin"),
                    name=instrument.get("name", ""),
                    instrument_type=instrument.get("instrumentType", ""),
                    currency=instrument.get("currency", "RUB"),
                    lot=instrument.get("lot", 1),
                    min_price_increment=instrument.get("minPriceIncrement")
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"T-Bank find instrument failed for '{query}': {e}")
            return []
    
    async def get_last_prices(self, figis: List[str]) -> List[TBankPrice]:
        """Get last prices for instruments.

        Args:
            figis: List of FIGI identifiers

        Returns:
            List of price data
        """
        try:
            url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetLastPrices"
            
            payload = {"figi": figis}
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            last_prices = data.get("lastPrices", [])
            
            result = []
            for price_data in last_prices:
                price_obj = price_data.get("price", {})
                units = price_obj.get("units", 0)
                nano = price_obj.get("nano", 0)
                price_value = float(units) + float(nano) / 1e9
                
                time_str = price_data.get("time")
                time_obj = None
                if time_str:
                    try:
                        time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                result.append(TBankPrice(
                    figi=price_data.get("figi", ""),
                    price=price_value,
                    time=time_obj
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"T-Bank get last prices failed for {figis}: {e}")
            return []
    
    async def get_close_prices(self, figis: List[str]) -> List[TBankClosePrice]:
        """Get close prices for instruments.

        Args:
            figis: List of FIGI identifiers

        Returns:
            List of close price data
        """
        try:
            url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetClosePrices"
            
            payload = {"figi": figis}
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            close_prices = data.get("closePrices", [])
            
            result = []
            requested_figis = set(figis)
            for price_data in close_prices:
                figi = price_data.get("figi", "")
                if figi in requested_figis:
                    price_obj = price_data.get("price", {})
                    units = price_obj.get("units", 0)
                    nano = price_obj.get("nano", 0)
                    price_value = float(units) + float(nano) / 1e9
                    
                    result.append(TBankClosePrice(
                        figi=figi,
                        price=price_value
                    ))
            
            return result
            
        except Exception as e:
            logger.error(f"T-Bank get close prices failed for {figis}: {e}")
            return []
    
    async def get_trading_status(self, figi: str) -> Optional[TBankTradingStatus]:
        """Get trading status for instrument.

        Args:
            figi: FIGI identifier

        Returns:
            Trading status data or None
        """
        try:
            url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.MarketDataService/GetTradingStatus"
            
            payload = {"figi": figi}
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            
            time_str = data.get("time")
            time_obj = None
            if time_str:
                try:
                    time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                except:
                    pass
            
            return TBankTradingStatus(
                figi=figi,
                trading_status=data.get("tradingStatus", ""),
                time=time_obj
            )
            
        except Exception as e:
            logger.error(f"T-Bank get trading status failed for {figi}: {e}")
            return None
    
    async def get_dividends(self, figi: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[TBankDividend]:
        """Get dividends for instrument.

        Args:
            figi: FIGI identifier
            from_date: Start date (default: 2023-01-01)
            to_date: End date (default: 2030-01-01)

        Returns:
            List of dividend data
        """
        try:
            url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.InstrumentsService/GetDividends"
            
            if not from_date:
                from_date = datetime(2023, 1, 1)
            if not to_date:
                to_date = datetime(2030, 1, 1)
            
            payload = {
                "figi": figi,
                "from": from_date.isoformat() + "Z",
                "to": to_date.isoformat() + "Z"
            }
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            dividends = data.get("dividends", [])
            
            result = []
            for dividend_data in dividends:
                payment_date_str = dividend_data.get("paymentDate")
                declared_date_str = dividend_data.get("declaredDate")
                
                payment_date = None
                if payment_date_str:
                    try:
                        payment_date = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                declared_date = None
                if declared_date_str:
                    try:
                        declared_date = datetime.fromisoformat(declared_date_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                dividend_obj = dividend_data.get("dividendNet", {})
                units = dividend_obj.get("units", 0)
                nano = dividend_obj.get("nano", 0)
                dividend_value = float(units) + float(nano) / 1e9
                
                result.append(TBankDividend(
                    figi=figi,
                    payment_date=payment_date,
                    declared_date=declared_date,
                    dividend_net=dividend_value,
                    currency=dividend_data.get("currency", "RUB")
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"T-Bank get dividends failed for {figi}: {e}")
            return []
    
    async def get_bond_coupons(self, figi: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[TBankCoupon]:
        """Get bond coupons for instrument.

        Args:
            figi: FIGI identifier
            from_date: Start date (default: 2023-01-01)
            to_date: End date (default: 2030-01-01)

        Returns:
            List of coupon data
        """
        try:
            url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.InstrumentsService/GetBondCoupons"
            
            if not from_date:
                from_date = datetime(2023, 1, 1)
            if not to_date:
                to_date = datetime(2030, 1, 1)
            
            payload = {
                "figi": figi,
                "from": from_date.isoformat() + "Z",
                "to": to_date.isoformat() + "Z"
            }
            
            response = await self.client.post(url, json=payload, headers=self._get_headers())
            response.raise_for_status()
            
            data = response.json()
            coupons = data.get("coupons", [])
            
            result = []
            for coupon_data in coupons:
                coupon_date_str = coupon_data.get("couponDate")
                fix_date_str = coupon_data.get("fixDate")
                
                coupon_date = None
                if coupon_date_str:
                    try:
                        coupon_date = datetime.fromisoformat(coupon_date_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                fix_date = None
                if fix_date_str:
                    try:
                        fix_date = datetime.fromisoformat(fix_date_str.replace('Z', '+00:00'))
                    except:
                        pass
                
                coupon_obj = coupon_data.get("couponValue", {})
                units = coupon_obj.get("units", 0)
                nano = coupon_obj.get("nano", 0)
                coupon_value = float(units) + float(nano) / 1e9
                
                result.append(TBankCoupon(
                    figi=figi,
                    coupon_date=coupon_date,
                    coupon_value=coupon_value,
                    coupon_number=coupon_data.get("couponNumber", 0),
                    fix_date=fix_date,
                    currency=coupon_data.get("currency", "RUB")
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"T-Bank get bond coupons failed for {figi}: {e}")
            return []
    
    async def get_instrument_data(self, query: str) -> Optional[Dict[str, Any]]:
        """Get complete instrument data including prices and status.

        Args:
            query: Search query (name, ticker, ISIN)

        Returns:
            Complete instrument data or None
        """
        try:
            instruments = await self.find_instrument(query)
            if not instruments:
                return None
            
            instrument = instruments[0]
            figi = instrument.figi
            
            last_prices_task = self.get_last_prices([figi])
            close_prices_task = self.get_close_prices([figi])
            trading_status_task = self.get_trading_status(figi)
            
            last_prices, close_prices, trading_status = await asyncio.gather(
                last_prices_task, close_prices_task, trading_status_task, return_exceptions=True
            )
            
            if isinstance(last_prices, Exception):
                logger.error(f"Failed to get last prices: {last_prices}")
                last_prices = []
            if isinstance(close_prices, Exception):
                logger.error(f"Failed to get close prices: {close_prices}")
                close_prices = []
            if isinstance(trading_status, Exception):
                logger.error(f"Failed to get trading status: {trading_status}")
                trading_status = None
            
            dividends = []
            coupons = []
            
            if instrument.instrument_type in ["share", "stock"]:
                dividends = await self.get_dividends(figi)
            elif instrument.instrument_type in ["bond", "corporate_bond", "government_bond"]:
                coupons = await self.get_bond_coupons(figi)
            
            last_price = last_prices[0].price if last_prices else None
            close_price = close_prices[0].price if close_prices else None
            change_pct = None
            
            if last_price and close_price and close_price > 0:
                change_pct = ((last_price / close_price) - 1) * 100
            
            next_coupon = None
            if coupons:
                from datetime import timezone
                now = datetime.now(timezone.utc)
                future_coupons = [c for c in coupons if c.coupon_date and c.coupon_date > now]
                if future_coupons:
                    next_coupon = min(future_coupons, key=lambda x: x.coupon_date)
            
            return {
                "instrument": instrument,
                "last_price": last_price,
                "close_price": close_price,
                "change_pct": change_pct,
                "trading_status": trading_status.trading_status if trading_status else None,
                "dividends": dividends,
                "coupons": coupons,
                "next_coupon": next_coupon
            }
            
        except Exception as e:
            logger.error(f"T-Bank get instrument data failed for '{query}': {e}")
            return None

    async def get_all_bonds_base(self) -> List[Dict[str, Any]]:
        bonds: List[Dict[str, Any]] = []
        page_token = ""

        while True:
            try:
                url = f"{self.base_url}/tinkoff.public.invest.api.contract.v1.InstrumentsService/Bonds"
                payload = {
                    "instrumentStatus": "INSTRUMENT_STATUS_BASE",
                }
                if page_token:
                    payload["pageToken"] = page_token

                response = await self.client.post(url, json=payload, headers=self._get_headers())
                response.raise_for_status()
                data = response.json()
                bonds.extend(data.get("instruments", []))
                page_token = data.get("nextPageToken", "")
                if not page_token:
                    break
            except Exception as e:
                logger.error(f"T-Bank get_all_bonds_base failed at page {page_token}: {e}")
                break

        logger.info(f"Fetched {len(bonds)} bonds via T-Bank InstrumentsService/Bonds")
        return bonds


tbank_rest_client = TBankRestClient()