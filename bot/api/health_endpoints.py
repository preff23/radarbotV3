"""
API endpoints для мониторинга здоровья системы
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from bot.core.health_monitor import health_monitor
from bot.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/health", tags=["Health Monitoring"])


@router.get("/")
async def get_health_status(force_check: bool = False) -> Dict[str, Any]:
    """Получает статус здоровья системы"""
    try:
        health = await health_monitor.get_system_health(force_check=force_check)
        
        return {
            "success": True,
            "data": {
                "overall_status": health.overall_status.value,
                "timestamp": health.timestamp,
                "uptime_seconds": health.uptime,
                "uptime_hours": round(health.uptime / 3600, 2),
                "version": health.version,
                "components": [
                    {
                        "name": comp.name,
                        "status": comp.status.value,
                        "message": comp.message,
                        "response_time": comp.response_time,
                        "last_check": comp.last_check,
                        "details": comp.details
                    }
                    for comp in health.components
                ]
            }
        }
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health status")


@router.get("/summary")
async def get_health_summary() -> Dict[str, Any]:
    """Получает краткую сводку здоровья системы"""
    try:
        summary = health_monitor.get_health_summary()
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        logger.error(f"Error getting health summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health summary")


@router.get("/components/{component_name}")
async def get_component_health(component_name: str) -> Dict[str, Any]:
    """Получает здоровье конкретного компонента"""
    try:
        # Выполняем проверку конкретного компонента
        if component_name == "database":
            component_health = await health_monitor.check_database_health()
        elif component_name == "cache":
            component_health = await health_monitor.check_cache_health()
        elif component_name == "errors":
            component_health = await health_monitor.check_errors_health()
        elif component_name == "memory":
            component_health = await health_monitor.check_memory_health()
        elif component_name == "external_apis":
            component_health = await health_monitor.check_external_apis_health()
        else:
            raise HTTPException(status_code=404, detail="Component not found")
        
        return {
            "success": True,
            "data": {
                "name": component_health.name,
                "status": component_health.status.value,
                "message": component_health.message,
                "response_time": component_health.response_time,
                "last_check": component_health.last_check,
                "details": component_health.details
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting component health for {component_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get component health")


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Получает метрики системы"""
    try:
        # Получаем метрики из разных источников
        cache_stats = health_monitor.ocr_cache.get_stats() if hasattr(health_monitor, 'ocr_cache') else {}
        error_stats = health_monitor.error_handler.get_error_stats() if hasattr(health_monitor, 'error_handler') else {}
        
        return {
            "success": True,
            "data": {
                "cache": cache_stats,
                "errors": error_stats,
                "uptime": health_monitor.get_uptime(),
                "system": health_monitor.get_health_summary()
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")


@router.post("/check")
async def force_health_check() -> Dict[str, Any]:
    """Принудительно выполняет проверку здоровья всех компонентов"""
    try:
        health = await health_monitor.get_system_health(force_check=True)
        
        return {
            "success": True,
            "message": "Health check completed",
            "data": {
                "overall_status": health.overall_status.value,
                "components_checked": len(health.components),
                "timestamp": health.timestamp
            }
        }
    except Exception as e:
        logger.error(f"Error during forced health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")
