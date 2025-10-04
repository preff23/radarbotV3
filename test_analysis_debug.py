#!/usr/bin/env python3
"""
Тест генерации анализа на сервере
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager

async def test_analysis_generation():
    """Тест генерации анализа"""
    print("🧪 Тест генерации анализа на сервере...")
    
    try:
        # Получаем первого пользователя через SQL
        from sqlalchemy import text
        with db_manager.SessionLocal() as session:
            result = session.execute(text("SELECT * FROM users LIMIT 1"))
            user_row = result.fetchone()
            if not user_row:
                print("❌ Нет пользователей в базе данных")
                return False
            
            # Создаем объект пользователя
            from bot.core.db import User
            test_user = User(
                id=user_row[0],
                telegram_id=user_row[3],
                first_name=user_row[4],
                last_name=user_row[5],
                username=user_row[6]
            )
        print(f"👤 Тестируем пользователя: {test_user.first_name} {test_user.last_name} (ID: {test_user.id})")
        
        # Запускаем анализ
        analyzer = PortfolioAnalyzer()
        print("🔄 Запускаем анализ...")
        
        result = await analyzer.run_analysis(test_user.id)
        
        if "error" in result:
            print(f"❌ Ошибка анализа: {result['error']}")
            return False
        
        print("✅ Анализ завершен успешно")
        
        # Проверяем AI анализ
        if 'ai_analysis' in result:
            ai_text = result['ai_analysis']
            print(f"✅ AI анализ: {len(ai_text)} символов")
            print(f"📝 Превью: {ai_text[:200]}...")
        else:
            print("❌ AI анализ не найден в результате")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_analysis_generation())