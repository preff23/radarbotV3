#!/usr/bin/env python3
"""
Тест отладки payload для AI
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer

async def test_payload_debug():
    """Тест отладки payload"""
    print("🧪 Тест отладки payload для AI...")
    
    try:
        analyzer = PortfolioAnalyzer()
        
        # Тестируем загрузку макро данных
        print("🔄 Тестируем загрузку макро данных...")
        macro_data = await analyzer._get_macro_data()
        print(f"✅ Макро данные: {json.dumps(macro_data, ensure_ascii=False, indent=2)}")
        
        # Тестируем загрузку новостей
        print("\n🔄 Тестируем загрузку новостей...")
        news = await analyzer._get_news([])
        print(f"✅ Новости: {len(news)} статей")
        
        # Тестируем загрузку календаря
        print("\n🔄 Тестируем загрузку календаря...")
        calendar = await analyzer._get_bond_calendar([])
        print(f"✅ Календарь: {len(calendar)} событий")
        
        # Тестируем загрузку истории платежей
        print("\n🔄 Тестируем загрузку истории платежей...")
        payment_history = await analyzer._get_payment_history([])
        print(f"✅ История платежей: {len(payment_history)} записей")
        
        print("\n✅ Все сервисы работают корректно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_payload_debug())
