#!/usr/bin/env python3
"""
Тест для проверки пользователей в базе данных
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/Users/goretofff/Desktop/radar3.0')

from bot.core.db import DatabaseManager
from bot.core.logging import get_logger

logger = get_logger(__name__)

async def test_db_users():
    """Проверяем пользователей в базе данных"""
    print("🔍 Проверяем пользователей в базе данных...")
    
    db_manager = DatabaseManager()
    
    try:
        # Получаем всех пользователей
        users = db_manager.get_all_users()
        print(f"👥 Найдено пользователей: {len(users)}")
        
        for user in users[:5]:  # Показываем первых 5
            print(f"  - ID: {user.id}, Phone: {user.phone}, Created: {user.created_at}")
            
            # Проверяем позиции пользователя
            holdings = db_manager.get_user_holdings(user.id)
            print(f"    Позиций: {len(holdings)}")
            
            for holding in holdings[:3]:  # Показываем первые 3 позиции
                print(f"      - {holding.normalized_name} ({holding.security_type}) - ISIN: {holding.isin}")
            
            print()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_users())
