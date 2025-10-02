"""
API endpoints для AI запросов к corpbonds.ru
Позволяет AI активно запрашивать дополнительные данные об облигациях
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from bot.services.ai_corpbonds_integration import ai_corpbonds
from bot.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ai/corpbonds", tags=["ai-corpbonds"])


class AIBondRequest(BaseModel):
    """Запрос данных облигации от AI"""
    isin: str
    context: str = ""  # Контекст запроса (например, "анализ рисков", "рейтинги")


class AIMultipleBondsRequest(BaseModel):
    """Запрос данных нескольких облигаций от AI"""
    requests: List[AIBondRequest]


class AIBondResponse(BaseModel):
    """Ответ с данными облигации для AI"""
    success: bool
    isin: str
    context: str
    data: Dict[str, Any] = {}
    error: str = ""
    formatted_for_ai: str = ""


@router.post("/bond", response_model=AIBondResponse)
async def ai_get_bond_data(request: AIBondRequest):
    """
    Получить данные облигации для AI анализа
    
    Args:
        request: Запрос с ISIN и контекстом
        
    Returns:
        Структурированные данные для AI
    """
    try:
        logger.info(f"AI requesting bond data: {request.isin}, context: {request.context}")
        
        # Получаем данные через AI интеграцию
        result = await ai_corpbonds.get_bond_data_for_ai(request.isin, request.context)
        
        if not result.get("success"):
            return AIBondResponse(
                success=False,
                isin=request.isin,
                context=request.context,
                error=result.get("error", "Unknown error")
            )
        
        # Форматируем для AI
        formatted = ai_corpbonds.format_ai_response(result)
        
        return AIBondResponse(
            success=True,
            isin=request.isin,
            context=request.context,
            data=result.get("data", {}),
            formatted_for_ai=formatted
        )
        
    except Exception as e:
        logger.error(f"Error in AI bond data request: {e}")
        return AIBondResponse(
            success=False,
            isin=request.isin,
            context=request.context,
            error=f"Внутренняя ошибка: {str(e)}"
        )


@router.post("/bonds", response_model=Dict[str, Any])
async def ai_get_multiple_bonds_data(request: AIMultipleBondsRequest):
    """
    Получить данные нескольких облигаций для AI анализа
    
    Args:
        request: Список запросов с ISIN и контекстами
        
    Returns:
        Результаты для всех запросов
    """
    try:
        logger.info(f"AI requesting data for {len(request.requests)} bonds")
        
        # Конвертируем в формат для сервиса
        requests_data = [
            {"isin": req.isin, "context": req.context}
            for req in request.requests
        ]
        
        # Получаем данные
        result = await ai_corpbonds.get_multiple_bonds_for_ai(requests_data)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        # Форматируем результаты для AI
        formatted_results = []
        for i, res in enumerate(result.get("results", [])):
            if res.get("success"):
                formatted = ai_corpbonds.format_ai_response(res)
                formatted_results.append({
                    "success": True,
                    "isin": res.get("isin"),
                    "context": res.get("context"),
                    "data": res.get("data", {}),
                    "formatted_for_ai": formatted
                })
            else:
                formatted_results.append({
                    "success": False,
                    "isin": res.get("isin"),
                    "context": res.get("context"),
                    "error": res.get("error", "Unknown error")
                })
        
        return {
            "success": True,
            "total_requests": result.get("total_requests", 0),
            "successful_requests": result.get("successful_requests", 0),
            "failed_requests": result.get("failed_requests", 0),
            "results": formatted_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI multiple bonds request: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@router.get("/bond/{isin}/analysis")
async def ai_get_bond_analysis(isin: str, analysis_type: str = "full"):
    """
    Получить анализ облигации для AI
    
    Args:
        isin: ISIN облигации
        analysis_type: Тип анализа (full, risk, rating, yield, liquidity)
        
    Returns:
        Анализ облигации
    """
    try:
        logger.info(f"AI requesting {analysis_type} analysis for {isin}")
        
        # Определяем контекст на основе типа анализа
        context_map = {
            "full": "полный анализ",
            "risk": "анализ рисков",
            "rating": "анализ рейтингов",
            "yield": "анализ доходности",
            "liquidity": "анализ ликвидности"
        }
        
        context = context_map.get(analysis_type, "полный анализ")
        
        # Получаем данные
        result = await ai_corpbonds.get_bond_data_for_ai(isin, context)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Bond not found"))
        
        # Форматируем для AI
        formatted = ai_corpbonds.format_ai_response(result)
        
        return {
            "success": True,
            "isin": isin,
            "analysis_type": analysis_type,
            "data": result.get("data", {}),
            "formatted_analysis": formatted,
            "timestamp": result.get("timestamp")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AI bond analysis request: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")


@router.get("/health")
async def ai_corpbonds_health():
    """
    Проверка работоспособности AI интеграции с corpbonds.ru
    """
    try:
        # Тестируем на известной облигации
        test_result = await ai_corpbonds.get_bond_data_for_ai("RU000A10BNF8", "тест")
        
        if test_result.get("success"):
            return {
                "status": "healthy",
                "message": "AI интеграция с corpbonds.ru работает корректно",
                "test_bond": "RU000A10BNF8",
                "cache_size": len(ai_corpbonds._request_cache)
            }
        else:
            return {
                "status": "error",
                "message": f"Ошибка тестирования: {test_result.get('error')}"
            }
        
    except Exception as e:
        logger.error(f"AI corpbonds health check failed: {e}")
        return {
            "status": "error",
            "message": f"Ошибка проверки: {str(e)}"
        }


@router.delete("/cache")
async def clear_ai_cache():
    """
    Очистить кэш AI запросов к corpbonds.ru
    """
    try:
        ai_corpbonds.clear_cache()
        logger.info("AI corpbonds cache cleared via API")
        return {"success": True, "message": "Кэш AI запросов очищен"}
    except Exception as e:
        logger.error(f"Error clearing AI cache: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке кэша: {str(e)}")
