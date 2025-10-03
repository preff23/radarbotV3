#!/usr/bin/env python3
"""
Тест анализа 25 облигаций без OCR
"""

import asyncio
import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.core.db import db_manager, User, PortfolioAccount, PortfolioHoldingV2, PortfolioCashPosition
from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
import time

# Список 25 реальных облигаций для тестирования
TEST_BONDS = [
    {"isin": "RU000A10B2M3", "name": "Быстроденьги 002Р-08", "ticker": "БДеньг-2P8", "quantity": 5.0},
    {"isin": "RU000A10CRC4", "name": "Норильский Никель БО-001Р-14-USD", "ticker": "НорНик1P14", "quantity": 20.0},
    {"isin": "RU000A10ATB6", "name": "КЛС-Трейд БО-03", "ticker": "KЛC-TPEЙД БO-03", "quantity": 25.0},
    {"isin": "RU000A107PW1", "name": "МФК Быстроденьги 002Р-05", "ticker": "БДеньг-2P5", "quantity": 5.0},
    {"isin": "RU000A1082K7", "name": "МФК ВЭББАНКИР 06", "ticker": "ВЭББНКР 06", "quantity": 10.0},
    {"isin": "RU000A10C8H9", "name": "Оил Ресурс 001Р-02", "ticker": "ОилРес1P2", "quantity": 26.0},
    {"isin": "RU000A108C17", "name": "ПИР БО-02-001Р", "ticker": "ПИР 1P2", "quantity": 3.0},
    {"isin": "RU000A10CTH9", "name": "Полипласт П02-БО-11", "ticker": "ПолипП2Б11", "quantity": 88.0},
    {"isin": "RU000A10AHB1", "name": "РДВ Технологии 001Р-01", "ticker": "НовТех1Р1", "quantity": 3.0},
    {"isin": "RU000A109NM3", "name": "РЕГИОНСПЕЦТРАНС-01", "ticker": "РСТ-01", "quantity": 10.0},
    {"isin": "RU000A10BRN3", "name": "Сибирский КХП 001Р-04", "ticker": "СибКХП 1P4", "quantity": 5.0},
    {"isin": "RU000A10C758", "name": "ТД РКС 0662П06", "ticker": "РКС2Р6", "quantity": 15.0},
    {"isin": "RU000A0JVWJ6", "name": "Транспорт лизинг комп 066П03", "ticker": "ГТЛК БО-06", "quantity": 8.0},
    {"isin": "RU000A10C9Z9", "name": "УПТК-65 001Р-01", "ticker": "УПТК65 1P1", "quantity": 12.0},
    {"isin": "RU000A10ANT1", "name": "РДВ Технологии 001Р-01", "ticker": "РДВ ТЕХ 01", "quantity": 7.0},
    {"isin": "RU000A10B2M3", "name": "Быстроденьги 002Р-08", "ticker": "БДеньг-2P8", "quantity": 3.0},
    {"isin": "RU000A10CRC4", "name": "Норильский Никель БО-001Р-14-USD", "ticker": "НорНик1P14", "quantity": 15.0},
    {"isin": "RU000A10ATB6", "name": "КЛС-Трейд БО-03", "ticker": "KЛC-TPEЙД БO-03", "quantity": 20.0},
    {"isin": "RU000A107PW1", "name": "МФК Быстроденьги 002Р-05", "ticker": "БДеньг-2P5", "quantity": 8.0},
    {"isin": "RU000A1082K7", "name": "МФК ВЭББАНКИР 06", "ticker": "ВЭББНКР 06", "quantity": 12.0},
    {"isin": "RU000A10C8H9", "name": "Оил Ресурс 001Р-02", "ticker": "ОилРес1P2", "quantity": 18.0},
    {"isin": "RU000A108C17", "name": "ПИР БО-02-001Р", "ticker": "ПИР 1P2", "quantity": 6.0},
    {"isin": "RU000A10CTH9", "name": "Полипласт П02-БО-11", "ticker": "ПолипП2Б11", "quantity": 45.0},
    {"isin": "RU000A10AHB1", "name": "РДВ Технологии 001Р-01", "ticker": "НовТех1Р1", "quantity": 4.0},
    {"isin": "RU000A109NM3", "name": "РЕГИОНСПЕЦТРАНС-01", "ticker": "РСТ-01", "quantity": 9.0}
]

async def main():
    print("🔧 Инициализация базы данных...")
    
    # Создаем тестового пользователя
    test_phone = "+79999999999"
    test_user = db_manager.create_user(
        telegram_id=999999999,
        phone_number=test_phone,
        first_name="Test",
        last_name="User"
    )
    print(f"✅ Пользователь создан: {test_user.id}")
    
    # Создаем тестовый аккаунт
    session = db_manager.SessionLocal()
    try:
        account = db_manager.get_or_create_account(
            user_id=test_user.id,
            account_id="test_account_25_bonds",
            account_name="Тестовый счет 25 облигаций",
            portfolio_value=1000000.0,
            session=session
        )
        print(f"✅ Аккаунт создан: {account.id}")
        
        # Добавляем 25 облигаций
        print(f"📊 Добавляем {len(TEST_BONDS)} облигаций...")
        for i, bond in enumerate(TEST_BONDS):
            holding = db_manager.add_holding(
                user_id=test_user.id,
                raw_name=bond["name"],
                normalized_name=bond["name"],
                normalized_key=bond["ticker"],
                account_internal_id=account.id,
                raw_isin=bond["isin"],
                isin=bond["isin"],
                raw_ticker=bond["ticker"],
                ticker=bond["ticker"],
                raw_type="облигация",
                security_type="bond",
                raw_quantity=bond["quantity"],
                session=session
            )
            print(f"  {i+1:2d}. {bond['ticker']} - {bond['quantity']} шт.")
        
        # Добавляем немного наличных
        cash = PortfolioCashPosition(
            user_id=test_user.id,
            account_internal_id=account.id,
            raw_name="Рубль",
            amount=50000.0,
            currency="RUB"
        )
        session.add(cash)
        session.commit()
        print(f"✅ Добавлено 50,000 ₽ наличных")
        
    finally:
        session.close()
    
    print(f"\n🚀 ЗАПУСКАЕМ АНАЛИЗ 25 ОБЛИГАЦИЙ...")
    print("=" * 60)
    
    # Запускаем анализ
    analyzer = PortfolioAnalyzer()
    start_time = time.time()
    
    try:
        analysis_result = await analyzer.run_analysis(test_user.id)
        analysis_duration = time.time() - start_time
        
        print(f"\n✅ АНАЛИЗ ЗАВЕРШЕН ЗА {analysis_duration:.2f} СЕКУНД")
        print("=" * 60)
        
        if "error" in analysis_result:
            print(f"❌ Ошибка анализа: {analysis_result['error']}")
        else:
            print(f"📊 Результат анализа:")
            print(f"  - Сводка: {analysis_result.get('summary', 'Нет данных')[:100]}...")
            print(f"  - Рекомендации: {len(analysis_result.get('recommendations', []))} шт.")
            print(f"  - Риски: {len(analysis_result.get('risks', []))} шт.")
            print(f"  - Метрики: {len(analysis_result.get('metrics', {}))} показателей")
            
    except Exception as e:
        analysis_duration = time.time() - start_time
        print(f"\n❌ ОШИБКА АНАЛИЗА ЗА {analysis_duration:.2f} СЕКУНД")
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
