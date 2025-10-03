"""
API endpoints для мониторинга и управления кэшем
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from bot.utils.ocr_cache import ocr_cache
from bot.core.error_handler import error_handler
from bot.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/cache", tags=["Cache Management"])


@router.get("/ocr/stats")
async def get_ocr_cache_stats() -> Dict[str, Any]:
    """Получает статистику кэша OCR"""
    try:
        stats = ocr_cache.get_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting OCR cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")


@router.delete("/ocr/clear")
async def clear_ocr_cache() -> Dict[str, Any]:
    """Очищает кэш OCR"""
    try:
        ocr_cache.clear()
        return {
            "success": True,
            "message": "OCR cache cleared successfully"
        }
    except Exception as e:
        logger.error(f"Error clearing OCR cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.post("/ocr/cleanup")
async def cleanup_ocr_cache() -> Dict[str, Any]:
    """Очищает истекшие записи из кэша OCR"""
    try:
        ocr_cache.cleanup_expired()
        stats = ocr_cache.get_stats()
        return {
            "success": True,
            "message": "OCR cache cleanup completed",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error cleaning up OCR cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup cache")


@router.get("/errors/stats")
async def get_error_stats() -> Dict[str, Any]:
    """Получает статистику ошибок"""
    try:
        stats = error_handler.get_error_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting error stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error stats")


@router.delete("/errors/reset")
async def reset_error_counters() -> Dict[str, Any]:
    """Сбрасывает счетчики ошибок"""
    try:
        error_handler.reset_error_counters()
        return {
            "success": True,
            "message": "Error counters reset successfully"
        }
    except Exception as e:
        logger.error(f"Error resetting error counters: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset error counters")


@router.get("/health")
async def cache_health_check() -> Dict[str, Any]:
    """Проверка здоровья кэша и системы обработки ошибок"""
    try:
        ocr_stats = ocr_cache.get_stats()
        error_stats = error_handler.get_error_stats()
        
        # Проверяем, что кэш работает нормально
        cache_healthy = ocr_stats["cache_size"] < ocr_stats["max_size"] * 0.9  # Не переполнен
        
        # Проверяем, что нет критических ошибок
        critical_errors = error_stats["counters"].get("unknown_critical", 0)
        errors_healthy = critical_errors < 10  # Не более 10 критических ошибок
        
        overall_healthy = cache_healthy and errors_healthy
        
        return {
            "success": True,
            "healthy": overall_healthy,
            "data": {
                "cache": {
                    "healthy": cache_healthy,
                    "stats": ocr_stats
                },
                "errors": {
                    "healthy": errors_healthy,
                    "stats": error_stats
                }
            }
        }
    except Exception as e:
        logger.error(f"Error in cache health check: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e)
        }
