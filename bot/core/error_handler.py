"""
Централизованная система обработки ошибок для RadarBot 3.0
"""

import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from bot.core.logging import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"           # Незначительные ошибки, не влияют на работу
    MEDIUM = "medium"     # Средние ошибки, могут влиять на функциональность
    HIGH = "high"         # Серьезные ошибки, влияют на работу
    CRITICAL = "critical" # Критические ошибки, останавливают работу


class ErrorCategory(Enum):
    """Категории ошибок"""
    OCR = "ocr"                    # Ошибки OCR
    API = "api"                    # Ошибки внешних API
    DATABASE = "database"          # Ошибки базы данных
    TELEGRAM = "telegram"          # Ошибки Telegram API
    VALIDATION = "validation"      # Ошибки валидации
    NETWORK = "network"            # Сетевые ошибки
    BUSINESS_LOGIC = "business"    # Ошибки бизнес-логики
    UNKNOWN = "unknown"            # Неизвестные ошибки


@dataclass
class ErrorContext:
    """Контекст ошибки"""
    user_id: Optional[str] = None
    phone_number: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorInfo:
    """Информация об ошибке"""
    error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    message: str
    traceback: str
    timestamp: str


class ErrorHandler:
    """Централизованный обработчик ошибок"""
    
    def __init__(self):
        self.error_counters = {}
        self.error_handlers = {}
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Настройка обработчиков по умолчанию"""
        self.error_handlers = {
            ErrorCategory.OCR: self._handle_ocr_error,
            ErrorCategory.API: self._handle_api_error,
            ErrorCategory.DATABASE: self._handle_database_error,
            ErrorCategory.TELEGRAM: self._handle_telegram_error,
            ErrorCategory.VALIDATION: self._handle_validation_error,
            ErrorCategory.NETWORK: self._handle_network_error,
            ErrorCategory.BUSINESS_LOGIC: self._handle_business_error,
            ErrorCategory.UNKNOWN: self._handle_unknown_error,
        }
    
    def handle_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[ErrorContext] = None,
        operation: Optional[str] = None
    ) -> ErrorInfo:
        """
        Обрабатывает ошибку и возвращает информацию о ней
        
        Args:
            error: Исключение
            severity: Уровень серьезности
            category: Категория ошибки
            context: Контекст ошибки
            operation: Название операции
            
        Returns:
            ErrorInfo: Информация об ошибке
        """
        from datetime import datetime
        
        # Создаем контекст если не передан
        if context is None:
            context = ErrorContext(operation=operation)
        
        # Создаем информацию об ошибке
        error_info = ErrorInfo(
            error=error,
            severity=severity,
            category=category,
            context=context,
            message=str(error),
            traceback=traceback.format_exc(),
            timestamp=datetime.now().isoformat()
        )
        
        # Логируем ошибку
        self._log_error(error_info)
        
        # Увеличиваем счетчик ошибок
        self._increment_error_counter(category, severity)
        
        # Вызываем специфичный обработчик
        if category in self.error_handlers:
            try:
                self.error_handlers[category](error_info)
            except Exception as handler_error:
                logger.error(f"Error in error handler for {category}: {handler_error}")
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """Логирует ошибку в зависимости от уровня серьезности"""
        log_data = {
            "error": error_info.message,
            "category": error_info.category.value,
            "severity": error_info.severity.value,
            "user_id": error_info.context.user_id,
            "phone": error_info.context.phone_number,
            "operation": error_info.context.operation,
            "timestamp": error_info.timestamp
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"CRITICAL ERROR: {log_data}")
            logger.critical(f"Traceback: {error_info.traceback}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(f"HIGH ERROR: {log_data}")
            logger.error(f"Traceback: {error_info.traceback}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"MEDIUM ERROR: {log_data}")
        else:
            logger.info(f"LOW ERROR: {log_data}")
    
    def _increment_error_counter(self, category: ErrorCategory, severity: ErrorSeverity):
        """Увеличивает счетчик ошибок"""
        key = f"{category.value}_{severity.value}"
        self.error_counters[key] = self.error_counters.get(key, 0) + 1
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Возвращает статистику ошибок"""
        return {
            "counters": self.error_counters.copy(),
            "total_errors": sum(self.error_counters.values()),
            "categories": list(set(key.split('_')[0] for key in self.error_counters.keys())),
            "severities": list(set(key.split('_')[1] for key in self.error_counters.keys()))
        }
    
    def reset_error_counters(self):
        """Сбрасывает счетчики ошибок"""
        self.error_counters.clear()
    
    # Специфичные обработчики ошибок
    
    def _handle_ocr_error(self, error_info: ErrorInfo):
        """Обработка ошибок OCR"""
        logger.warning(f"OCR error for user {error_info.context.user_id}: {error_info.message}")
        # Можно добавить отправку уведомлений администратору
    
    def _handle_api_error(self, error_info: ErrorInfo):
        """Обработка ошибок внешних API"""
        logger.error(f"API error: {error_info.message}")
        # Можно добавить retry логику или fallback
    
    def _handle_database_error(self, error_info: ErrorInfo):
        """Обработка ошибок базы данных"""
        logger.error(f"Database error: {error_info.message}")
        # Можно добавить проверку соединения с БД
    
    def _handle_telegram_error(self, error_info: ErrorInfo):
        """Обработка ошибок Telegram API"""
        logger.error(f"Telegram error: {error_info.message}")
        # Можно добавить проверку токена бота
    
    def _handle_validation_error(self, error_info: ErrorInfo):
        """Обработка ошибок валидации"""
        logger.warning(f"Validation error: {error_info.message}")
    
    def _handle_network_error(self, error_info: ErrorInfo):
        """Обработка сетевых ошибок"""
        logger.error(f"Network error: {error_info.message}")
        # Можно добавить retry логику
    
    def _handle_business_error(self, error_info: ErrorInfo):
        """Обработка ошибок бизнес-логики"""
        logger.error(f"Business logic error: {error_info.message}")
    
    def _handle_unknown_error(self, error_info: ErrorInfo):
        """Обработка неизвестных ошибок"""
        logger.error(f"Unknown error: {error_info.message}")


# Глобальный экземпляр обработчика ошибок
error_handler = ErrorHandler()


def handle_error(
    error: Exception,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: Optional[ErrorContext] = None,
    operation: Optional[str] = None
) -> ErrorInfo:
    """
    Удобная функция для обработки ошибок
    
    Args:
        error: Исключение
        severity: Уровень серьезности
        category: Категория ошибки
        context: Контекст ошибки
        operation: Название операции
        
    Returns:
        ErrorInfo: Информация об ошибке
    """
    return error_handler.handle_error(error, severity, category, context, operation)


def safe_execute(
    func: Callable,
    *args,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: Optional[ErrorContext] = None,
    operation: Optional[str] = None,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Безопасное выполнение функции с обработкой ошибок
    
    Args:
        func: Функция для выполнения
        *args: Аргументы функции
        severity: Уровень серьезности ошибки
        category: Категория ошибки
        context: Контекст ошибки
        operation: Название операции
        default_return: Значение по умолчанию при ошибке
        **kwargs: Именованные аргументы функции
        
    Returns:
        Результат выполнения функции или default_return при ошибке
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_error(e, severity, category, context, operation)
        return default_return


async def safe_execute_async(
    func: Callable,
    *args,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    context: Optional[ErrorContext] = None,
    operation: Optional[str] = None,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Безопасное выполнение асинхронной функции с обработкой ошибок
    
    Args:
        func: Асинхронная функция для выполнения
        *args: Аргументы функции
        severity: Уровень серьезности ошибки
        category: Категория ошибки
        context: Контекст ошибки
        operation: Название операции
        default_return: Значение по умолчанию при ошибке
        **kwargs: Именованные аргументы функции
        
    Returns:
        Результат выполнения функции или default_return при ошибке
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        handle_error(e, severity, category, context, operation)
        return default_return
