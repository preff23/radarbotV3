#!/usr/bin/env python3
"""
Тест отдельных методов анализа
"""
import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User

async def test_analysis_methods():
    """Тест методов анализа"""
    print("🔍 Тест методов анализа...")
    
    try:
        # Получаем пользователя
        session = db_manager.SessionLocal()
        users = session.query(User).limit(1).all()
        session.close()
        
        if not users:
            print("❌ Нет пользователей в базе данных")
            return None
        
        test_user = users[0]
        print(f"✅ Пользователь ID: {test_user.id}")
        
        # Создаем анализатор
        analyzer = PortfolioAnalyzer()
        
        # Загружаем данные
        holdings = await analyzer._load_user_holdings(test_user.id)
        accounts = await analyzer._load_user_accounts(test_user.id)
        cash_map = await analyzer._load_account_cash(test_user.id, accounts)
        
        bond_holdings = [h for h in holdings if h.security_type == "bond"]
        share_holdings = [h for h in holdings if h.security_type == "share"]
        
        integrated_bond_data = await analyzer._get_integrated_bond_data(bond_holdings)
        share_snapshots = await analyzer._get_market_data(share_holdings)
        
        all_snapshots = integrated_bond_data + share_snapshots
        
        print(f"✅ Данные загружены: {len(all_snapshots)} снапшотов")
        
        # Тест 1: _generate_analysis
        print("📋 Тест 1: _generate_analysis...")
        start_time = datetime.now()
        try:
            analysis_result = await analyzer._generate_analysis(
                all_snapshots,
                [],  # bond_calendar
                [],  # news_items
                {},  # payment_history
                len(share_holdings) > 0,  # has_shares
                holdings
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"✅ _generate_analysis завершен за {duration:.2f} сек")
        except Exception as e:
            print(f"❌ Ошибка в _generate_analysis: {e}")
            return False
        
        # Тест 2: _generate_ai_analysis
        print("📋 Тест 2: _generate_ai_analysis...")
        start_time = datetime.now()
        try:
            ai_result = await analyzer._generate_ai_analysis(
                all_snapshots,
                [],  # bond_calendar
                [],  # news_items
                {},  # ocr_meta
                {},  # payment_history
                accounts
            )
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            print(f"✅ _generate_ai_analysis завершен за {duration:.2f} сек")
        except Exception as e:
            print(f"❌ Ошибка в _generate_ai_analysis: {e}")
            return False
        
        print("🎉 Все методы работают!")
        return True
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_analysis_methods())
