#!/usr/bin/env python3
"""
Тест полного payload для AI анализа
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User, PortfolioAccount, PortfolioHoldingV2, PortfolioCashPosition

async def test_ai_payload():
    """Тест полного payload для AI"""
    print("🧪 Тест полного payload для AI анализа...")
    
    try:
        # Создаем тестового пользователя
        test_user = User(
            telegram_id=12345,
            first_name="Test",
            last_name="User",
            username="testuser"
        )
        db_manager.db_session.add(test_user)
        db_manager.db_session.commit()
        db_manager.db_session.refresh(test_user)
        
        # Создаем тестовый аккаунт
        test_account = PortfolioAccount(
            user_id=test_user.id,
            account_id="test_account_1",
            account_name="Test Account",
            currency="RUB",
            portfolio_value=1000000.0
        )
        db_manager.db_session.add(test_account)
        db_manager.db_session.commit()
        db_manager.db_session.refresh(test_account)
        
        # Создаем тестовые облигации
        test_bonds = [
            {
                "name": "Газпром 001P-05",
                "isin": "RU000A10B2M3",
                "ticker": "RU000A10B2M3",
                "quantity": "100",
                "price": 95.5
            },
            {
                "name": "Сбербанк 001P-06", 
                "isin": "RU000A10ATB6",
                "ticker": "RU000A10ATB6",
                "quantity": "50",
                "price": 98.2
            }
        ]
        
        for bond in test_bonds:
            holding = PortfolioHoldingV2(
                user_id=test_user.id,
                account_internal_id=test_account.id,
                raw_name=bond["name"],
                normalized_name=bond["name"],
                raw_isin=bond["isin"],
                isin=bond["isin"],
                raw_ticker=bond["ticker"],
                ticker=bond["ticker"],
                raw_type="bond",
                security_type="bond",
                raw_quantity=bond["quantity"],
                quantity=float(bond["quantity"])
            )
            db_manager.db_session.add(holding)
        
        # Создаем кэш
        cash = PortfolioCashPosition(
            user_id=test_user.id,
            account_internal_id=test_account.id,
            raw_name="Рубль",
            amount=50000.0,
            currency="RUB"
        )
        db_manager.db_session.add(cash)
        db_manager.db_session.commit()
        
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
    asyncio.run(test_ai_payload())
