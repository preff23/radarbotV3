import requests
import json
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
import re
from bot.core.logging import get_logger

logger = get_logger(__name__)


class CorpBondsParserV2:
    """Улучшенный парсер для извлечения данных об облигациях с corpbonds.ru"""
    
    def __init__(self):
        self.base_url = "https://corpbonds.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def get_bond_info(self, isin: str) -> Dict[str, Any]:
        """Получает полную информацию об облигации по ISIN"""
        try:
            # Пробуем прямую ссылку на облигацию
            bond_url = f"{self.base_url}/bond/{isin}"
            
            response = self.session.get(bond_url)
            
            if response.status_code == 200:
                return await self._parse_bond_page(bond_url, response.content)
            else:
                return {"error": f"Облигация {isin} не найдена на corpbonds.ru (статус: {response.status_code})"}
            
        except Exception as e:
            logger.error(f"Error parsing bond {isin}: {e}")
            return {"error": f"Ошибка при парсинге облигации {isin}: {str(e)}"}
    
    async def _parse_bond_page(self, bond_url: str, content: bytes) -> Dict[str, Any]:
        """Парсит страницу облигации"""
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            bond_data = {
                "url": bond_url,
                "basic_info": self._extract_basic_info(soup),
                "financial_data": self._extract_financial_data(soup),
                "ratings": self._extract_ratings(soup),
                "events": self._extract_events(soup),
                "issuer_info": self._extract_issuer_info(soup),
                "market_data": self._extract_market_data(soup),
                "raw_html": soup.get_text()  # Для отладки
            }
            
            return bond_data
            
        except Exception as e:
            logger.error(f"Error parsing bond page {bond_url}: {e}")
            return {"error": f"Ошибка при парсинге страницы облигации: {str(e)}"}
    
    def _extract_basic_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает основную информацию об облигации"""
        info = {}
        
        try:
            # Название облигации из заголовка
            title = soup.find('title')
            if title:
                title_text = title.get_text(strip=True)
                # Извлекаем название из заголовка
                if 'Облигация' in title_text:
                    parts = title_text.split('Облигация')
                    if len(parts) > 1:
                        bond_name = parts[1].split('(')[0].strip()
                        info['name'] = bond_name
            
            # ISIN из заголовка
            isin_pattern = r'RU\d{10}'
            title_text = title.get_text() if title else ""
            isin_match = re.search(isin_pattern, title_text)
            if isin_match:
                info['isin'] = isin_match.group()
            
            # Ищем информацию в тексте страницы
            text = soup.get_text()
            
            # Номинал
            nominal_patterns = [
                r'номинал[:\s]*(\d+(?:\.\d+)?)',
                r'номинальн[аяой]\s*стоимост[ьи][:\s]*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*руб'
            ]
            
            for pattern in nominal_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['nominal'] = float(match.group(1))
                    break
            
            # Валюта
            if 'руб' in text.lower() or 'rub' in text.lower():
                info['currency'] = 'RUB'
            
            # Дата погашения
            maturity_patterns = [
                r'погашен[ияе][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'дата\s*погашен[ияе][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})',
                r'до\s*погашен[ияе][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})'
            ]
            
            for pattern in maturity_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['maturity_date'] = match.group(1)
                    break
            
            # Купонная ставка
            coupon_patterns = [
                r'купон[ная\s]*ставк[аи][:\s]*(\d+(?:\.\d+)?)',
                r'ставк[аи]\s*купон[а][:\s]*(\d+(?:\.\d+)?)',
                r'(\d+(?:\.\d+)?)\s*%[:\s]*купон'
            ]
            
            for pattern in coupon_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['coupon_rate'] = float(match.group(1))
                    break
            
            # Частота выплат
            frequency_patterns = [
                r'выплат[аы][:\s]*(ежегодно|ежеквартально|раз в год|раз в квартал|ежемесячно)',
                r'периодичност[ьи][:\s]*(ежегодно|ежеквартально|раз в год|раз в квартал|ежемесячно)'
            ]
            
            for pattern in frequency_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['payment_frequency'] = match.group(1)
                    break
            
            # Размер выпуска
            issue_patterns = [
                r'размер\s*выпуск[а][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'объем\s*выпуск[а][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'выпущено[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in issue_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    info['issue_size'] = match.group(1)
                    break
            
        except Exception as e:
            logger.error(f"Error extracting basic info: {e}")
        
        return info
    
    def _extract_financial_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает финансовые данные эмитента"""
        financial = {}
        
        try:
            text = soup.get_text()
            
            # Выручка
            revenue_patterns = [
                r'выручк[аи][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'доход[ыов][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'revenue[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in revenue_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    financial['revenue'] = match.group(1)
                    break
            
            # Чистая прибыль
            profit_patterns = [
                r'чист[аяой]\s*прибыль[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'net\s*profit[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'прибыль[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in profit_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    financial['net_profit'] = match.group(1)
                    break
            
            # Активы
            assets_patterns = [
                r'актив[ыов][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'assets[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'имуществ[оа][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in assets_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    financial['assets'] = match.group(1)
                    break
            
            # Долг
            debt_patterns = [
                r'долг[аи][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'debt[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'заемн[ыеые]\s*средств[а][:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in debt_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    financial['debt'] = match.group(1)
                    break
            
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
                (r'(S&P|Standard.*Poors?)[:\s]*([A-Z][+-]?)', 'S&P'),
                (r'(Moody\'s|Moodys)[:\s]*([A-Z][0-9])', 'Moody\'s'),
                (r'(Fitch)[:\s]*([A-Z][+-]?)', 'Fitch'),
                (r'(Эксперт РА|ЭкспертРА)[:\s]*([A-Z][+-]?)', 'Эксперт РА'),
                (r'(АКРА|ACRA)[:\s]*([A-Z][+-]?)', 'АКРА'),
                (r'(НРА|НКР)[:\s]*([A-Z][+-]?)', 'НРА')
            ]
            
            for pattern, agency in rating_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        rating_value = match[1] if len(match) > 1 else match[0]
                        ratings.append({
                            'agency': agency,
                            'rating': rating_value.strip(),
                            'date': None
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
                (r'купон[:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})[:\s]*(\d+(?:\.\d+)?)', 'coupon'),
                (r'погашен[ие][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})', 'maturity'),
                (r'оферт[аы][:\s]*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})', 'offer')
            ]
            
            for pattern, event_type in event_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        if len(match) == 2:  # Купон с суммой
                            events.append({
                                'type': event_type,
                                'date': match[0],
                                'amount': match[1]
                            })
                        else:  # Погашение или оферта
                            events.append({
                                'type': event_type,
                                'date': match[0],
                                'amount': None
                            })
                    else:  # Просто дата
                        events.append({
                            'type': event_type,
                            'date': match,
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
            
            # Название эмитента из заголовка
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if 'Облигация' in title_text:
                    parts = title_text.split('Облигация')
                    if len(parts) > 1:
                        issuer_part = parts[1].split('(')[0].strip()
                        issuer['name'] = issuer_part
            
            # Отрасль
            sector_patterns = [
                r'отрасль[:\s]*([^,\n]+)',
                r'сектор[:\s]*([^,\n]+)',
                r'деятельност[ьи][:\s]*([^,\n]+)',
                r'сфера[:\s]*([^,\n]+)'
            ]
            
            for pattern in sector_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    issuer['sector'] = match.group(1).strip()
                    break
            
            # Если не нашли отрасль, определяем по названию эмитента
            if 'sector' not in issuer and 'name' in issuer:
                issuer_name = issuer['name'].lower()
                if 'русгидро' in issuer_name or 'rusgidro' in issuer_name:
                    issuer['sector'] = 'Энергетика'
                elif 'газпром' in issuer_name:
                    issuer['sector'] = 'Нефтегаз'
                elif 'сбербанк' in issuer_name:
                    issuer['sector'] = 'Банковский сектор'
            
        except Exception as e:
            logger.error(f"Error extracting issuer info: {e}")
        
        return issuer
    
    def _extract_market_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Извлекает рыночные данные"""
        market = {}
        
        try:
            text = soup.get_text()
            
            # Текущая цена
            price_patterns = [
                r'цена[:\s]*(\d+(?:\.\d+)?)',
                r'стоимост[ьи][:\s]*(\d+(?:\.\d+)?)',
                r'price[:\s]*(\d+(?:\.\d+)?)'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    market['price'] = float(match.group(1))
                    break
            
            # Доходность
            yield_patterns = [
                r'доходност[ьи][:\s]*(\d+(?:\.\d+)?)',
                r'yield[:\s]*(\d+(?:\.\d+)?)',
                r'доход[:\s]*(\d+(?:\.\d+)?)'
            ]
            
            for pattern in yield_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    market['yield'] = float(match.group(1))
                    break
            
            # Объем торгов
            volume_patterns = [
                r'объем[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'volume[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)',
                r'торгов[:\s]*(\d+(?:\s?\d+)*(?:\.\d+)?)'
            ]
            
            for pattern in volume_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    market['volume'] = match.group(1)
                    break
            
        except Exception as e:
            logger.error(f"Error extracting market data: {e}")
        
        return market


# Создаем экземпляр парсера
corpbonds_parser_v2 = CorpBondsParserV2()
