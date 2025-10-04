#!/usr/bin/env python3
"""
Тест анализа существующего пользователя
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager

async def test_existing_analysis():
    """Тест анализа существующего пользователя"""
    print("🧪 Тест анализа существующего пользователя...")
    
    try:
        # Получаем первого пользователя из базы
        users = db_manager.get_all_users()
        if not users:
            print("❌ Нет пользователей в базе данных")
            return False
        
        test_user = users[0]
        print(f"👤 Тестируем пользователя: {test_user.first_name} {test_user.last_name} (ID: {test_user.id})")
        
        # Запускаем анализ
        analyzer = PortfolioAnalyzer()
        print("🔄 Запускаем анализ...")
        
        result = await analyzer.run_analysis(test_user.id)
        
        if "error" in result:
            print(f"❌ Ошибка анализа: {result['error']}")
            return False
        
        print("✅ Анализ завершен успешно")
        print(f"📊 Результат: {result.get('summary', 'Нет summary')[:200]}...")
        
        # Проверяем, что все данные загружены
        print("\n🔍 Проверяем загруженные данные:")
        
        # Проверяем макро данные
        if 'macro_data' in result:
            print(f"✅ Макро данные: {result['macro_data']}")
        else:
            print("❌ Макро данные не найдены")
        
        # Проверяем календарь
        if 'bond_calendar' in result:
            print(f"✅ Календарь облигаций: {len(result['bond_calendar'])} событий")
        else:
            print("❌ Календарь облигаций не найден")
        
        # Проверяем новости
        if 'news' in result:
            print(f"✅ Новости: {len(result['news'])} статей")
        else:
            print("❌ Новости не найдены")
        
        # Проверяем историю платежей
        if 'payment_history' in result:
            print(f"✅ История платежей: {len(result['payment_history'])} записей")
        else:
            print("❌ История платежей не найдена")
        
        # Проверяем позиции
        if 'positions' in result:
            print(f"✅ Позиции: {len(result['positions'])} позиций")
            for pos in result['positions'][:2]:  # Показываем первые 2
                print(f"   - {pos.get('name', 'N/A')}: {pos.get('last_price', 'N/A')} {pos.get('currency', 'N/A')}")
        else:
            print("❌ Позиции не найдены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_existing_analysis())
