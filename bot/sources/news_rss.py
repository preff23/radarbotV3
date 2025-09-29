import asyncio
import httpx
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from bot.core.config import config
from bot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NewsItem:
    title: str
    link: str
    description: Optional[str] = None
    published_at: datetime = None
    source: str = ""
    related_tickers: List[str] = None
    related_issuers: List[str] = None
    matched_terms: List[str] = None
    
    def __post_init__(self):
        if self.related_tickers is None:
            self.related_tickers = []
        if self.related_issuers is None:
            self.related_issuers = []
        if self.matched_terms is None:
            self.matched_terms = []


class RSSNewsSource:
    
    def __init__(self, url: str, source_name: str, timeout: int = 10):
        self.url = url
        self.source_name = source_name
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def fetch_news(self, max_age_hours: int = 24) -> List[NewsItem]:
        try:
            response = await self.client.get(self.url)
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            news_items = []
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for entry in feed.entries:
                try:
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6])
                    
                    if published_at and published_at < cutoff_time:
                        continue
                    
                    news_item = NewsItem(
                        title=entry.get('title', ''),
                        link=entry.get('link', ''),
                        description=entry.get('description', ''),
                        published_at=published_at or datetime.now(),
                        source=self.source_name
                    )
                    
                    news_items.append(news_item)
                    
                except Exception as e:
                    logger.warning(f"Failed to parse news entry: {e}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"Failed to fetch news from {self.source_name}: {e}")
            return []
    
    async def close(self):
        await self.client.aclose()


class NewsAggregator:
    
    def __init__(self):
        self.sources = [
            RSSNewsSource(config.news_rss_rbc, "RBC"),
            RSSNewsSource("https://lenta.ru/rss", "Lenta.ru"),
            RSSNewsSource("https://www.vedomosti.ru/rss/news", "Ведомости"),
            RSSNewsSource("https://www.kommersant.ru/rss/main.xml", "Коммерсантъ")
        ]
    
    async def fetch_all_news(self, max_age_hours: int = 24) -> List[NewsItem]:
        all_news = []
        
        tasks = [source.fetch_news(max_age_hours) for source in self.sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch from source {i}: {result}")
            else:
                all_news.extend(result)
        
        all_news.sort(key=lambda x: x.published_at or datetime.min, reverse=True)
        
        return all_news
    
    async def get_news_for_securities(self, 
                                    tickers: List[str], 
                                    issuers: List[str],
                                    max_age_hours: int = 24) -> List[NewsItem]:
        """Get news relevant to specific securities."""
        all_news = await self.fetch_all_news(max_age_hours)
        
        relevant_news = []
        search_terms = set()
        
        search_terms.update(ticker.upper() for ticker in tickers)
        
        for issuer in issuers:
            search_terms.add(issuer.upper())
            words = issuer.upper().split()
            for word in words:
                if len(word) > 3:
                    search_terms.add(word)
        
        sector_keywords = self._get_sector_keywords(tickers, issuers)
        search_terms.update(sector_keywords)
        
        market_keywords = {
            'ОБЛИГАЦИИ', 'ОБЛИГАЦИЯ', 'BOND', 'BONDS',
            'АКЦИИ', 'АКЦИЯ', 'SHARE', 'SHARES', 'STOCK', 'STOCKS',
            'ФОНДОВЫЙ', 'ФОНДОВАЯ', 'РЫНОК', 'MARKET',
            'ИНВЕСТИЦИИ', 'INVESTMENT', 'ИНВЕСТИЦИОННЫЙ',
            'ФИНАНСЫ', 'FINANCE', 'ФИНАНСОВЫЙ',
            'БАНК', 'BANK', 'БАНКОВСКИЙ',
            'НЕФТЬ', 'OIL', 'НЕФТЯНОЙ',
            'ГАЗ', 'GAS', 'ГАЗОВЫЙ',
            'ЭНЕРГЕТИКА', 'ENERGY', 'ЭНЕРГЕТИЧЕСКИЙ',
            'МЕТАЛЛУРГИЯ', 'METALLURGY', 'МЕТАЛЛУРГИЧЕСКИЙ',
            'ТЕЛЕКОММУНИКАЦИИ', 'TELECOM', 'ТЕЛЕКОМ',
            'ТРАНСПОРТ', 'TRANSPORT', 'ТРАНСПОРТНЫЙ',
            'СТРОИТЕЛЬСТВО', 'CONSTRUCTION', 'СТРОИТЕЛЬНЫЙ',
            'СЕЛЬСКОЕ ХОЗЯЙСТВО', 'AGRICULTURE', 'СЕЛЬСКОХОЗЯЙСТВЕННЫЙ'
        }
        search_terms.update(market_keywords)
        
        matched_news = []
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        for news_item in all_news:
            if news_item.published_at and news_item.published_at < cutoff_time:
                continue

            title_upper = news_item.title.upper()
            description_upper = (news_item.description or "").upper()
            full_text = f"{title_upper} {description_upper}"

            related_tickers = [ticker for ticker in tickers if ticker.upper() in full_text]
            related_issuers = [issuer for issuer in issuers if issuer.upper() in full_text]

            if not related_tickers and not related_issuers:
                continue

            relevance_score = self._calculate_relevance(news_item, search_terms)
            if relevance_score <= 0:
                continue

            news_item.related_tickers = related_tickers
            news_item.related_issuers = related_issuers
            matched_news.append((news_item, relevance_score))

        matched_news.sort(key=lambda x: x[1], reverse=True)

        filtered_news = []
        seen_links = set()
        for news_item, _ in matched_news:
            if news_item.link in seen_links:
                continue
            filtered_news.append(news_item)
            seen_links.add(news_item.link)
            if len(filtered_news) >= 4:
                break

        return filtered_news
    
    def _get_sector_keywords(self, tickers: List[str], issuers: List[str]) -> Set[str]:
        keywords = set()
        
        ticker_sectors = {
            'SBER': {'СБЕРБАНК', 'БАНК', 'ФИНАНСЫ', 'БАНКОВСКИЙ'},
            'GAZP': {'ГАЗПРОМ', 'ГАЗ', 'ЭНЕРГЕТИКА', 'НЕФТЕГАЗ'},
            'LKOH': {'ЛУКОЙЛ', 'НЕФТЬ', 'НЕФТЯНОЙ', 'ЭНЕРГЕТИКА'},
            'ROSN': {'РОСНЕФТЬ', 'НЕФТЬ', 'НЕФТЯНОЙ', 'ЭНЕРГЕТИКА'},
            'NVTK': {'НОВАТЭК', 'ГАЗ', 'ГАЗОВЫЙ', 'ЭНЕРГЕТИКА'},
            'MAGN': {'МАГНИТ', 'РИТЕЙЛ', 'ТОРГОВЛЯ', 'СЕТЬ'},
            'YNDX': {'ЯНДЕКС', 'ТЕХНОЛОГИИ', 'ИТ', 'ИНТЕРНЕТ'},
            'TCSG': {'ТИНЬКОФФ', 'БАНК', 'ФИНТЕХ', 'БАНКОВСКИЙ'},
            'VKCO': {'ВК', 'ТЕХНОЛОГИИ', 'ИТ', 'СОЦИАЛЬНЫЕ СЕТИ'},
            'AFLT': {'АЭРОФЛОТ', 'АВИАЦИЯ', 'ТРАНСПОРТ', 'АВИАКОМПАНИЯ'}
        }
        
        for ticker in tickers:
            if ticker in ticker_sectors:
                keywords.update(ticker_sectors[ticker])
        
        for issuer in issuers:
            issuer_upper = issuer.upper()
            if 'БАНК' in issuer_upper or 'BANK' in issuer_upper:
                keywords.update({'БАНК', 'ФИНАНСЫ', 'БАНКОВСКИЙ'})
            elif 'НЕФТЬ' in issuer_upper or 'OIL' in issuer_upper:
                keywords.update({'НЕФТЬ', 'ЭНЕРГЕТИКА', 'НЕФТЯНОЙ'})
            elif 'ГАЗ' in issuer_upper or 'GAS' in issuer_upper:
                keywords.update({'ГАЗ', 'ЭНЕРГЕТИКА', 'ГАЗОВЫЙ'})
            elif 'МЕТАЛЛ' in issuer_upper or 'METAL' in issuer_upper:
                keywords.update({'МЕТАЛЛУРГИЯ', 'МЕТАЛЛ', 'МЕТАЛЛУРГИЧЕСКИЙ'})
            elif 'ТЕХНОЛОГИИ' in issuer_upper or 'TECH' in issuer_upper:
                keywords.update({'ТЕХНОЛОГИИ', 'ИТ', 'ИНТЕРНЕТ'})
            elif 'ТРАНСПОРТ' in issuer_upper or 'TRANSPORT' in issuer_upper:
                keywords.update({'ТРАНСПОРТ', 'ТРАНСПОРТНЫЙ'})
            elif 'СТРОИТЕЛЬСТВО' in issuer_upper or 'CONSTRUCTION' in issuer_upper:
                keywords.update({'СТРОИТЕЛЬСТВО', 'СТРОИТЕЛЬНЫЙ'})
        
        return keywords
    
    def _calculate_relevance(self, news_item: NewsItem, search_terms: Set[str]) -> float:
        text = f"{news_item.title} {news_item.description or ''}".upper()
        
        score = 0.0
        matched_terms = []
        
        for term in search_terms:
            if len(term) <= 6 and term.isalpha():
                if term in text:
                    score += 10.0
                    matched_terms.append(term)
        
        for term in search_terms:
            if len(term) > 6:
                if term in text:
                    score += 5.0
                    matched_terms.append(term)
        
        if not matched_terms:
            sector_keywords = {
                'ОБЛИГАЦИИ', 'ОБЛИГАЦИЯ', 'BOND', 'BONDS',
                'АКЦИИ', 'АКЦИЯ', 'SHARE', 'SHARES', 'STOCK', 'STOCKS',
                'ФОНДОВЫЙ', 'ФОНДОВАЯ', 'РЫНОК', 'MARKET',
                'ИНВЕСТИЦИИ', 'INVESTMENT', 'ИНВЕСТИЦИОННЫЙ',
                'ФИНАНСЫ', 'FINANCE', 'ФИНАНСОВЫЙ',
                'БАНК', 'BANK', 'БАНКОВСКИЙ',
                'НЕФТЬ', 'OIL', 'НЕФТЯНОЙ',
                'ГАЗ', 'GAS', 'ГАЗОВЫЙ',
                'ЭНЕРГЕТИКА', 'ENERGY', 'ЭНЕРГЕТИЧЕСКИЙ'
            }
            
            for keyword in sector_keywords:
                if keyword in text:
                    score += 2.0
                    matched_terms.append(keyword)
        
        financial_indicators = ['ПРИБЫЛЬ', 'УБЫТОК', 'ДОХОД', 'РЕВЕНЬЮ', 'КУРС', 'ЦЕНА', 'ТОРГИ', 'БИРЖА']
        for indicator in financial_indicators:
            if indicator in text:
                score += 1.0
        
        news_item.matched_terms = matched_terms
        
        return score
    
    async def close(self):
        for source in self.sources:
            await source.close()


news_aggregator = NewsAggregator()


async def get_news_for_portfolio(tickers: List[str], 
                               issuers: List[str],
                               max_age_hours: int = 24) -> List[NewsItem]:
    """Get news for portfolio securities.

    Args:
        tickers: List of security tickers
        issuers: List of issuer names
        max_age_hours: Maximum age of news in hours

    Returns:
        List of relevant news items
    """
    logger.info(f"Getting news for portfolio: {len(tickers)} tickers, {len(issuers)} issuers")
    logger.info(f"Tickers: {tickers}")
    logger.info(f"Issuers: {issuers}")
    
    result = await news_aggregator.get_news_for_securities(tickers, issuers, max_age_hours)
    
    logger.info(f"Found {len(result)} relevant news items")
    return result


async def get_latest_news(max_items: int = 10, max_age_hours: int = 24) -> List[NewsItem]:
    """Get latest news from all sources.

    Args:
        max_items: Maximum number of news items
        max_age_hours: Maximum age of news in hours

    Returns:
        List of latest news items
    """
    all_news = await news_aggregator.fetch_all_news(max_age_hours)
    return all_news[:max_items]