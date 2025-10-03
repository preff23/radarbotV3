#!/usr/bin/env python3
"""
Тестовый скрипт для анализа 28 случайных облигаций
"""

import asyncio
import sys
import time
import random
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_28_bonds_analysis():
    """Тестирует анализ 28 случайных облигаций"""
    print("🧪 ТЕСТ АНАЛИЗА 28 СЛУЧАЙНЫХ ОБЛИГАЦИЙ")
    print("=" * 60)
    
    # Список случайных ISIN облигаций
    test_isins = [
        "RU000A10B2M3", "RU000A10CRC4", "RU000A10ATB6", "RU000A107PW1",
        "RU000A1082K7", "RU000A10C8H9", "RU000A108C17", "RU000A10CTH9",
        "RU000A10AHB1", "RU000A109NM3", "RU000A10BRN3", "RU000A10C758",
        "RU000A0JVWJ6", "RU000A10C9Z9", "RU000A10B2M3", "RU000A10CRC4",
        "RU000A10ATB6", "RU000A107PW1", "RU000A1082K7", "RU000A10C8H9",
        "RU000A108C17", "RU000A10CTH9", "RU000A10AHB1", "RU000A109NM3",
        "RU000A10BRN3", "RU000A10C758", "RU000A0JVWJ6", "RU000A10C9Z9"
    ]
    
    print(f"📊 Тестируем анализ для {len(test_isins)} облигаций")
    print(f"🔗 ISIN облигаций: {', '.join(test_isins[:5])}...")
    print()
    
    # Создаем анализатор
    analyzer = PortfolioAnalyzer()
    
    # Тестируем загрузку данных
    print("🚀 Запуск тестирования...")
    
    start_time = time.time()
    
    try:
        # Тестируем загрузку календаря облигаций
        print("📅 Тестируем загрузку календаря облигаций...")
        from bot.providers.aggregator import market_aggregator
        
        calendar_start = time.time()
        calendar_results = []
        for i, isin in enumerate(test_isins):
            print(f"  📊 Загружаем календарь для {isin} ({i+1}/{len(test_isins)})...")
            calendar = await market_aggregator.get_bond_calendar(isin)
            calendar_results.append(calendar)
            coupons_count = len(calendar.get('coupons', [])) if calendar else 0
            print(f"  ✅ Календарь для {isin}: {coupons_count} купонов")
        
        calendar_duration = time.time() - calendar_start
        print(f"📅 Загрузка календаря завершена за {calendar_duration:.2f} секунд")
        
        # Тестируем загрузку новостей
        print("📰 Тестируем загрузку новостей...")
        news_start = time.time()
        from bot.sources.news_rss import NewsAggregator
        news_loader = NewsAggregator()
        news = await news_loader.fetch_all_news()
        news_duration = time.time() - news_start
        print(f"📰 Загрузка новостей завершена за {news_duration:.2f} секунд: {len(news)} новостей")
        
        # Тестируем загрузку данных облигаций
        print("🔗 Тестируем загрузку данных облигаций...")
        bonds_start = time.time()
        from bot.services.corpbonds_service import CorpBondsService
        corpbonds_service = CorpBondsService()
        bonds_data = await corpbonds_service.get_multiple_bonds_data(test_isins)
        bonds_duration = time.time() - bonds_start
        print(f"🔗 Загрузка данных облигаций завершена за {bonds_duration:.2f} секунд: {len(bonds_data)} облигаций")
        
        # Тестируем загрузку макро данных
        print("📈 Тестируем загрузку макро данных...")
        macro_start = time.time()
        macro_data = await analyzer._get_macro_data()
        macro_duration = time.time() - macro_start
        print(f"📈 Загрузка макро данных завершена за {macro_duration:.2f} секунд")
        
        # Тестируем загрузку истории платежей
        print("💰 Тестируем загрузку истории платежей...")
        payment_start = time.time()
        from bot.analytics.payment_history import PaymentHistoryAnalyzer
        payment_analyzer = PaymentHistoryAnalyzer()
        
        # Создаем mock snapshots для тестирования
        from bot.providers.aggregator import MarketSnapshot
        mock_snapshots = []
        for isin in test_isins:
            snapshot = MarketSnapshot(secid=isin)
            snapshot.security_type = "bond"
            mock_snapshots.append(snapshot)
        
        payment_history = await payment_analyzer.get_payment_history(mock_snapshots)
        payment_duration = time.time() - payment_start
        print(f"💰 Загрузка истории платежей завершена за {payment_duration:.2f} секунд")
        
        total_duration = time.time() - start_time
        print(f"\n✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ ЗА {total_duration:.2f} СЕКУНД")
        print("=" * 60)
        print(f"📅 Календарь ({len(test_isins)} облигаций): {calendar_duration:.2f}с")
        print(f"📰 Новости: {news_duration:.2f}с")
        print(f"🔗 Облигации ({len(test_isins)} облигаций): {bonds_duration:.2f}с")
        print(f"📈 Макро: {macro_duration:.2f}с")
        print(f"💰 История платежей ({len(test_isins)} облигаций): {payment_duration:.2f}с")
        print(f"⏱️  Общее время: {total_duration:.2f}с")
        print(f"📊 Среднее время на облигацию: {total_duration/len(test_isins):.2f}с")
        
        # Анализируем производительность
        print("\n🔍 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ:")
        print("-" * 40)
        if total_duration > 60:
            print("❌ Анализ слишком медленный (>60 секунд)")
        elif total_duration > 30:
            print("⚠️  Анализ медленный (30-60 секунд)")
        else:
            print("✅ Анализ быстрый (<30 секунд)")
        
        if calendar_duration > 20:
            print("❌ Загрузка календаря слишком медленная")
        elif calendar_duration > 10:
            print("⚠️  Загрузка календаря медленная")
        else:
            print("✅ Загрузка календаря быстрая")
        
        if bonds_duration > 20:
            print("❌ Загрузка данных облигаций слишком медленная")
        elif bonds_duration > 10:
            print("⚠️  Загрузка данных облигаций медленная")
        else:
            print("✅ Загрузка данных облигаций быстрая")
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ Ошибка тестирования за {duration:.2f} секунд: {e}")
        logger.error(f"28 bonds test failed: {e}", exc_info=True)
        
        # Показываем детали ошибки
        import traceback
        print("\n🔍 ДЕТАЛИ ОШИБКИ:")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_28_bonds_analysis())
