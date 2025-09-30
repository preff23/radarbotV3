#!/usr/bin/env python3
"""
Тест реального анализа портфеля с календарем выплат
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/Users/goretofff/Desktop/radar3.0')

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.logging import get_logger

logger = get_logger(__name__)

async def test_real_analysis():
    """Тестируем реальный анализ портфеля"""
    print("🔍 Тестирование реального анализа портфеля...")
    
    analyzer = PortfolioAnalyzer()
    
    # Создаем тестовые данные пользователя с облигациями
    test_user_id = 999999  # Используем тестовый ID
    
    print(f"📊 Создаем тестового пользователя {test_user_id}...")
    
    # Создаем тестового пользователя и добавляем облигации
    from bot.core.db import DatabaseManager
    db_manager = DatabaseManager()
    
    # Создаем пользователя
    user = db_manager.create_user(
        telegram_id=test_user_id,
        phone_number="+79999999999",
        username="test_user"
    )
    print(f"✅ Пользователь создан: {user.id}")
    
    # Добавляем тестовые облигации
    test_bonds = [
        {
            "raw_name": "Быстроденьги МФК",
            "normalized_name": "Быстроденьги МФК",
            "normalized_key": "RU000A10B2M3",
            "ticker": "RU000A10B2M3",
            "isin": "RU000A10B2M3",
            "security_type": "bond",
            "raw_quantity": 100,
            "raw_quantity_unit": "шт"
        },
        {
            "raw_name": "Атомэнергопром",
            "normalized_name": "Атомэнергопром",
            "normalized_key": "RU000A10CT33",
            "ticker": "RU000A10CT33", 
            "isin": "RU000A10CT33",
            "security_type": "bond",
            "raw_quantity": 50,
            "raw_quantity_unit": "шт"
        },
        {
            "raw_name": "Банк ГПБ",
            "normalized_name": "Банк ГПБ",
            "normalized_key": "RU000A104B46",
            "ticker": "RU000A104B46",
            "isin": "RU000A104B46", 
            "security_type": "bond",
            "raw_quantity": 25,
            "raw_quantity_unit": "шт"
        }
    ]
    
    for bond_data in test_bonds:
        holding = db_manager.add_holding(
            user_id=user.id,
            **bond_data
        )
        print(f"✅ Добавлена облигация: {holding.normalized_name}")
    
    print(f"\n📋 Всего позиций у пользователя: {len(db_manager.get_user_holdings(user.id))}")
    
    # Теперь тестируем анализ
    print(f"\n🔍 Запускаем анализ портфеля...")
    
    # Добавляем отладочную информацию
    print(f"🔍 Отладочная информация:")
    holdings = db_manager.get_user_holdings(user.id)
    for holding in holdings:
        print(f"  - {holding.normalized_name} ({holding.security_type}) - ISIN: {holding.isin}")
    
    result = await analyzer.run_analysis(user.id)
    
    print(f"\n📊 Результаты анализа:")
    print(f"  - Ошибка: {result.get('error', 'Нет')}")
    print(f"  - Календарь выплат: {len(result.get('bond_calendar', []))} событий")
    print(f"  - Топ-3 стабильных: {len(result.get('top_stable', []))} позиций")
    print(f"  - Топ-3 рискованных: {len(result.get('top_risky', []))} позиций")
    
    # Показываем календарь выплат
    if result.get('bond_calendar'):
        print(f"\n📅 КАЛЕНДАРЬ ВЫПЛАТ:")
        for i, event in enumerate(result['bond_calendar'][:10]):  # Показываем первые 10 событий
            print(f"  {i+1}. {event.get('name', 'Unknown')}: {event.get('date', 'No date')} - {event.get('value', 'No value')} ₽ ({event.get('type', 'unknown')})")
    else:
        print(f"\n❌ Календарь выплат пуст!")
    
    # Показываем топ-3 стабильных
    if result.get('top_stable'):
        print(f"\n📈 ТОП-3 СТАБИЛЬНЫХ ЦЕННЫХ БУМАГ:")
        for i, position in enumerate(result['top_stable']):
            print(f"  {i+1}. {position.get('name', 'Unknown')} ({position.get('type', 'unknown')}) - YTM: {position.get('ytm', 'N/A')}%, Изменение: {position.get('change_pct', 'N/A')}%")
    else:
        print(f"\n❌ Стабильные позиции не найдены!")
    
    # Показываем топ-3 рискованных
    if result.get('top_risky'):
        print(f"\n📉 ТОП-3 РИСКОВАННЫХ ЦЕННЫХ БУМАГ:")
        for i, position in enumerate(result['top_risky']):
            print(f"  {i+1}. {position.get('name', 'Unknown')} ({position.get('type', 'unknown')}) - YTM: {position.get('ytm', 'N/A')}%, Изменение: {position.get('change_pct', 'N/A')}%")
    else:
        print(f"\n❌ Рискованные позиции не найдены!")
    
    # Очищаем тестовые данные
    print(f"\n🧹 Очищаем тестовые данные...")
    # Удаляем позиции пользователя
    holdings = db_manager.get_user_holdings(user.id)
    for holding in holdings:
        holding.is_active = False
    db_manager.SessionLocal().commit()
    print(f"✅ Тестовые данные удалены")
    
    print(f"\n✅ Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_real_analysis())
