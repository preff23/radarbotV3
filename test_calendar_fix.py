#!/usr/bin/env python3
"""
Тест для проверки календаря выплат
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/Users/goretofff/Desktop/radar3.0')

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.logging import get_logger

logger = get_logger(__name__)

async def test_calendar():
    """Тестируем календарь выплат"""
    print("🔍 Тестирование календаря выплат...")
    
    analyzer = PortfolioAnalyzer()
    
    # Тестируем с пользователем 521751895
    user_id = 521751895
    
    try:
        print(f"📊 Анализируем портфель пользователя {user_id}...")
        
        # Загружаем данные пользователя напрямую
        holdings = await analyzer._load_user_holdings(user_id)
        print(f"📋 Найдено позиций: {len(holdings)}")
        
        for holding in holdings[:3]:  # Показываем первые 3
            print(f"  - {holding.normalized_name} ({holding.security_type}) - ISIN: {holding.isin}")
        
        result = await analyzer.run_analysis(user_id)
        
        print(f"✅ Анализ завершен")
        print(f"📅 Календарь выплат: {len(result.get('bond_calendar', []))} событий")
        
        if result.get('bond_calendar'):
            print("🎉 Календарь выплат работает!")
            for event in result['bond_calendar'][:5]:  # Показываем первые 5 событий
                print(f"  - {event.get('name', 'Unknown')}: {event.get('date', 'No date')} - {event.get('value', 'No value')} ₽")
        else:
            print("❌ Календарь выплат пуст")
            
        # Проверяем топ-3 ценных бумаг
        print(f"📈 Топ-3 стабильных: {len(result.get('top_stable', []))} позиций")
        print(f"📉 Топ-3 рискованных: {len(result.get('top_risky', []))} позиций")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_calendar())
