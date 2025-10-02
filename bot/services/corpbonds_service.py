"""
Сервис для работы с данными corpbonds.ru
Интегрирует парсер corpbonds.ru в систему анализа портфеля
"""

import asyncio
from typing import Dict, Any, List, Optional
from bot.utils.corpbonds_parser_v2 import corpbonds_parser_v2
from bot.core.logging import get_logger

logger = get_logger(__name__)


class CorpBondsService:
    """Сервис для получения данных об облигациях с corpbonds.ru"""
    
    def __init__(self):
        self.parser = corpbonds_parser_v2
        self._cache = {}  # Простой кэш для избежания повторных запросов
    
    async def get_bond_data(self, isin: str) -> Dict[str, Any]:
        """
        Получает данные об облигации по ISIN
        
        Args:
            isin: ISIN облигации
            
        Returns:
            Словарь с данными об облигации или ошибкой
        """
        try:
            # Проверяем кэш
            if isin in self._cache:
                logger.info(f"Using cached data for {isin}")
                return self._cache[isin]
            
            logger.info(f"Fetching data for bond {isin} from corpbonds.ru")
            
            # Получаем данные через парсер
            bond_data = await self.parser.get_bond_info(isin)
            
            # Кэшируем результат
            if "error" not in bond_data:
                self._cache[isin] = bond_data
                logger.info(f"Successfully cached data for {isin}")
            else:
                logger.warning(f"Failed to get data for {isin}: {bond_data['error']}")
            
            return bond_data
            
        except Exception as e:
            logger.error(f"Error in CorpBondsService.get_bond_data for {isin}: {e}")
            return {"error": f"Ошибка сервиса corpbonds.ru: {str(e)}"}
    
    async def get_multiple_bonds_data(self, isins: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Получает данные для нескольких облигаций
        
        Args:
            isins: Список ISIN облигаций
            
        Returns:
            Словарь {isin: данные_облигации}
        """
        logger.info(f"Fetching data for {len(isins)} bonds from corpbonds.ru")
        
        # Создаем задачи для параллельного выполнения
        tasks = [self.get_bond_data(isin) for isin in isins]
        
        try:
            # Выполняем все запросы параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Формируем результат
            bond_data = {}
            for i, result in enumerate(results):
                isin = isins[i]
                if isinstance(result, Exception):
                    bond_data[isin] = {"error": f"Ошибка при получении данных: {str(result)}"}
                else:
                    bond_data[isin] = result
            
            successful_count = sum(1 for data in bond_data.values() if "error" not in data)
            logger.info(f"Successfully fetched data for {successful_count}/{len(isins)} bonds")
            
            return bond_data
            
        except Exception as e:
            logger.error(f"Error in CorpBondsService.get_multiple_bonds_data: {e}")
            return {isin: {"error": f"Ошибка сервиса: {str(e)}"} for isin in isins}
    
    def extract_bond_summary(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Извлекает краткую сводку по облигации для AI анализа
        
        Args:
            bond_data: Полные данные об облигации
            
        Returns:
            Краткая сводка с ключевыми параметрами
        """
        if "error" in bond_data:
            return bond_data
        
        try:
            summary = {
                "isin": bond_data.get("basic_info", {}).get("isin", "N/A"),
                "name": bond_data.get("basic_info", {}).get("name", "N/A"),
                "url": bond_data.get("url", ""),
            }
            
            # Основные параметры
            basic_info = bond_data.get("basic_info", {})
            summary.update({
                "nominal": basic_info.get("nominal"),
                "currency": basic_info.get("currency"),
                "coupon_rate": basic_info.get("coupon_rate"),
                "maturity_date": basic_info.get("maturity_date"),
                "payment_frequency": basic_info.get("payment_frequency"),
            })
            
            # Рыночные данные
            market_data = bond_data.get("market_data", {})
            summary.update({
                "current_price": market_data.get("price"),
                "yield": market_data.get("yield"),
            })
            
            # Рейтинги
            ratings = bond_data.get("ratings", [])
            if ratings:
                # Берем первый рейтинг каждого агентства
                unique_ratings = {}
                for rating in ratings:
                    agency = rating.get("agency", "")
                    if agency and agency not in unique_ratings:
                        unique_ratings[agency] = rating.get("rating", "")
                summary["ratings"] = unique_ratings
            
            # Информация об эмитенте
            issuer_info = bond_data.get("issuer_info", {})
            summary.update({
                "issuer_name": issuer_info.get("name"),
                "sector": issuer_info.get("sector"),
            })
            
            # События (ближайшие купоны)
            events = bond_data.get("events", [])
            upcoming_coupons = []
            for event in events[:5]:  # Берем первые 5 событий
                if event.get("type") == "coupon":
                    upcoming_coupons.append({
                        "date": event.get("date"),
                        "amount": event.get("amount")
                    })
            summary["upcoming_coupons"] = upcoming_coupons
            
            return summary
            
        except Exception as e:
            logger.error(f"Error extracting bond summary: {e}")
            return {"error": f"Ошибка при обработке данных: {str(e)}"}
    
    def format_for_ai_analysis(self, bonds_data: Dict[str, Dict[str, Any]]) -> str:
        """
        Форматирует данные облигаций для передачи в AI анализ
        
        Args:
            bonds_data: Словарь с данными облигаций
            
        Returns:
            Отформатированная строка для AI
        """
        if not bonds_data:
            return "Данные corpbonds.ru недоступны"
        
        formatted_data = []
        formatted_data.append("=== ДАННЫЕ CORPBONDS.RU ===")
        
        for isin, data in bonds_data.items():
            if "error" in data:
                formatted_data.append(f"\n{isin}: Ошибка - {data['error']}")
                continue
            
            summary = self.extract_bond_summary(data)
            if "error" in summary:
                formatted_data.append(f"\n{isin}: Ошибка обработки - {summary['error']}")
                continue
            
            formatted_data.append(f"\n--- {summary.get('name', isin)} ({isin}) ---")
            formatted_data.append(f"Ссылка: {summary.get('url', 'N/A')}")
            
            if summary.get("nominal"):
                formatted_data.append(f"Номинал: {summary['nominal']} {summary.get('currency', '')}")
            
            if summary.get("coupon_rate"):
                formatted_data.append(f"Купонная ставка: {summary['coupon_rate']}%")
            
            if summary.get("maturity_date"):
                formatted_data.append(f"Дата погашения: {summary['maturity_date']}")
            
            if summary.get("current_price"):
                formatted_data.append(f"Текущая цена: {summary['current_price']}%")
            
            if summary.get("yield"):
                formatted_data.append(f"Доходность: {summary['yield']}%")
            
            if summary.get("ratings"):
                ratings_str = ", ".join([f"{agency}: {rating}" for agency, rating in summary["ratings"].items()])
                formatted_data.append(f"Рейтинги: {ratings_str}")
            
            if summary.get("issuer_name"):
                formatted_data.append(f"Эмитент: {summary['issuer_name']}")
            
            if summary.get("sector"):
                formatted_data.append(f"Отрасль: {summary['sector']}")
            
            if summary.get("upcoming_coupons"):
                formatted_data.append("Ближайшие купоны:")
                for coupon in summary["upcoming_coupons"]:
                    formatted_data.append(f"  {coupon['date']}: {coupon['amount']} руб")
        
        return "\n".join(formatted_data)
    
    def clear_cache(self):
        """Очищает кэш данных"""
        self._cache.clear()
        logger.info("CorpBonds cache cleared")


# Создаем глобальный экземпляр сервиса
corpbonds_service = CorpBondsService()
