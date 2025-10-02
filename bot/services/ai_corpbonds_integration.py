"""
Интеграция AI с парсером corpbonds.ru
Позволяет AI активно запрашивать дополнительные данные об облигациях
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from bot.services.corpbonds_service import corpbonds_service
from bot.core.logging import get_logger

logger = get_logger(__name__)


class AICorpBondsIntegration:
    """Интеграция AI с парсером corpbonds.ru для активного получения данных"""
    
    def __init__(self):
        self.service = corpbonds_service
        self._request_cache = {}  # Кэш для запросов AI
    
    async def get_bond_data_for_ai(self, isin: str, context: str = "") -> Dict[str, Any]:
        """
        Получает данные облигации для AI анализа
        
        Args:
            isin: ISIN облигации
            context: Контекст запроса от AI (например, "нужны рейтинги", "анализ рисков")
            
        Returns:
            Структурированные данные для AI
        """
        try:
            logger.info(f"AI requesting bond data for {isin}, context: {context}")
            
            # Получаем данные через сервис
            bond_data = await self.service.get_bond_data(isin)
            
            if "error" in bond_data:
                return {
                    "success": False,
                    "error": bond_data["error"],
                    "isin": isin,
                    "context": context
                }
            
            # Извлекаем детальную информацию
            detailed_info = self._extract_detailed_info(bond_data, context)
            
            # Кэшируем результат
            cache_key = f"{isin}_{context}"
            self._request_cache[cache_key] = detailed_info
            
            return {
                "success": True,
                "isin": isin,
                "context": context,
                "data": detailed_info,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            logger.error(f"Error in AI bond data request for {isin}: {e}")
            return {
                "success": False,
                "error": f"Ошибка получения данных: {str(e)}",
                "isin": isin,
                "context": context
            }
    
    def _extract_detailed_info(self, bond_data: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Извлекает детальную информацию в зависимости от контекста запроса AI"""
        
        info = {
            "basic_info": bond_data.get("basic_info", {}),
            "market_data": bond_data.get("market_data", {}),
            "ratings": bond_data.get("ratings", []),
            "events": bond_data.get("events", []),
            "issuer_info": bond_data.get("issuer_info", {}),
            "financial_data": bond_data.get("financial_data", {}),
            "url": bond_data.get("url", "")
        }
        
        # Добавляем контекстно-специфичную информацию
        if "рейтинг" in context.lower() or "rating" in context.lower():
            info["rating_analysis"] = self._analyze_ratings(bond_data.get("ratings", []))
        
        if "риск" in context.lower() or "risk" in context.lower():
            info["risk_analysis"] = self._analyze_risks(bond_data)
        
        if "доходность" in context.lower() or "yield" in context.lower():
            info["yield_analysis"] = self._analyze_yield(bond_data)
        
        if "ликвидность" in context.lower() or "liquidity" in context.lower():
            info["liquidity_analysis"] = self._analyze_liquidity(bond_data)
        
        return info
    
    def _analyze_ratings(self, ratings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ рейтингов для AI"""
        if not ratings:
            return {"status": "no_ratings", "message": "Рейтинги недоступны"}
        
        # Группируем рейтинги по агентствам
        agencies = {}
        for rating in ratings:
            agency = rating.get("agency", "Unknown")
            if agency not in agencies:
                agencies[agency] = []
            agencies[agency].append(rating.get("rating", "N/A"))
        
        # Определяем общий уровень риска
        risk_level = "medium"
        if any("AAA" in str(ratings) for ratings in agencies.values()):
            risk_level = "low"
        elif any("A" in str(ratings) for ratings in agencies.values()):
            risk_level = "medium"
        elif any("B" in str(ratings) for ratings in agencies.values()):
            risk_level = "high"
        
        return {
            "agencies": agencies,
            "risk_level": risk_level,
            "total_ratings": len(ratings),
            "analysis": f"Общий уровень риска: {risk_level}"
        }
    
    def _analyze_risks(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ рисков для AI"""
        risks = []
        
        # Анализ цены
        market_data = bond_data.get("market_data", {})
        price = market_data.get("price")
        if price:
            if price > 105:
                risks.append("Высокая цена - риск снижения")
            elif price < 95:
                risks.append("Низкая цена - возможен дефолт")
        
        # Анализ доходности
        yield_rate = market_data.get("yield")
        if yield_rate:
            if yield_rate > 20:
                risks.append("Очень высокая доходность - высокий риск")
            elif yield_rate < 5:
                risks.append("Низкая доходность - низкий риск")
        
        # Анализ рейтингов
        ratings = bond_data.get("ratings", [])
        if not ratings:
            risks.append("Отсутствие рейтингов - неопределенный риск")
        
        return {
            "identified_risks": risks,
            "risk_count": len(risks),
            "overall_assessment": "high" if len(risks) > 2 else "medium" if len(risks) > 0 else "low"
        }
    
    def _analyze_yield(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ доходности для AI"""
        market_data = bond_data.get("market_data", {})
        basic_info = bond_data.get("basic_info", {})
        
        yield_rate = market_data.get("yield")
        coupon_rate = basic_info.get("coupon_rate")
        
        analysis = {
            "current_yield": yield_rate,
            "coupon_rate": coupon_rate,
            "yield_vs_coupon": None,
            "attractiveness": "unknown"
        }
        
        if yield_rate and coupon_rate:
            if yield_rate > coupon_rate:
                analysis["yield_vs_coupon"] = "above_coupon"
                analysis["attractiveness"] = "attractive"
            else:
                analysis["yield_vs_coupon"] = "below_coupon"
                analysis["attractiveness"] = "less_attractive"
        
        return analysis
    
    def _analyze_liquidity(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ ликвидности для AI"""
        # Пока базовая реализация, можно расширить
        return {
            "status": "analysis_not_available",
            "message": "Детальный анализ ликвидности требует дополнительных данных"
        }
    
    async def get_multiple_bonds_for_ai(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Получает данные для множественных запросов AI
        
        Args:
            requests: Список запросов [{"isin": "RU000A10BNF8", "context": "анализ рисков"}]
            
        Returns:
            Результаты для всех запросов
        """
        logger.info(f"AI requesting data for {len(requests)} bonds")
        
        # Создаем задачи для параллельного выполнения
        tasks = []
        for req in requests:
            isin = req.get("isin")
            context = req.get("context", "")
            tasks.append(self.get_bond_data_for_ai(isin, context))
        
        try:
            # Выполняем все запросы параллельно
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Формируем результат
            response = {
                "success": True,
                "total_requests": len(requests),
                "successful_requests": 0,
                "failed_requests": 0,
                "results": []
            }
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    response["results"].append({
                        "success": False,
                        "error": str(result),
                        "request": requests[i]
                    })
                    response["failed_requests"] += 1
                else:
                    response["results"].append(result)
                    if result.get("success"):
                        response["successful_requests"] += 1
                    else:
                        response["failed_requests"] += 1
            
            logger.info(f"AI requests completed: {response['successful_requests']}/{response['total_requests']} successful")
            return response
            
        except Exception as e:
            logger.error(f"Error in multiple AI bond requests: {e}")
            return {
                "success": False,
                "error": f"Ошибка обработки запросов: {str(e)}",
                "total_requests": len(requests)
            }
    
    def format_ai_response(self, ai_data: Dict[str, Any]) -> str:
        """Форматирует ответ для передачи в AI промпт"""
        
        if not ai_data.get("success"):
            return f"❌ Ошибка получения данных: {ai_data.get('error', 'Неизвестная ошибка')}"
        
        data = ai_data.get("data", {})
        isin = ai_data.get("isin", "N/A")
        context = ai_data.get("context", "")
        
        formatted = [f"📊 ДАННЫЕ ОБЛИГАЦИИ {isin}"]
        if context:
            formatted.append(f"🎯 Контекст запроса: {context}")
        
        # Основная информация
        basic_info = data.get("basic_info", {})
        if basic_info:
            formatted.append("\n📋 ОСНОВНАЯ ИНФОРМАЦИЯ:")
            formatted.append(f"  Название: {basic_info.get('name', 'N/A')}")
            formatted.append(f"  Номинал: {basic_info.get('nominal', 'N/A')} {basic_info.get('currency', '')}")
            formatted.append(f"  Купонная ставка: {basic_info.get('coupon_rate', 'N/A')}%")
            formatted.append(f"  Дата погашения: {basic_info.get('maturity_date', 'N/A')}")
        
        # Рыночные данные
        market_data = data.get("market_data", {})
        if market_data:
            formatted.append("\n📈 РЫНОЧНЫЕ ДАННЫЕ:")
            formatted.append(f"  Текущая цена: {market_data.get('price', 'N/A')}%")
            formatted.append(f"  Доходность: {market_data.get('yield', 'N/A')}%")
        
        # Рейтинги
        ratings = data.get("ratings", [])
        if ratings:
            formatted.append("\n⭐ РЕЙТИНГИ:")
            for rating in ratings:
                formatted.append(f"  {rating.get('agency', 'N/A')}: {rating.get('rating', 'N/A')}")
        
        # Контекстно-специфичный анализ
        if "rating_analysis" in data:
            rating_analysis = data["rating_analysis"]
            formatted.append(f"\n🔍 АНАЛИЗ РЕЙТИНГОВ:")
            formatted.append(f"  Уровень риска: {rating_analysis.get('risk_level', 'N/A')}")
            formatted.append(f"  Анализ: {rating_analysis.get('analysis', 'N/A')}")
        
        if "risk_analysis" in data:
            risk_analysis = data["risk_analysis"]
            formatted.append(f"\n⚠️ АНАЛИЗ РИСКОВ:")
            formatted.append(f"  Общая оценка: {risk_analysis.get('overall_assessment', 'N/A')}")
            for risk in risk_analysis.get("identified_risks", []):
                formatted.append(f"  • {risk}")
        
        if "yield_analysis" in data:
            yield_analysis = data["yield_analysis"]
            formatted.append(f"\n💰 АНАЛИЗ ДОХОДНОСТИ:")
            formatted.append(f"  Привлекательность: {yield_analysis.get('attractiveness', 'N/A')}")
            formatted.append(f"  Доходность vs Купон: {yield_analysis.get('yield_vs_coupon', 'N/A')}")
        
        # Ссылка на источник
        if data.get("url"):
            formatted.append(f"\n🔗 Источник: {data['url']}")
        
        return "\n".join(formatted)
    
    def clear_cache(self):
        """Очищает кэш запросов AI"""
        self._request_cache.clear()
        logger.info("AI corpbonds cache cleared")


# Создаем глобальный экземпляр
ai_corpbonds = AICorpBondsIntegration()
