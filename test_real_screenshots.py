#!/usr/bin/env python3
"""
Тест анализа с реальными скриншотами портфеля
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
from bot.pipeline.portfolio_ingest_pipeline import PortfolioIngestPipeline

setup_logging()
logger = get_logger(__name__)

async def test_real_screenshots():
    """Тест анализа с реальными скриншотами"""
    print("🧪 ТЕСТ АНАЛИЗА С РЕАЛЬНЫМИ СКРИНШОТАМИ")
    print("=" * 60)
    
    try:
        # Создаем тестового пользователя
        test_user_id = 888888
        test_phone = "+78888888888"
        
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
                username="test_screenshots_user"
            )
            user_id = user.id
            print(f"✅ Пользователь создан: {user_id}")
            
            # Создаем тестовый аккаунт
            account = db_manager.get_or_create_account(
                user_id=user_id,
                account_id="test_screenshots_account",
                account_name="Тестовый счет (скриншоты)",
                portfolio_value=0.0,  # Будет обновлено после OCR
                session=session
            )
            account_id = account.id
            print(f"✅ Аккаунт создан: {account_id}")
        finally:
            session.close()
        
        # Тестируем OCR на реальных скриншотах
        print("\n📸 ТЕСТИРУЕМ OCR НА РЕАЛЬНЫХ СКРИНШОТАХ...")
        print("=" * 60)
        
        pipeline = PortfolioIngestPipeline()
        
        # Тест 1: test4.jpeg
        print("\n🔍 Обрабатываем test4.jpeg...")
        start_time = time.time()
        
        try:
            # Читаем файл
            with open("/home/ubuntu/radarbotV3/photo/test4.jpeg", "rb") as f:
                image_bytes = f.read()
            
            ocr_result = await pipeline.ingest_from_photo(
                phone_number=test_phone,
                image_bytes=image_bytes
            )
            
            ocr_duration = time.time() - start_time
            print(f"✅ OCR test4.jpeg завершен за {ocr_duration:.2f} секунд")
            
            if ocr_result and ocr_result.positions:
                print(f"📊 Найдено {len(ocr_result.positions)} позиций")
                print(f"  Добавлено: {ocr_result.added}, объединено: {ocr_result.merged}")
            else:
                print("❌ OCR не смог распознать данные в test4.jpeg")
                
        except Exception as e:
            print(f"❌ Ошибка OCR test4.jpeg: {e}")
            ocr_result = None
        
        # Тест 2: test5.jpeg
        print("\n🔍 Обрабатываем test5.jpeg...")
        start_time = time.time()
        
        try:
            # Читаем файл
            with open("/home/ubuntu/radarbotV3/photo/test5.jpeg", "rb") as f:
                image_bytes2 = f.read()
            
            ocr_result2 = await pipeline.ingest_from_photo(
                phone_number=test_phone,
                image_bytes=image_bytes2
            )
            
            ocr_duration = time.time() - start_time
            print(f"✅ OCR test5.jpeg завершен за {ocr_duration:.2f} секунд")
            
            if ocr_result2 and ocr_result2.positions:
                print(f"📊 Найдено {len(ocr_result2.positions)} позиций")
                print(f"  Добавлено: {ocr_result2.added}, объединено: {ocr_result2.merged}")
            else:
                print("❌ OCR не смог распознать данные в test5.jpeg")
                
        except Exception as e:
            print(f"❌ Ошибка OCR test5.jpeg: {e}")
            ocr_result2 = None
        
        # Проверяем, есть ли данные для анализа
        holdings = db_manager.get_user_holdings(user_id)
        print(f"\n📈 Всего позиций в портфеле: {len(holdings)}")
        
        if not holdings:
            print("❌ Нет позиций для анализа. OCR не смог распознать данные.")
            return False
        
        # Показываем что распознано
        print("\n📋 РАСПОЗНАННЫЕ ПОЗИЦИИ:")
        for i, holding in enumerate(holdings[:10]):  # Показываем первые 10
            print(f"  {i+1}. {holding.normalized_name} - {holding.raw_quantity} шт.")
        
        if len(holdings) > 10:
            print(f"  ... и еще {len(holdings) - 10} позиций")
        
        # Запускаем полный анализ
        print(f"\n🚀 ЗАПУСКАЕМ ПОЛНЫЙ АНАЛИЗ ПОРТФЕЛЯ...")
        print("=" * 60)
        
        start_time = time.time()
        
        analyzer = PortfolioAnalyzer()
        result = await analyzer.run_analysis(user_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ АНАЛИЗ ЗАВЕРШЕН ЗА {duration:.2f} СЕКУНД")
        print("=" * 60)
        
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
        
        # Показываем краткий AI анализ
        if "ai_analysis" in result and result["ai_analysis"]:
            print(f"\n🤖 КРАТКИЙ AI АНАЛИЗ:")
            print("-" * 40)
            ai_text = result["ai_analysis"]
            # Показываем первые 500 символов
            preview = ai_text[:500] + "..." if len(ai_text) > 500 else ai_text
            print(preview)
        
        print(f"\n🎉 ТЕСТ С РЕАЛЬНЫМИ СКРИНШОТАМИ ПРОЙДЕН УСПЕШНО!")
        print(f"⏱️ Общее время: {duration:.2f} секунд")
        print(f"📊 Позиций проанализировано: {len(holdings)}")
        
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
    
    print("🚀 Запуск теста с реальными скриншотами...")
    success = await test_real_screenshots()
    
    if success:
        print("\n✅ ВСЕ ТЕСТЫ С РЕАЛЬНЫМИ СКРИНШОТАМИ ПРОЙДЕНЫ УСПЕШНО!")
        sys.exit(0)
    else:
        print("\n❌ ТЕСТЫ С РЕАЛЬНЫМИ СКРИНШОТАМИ НЕ ПРОШЛИ!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
