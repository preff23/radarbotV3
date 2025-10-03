#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции парсера corpbonds.ru
"""

import asyncio
import json
from bot.services.corpbonds_service import corpbonds_service


async def test_corpbonds_service():
    """Тестирует сервис corpbonds.ru"""
    
    print("🔍 Тестирование сервиса corpbonds.ru...")
    print("=" * 60)
    
    # Тестовые ISIN облигаций
    test_isins = [
        "RU000A10BNF8",  # РусГидро БО-П13
        "RU000A1082X0",  # Группа ЛСР ПАО БО 001Р-09
    ]
    
    # Тест 1: Получение данных одной облигации
    print("\n📋 ТЕСТ 1: Получение данных одной облигации")
    print("-" * 40)
    
    bond_data = await corpbonds_service.get_bond_data(test_isins[0])
    
    if "error" in bond_data:
        print(f"❌ Ошибка: {bond_data['error']}")
    else:
        print(f"✅ Данные получены для {test_isins[0]}")
        summary = corpbonds_service.extract_bond_summary(bond_data)
        print(f"📊 Краткая сводка: {json.dumps(summary, ensure_ascii=False, indent=2)}")
    
    # Тест 2: Получение данных нескольких облигаций
    print("\n📋 ТЕСТ 2: Получение данных нескольких облигаций")
    print("-" * 40)
    
    multiple_data = await corpbonds_service.get_multiple_bonds_data(test_isins)
    
    successful_count = sum(1 for data in multiple_data.values() if "error" not in data)
    print(f"✅ Получены данные для {successful_count}/{len(test_isins)} облигаций")
    
    for isin, data in multiple_data.items():
        if "error" in data:
            print(f"❌ {isin}: {data['error']}")
        else:
            summary = corpbonds_service.extract_bond_summary(data)
            print(f"✅ {isin}: {summary.get('name', 'N/A')}")
    
    # Тест 3: Форматирование для AI
    print("\n📋 ТЕСТ 3: Форматирование для AI анализа")
    print("-" * 40)
    
    formatted_data = corpbonds_service.format_for_ai_analysis(multiple_data)
    print("📄 Отформатированные данные:")
    print(formatted_data[:500] + "..." if len(formatted_data) > 500 else formatted_data)
    
    # Тест 4: Кэширование
    print("\n📋 ТЕСТ 4: Проверка кэширования")
    print("-" * 40)
    
    # Первый запрос
    start_time = asyncio.get_event_loop().time()
    await corpbonds_service.get_bond_data(test_isins[0])
    first_time = asyncio.get_event_loop().time() - start_time
    
    # Второй запрос (должен быть из кэша)
    start_time = asyncio.get_event_loop().time()
    await corpbonds_service.get_bond_data(test_isins[0])
    second_time = asyncio.get_event_loop().time() - start_time
    
    print(f"⏱️ Первый запрос: {first_time:.3f} сек")
    print(f"⏱️ Второй запрос (кэш): {second_time:.3f} сек")
    print(f"🚀 Ускорение: {first_time/second_time:.1f}x")
    
    print("\n✅ Все тесты завершены!")


async def test_api_endpoints():
    """Тестирует API endpoints (симуляция)"""
    
    print("\n🔍 Тестирование API endpoints...")
    print("=" * 60)
    
    # Симулируем вызовы API
    from bot.api.corpbonds_endpoints import get_bond_data, get_multiple_bonds_data
    
    # Тест API для одной облигации
    print("\n📋 ТЕСТ API: Получение данных одной облигации")
    print("-" * 40)
    
    try:
        response = await get_bond_data("RU000A10BNF8")
        print(f"✅ API Response: {response.success}")
        if response.success:
            print(f"📊 Данные: {response.data.get('name', 'N/A')}")
        else:
            print(f"❌ Ошибка: {response.error}")
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
    
    print("\n✅ API тесты завершены!")


async def main():
    """Основная функция"""
    try:
        await test_corpbonds_service()
        await test_api_endpoints()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
