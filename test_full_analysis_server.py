#!/usr/bin/env python3
"""
Тест полного анализа портфеля на сервере
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.core.logging import setup_logging, get_logger
from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.db import db_manager, create_tables

setup_logging()
logger = get_logger(__name__)

async def test_full_analysis():
    """Тест полного анализа портфеля"""
    print("🧪 ТЕСТ ПОЛНОГО АНАЛИЗА ПОРТФЕЛЯ")
    print("=" * 50)
    
    try:
        # Создаем тестового пользователя
        test_user_id = 999999
        test_phone = "+79999999999"
        
        print(f"📱 Создаем тестового пользователя: {test_phone}")
        
        # Удаляем пользователя если существует
        try:
            db_manager.delete_user(test_user_id)
        except:
            pass
        
        # Создаем пользователя
        session = db_manager.SessionLocal()
        try:
            user = db_manager.create_user(
                telegram_id=test_user_id,
                phone_number=test_phone,
                username="test_user"
            )
            print(f"✅ Пользователь создан: {user.id}")
            
            # Создаем тестовый аккаунт
            account = db_manager.get_or_create_account(
                user_id=user.id,
                account_id="test_account_1",
                account_name="Тестовый счет",
                portfolio_value=1000000.0,
                session=session
            )
            print(f"✅ Аккаунт создан: {account.id}")
        finally:
            session.close()
        
        # Создаем тестовые позиции облигаций
        test_bonds = [
            {"isin": "RU000A10C9Z9", "name": "РусГидро БО-П13", "quantity": 1000, "price": 1000.0},
            {"isin": "RU000A10B2M3", "name": "Сбер БО-001Р-09", "quantity": 500, "price": 1000.0},
            {"isin": "RU000A10BRN3", "name": "Газпром БО-001Р-09", "quantity": 200, "price": 1000.0},
            {"isin": "RU000A10CTH9", "name": "Лукойл БО-001Р-09", "quantity": 300, "price": 1000.0},
            {"isin": "RU000A10AHB1", "name": "Норильский никель БО-001Р-09", "quantity": 150, "price": 1000.0},
        ]
        
        # Создаем тестовые позиции в одной сессии
        session = db_manager.SessionLocal()
        try:
            print(f"📊 Создаем {len(test_bonds)} тестовых позиций облигаций...")
            
            for bond in test_bonds:
                holding = db_manager.add_holding(
                    user_id=user.id,
                    raw_name=bond["name"],
                    normalized_name=bond["name"],
                    normalized_key=bond["name"],
                    account_internal_id=account.id,
                    raw_isin=bond["isin"],
                    isin=bond["isin"],
                    raw_quantity=bond["quantity"],
                    raw_type="bond",
                    session=session
                )
                print(f"  ✅ {bond['name']} ({bond['isin']})")
            
            # Создаем тестовые позиции акций
            test_shares = [
                {"ticker": "SBER", "name": "Сбербанк", "quantity": 100, "price": 250.0},
                {"ticker": "GAZP", "name": "Газпром", "quantity": 50, "price": 150.0},
            ]
            
            print(f"📈 Создаем {len(test_shares)} тестовых позиций акций...")
            
            for share in test_shares:
                holding = db_manager.add_holding(
                    user_id=user.id,
                    raw_name=share["name"],
                    normalized_name=share["name"],
                    normalized_key=share["name"],
                    account_internal_id=account.id,
                    raw_ticker=share["ticker"],
                    ticker=share["ticker"],
                    raw_quantity=share["quantity"],
                    raw_type="share",
                    session=session
                )
                print(f"  ✅ {share['name']} ({share['ticker']})")
            
            # Создаем тестовые денежные позиции
            cash_positions = [
                {"currency": "RUB", "amount": 50000.0},
                {"currency": "USD", "amount": 1000.0},
            ]
            
            print(f"💰 Создаем {len(cash_positions)} денежных позиций...")
            
            for cash in cash_positions:
                from bot.core.db import PortfolioCashPosition
                cash_position = PortfolioCashPosition(
                    user_id=user.id,
                    account_internal_id=account.id,
                    raw_name=f"Cash {cash['currency']}",
                    currency=cash["currency"],
                    amount=cash["amount"]
                )
                session.add(cash_position)
                print(f"  ✅ {cash['amount']} {cash['currency']}")
            
            session.commit()
        finally:
            session.close()
        
        print("\n🚀 ЗАПУСКАЕМ ПОЛНЫЙ АНАЛИЗ...")
        print("=" * 50)
        
        # Запускаем анализ
        start_time = time.time()
        
        analyzer = PortfolioAnalyzer()
        result = await analyzer.run_analysis(user.id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ АНАЛИЗ ЗАВЕРШЕН ЗА {duration:.2f} СЕКУНД")
        print("=" * 50)
        
        # Проверяем результат
        if "error" in result:
            print(f"❌ ОШИБКА: {result['error']}")
            return False
        
        print("✅ Анализ выполнен успешно!")
        print(f"📊 Результат содержит {len(result)} ключей:")
        for key in result.keys():
            print(f"  - {key}")
        
        # Проверяем основные компоненты
        if "ai_analysis" in result:
            print(f"🤖 AI анализ: {len(result['ai_analysis'])} символов")
        
        if "bond_calendar" in result:
            print(f"📅 Календарь: {len(result['bond_calendar'])} событий")
        
        if "news" in result:
            print(f"📰 Новости: {len(result['news'])} статей")
        
        if "metrics" in result:
            print(f"📈 Метрики: {len(result['metrics'])} показателей")
        
        print(f"\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print(f"⏱️ Время выполнения: {duration:.2f} секунд")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ТЕСТЕ: {e}")
        logger.error(f"Test error: {e}", exc_info=True)
        return False
    
    finally:
        # Очищаем тестовые данные
        try:
            db_manager.delete_user(test_user_id)
            print("🧹 Тестовые данные очищены")
        except:
            pass

async def main():
    """Главная функция"""
    print("🔧 Инициализация базы данных...")
    create_tables()
    
    print("🚀 Запуск теста...")
    success = await test_full_analysis()
    
    if success:
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        sys.exit(0)
    else:
        print("\n❌ ТЕСТЫ НЕ ПРОШЛИ!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
