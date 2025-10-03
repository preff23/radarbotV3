#!/usr/bin/env python3
"""
Тест AI анализа с существующим пользователем
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User
from dotenv import load_dotenv

load_dotenv()

async def test_existing_user_analysis():
    """Тестируем AI анализ с существующим пользователем"""
    print("🧪 Тестируем AI анализ с существующим пользователем...")
    
    try:
        session = db_manager.SessionLocal()
        
        # Находим существующего пользователя
        test_user = session.query(User).first()
        if not test_user:
            print("❌ Пользователи не найдены в базе")
            return False
        
        print(f"✅ Найден пользователь: {test_user.telegram_id} ({test_user.phone_number})")
        
        # Создаем анализатор
        analyzer = PortfolioAnalyzer()
        
        print("🔄 Запускаем анализ...")
        
        # Запускаем анализ
        result = await analyzer.run_analysis(test_user.id)
        
        print(f"✅ Анализ завершен!")
        print(f"📊 Результат: {result.get('ai_analysis', 'Нет анализа')[:200]}...")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_existing_user_analysis())
