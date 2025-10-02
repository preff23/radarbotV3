"""
API endpoints для работы с данными corpbonds.ru
Предоставляет данные облигаций для мини-приложения
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from bot.services.corpbonds_service import corpbonds_service
from bot.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/corpbonds", tags=["corpbonds"])


class BondDataRequest(BaseModel):
    """Запрос данных об облигации"""
    isin: str


class BondDataResponse(BaseModel):
    """Ответ с данными об облигации"""
    isin: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MultipleBondsRequest(BaseModel):
    """Запрос данных о нескольких облигациях"""
    isins: List[str]


class MultipleBondsResponse(BaseModel):
    """Ответ с данными о нескольких облигациях"""
    success: bool
    data: Dict[str, Dict[str, Any]]
    errors: List[str]


@router.get("/bond/{isin}", response_model=BondDataResponse)
async def get_bond_data(isin: str):
    """
    Получить данные об облигации по ISIN
    
    Args:
        isin: ISIN облигации
        
    Returns:
        Данные об облигации или ошибка
    """
    try:
        logger.info(f"API request for bond data: {isin}")
        
        # Получаем данные через сервис
        bond_data = await corpbonds_service.get_bond_data(isin)
        
        if "error" in bond_data:
            return BondDataResponse(
                isin=isin,
                success=False,
                error=bond_data["error"]
            )
        
        # Извлекаем краткую сводку
        summary = corpbonds_service.extract_bond_summary(bond_data)
        
        return BondDataResponse(
            isin=isin,
            success=True,
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error in get_bond_data API for {isin}: {e}")
        return BondDataResponse(
            isin=isin,
            success=False,
            error=f"Внутренняя ошибка сервера: {str(e)}"
        )


@router.post("/bonds", response_model=MultipleBondsResponse)
async def get_multiple_bonds_data(request: MultipleBondsRequest):
    """
    Получить данные о нескольких облигациях
    
    Args:
        request: Список ISIN облигаций
        
    Returns:
        Данные об облигациях
    """
    try:
        logger.info(f"API request for multiple bonds data: {len(request.isins)} bonds")
        
        if not request.isins:
            return MultipleBondsResponse(
                success=False,
                data={},
                errors=["Список ISIN не может быть пустым"]
            )
        
        # Получаем данные через сервис
        bonds_data = await corpbonds_service.get_multiple_bonds_data(request.isins)
        
        # Формируем ответ
        processed_data = {}
        errors = []
        
        for isin, data in bonds_data.items():
            if "error" in data:
                errors.append(f"{isin}: {data['error']}")
                processed_data[isin] = {"error": data["error"]}
            else:
                summary = corpbonds_service.extract_bond_summary(data)
                processed_data[isin] = summary
        
        return MultipleBondsResponse(
            success=len(errors) == 0,
            data=processed_data,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Error in get_multiple_bonds_data API: {e}")
        return MultipleBondsResponse(
            success=False,
            data={},
            errors=[f"Внутренняя ошибка сервера: {str(e)}"]
        )


@router.get("/bond/{isin}/summary")
async def get_bond_summary(isin: str):
    """
    Получить краткую сводку по облигации для мини-приложения
    
    Args:
        isin: ISIN облигации
        
    Returns:
        Краткая сводка с ключевыми параметрами
    """
    try:
        logger.info(f"API request for bond summary: {isin}")
        
        # Получаем данные
        bond_data = await corpbonds_service.get_bond_data(isin)
        
        if "error" in bond_data:
            raise HTTPException(status_code=404, detail=bond_data["error"])
        
        # Извлекаем краткую сводку
        summary = corpbonds_service.extract_bond_summary(bond_data)
        
        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_bond_summary API for {isin}: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.get("/bonds/summaries")
async def get_bonds_summaries(isins: str = Query(..., description="Список ISIN через запятую")):
    """
    Получить краткие сводки по нескольким облигациям
    
    Args:
        isins: Список ISIN через запятую
        
    Returns:
        Словарь с краткими сводками
    """
    try:
        # Парсим список ISIN
        isin_list = [isin.strip() for isin in isins.split(",") if isin.strip()]
        
        if not isin_list:
            raise HTTPException(status_code=400, detail="Список ISIN не может быть пустым")
        
        logger.info(f"API request for bonds summaries: {len(isin_list)} bonds")
        
        # Получаем данные
        bonds_data = await corpbonds_service.get_multiple_bonds_data(isin_list)
        
        # Формируем ответ
        summaries = {}
        for isin, data in bonds_data.items():
            if "error" not in data:
                summary = corpbonds_service.extract_bond_summary(data)
                if "error" not in summary:
                    summaries[isin] = summary
                else:
                    summaries[isin] = {"error": summary["error"]}
            else:
                summaries[isin] = {"error": data["error"]}
        
        return summaries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_bonds_summaries API: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")


@router.delete("/cache")
async def clear_cache():
    """
    Очистить кэш данных corpbonds.ru
    """
    try:
        corpbonds_service.clear_cache()
        logger.info("CorpBonds cache cleared via API")
        return {"success": True, "message": "Кэш очищен"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при очистке кэша: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса corpbonds.ru
    """
    try:
        # Тестируем на известной облигации
        test_isin = "RU000A10BNF8"  # РусГидро БО-П13
        test_data = await corpbonds_service.get_bond_data(test_isin)
        
        if "error" in test_data:
            return {
                "status": "error",
                "message": f"Ошибка при тестировании: {test_data['error']}"
            }
        
        return {
            "status": "healthy",
            "message": "Сервис corpbonds.ru работает корректно",
            "test_bond": test_isin
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": f"Ошибка проверки: {str(e)}"
        }
