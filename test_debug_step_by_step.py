#!/usr/bin/env python3
"""
Пошаговый тест для отладки зависания анализа
"""
import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User

async def test_step_by_step():
    """Пошаговый тест анализа"""
    print("🔍 Пошаговый тест анализа портфеля...")
    
    try:
        # Шаг 1: Получаем пользователя
        print("📋 Шаг 1: Получение пользователя...")
        session = db_manager.SessionLocal()
        users = session.query(User).limit(1).all()
        session.close()
        
        if not users:
            print("❌ Нет пользователей в базе данных")
            return None
        
        test_user = users[0]
        print(f"✅ Пользователь ID: {test_user.id}")
        
        # Шаг 2: Создаем анализатор
        print("📋 Шаг 2: Создание анализатора...")
        analyzer = PortfolioAnalyzer()
        print("✅ Анализатор создан")
        
        # Шаг 3: Загружаем холдинги
        print("📋 Шаг 3: Загрузка холдингов...")
        holdings = await analyzer._load_user_holdings(test_user.id)
        print(f"✅ Загружено {len(holdings)} холдингов")
        
        # Шаг 4: Загружаем аккаунты
        print("📋 Шаг 4: Загрузка аккаунтов...")
        accounts = await analyzer._load_user_accounts(test_user.id)
        print(f"✅ Загружено {len(accounts)} аккаунтов")
        
        # Шаг 5: Загружаем наличность
        print("📋 Шаг 5: Загрузка наличности...")
        cash_map = await analyzer._load_account_cash(test_user.id, accounts)
        print(f"✅ Загружена наличность для {len(cash_map)} аккаунтов")
        
        # Шаг 6: Разделяем холдинги
        print("📋 Шаг 6: Разделение холдингов...")
        bond_holdings = [h for h in holdings if h.security_type == "bond"]
        share_holdings = [h for h in holdings if h.security_type == "share"]
        print(f"✅ Облигации: {len(bond_holdings)}, Акции: {len(share_holdings)}")
        
        # Шаг 7: Загружаем данные облигаций
        print("📋 Шаг 7: Загрузка данных облигаций...")
        start_time = datetime.now()
        integrated_bond_data = await analyzer._get_integrated_bond_data(bond_holdings)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ Данные облигаций загружены за {duration:.2f} сек: {len(integrated_bond_data)}")
        
        # Шаг 8: Загружаем данные акций
        print("📋 Шаг 8: Загрузка данных акций...")
        start_time = datetime.now()
        share_snapshots = await analyzer._get_market_data(share_holdings)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"✅ Данные акций загружены за {duration:.2f} сек: {len(share_snapshots)}")
        
        print("🎉 Все шаги выполнены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка на шаге: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_step_by_step())
