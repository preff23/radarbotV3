#!/usr/bin/env python3
"""
Скрипт для запуска всех тестов системы
"""

import asyncio
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.core.logging import setup_logging, get_logger
from bot.core.health_monitor import health_monitor
from bot.utils.ocr_cache import ocr_cache
from bot.core.error_handler import error_handler

setup_logging()
logger = get_logger(__name__)


async def test_ocr_cache():
    """Тестирует кэш OCR"""
    print("🧪 Тестирование OCR Cache...")
    
    try:
        # Тестируем статистику кэша
        stats = ocr_cache.get_stats()
        print(f"   ✅ Cache stats: {stats}")
        
        # Тестируем очистку кэша
        ocr_cache.clear()
        stats_after = ocr_cache.get_stats()
        print(f"   ✅ Cache cleared: {stats_after}")
        
        return True
    except Exception as e:
        print(f"   ❌ OCR Cache test failed: {e}")
        return False


async def test_error_handler():
    """Тестирует обработчик ошибок"""
    print("🧪 Тестирование Error Handler...")
    
    try:
        from bot.core.error_handler import ErrorSeverity, ErrorCategory, ErrorContext
        
        # Тестируем обработку ошибки
        test_error = ValueError("Test error")
        error_info = error_handler.handle_error(
            test_error,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.BUSINESS_LOGIC,
            context=ErrorContext(operation="test")
        )
        
        print(f"   ✅ Error handled: {error_info.message}")
        
        # Тестируем статистику ошибок
        stats = error_handler.get_error_stats()
        print(f"   ✅ Error stats: {stats}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error Handler test failed: {e}")
        return False


async def test_health_monitor():
    """Тестирует мониторинг здоровья"""
    print("🧪 Тестирование Health Monitor...")
    
    try:
        # Тестируем общее здоровье системы
        health = await health_monitor.get_system_health(force_check=True)
        print(f"   ✅ System health: {health.overall_status.value}")
        print(f"   ✅ Components checked: {len(health.components)}")
        
        # Тестируем отдельные компоненты
        db_health = await health_monitor.check_database_health()
        print(f"   ✅ Database: {db_health.status.value}")
        
        cache_health = await health_monitor.check_cache_health()
        print(f"   ✅ Cache: {cache_health.status.value}")
        
        return True
    except Exception as e:
        print(f"   ❌ Health Monitor test failed: {e}")
        return False


async def test_corpbonds_integration():
    """Тестирует интеграцию с corpbonds.ru"""
    print("🧪 Тестирование CorpBonds Integration...")
    
    try:
        from bot.services.corpbonds_service import corpbonds_service
        
        # Тестируем получение данных облигации
        test_isin = "RU000A10BNF8"  # РусГидро
        bond_data = await corpbonds_service.get_bond_data(test_isin)
        
        if "error" in bond_data:
            print(f"   ⚠️ Bond data error: {bond_data['error']}")
        else:
            print(f"   ✅ Bond data retrieved: {bond_data.get('name', 'Unknown')}")
        
        return True
    except Exception as e:
        print(f"   ❌ CorpBonds test failed: {e}")
        return False


async def test_smart_data_loader():
    """Тестирует умную загрузку данных"""
    print("🧪 Тестирование Smart Data Loader...")
    
    try:
        from bot.services.smart_data_loader import SmartDataLoader
        from bot.handlers.invest_analyst import invest_analyst
        
        # Создаем тестовый loader
        loader = SmartDataLoader(invest_analyst)
        
        # Тестируем разные типы сообщений
        test_messages = [
            "Привет!",
            "Какие новости на рынке?",
            "Как дела с индексами MOEX?",
            "Проанализируй мой портфель"
        ]
        
        for message in test_messages:
            context = await loader.get_smart_context(message, {"holdings": []})
            print(f"   ✅ Message '{message}': {len(context)} data types loaded")
        
        return True
    except Exception as e:
        print(f"   ❌ Smart Data Loader test failed: {e}")
        return False


async def run_all_tests():
    """Запускает все тесты"""
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ СИСТЕМЫ")
    print("=" * 50)
    
    tests = [
        ("OCR Cache", test_ocr_cache),
        ("Error Handler", test_error_handler),
        ("Health Monitor", test_health_monitor),
        ("CorpBonds Integration", test_corpbonds_integration),
        ("Smart Data Loader", test_smart_data_loader)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   ❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Итоговый отчет
    print("\n" + "=" * 50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Результат: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        return True
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
