#!/usr/bin/env python3
"""
Тестовый скрипт для анализа портфеля
"""

import asyncio
import sys
import time
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_portfolio_analysis():
    """Тестирует анализ портфеля"""
    print("🧪 ТЕСТ АНАЛИЗА ПОРТФЕЛЯ")
    print("=" * 50)
    
    # Создаем тестовые данные портфеля
    test_portfolio = {
        "accounts": [
            {
                "account_id": "test_account_1",
                "account_name": "Брокерский счет 5",
                "total_value": 680440.59,
                "holdings": [
                    {
                        "security_name": "КЛС-Трейд БО-03",
                        "security_type": "bond",
                        "quantity": 100,
                        "current_value": 5943.97,
                        "isin": "RU000A10B2M3"
                    },
                    {
                        "security_name": "Быстроденьги 0029-08",
                        "security_type": "bond", 
                        "quantity": 200,
                        "current_value": 160249.24,
                        "isin": "RU000A10CRC4"
                    },
                    {
                        "security_name": "ГМК Норильский никель БО-001P-14-USD",
                        "security_type": "bond",
                        "quantity": 50,
                        "current_value": 99999.28,
                        "isin": "RU000A10ATB6"
                    }
                ],
                "cash_positions": [
                    {
                        "currency": "RUB",
                        "amount": 326839.58
                    }
                ]
            }
        ]
    }
    
    print(f"📊 Тестовый портфель: {len(test_portfolio['accounts'])} счетов")
    print(f"📈 Облигаций: {sum(len(acc['holdings']) for acc in test_portfolio['accounts'])}")
    print()
    
    # Создаем анализатор
    analyzer = PortfolioAnalyzer()
    
    # Тестируем анализ
    start_time = time.time()
    print("🚀 Запуск анализа...")
    
    try:
        # Сначала нужно создать пользователя в базе данных
        from bot.core.db import db_manager, User
        from bot.core.config import config
        
        # Используем тестовую базу данных
        import os
        os.environ['DATABASE_URL'] = 'sqlite:///test_radar_bot.db'
        
        # Пересоздаем db_manager с тестовой базой
        from bot.core.db import DatabaseManager
        test_db_manager = DatabaseManager()
        
        # Создаем тестового пользователя
        user = test_db_manager.create_user(
            phone_number="+79151731545",
            telegram_id=123456789,
            username="test_user"
        )
        
        # Создаем тестовые данные портфеля
        from bot.core.db import PortfolioHoldingV2, PortfolioAccount, PortfolioCashPosition
        
        # Создаем счет
        session = test_db_manager.SessionLocal()
        account = test_db_manager.get_or_create_account(
            user_id=user.id,
            account_id="test_account_1",
            session=session,
            account_name="Брокерский счет 5",
            portfolio_value=680440.59
        )
        
        # Добавляем облигации
        test_db_manager.add_holding(
            user_id=user.id,
            raw_name="КЛС-Трейд БО-03",
            normalized_name="КЛС-Трейд БО-03",
            normalized_key="КЛС-Трейд БО-03",
            raw_quantity=100,
            isin="RU000A10B2M3",
            security_type="bond",
            account_internal_id=account.id
        )
        
        test_db_manager.add_holding(
            user_id=user.id,
            raw_name="Быстроденьги 0029-08",
            normalized_name="Быстроденьги 0029-08",
            normalized_key="Быстроденьги 0029-08",
            raw_quantity=200,
            isin="RU000A10CRC4",
            security_type="bond",
            account_internal_id=account.id
        )
        
        test_db_manager.add_holding(
            user_id=user.id,
            raw_name="ГМК Норильский никель БО-001P-14-USD",
            normalized_name="ГМК Норильский никель БО-001P-14-USD",
            normalized_key="ГМК Норильский никель БО-001P-14-USD",
            raw_quantity=50,
            isin="RU000A10ATB6",
            security_type="bond",
            account_internal_id=account.id
        )
        
        # Добавляем кэш
        from bot.core.db import PortfolioCashPosition
        cash = PortfolioCashPosition(
            user_id=user.id,
            account_internal_id=account.id,
            currency="RUB",
            amount=326839.58
        )
        session.add(cash)
        session.commit()
        session.close()
        
        print(f"✅ Создан тестовый портфель для пользователя {user.id}")
        
        result = await analyzer.run_analysis(user.id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Анализ завершен за {duration:.2f} секунд")
        print(f"📝 Результат: {len(result) if result else 0} символов")
        
        if result:
            print("\n📋 ПРЕВЬЮ РЕЗУЛЬТАТА:")
            print("-" * 30)
            print(result[:500] + "..." if len(result) > 500 else result)
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ Ошибка анализа за {duration:.2f} секунд: {e}")
        logger.error(f"Test analysis failed: {e}", exc_info=True)
        
        # Показываем детали ошибки
        import traceback
        print("\n🔍 ДЕТАЛИ ОШИБКИ:")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_portfolio_analysis())
