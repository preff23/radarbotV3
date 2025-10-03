#!/usr/bin/env python3
"""
Тест AI анализа с созданием пользователя
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User, PortfolioAccount, PortfolioHoldingV2, PortfolioCashPosition
from dotenv import load_dotenv

load_dotenv()

async def test_ai_analysis_with_user():
    """Тестируем AI анализ с созданием пользователя"""
    print("🧪 Тестируем AI анализ с созданием пользователя...")
    
    try:
        session = db_manager.SessionLocal()
        
        # Создаем тестового пользователя
        test_user = User(
            telegram_id=123456789,
            phone_number="+79151731545",
            first_name="Test",
            last_name="User"
        )
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        print(f"✅ Создан пользователь: {test_user.id}")
        
        # Создаем тестовый счет
        test_account = PortfolioAccount(
            user_id=test_user.id,
            account_id="test_account_1",
            account_name="Тестовый счет",
            account_type="broker",
            portfolio_value=100000.0
        )
        session.add(test_account)
        session.commit()
        session.refresh(test_account)
        
        print(f"✅ Создан счет: {test_account.id}")
        
        # Создаем тестовые позиции
        test_holding = PortfolioHoldingV2(
            user_id=test_user.id,
            account_internal_id=test_account.id,
            raw_name="Газпром БО-001Р-02",
            normalized_name="Газпром БО-001Р-02",
            raw_isin="RU000A0JX0S9",
            isin="RU000A0JX0S9",
            raw_ticker="ГАЗПРОМ БО-001Р-02",
            ticker="ГАЗПРОМ БО-001Р-02",
            raw_type="bond",
            security_type="bond",
            raw_quantity=10,
            current_price=1000.0,
            normalized_key="ГАЗПРОМ БО-001Р-02"
        )
        session.add(test_holding)
        
        # Создаем кэш позицию
        test_cash = PortfolioCashPosition(
            user_id=test_user.id,
            account_internal_id=test_account.id,
            raw_name="Рубли",
            currency="RUB",
            amount=50000.0
        )
        session.add(test_cash)
        
        session.commit()
        print("✅ Созданы тестовые позиции")
        
        # Создаем анализатор
        analyzer = PortfolioAnalyzer()
        
        print("🔄 Запускаем анализ...")
        
        # Запускаем анализ
        result = await analyzer.run_analysis(test_user.id)
        
        print(f"✅ Анализ завершен!")
        print(f"📊 Результат: {result.get('ai_analysis', 'Нет анализа')[:200]}...")
        
        # Очищаем тестовые данные
        session.delete(test_holding)
        session.delete(test_cash)
        session.delete(test_account)
        session.delete(test_user)
        session.commit()
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_ai_analysis_with_user())
