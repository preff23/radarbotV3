"""
Система мониторинга здоровья приложения
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from bot.core.logging import get_logger
from bot.core.db import db_manager
from bot.core.config import config
from bot.utils.ocr_cache import ocr_cache
from bot.core.error_handler import error_handler

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Статусы здоровья компонентов"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Здоровье отдельного компонента"""
    name: str
    status: HealthStatus
    message: str
    response_time: Optional[float] = None
    last_check: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


@dataclass
class SystemHealth:
    """Общее здоровье системы"""
    overall_status: HealthStatus
    components: List[ComponentHealth]
    timestamp: float
    uptime: float
    version: str = "3.0"


class HealthMonitor:
    """Монитор здоровья системы"""
    
    def __init__(self):
        self.start_time = time.time()
        self.last_checks = {}
        self.check_intervals = {
            "database": 30,      # 30 секунд
            "cache": 60,         # 1 минута
            "errors": 60,        # 1 минута
            "memory": 120,       # 2 минуты
            "external_apis": 300 # 5 минут
        }
    
    def get_uptime(self) -> float:
        """Возвращает время работы в секундах"""
        return time.time() - self.start_time
    
    async def check_database_health(self) -> ComponentHealth:
        """Проверяет здоровье базы данных"""
        start_time = time.time()
        
        try:
            # Простой запрос к БД
            users_count = db_manager.get_users_count()
            response_time = time.time() - start_time
            
            if response_time > 5.0:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.WARNING,
                    message=f"Database slow response: {response_time:.2f}s",
                    response_time=response_time,
                    last_check=time.time(),
                    details={"users_count": users_count}
                )
            elif response_time > 10.0:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.CRITICAL,
                    message=f"Database very slow: {response_time:.2f}s",
                    response_time=response_time,
                    last_check=time.time(),
                    details={"users_count": users_count}
                )
            else:
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database responding normally",
                    response_time=response_time,
                    last_check=time.time(),
                    details={"users_count": users_count}
                )
                
        except Exception as e:
            return ComponentHealth(
                name="database",
                status=HealthStatus.CRITICAL,
                message=f"Database error: {str(e)}",
                response_time=time.time() - start_time,
                last_check=time.time()
            )
    
    async def check_cache_health(self) -> ComponentHealth:
        """Проверяет здоровье кэша"""
        try:
            stats = ocr_cache.get_stats()
            
            # Проверяем заполненность кэша
            cache_usage = stats["cache_size"] / stats["max_size"]
            
            if cache_usage > 0.9:
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.WARNING,
                    message=f"Cache almost full: {cache_usage:.1%}",
                    last_check=time.time(),
                    details=stats
                )
            elif cache_usage > 0.95:
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.CRITICAL,
                    message=f"Cache critically full: {cache_usage:.1%}",
                    last_check=time.time(),
                    details=stats
                )
            else:
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.HEALTHY,
                    message=f"Cache healthy: {cache_usage:.1%} usage",
                    last_check=time.time(),
                    details=stats
                )
                
        except Exception as e:
            return ComponentHealth(
                name="cache",
                status=HealthStatus.CRITICAL,
                message=f"Cache error: {str(e)}",
                last_check=time.time()
            )
    
    async def check_errors_health(self) -> ComponentHealth:
        """Проверяет здоровье системы ошибок"""
        try:
            stats = error_handler.get_error_stats()
            total_errors = stats["total_errors"]
            
            # Проверяем количество критических ошибок
            critical_errors = stats["counters"].get("unknown_critical", 0)
            high_errors = stats["counters"].get("unknown_high", 0)
            
            if critical_errors > 10:
                return ComponentHealth(
                    name="errors",
                    status=HealthStatus.CRITICAL,
                    message=f"Too many critical errors: {critical_errors}",
                    last_check=time.time(),
                    details=stats
                )
            elif critical_errors > 5 or high_errors > 20:
                return ComponentHealth(
                    name="errors",
                    status=HealthStatus.WARNING,
                    message=f"Elevated error levels: {critical_errors} critical, {high_errors} high",
                    last_check=time.time(),
                    details=stats
                )
            else:
                return ComponentHealth(
                    name="errors",
                    status=HealthStatus.HEALTHY,
                    message=f"Error levels normal: {total_errors} total errors",
                    last_check=time.time(),
                    details=stats
                )
                
        except Exception as e:
            return ComponentHealth(
                name="errors",
                status=HealthStatus.CRITICAL,
                message=f"Error monitoring failed: {str(e)}",
                last_check=time.time()
            )
    
    async def check_memory_health(self) -> ComponentHealth:
        """Проверяет использование памяти"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Простые пороги для памяти
            if memory_mb > 1000:  # 1GB
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.WARNING,
                    message=f"High memory usage: {memory_mb:.1f}MB",
                    last_check=time.time(),
                    details={"memory_mb": memory_mb}
                )
            elif memory_mb > 2000:  # 2GB
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.CRITICAL,
                    message=f"Very high memory usage: {memory_mb:.1f}MB",
                    last_check=time.time(),
                    details={"memory_mb": memory_mb}
                )
            else:
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.HEALTHY,
                    message=f"Memory usage normal: {memory_mb:.1f}MB",
                    last_check=time.time(),
                    details={"memory_mb": memory_mb}
                )
                
        except ImportError:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not available for memory monitoring",
                last_check=time.time()
            )
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.CRITICAL,
                message=f"Memory check failed: {str(e)}",
                last_check=time.time()
            )
    
    async def check_external_apis_health(self) -> ComponentHealth:
        """Проверяет доступность внешних API"""
        try:
            import httpx
            
            # Проверяем доступность основных API
            checks = []
            
            # MOEX API
            try:
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get("https://iss.moex.com/iss/engines/stock/markets/index/boards/SNDX/securities/IMOEX.json")
                    checks.append(("MOEX", response.status_code == 200))
            except:
                checks.append(("MOEX", False))
            
            # T-Bank API (если настроен)
            try:
                if config.tin_token:
                    async with httpx.AsyncClient(timeout=5) as client:
                        headers = {"Authorization": f"Bearer {config.tin_token}"}
                        response = await client.get(f"{config.tin_api_base}/tinkoff.public.invest.api.contract.v1.InstrumentsService/Shares", headers=headers)
                        checks.append(("T-Bank", response.status_code == 200))
                else:
                    checks.append(("T-Bank", None))  # Не настроен
            except:
                checks.append(("T-Bank", False))
            
            # Анализируем результаты
            available_apis = [name for name, status in checks if status is True]
            failed_apis = [name for name, status in checks if status is False]
            unavailable_apis = [name for name, status in checks if status is None]
            
            if len(failed_apis) > len(available_apis):
                return ComponentHealth(
                    name="external_apis",
                    status=HealthStatus.CRITICAL,
                    message=f"Multiple API failures: {failed_apis}",
                    last_check=time.time(),
                    details={
                        "available": available_apis,
                        "failed": failed_apis,
                        "unavailable": unavailable_apis
                    }
                )
            elif failed_apis:
                return ComponentHealth(
                    name="external_apis",
                    status=HealthStatus.WARNING,
                    message=f"Some API failures: {failed_apis}",
                    last_check=time.time(),
                    details={
                        "available": available_apis,
                        "failed": failed_apis,
                        "unavailable": unavailable_apis
                    }
                )
            else:
                return ComponentHealth(
                    name="external_apis",
                    status=HealthStatus.HEALTHY,
                    message=f"All APIs available: {available_apis}",
                    last_check=time.time(),
                    details={
                        "available": available_apis,
                        "failed": failed_apis,
                        "unavailable": unavailable_apis
                    }
                )
                
        except Exception as e:
            return ComponentHealth(
                name="external_apis",
                status=HealthStatus.CRITICAL,
                message=f"API health check failed: {str(e)}",
                last_check=time.time()
            )
    
    async def get_system_health(self, force_check: bool = False) -> SystemHealth:
        """Получает общее здоровье системы"""
        current_time = time.time()
        components = []
        
        # Проверяем каждый компонент
        checks = [
            ("database", self.check_database_health),
            ("cache", self.check_cache_health),
            ("errors", self.check_errors_health),
            ("memory", self.check_memory_health),
            ("external_apis", self.check_external_apis_health)
        ]
        
        for component_name, check_func in checks:
            # Проверяем, нужно ли выполнять проверку
            if not force_check and component_name in self.last_checks:
                interval = self.check_intervals.get(component_name, 60)
                if current_time - self.last_checks[component_name] < interval:
                    # Используем кэшированный результат
                    continue
            
            try:
                component_health = await check_func()
                components.append(component_health)
                self.last_checks[component_name] = current_time
            except Exception as e:
                logger.error(f"Error checking {component_name} health: {e}")
                components.append(ComponentHealth(
                    name=component_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {str(e)}",
                    last_check=current_time
                ))
        
        # Определяем общий статус
        if any(c.status == HealthStatus.CRITICAL for c in components):
            overall_status = HealthStatus.CRITICAL
        elif any(c.status == HealthStatus.WARNING for c in components):
            overall_status = HealthStatus.WARNING
        elif all(c.status == HealthStatus.HEALTHY for c in components):
            overall_status = HealthStatus.HEALTHY
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            timestamp=current_time,
            uptime=self.get_uptime()
        )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Возвращает краткую сводку здоровья системы"""
        return {
            "uptime_seconds": self.get_uptime(),
            "uptime_hours": self.get_uptime() / 3600,
            "last_checks": self.last_checks,
            "check_intervals": self.check_intervals
        }


# Глобальный экземпляр монитора
health_monitor = HealthMonitor()
