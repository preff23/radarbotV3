#!/usr/bin/env python3
"""
Тест AI анализа для отладки ошибок
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

async def test_ai_analysis():
    """Тестируем AI анализ"""
    print("🧪 Тестируем AI анализ...")
    
    try:
        # Создаем тестового пользователя
        session = db_manager.SessionLocal()
        
        # Проверяем, есть ли пользователь
        test_user = session.query(User).filter(User.telegram_id == 123456789).first()
        if not test_user:
            print("❌ Тестовый пользователь не найден")
            return False
        
        print(f"✅ Найден пользователь: {test_user.telegram_id}")
        
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
    asyncio.run(test_ai_analysis())
