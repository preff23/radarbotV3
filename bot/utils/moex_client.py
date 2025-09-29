import asyncio
import httpx
from typing import Dict, Any, Optional
from bot.core.logging import get_logger

logger = get_logger(__name__)


class MOEXClient:
    
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
    
    async def get_index_data(self, index_name: str) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{self.base_url}/engines/stock/markets/index/securities/{index_name}.json"
                params = {
                    "iss.meta": "off",
                    "iss.only": "marketdata"
                }

                response = await client.get(url, params=params)
                response.raise_for_status()

                payload = response.json() or {}
                marketdata = payload.get("marketdata", {})
                rows = marketdata.get("data", [])
                columns = marketdata.get("columns", [])

                if not rows or not columns:
                    logger.warning(f"MOEX index response missing data for {index_name}")
                    return None

                row = rows[0]
                market_dict = dict(zip(columns, row))

                return {
                    "last": market_dict.get("LAST"),
                    "change": market_dict.get("LASTCHANGE"),
                    "change_percent": market_dict.get("LASTCHANGEPRCNT"),
                    "time": market_dict.get("TIME"),
                }

        except Exception as e:
            logger.warning(f"Error getting MOEX index data for {index_name}: {e}")
            return None
    
    async def get_security_data(self, ticker: str, engine: str = "stock", market: str = "shares", board: Optional[str] = None) -> Optional[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if board:
                    url = f"{self.base_url}/engines/{engine}/markets/{market}/boards/{board}/securities/{ticker}.json"
                else:
                    url = f"{self.base_url}/engines/{engine}/markets/{market}/securities/{ticker}.json"

                params = {
                    "iss.meta": "off",
                    "iss.only": "securities,marketdata,description"
                }

                response = await client.get(url, params=params)
                response.raise_for_status()

                payload = response.json() or {}
                securities_block = payload.get("securities", {})
                market_block = payload.get("marketdata", {})
                description_block = payload.get("description", {})

                securities_rows = securities_block.get("data", [])
                securities_columns = securities_block.get("columns", [])

                market_rows = market_block.get("data", [])
                market_columns = market_block.get("columns", [])

                desc_rows = description_block.get("data", [])
                desc_columns = description_block.get("columns", [])

                if not market_rows or not market_columns:
                    return None

                market_dict = dict(zip(market_columns, market_rows[0]))

                securities_dict = {}
                if securities_rows and securities_columns:
                    securities_dict = dict(zip(securities_columns, securities_rows[0]))

                description_dict = {}
                if desc_rows and desc_columns:
                    description_dict = dict(zip(desc_columns, desc_rows[0]))

                return {
                    "ticker": securities_dict.get("SECID", ticker),
                    "name": description_dict.get("shortname", securities_dict.get("SECNAME", ticker)),
                    "currency": market_dict.get("CURRENCYID"),
                    "last": market_dict.get("LAST"),
                    "change": market_dict.get("LASTCHANGE"),
                    "change_percent": market_dict.get("LASTCHANGEPRCNT"),
                    "bid": market_dict.get("BID"),
                    "ask": market_dict.get("OFFER"),
                }

        except Exception as e:
            logger.warning(f"Error getting MOEX security data for {ticker}: {e}")
            return None