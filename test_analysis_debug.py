#!/usr/bin/env python3
"""
Тест анализа портфеля без OCR для отладки проблем
"""
import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, User, PortfolioAccount, PortfolioHoldingV2, PortfolioCashPosition

async def test_analysis():
    """Тест анализа с готовыми данными"""
    print("🔍 Запуск теста анализа портфеля...")
    
    # Создаем тестового пользователя
    test_user = User(
        telegram_id=999999999,
        phone_number="+7999999999",
        first_name="Test",
        last_name="User",
        created_at=datetime.now()
    )
    
    # Создаем тестовый аккаунт
    test_account = PortfolioAccount(
        user_id=test_user.id,
        account_id="test_debug_account",
        account_name="Test Account",
        portfolio_value=100000.0,
        created_at=datetime.now()
    )
    
    # Создаем тестовые облигации
    test_holdings = [
        PortfolioHoldingV2(
            user_id=test_user.id,
            account_internal_id=test_account.id,
            raw_name="Быстроденьги 002Р-08",
            normalized_name="Быстроденьги 002Р-08",
            normalized_key="Быстроденьги 002Р-08",
            raw_isin="RU000A103ZJ0",
            isin="RU000A103ZJ0",
            raw_ticker="Быстроденьги 002Р-08",
            ticker="Быстроденьги 002Р-08",
            raw_type="bond",
            security_type="bond",
            raw_quantity=5,
            created_at=datetime.now()
        ),
        PortfolioHoldingV2(
            user_id=test_user.id,
            account_internal_id=test_account.id,
            raw_name="КЛС-Трейд БО-03",
            normalized_name="КЛС-Трейд БО-03",
            normalized_key="КЛС-Трейд БО-03",
            raw_isin="RU000A0JXTS8",
            isin="RU000A0JXTS8",
            raw_ticker="КЛС-Трейд БО-03",
            ticker="КЛС-Трейд БО-03",
            raw_type="bond",
            security_type="bond",
            raw_quantity=25,
            created_at=datetime.now()
        )
    ]
    
    # Создаем тестовую наличность
    test_cash = PortfolioCashPosition(
        user_id=test_user.id,
        account_internal_id=test_account.id,
        raw_name="RUB",
        currency="RUB",
        amount=50000.0,
        created_at=datetime.now()
    )
    
    try:
        # Добавляем в базу данных
        session = db_manager.SessionLocal()
        
        # Сначала сохраняем пользователя
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        
        # Теперь создаем аккаунт с правильным user_id
        test_account.user_id = test_user.id
        session.add(test_account)
        session.commit()
        session.refresh(test_account)
        
        # Обновляем user_id в облигациях и наличности
        for holding in test_holdings:
            holding.user_id = test_user.id
            holding.account_internal_id = test_account.id
            session.add(holding)
        
        test_cash.user_id = test_user.id
        test_cash.account_internal_id = test_account.id
        session.add(test_cash)
        
        session.commit()
        session.close()
        
        print(f"✅ Создан тестовый пользователь ID: {test_user.id}")
        print(f"✅ Создан тестовый аккаунт ID: {test_account.id}")
        print(f"✅ Добавлено {len(test_holdings)} облигаций")
        print(f"✅ Добавлена наличность: {test_cash.amount} {test_cash.currency}")
        
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
    
    finally:
        # Очищаем тестовые данные
        try:
            session = db_manager.SessionLocal()
            session.query(PortfolioHoldingV2).filter(PortfolioHoldingV2.user_id == test_user.id).delete()
            session.query(PortfolioCashPosition).filter(PortfolioCashPosition.user_id == test_user.id).delete()
            session.query(PortfolioAccount).filter(PortfolioAccount.user_id == test_user.id).delete()
            session.query(User).filter(User.id == test_user.id).delete()
            session.commit()
            session.close()
            print("🧹 Тестовые данные очищены")
        except Exception as e:
            print(f"⚠️ Ошибка очистки: {e}")

if __name__ == "__main__":
    # Устанавливаем переменную окружения для тестовой базы
    os.environ['DATABASE_URL'] = 'sqlite:///test_debug.db'
    
    # Переинициализируем db_manager с тестовой базой
    from bot.core.db import DatabaseManager
    db_manager = DatabaseManager()
    
    asyncio.run(test_analysis())
