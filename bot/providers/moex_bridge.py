import asyncio
from typing import Optional, Dict, Any, List
from difflib import SequenceMatcher
from bot.providers.moex_iss.client import MOEXISSClient
from bot.providers.moex_iss.models import SearchResult, ShareSnapshot, BondSnapshot, BondCalendar
from bot.utils.normalize import normalize_security_name
from bot.core.logging import get_logger

logger = get_logger(__name__)


class MOEXBridge:
    
    def __init__(self):
        self.client = MOEXISSClient()
    
    async def normalize_name(self, name: str) -> str:
        return normalize_security_name(name)
    
    async def resolve_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Resolve security by name with fuzzy matching.

        Args:
            name: Security name to resolve

        Returns:
            Dict with secid, type, board, shortname, name or None
        """
        try:
            results = await self.client.search_securities(name, limit=20)
            if not results:
                return None
            
            scored_results = []
            for result in results:
                score = self._calculate_match_score(name, result)
                if score >= 0.8:
                    scored_results.append((score, result))
            
            if not scored_results:
                return None
            
            scored_results.sort(key=lambda x: x[0], reverse=True)
            best_score, best_result = scored_results[0]
            
            return {
                "secid": best_result.secid,
                "type": best_result.type,
                "board": best_result.board,
                "shortname": best_result.shortname,
                "name": best_result.name,
                "isin": best_result.isin,
                "score": best_score
            }
            
        except Exception as e:
            logger.error(f"Failed to resolve name '{name}': {e}")
            return None
    
    def _calculate_match_score(self, query: str, result: SearchResult) -> float:
        query_upper = query.upper()
        name_upper = result.name.upper()
        shortname_upper = result.shortname.upper()
        secid_upper = result.secid.upper()
        
        if query_upper == secid_upper:
            return 1.0
        
        if query_upper == shortname_upper:
            return 0.95
        
        if query_upper == name_upper:
            return 0.9
        
        if name_upper.startswith(query_upper) or shortname_upper.startswith(query_upper):
            return 0.85
        
        name_score = SequenceMatcher(None, query_upper, name_upper).ratio()
        shortname_score = SequenceMatcher(None, query_upper, shortname_upper).ratio()
        secid_score = SequenceMatcher(None, query_upper, secid_upper).ratio()
        
        best_score = max(name_score, shortname_score, secid_score)
        
        if best_score >= 0.8:
            return best_score
        
        return 0.0
    
    async def share_snapshot(self, secid_or_ticker: str) -> Optional[ShareSnapshot]:
        try:
            return await self.client.get_share_marketdata(secid_or_ticker)
        except Exception as e:
            logger.error(f"Failed to get share snapshot for {secid_or_ticker}: {e}")
            return None
    
    async def bond_snapshot(self, secid_or_isin: str) -> Optional[BondSnapshot]:
        try:
            return await self.client.get_bond_marketdata(secid_or_isin)
        except Exception as e:
            logger.error(f"Failed to get bond snapshot for {secid_or_isin}: {e}")
            return None
    
    async def bond_calendar_30d(self, secid: str) -> Optional[BondCalendar]:
        try:
            return await self.client.get_bond_calendar(secid, days_ahead=7)  # Сократили до 7 дней
        except Exception as e:
            logger.error(f"Failed to get bond calendar for {secid}: {e}")
            return None
    
    async def get_security_type(self, secid: str) -> Optional[str]:
        try:
            share_info = await self.client.get_share_info(secid)
            if share_info:
                return "share"
            
            bond_info = await self.client.get_bond_info(secid)
            if bond_info:
                return "bond"
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get security type for {secid}: {e}")
            return None
    
    async def batch_resolve(self, names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        results = {}
        
        batch_size = 5
        for i in range(0, len(names), batch_size):
            batch = names[i:i + batch_size]
            
            tasks = [self.resolve_by_name(name) for name in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for name, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch resolve error for '{name}': {result}")
                    results[name] = None
                else:
                    results[name] = result
            
            if i + batch_size < len(names):
                await asyncio.sleep(0.1)
        
        return results


moex_bridge = MOEXBridge()