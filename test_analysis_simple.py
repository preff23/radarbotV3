#!/usr/bin/env python3
"""
Простой тест анализа портфеля без создания пользователя
"""
import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User

async def test_analysis():
    """Тест анализа с существующим пользователем"""
    print("🔍 Запуск простого теста анализа портфеля...")
    
    try:
        # Получаем первого пользователя из базы
        session = db_manager.SessionLocal()
        users = session.query(User).limit(1).all()
        session.close()
        
        if not users:
            print("❌ Нет пользователей в базе данных")
            return None
        
        test_user = users[0]
        print(f"✅ Используем пользователя ID: {test_user.id}")
        
        # Запускаем анализ
        print("\n🚀 Запуск анализа...")
        start_time = datetime.now()
        
        analyzer = PortfolioAnalyzer()
        result = await analyzer.run_analysis(test_user.id)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️ Анализ завершен за {duration:.2f} секунд")
        
        if "error" in result:
            print(f"❌ Ошибка анализа: {result['error']}")
            print(f"📝 Детали: {result.get('summary', 'Нет деталей')}")
        else:
            print("✅ Анализ успешно завершен!")
            print(f"📊 Результат содержит {len(result)} ключей")
            for key in result.keys():
                print(f"  - {key}")
        
        return result
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Используем основную базу данных
    asyncio.run(test_analysis())
