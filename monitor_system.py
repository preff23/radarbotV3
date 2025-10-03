#!/usr/bin/env python3
"""
Скрипт для мониторинга системы в реальном времени
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.core.logging import setup_logging, get_logger
from bot.core.health_monitor import health_monitor, HealthStatus

setup_logging()
logger = get_logger(__name__)


def print_header():
    """Печатает заголовок мониторинга"""
    print("🔍 СИСТЕМА МОНИТОРИНГА RADARBOT 3.0")
    print("=" * 60)
    print("Нажмите Ctrl+C для выхода")
    print("=" * 60)


def get_status_emoji(status: HealthStatus) -> str:
    """Возвращает эмодзи для статуса"""
    if status == HealthStatus.HEALTHY:
        return "✅"
    elif status == HealthStatus.WARNING:
        return "⚠️"
    elif status == HealthStatus.CRITICAL:
        return "❌"
    else:
        return "❓"


def format_uptime(uptime_seconds: float) -> str:
    """Форматирует время работы"""
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


async def display_health_status():
    """Отображает статус здоровья системы"""
    try:
        health = await health_monitor.get_system_health(force_check=True)
        
        # Очищаем экран (работает в большинстве терминалов)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print_header()
        
        # Общий статус
        overall_emoji = get_status_emoji(health.overall_status)
        uptime_str = format_uptime(health.uptime)
        
        print(f"\n📊 ОБЩИЙ СТАТУС: {overall_emoji} {health.overall_status.value.upper()}")
        print(f"⏱️ Время работы: {uptime_str}")
        print(f"🕐 Последняя проверка: {time.strftime('%H:%M:%S', time.localtime(health.timestamp))}")
        
        # Компоненты
        print(f"\n🔧 КОМПОНЕНТЫ ({len(health.components)}):")
        print("-" * 60)
        
        for component in health.components:
            emoji = get_status_emoji(component.status)
            response_time = f" ({component.response_time:.2f}s)" if component.response_time else ""
            
            print(f"{emoji} {component.name.upper()}: {component.status.value}")
            print(f"   📝 {component.message}{response_time}")
            
            if component.details:
                for key, value in component.details.items():
                    print(f"   📊 {key}: {value}")
            print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        print("-" * 30)
        
        critical_components = [c for c in health.components if c.status == HealthStatus.CRITICAL]
        warning_components = [c for c in health.components if c.status == HealthStatus.WARNING]
        
        if critical_components:
            print("🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ:")
            for comp in critical_components:
                print(f"   • {comp.name}: {comp.message}")
        
        if warning_components:
            print("⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            for comp in warning_components:
                print(f"   • {comp.name}: {comp.message}")
        
        if not critical_components and not warning_components:
            print("✅ Все системы работают нормально")
        
        return health.overall_status
        
    except Exception as e:
        print(f"❌ Ошибка мониторинга: {e}")
        return HealthStatus.CRITICAL


async def monitor_loop(interval: int = 30):
    """Основной цикл мониторинга"""
    print("🚀 Запуск мониторинга...")
    
    try:
        while True:
            status = await display_health_status()
            
            # Если критический статус, увеличиваем частоту проверок
            if status == HealthStatus.CRITICAL:
                print(f"\n⏰ Следующая проверка через 10 секунд...")
                await asyncio.sleep(10)
            else:
                print(f"\n⏰ Следующая проверка через {interval} секунд...")
                await asyncio.sleep(interval)
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Мониторинг остановлен пользователем")
    except Exception as e:
        print(f"\n💥 Критическая ошибка мониторинга: {e}")


async def quick_check():
    """Быстрая проверка системы"""
    print("🔍 БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ")
    print("=" * 40)
    
    health = await health_monitor.get_system_health(force_check=True)
    
    print(f"📊 Общий статус: {get_status_emoji(health.overall_status)} {health.overall_status.value}")
    print(f"⏱️ Время работы: {format_uptime(health.uptime)}")
    print(f"🔧 Компонентов: {len(health.components)}")
    
    print("\n📋 Детали компонентов:")
    for component in health.components:
        emoji = get_status_emoji(component.status)
        print(f"  {emoji} {component.name}: {component.message}")


async def show_metrics():
    """Показывает метрики системы"""
    print("📊 МЕТРИКИ СИСТЕМЫ")
    print("=" * 30)
    
    try:
        from bot.utils.ocr_cache import ocr_cache
        from bot.core.error_handler import error_handler
        
        # Метрики кэша
        cache_stats = ocr_cache.get_stats()
        print(f"🗄️ OCR Cache:")
        print(f"   Размер: {cache_stats['cache_size']}/{cache_stats['max_size']}")
        print(f"   Hit Rate: {cache_stats['hit_rate']}%")
        print(f"   Запросов: {cache_stats['total_requests']}")
        
        # Метрики ошибок
        error_stats = error_handler.get_error_stats()
        print(f"\n🚨 Ошибки:")
        print(f"   Всего: {error_stats['total_errors']}")
        print(f"   Категории: {', '.join(error_stats['categories'])}")
        print(f"   Уровни: {', '.join(error_stats['severities'])}")
        
        # Время работы
        uptime = health_monitor.get_uptime()
        print(f"\n⏱️ Время работы: {format_uptime(uptime)}")
        
    except Exception as e:
        print(f"❌ Ошибка получения метрик: {e}")


def show_help():
    """Показывает справку"""
    print("🔍 СИСТЕМА МОНИТОРИНГА RADARBOT 3.0")
    print("=" * 50)
    print()
    print("Использование:")
    print("  python monitor_system.py [команда]")
    print()
    print("Команды:")
    print("  monitor     - Запуск непрерывного мониторинга (по умолчанию)")
    print("  check       - Быстрая проверка системы")
    print("  metrics     - Показать метрики системы")
    print("  help        - Показать эту справку")
    print()
    print("Примеры:")
    print("  python monitor_system.py monitor")
    print("  python monitor_system.py check")
    print("  python monitor_system.py metrics")


async def main():
    """Главная функция"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            await quick_check()
        elif command == "metrics":
            await show_metrics()
        elif command == "help":
            show_help()
        elif command == "monitor":
            await monitor_loop()
        else:
            print(f"❌ Неизвестная команда: {command}")
            show_help()
    else:
        # По умолчанию запускаем мониторинг
        await monitor_loop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
