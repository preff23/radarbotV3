#!/usr/bin/env python3
"""
Тестовый скрипт для проверки производительности анализа портфеля
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


async def test_analysis_performance():
    """Тестирует производительность анализа портфеля"""
    print("🧪 ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ АНАЛИЗА ПОРТФЕЛЯ")
    print("=" * 60)
    
    # Создаем анализатор
    analyzer = PortfolioAnalyzer()
    
    # Тестируем загрузку данных
    print("🚀 Тестируем загрузку данных...")
    
    start_time = time.time()
    
    try:
        # Тестируем загрузку календаря облигаций
        print("📅 Тестируем загрузку календаря облигаций...")
        from bot.providers.aggregator import market_aggregator
        
        test_isins = ["RU000A10B2M3", "RU000A10CRC4", "RU000A10ATB6"]
        
        calendar_start = time.time()
        calendar_results = []
        for isin in test_isins:
            print(f"  📊 Загружаем календарь для {isin}...")
            calendar = await market_aggregator.get_bond_calendar(isin)
            calendar_results.append(calendar)
            print(f"  ✅ Календарь для {isin}: {len(calendar.get('coupons', [])) if calendar else 0} купонов")
        
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
        
        total_duration = time.time() - start_time
        print(f"\n✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ ЗА {total_duration:.2f} СЕКУНД")
        print("=" * 60)
        print(f"📅 Календарь: {calendar_duration:.2f}с")
        print(f"📰 Новости: {news_duration:.2f}с")
        print(f"🔗 Облигации: {bonds_duration:.2f}с")
        print(f"📈 Макро: {macro_duration:.2f}с")
        print(f"⏱️  Общее время: {total_duration:.2f}с")
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ Ошибка тестирования за {duration:.2f} секунд: {e}")
        logger.error(f"Performance test failed: {e}", exc_info=True)
        
        # Показываем детали ошибки
        import traceback
        print("\n🔍 ДЕТАЛИ ОШИБКИ:")
        print(traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(test_analysis_performance())
