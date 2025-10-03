"""
Умная система загрузки данных для Инвеста
ИИ сам решает, какие данные ему нужны для ответа
"""

import asyncio
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from bot.core.logging import get_logger

logger = get_logger(__name__)


class DataType(Enum):
    """Типы данных, которые может запросить ИИ"""
    NEWS = "news"
    MOEX_INDICES = "moex_indices"
    CURRENCY_RATES = "currency_rates"
    ALTERNATIVES = "alternatives"
    CORPBONDS_DATA = "corpbonds_data"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"


class SmartDataLoader:
    """Умная система загрузки данных на основе контекста вопроса"""
    
    def __init__(self, invest_analyst):
        self.invest_analyst = invest_analyst
        self.cache = {}  # Простой кэш в памяти
        self.cache_ttl = {
            DataType.NEWS: 600,  # 10 минут
            DataType.MOEX_INDICES: 300,  # 5 минут
            DataType.CURRENCY_RATES: 60,  # 1 минута
            DataType.ALTERNATIVES: 1800,  # 30 минут
            DataType.CORPBONDS_DATA: 3600,  # 1 час
        }
    
    async def get_smart_context(self, message: str, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Умно определяет, какие данные нужны для ответа на вопрос
        """
        try:
            # Анализируем вопрос и определяем нужные данные
            needed_data = await self._analyze_message_context(message, portfolio_data)
            
            logger.info(f"Smart data loader: needed data types: {[d.value for d in needed_data]}")
            
            # Загружаем только нужные данные параллельно
            context = await self._load_data_parallel(needed_data, portfolio_data)
            
            return context
            
        except Exception as e:
            logger.error(f"Error in smart data loader: {e}")
            # Fallback к минимальному набору данных
            return await self._get_minimal_context()
    
    async def _analyze_message_context(self, message: str, portfolio_data: Dict[str, Any]) -> Set[DataType]:
        """
        Анализирует сообщение и определяет, какие данные нужны
        """
        message_lower = message.lower()
        needed_data = set()
        
        # Анализ по ключевым словам и контексту
        if self._needs_news_data(message_lower):
            needed_data.add(DataType.NEWS)
        
        if self._needs_market_data(message_lower):
            needed_data.add(DataType.MOEX_INDICES)
            needed_data.add(DataType.CURRENCY_RATES)
        
        if self._needs_alternatives_data(message_lower, portfolio_data):
            needed_data.add(DataType.ALTERNATIVES)
        
        if self._needs_corpbonds_data(message_lower, portfolio_data):
            needed_data.add(DataType.CORPBONDS_DATA)
        
        # Всегда добавляем базовые данные если портфель не пуст
        if portfolio_data.get("holdings"):
            if not needed_data:  # Если ничего не определено, добавляем минимум
                needed_data.add(DataType.MOEX_INDICES)
        
        return needed_data
    
    def _needs_news_data(self, message_lower: str) -> bool:
        """Определяет, нужны ли новости"""
        news_keywords = [
            'новости', 'news', 'события', 'события', 'происшествия',
            'что происходит', 'что случилось', 'обновления', 'тренды',
            'рынок', 'экономика', 'политика', 'санкции', 'война',
            'инфляция', 'ставки', 'цб', 'центробанк'
        ]
        return any(keyword in message_lower for keyword in news_keywords)
    
    def _needs_market_data(self, message_lower: str) -> bool:
        """Определяет, нужны ли рыночные данные"""
        market_keywords = [
            'индекс', 'moex', 'rts', 'курс', 'валюта', 'доллар', 'евро',
            'рубль', 'цена', 'стоимость', 'рынок', 'торги', 'бирж',
            'доходность', 'прибыль', 'убыток', 'рост', 'падение'
        ]
        return any(keyword in message_lower for keyword in market_keywords)
    
    def _needs_alternatives_data(self, message_lower: str, portfolio_data: Dict[str, Any]) -> bool:
        """Определяет, нужны ли альтернативные бумаги"""
        alternatives_keywords = [
            'рекомендац', 'замен', 'лучше', 'альтернатив', 'продать', 'купить',
            'что купить', 'что продать', 'совет', 'выбор', 'вариант'
        ]
        has_holdings = bool(portfolio_data.get("holdings"))
        return has_holdings and any(keyword in message_lower for keyword in alternatives_keywords)
    
    def _needs_corpbonds_data(self, message_lower: str, portfolio_data: Dict[str, Any]) -> bool:
        """Определяет, нужны ли данные corpbonds.ru"""
        corpbonds_keywords = [
            'рейтинг', 'rating', 'акра', 'эксперт ра', 'риск', 'дефолт',
            'доходность', 'ytm', 'купон', 'облигац', 'эмитент', 'отрасль',
            'финансовые', 'баланс', 'ликвидность'
        ]
        has_bonds = any(
            holding.get('isin', '').startswith('RU') 
            for holding in portfolio_data.get("holdings", [])
        )
        return has_bonds and any(keyword in message_lower for keyword in corpbonds_keywords)
    
    async def _load_data_parallel(self, needed_data: Set[DataType], portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Загружает нужные данные параллельно"""
        context = {}
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        
        if DataType.NEWS in needed_data:
            tasks.append(self._load_news_data())
        
        if DataType.MOEX_INDICES in needed_data:
            tasks.append(self._load_moex_data())
        
        if DataType.CURRENCY_RATES in needed_data:
            tasks.append(self._load_currency_data())
        
        if DataType.ALTERNATIVES in needed_data:
            tasks.append(self._load_alternatives_data(portfolio_data))
        
        # Выполняем все задачи параллельно
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error loading data: {result}")
                else:
                    context.update(result)
        
        return context
    
    async def _load_news_data(self) -> Dict[str, Any]:
        """Загружает новости с кэшированием"""
        cache_key = "news_data"
        if self._is_cached(cache_key, DataType.NEWS):
            return self.cache[cache_key]
        
        try:
            news_items = await self.invest_analyst.news_aggregator.get_news_for_securities(
                tickers=["SBER", "GAZP", "LKOH", "ROSN", "NVTK"],
                issuers=["Сбербанк", "Газпром", "ЛУКОЙЛ", "Роснефть", "Новатэк"],
                max_age_hours=24
            )
            
            result = {
                "news": [
                    {
                        "title": item.title,
                        "summary": item.description or "",
                        "url": item.link,
                        "published": item.published_at.strftime("%Y-%m-%d %H:%M") if item.published_at is not None else "",
                        "source": item.source
                    }
                    for item in news_items[:5]  # Ограничиваем количество
                ]
            }
            
            self._cache_data(cache_key, result, DataType.NEWS)
            return result
            
        except Exception as e:
            logger.error(f"Error loading news: {e}")
            return {"news": []}
    
    async def _load_moex_data(self) -> Dict[str, Any]:
        """Загружает данные MOEX с кэшированием"""
        cache_key = "moex_data"
        if self._is_cached(cache_key, DataType.MOEX_INDICES):
            return self.cache[cache_key]
        
        try:
            moex_data = {}
            indices = ["IMOEX", "RTSI"]  # Только основные индексы
            
            for index in indices:
                data = await self.invest_analyst.moex_client.get_index_data(index)
                if data:
                    moex_data[index] = data
            
            result = {"moex_indices": moex_data}
            self._cache_data(cache_key, result, DataType.MOEX_INDICES)
            return result
            
        except Exception as e:
            logger.error(f"Error loading MOEX data: {e}")
            return {"moex_indices": {}}
    
    async def _load_currency_data(self) -> Dict[str, Any]:
        """Загружает курсы валют с кэшированием"""
        cache_key = "currency_data"
        if self._is_cached(cache_key, DataType.CURRENCY_RATES):
            return self.cache[cache_key]
        
        try:
            currency_rates = {}
            currency_codes = ["USD000UTSTOM", "EUR_RUB__TOM"]  # Только основные валюты
            
            snapshots = await self.invest_analyst.market_aggregator.get_snapshot_for(currency_codes)
            for snapshot in snapshots:
                ticker = snapshot.ticker or snapshot.secid
                currency_rates[ticker] = {
                    "name": snapshot.name or ticker,
                    "price": snapshot.last_price,
                    "currency": snapshot.currency or "RUB",
                    "provider": snapshot.provider
                }
            
            result = {"currency_rates": currency_rates}
            self._cache_data(cache_key, result, DataType.CURRENCY_RATES)
            return result
            
        except Exception as e:
            logger.error(f"Error loading currency data: {e}")
            return {"currency_rates": {}}
    
    async def _load_alternatives_data(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Загружает альтернативные бумаги с кэшированием"""
        cache_key = "alternatives_data"
        if self._is_cached(cache_key, DataType.ALTERNATIVES):
            return self.cache[cache_key]
        
        try:
            holdings = portfolio_data.get("holdings", [])
            if not holdings:
                return {"alternatives": {}}
            
            alternatives = await self.invest_analyst._get_alternative_securities(holdings)
            result = {"alternatives": alternatives}
            self._cache_data(cache_key, result, DataType.ALTERNATIVES)
            return result
            
        except Exception as e:
            logger.error(f"Error loading alternatives: {e}")
            return {"alternatives": {}}
    
    async def _get_minimal_context(self) -> Dict[str, Any]:
        """Возвращает минимальный контекст для быстрого ответа"""
        return {
            "news": [],
            "moex_indices": {},
            "currency_rates": {},
            "alternatives": {}
        }
    
    def _is_cached(self, cache_key: str, data_type: DataType) -> bool:
        """Проверяет, есть ли данные в кэше и не истекли ли они"""
        if cache_key not in self.cache:
            return False
        
        cached_data = self.cache[cache_key]
        if "timestamp" not in cached_data:
            return False
        
        import time
        ttl = self.cache_ttl.get(data_type, 300)
        return time.time() - cached_data["timestamp"] < ttl
    
    def _cache_data(self, cache_key: str, data: Dict[str, Any], data_type: DataType):
        """Кэширует данные с временной меткой"""
        import time
        data["timestamp"] = time.time()
        self.cache[cache_key] = data
