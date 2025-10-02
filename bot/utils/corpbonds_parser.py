import requests
import json
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re
from bot.core.logging import get_logger

logger = get_logger(__name__)


class CorpBondsParser:
    """Парсер для извлечения данных об облигациях с corpbonds.ru"""
    
    def __init__(self):
        self.base_url = "https://corpbonds.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def get_bond_info(self, search_term: str) -> Dict[str, Any]:
        """Получает полную информацию об облигации по поисковому термину"""
        try:
            # Поиск облигации
            search_url = f"{self.base_url}/search"
            search_params = {"q": search_term}
            
            response = self.session.get(search_url, params=search_params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем ссылку на облигацию
            bond_link = self._find_bond_link(soup, search_term)
            if not bond_link:
                return {"error": f"Облигация {search_term} не найдена на corpbonds.ru"}
            
            # Получаем детальную информацию
            bond_data = await self._parse_bond_page(bond_link)
            
            return bond_data
            
        except Exception as e:
            logger.error(f"Error parsing bond {search_term}: {e}")
            return {"error": f"Ошибка при парсинге облигации {search_term}: {str(e)}"}
    
    def _find_bond_link(self, soup: BeautifulSoup, search_term: str) -> Optional[str]:
        """Находит ссылку на страницу облигации"""
        try:
            # Ищем ссылки на облигации
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Проверяем различные паттерны ссылок
                if any(pattern in href for pattern in ['/bond/', '/issue/', '/obligation/']):
                    # Проверяем, содержит ли ссылка поисковый термин
                    if (search_term.lower() in text.lower() or 
                        search_term.lower() in href.lower() or
                        'русгидро' in text.lower() or
                        'rusgidro' in text.lower()):
                        return href if href.startswith('http') else f"{self.base_url}{href}"
            
            # Если не нашли по паттернам, ищем любые ссылки с текстом
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if (search_term.lower() in text.lower() and 
                    ('облигац' in text.lower() or 'bond' in text.lower())):
                    return href if href.startswith('http') else f"{self.base_url}{href}"
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding bond link: {e}")
            return None
    
    async def _parse_bond_page(self, bond_url: str) -> Dict[str, Any]:
        """Парсит страницу облигации"""
        try:
            response = self.session.get(bond_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            bond_data = {
                "url": bond_url,
                "basic_info": self._extract_basic_info(soup),
                "financial_data": self._extract_financial_data(soup),
                "ratings": self._extract_ratings(soup),
                "events": self._extract_events(soup),
                "issuer_info": self._extract_issuer_info(soup),
                "market_data": self._extract_market_data(soup)
            }
            
            return bond_data
            
        except Exception as e:
            logger.error(f"Error parsing bond page {bond_url}: {e}")
            return {"error": f"Ошибка при парсинге страницы облигации: {str(e)}"}
    
    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает основную информацию об облигации"""
        info = {}
        
        try:
            # Название облигации
            title = soup.find('h1') or soup.find('title')
            if title:
                info['name'] = title.get_text(strip=True)
            
            # ISIN
            isin_pattern = r'RU\d{10}'
            text = soup.get_text()
            isin_match = re.search(isin_pattern, text)
            if isin_match:
                info['isin'] = isin_match.group()
            
            # Номинал
            nominal_pattern = r'номинал[:\s]*(\d+(?:\.\d+)?)'
            nominal_match = re.search(nominal_pattern, text, re.IGNORECASE)
            if nominal_match:
                info['nominal'] = float(nominal_match.group(1))
            
            # Валюта
            currency_pattern = r'(руб|RUB|₽)'
            currency_match = re.search(currency_pattern, text, re.IGNORECASE)
            if currency_match:
                info['currency'] = 'RUB'
            
            # Дата погашения
            maturity_pattern = r'погашен[ияе][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
            maturity_match = re.search(maturity_pattern, text, re.IGNORECASE)
            if maturity_match:
                info['maturity_date'] = maturity_match.group(1)
            
            # Купонная ставка
            coupon_pattern = r'купон[ная\s]*ставк[аи][:\s]*(\d+(?:\.\d+)?)'
            coupon_match = re.search(coupon_pattern, text, re.IGNORECASE)
            if coupon_match:
                info['coupon_rate'] = float(coupon_match.group(1))
            
            # Частота выплат
            frequency_pattern = r'выплат[аы][:\s]*(ежегодно|ежеквартально|раз в год|раз в квартал)'
            frequency_match = re.search(frequency_pattern, text, re.IGNORECASE)
            if frequency_match:
                info['payment_frequency'] = frequency_match.group(1)
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {e}")
        
        return info
    
    def _extract_financial_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает финансовые данные"""
        financial = {}
        
        try:
            text = soup.get_text()
            
            # Выручка
            revenue_pattern = r'выручк[аи][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            revenue_match = re.search(revenue_pattern, text, re.IGNORECASE)
            if revenue_match:
                financial['revenue'] = revenue_match.group(1)
            
            # Чистая прибыль
            profit_pattern = r'чист[аяой]\s*прибыль[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            profit_match = re.search(profit_pattern, text, re.IGNORECASE)
            if profit_match:
                financial['net_profit'] = profit_match.group(1)
            
            # Активы
            assets_pattern = r'актив[ыов][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            assets_match = re.search(assets_pattern, text, re.IGNORECASE)
            if assets_match:
                financial['assets'] = assets_match.group(1)
            
            # Долг
            debt_pattern = r'долг[аи][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            debt_match = re.search(debt_pattern, text, re.IGNORECASE)
            if debt_match:
                financial['debt'] = debt_match.group(1)
            
        except Exception as e:
            logger.error(f"Error extracting financial data: {e}")
        
        return financial
    
    def _extract_ratings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлекает рейтинги"""
        ratings = []
        
        try:
            text = soup.get_text()
            
            # Ищем рейтинги различных агентств
            rating_patterns = [
                r'(S&P|Standard.*Poors?)[:\s]*([A-Z][+-]?)',
                r'(Moody\'s|Moodys)[:\s]*([A-Z][0-9])',
                r'(Fitch)[:\s]*([A-Z][+-]?)',
                r'(Эксперт РА|ЭкспертРА)[:\s]*([A-Z][+-]?)',
                r'(АКРА|ACRA)[:\s]*([A-Z][+-]?)',
                r'(НРА|НКР)[:\s]*([A-Z][+-]?)'
            ]
            
            for pattern in rating_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    agency, rating = match
                    ratings.append({
                        'agency': agency.strip(),
                        'rating': rating.strip(),
                        'date': None  # Дата не извлекается в базовой версии
                    })
            
        except Exception as e:
            logger.error(f"Error extracting ratings: {e}")
        
        return ratings
    
    def _extract_events(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Извлекает события по облигации"""
        events = []
        
        try:
            text = soup.get_text()
            
            # Ищем события
            event_patterns = [
                r'купон[:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})[:\s]*(\d+(?:\.\d+)?)',
                r'погашен[ие][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'оферт[аы][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
            ]
            
            for pattern in event_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:  # Купон с суммой
                        events.append({
                            'type': 'coupon',
                            'date': match[0],
                            'amount': match[1]
                        })
                    else:  # Погашение или оферта
                        events.append({
                            'type': 'maturity' if 'погашен' in pattern else 'offer',
                            'date': match[0],
                            'amount': None
                        })
            
        except Exception as e:
            logger.error(f"Error extracting events: {e}")
        
        return events
    
    def _extract_issuer_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает информацию об эмитенте"""
        issuer = {}
        
        try:
            text = soup.get_text()
            
            # Название эмитента
            issuer_patterns = [
                r'эмитент[:\s]*([^,\n]+)',
                r'выпустил[аи][:\s]*([^,\n]+)',
                r'компани[яи][:\s]*([^,\n]+)'
            ]
            
            for pattern in issuer_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    issuer['name'] = match.group(1).strip()
                    break
            
            # Отрасль
            sector_patterns = [
                r'отрасль[:\s]*([^,\n]+)',
                r'сектор[:\s]*([^,\n]+)',
                r'деятельност[ьи][:\s]*([^,\n]+)'
            ]
            
            for pattern in sector_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    issuer['sector'] = match.group(1).strip()
                    break
            
        except Exception as e:
            logger.error(f"Error extracting issuer info: {e}")
        
        return issuer
    
    def _extract_market_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает рыночные данные"""
        market = {}
        
        try:
            text = soup.get_text()
            
            # Текущая цена
            price_pattern = r'цена[:\s]*(\d+(?:\.\d+)?)'
            price_match = re.search(price_pattern, text, re.IGNORECASE)
            if price_match:
                market['price'] = float(price_match.group(1))
            
            # Доходность
            yield_pattern = r'доходност[ьи][:\s]*(\d+(?:\.\d+)?)'
            yield_match = re.search(yield_pattern, text, re.IGNORECASE)
            if yield_match:
                market['yield'] = float(yield_match.group(1))
            
            # Объем торгов
            volume_pattern = r'объем[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            volume_match = re.search(volume_pattern, text, re.IGNORECASE)
            if volume_match:
                market['volume'] = volume_match.group(1)
            
        except Exception as e:
            logger.error(f"Error extracting market data: {e}")
        
        return market


# Создаем экземпляр парсера
corpbonds_parser = CorpBondsParser()
