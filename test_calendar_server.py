#!/usr/bin/env python3
"""
Тест календаря выплат на сервере
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/Users/goretofff/Desktop/radar3.0')

from bot.providers.moex_iss.client import MOEXISSClient
from bot.providers.aggregator import MarketDataAggregator
from bot.core.logging import get_logger

logger = get_logger(__name__)

async def test_calendar_direct():
    """Тестируем календарь выплат напрямую"""
    print("🔍 Тестирование календаря выплат напрямую...")
    
    # Тестовые облигации из нашей базы
    test_bonds = [
        "RU000A10B2M3",  # Быстроденьги МФК
        "RU000A105SK4",  # Роделен ЛК
        "RU000A10CT33",  # Атомэнергопром
        "RU000A104B46",  # Банк ГПБ
        "RU000A106P97",  # СОПФ ДОМ.РФ
    ]
    
    print(f"📋 Тестируем {len(test_bonds)} облигаций:")
    for bond in test_bonds:
        print(f"  - {bond}")
    
    print("\n" + "="*60)
    print("🌐 Тест 1: Прямой запрос к MOEX ISS...")
    
    moex_client = MOEXISSClient()
    
    for i, secid in enumerate(test_bonds):
        print(f"\n📊 Тестируем {secid} ({i+1}/{len(test_bonds)}):")
        try:
            calendar = await moex_client.get_bond_calendar(secid, days_ahead=365)
            if calendar:
                print(f"  ✅ Успешно загружен календарь")
                print(f"  📅 Купонов: {len(calendar.coupons)}")
                print(f"  🏦 Амортизаций: {len(calendar.amortizations)}")
                
                # Показываем ближайшие события
                from datetime import datetime
                upcoming_coupons = [c for c in calendar.coupons if c.coupon_date >= datetime.now()]
                if upcoming_coupons:
                    print("  💰 Ближайшие купоны:")
                    for coupon in sorted(upcoming_coupons, key=lambda x: x.coupon_date)[:3]:
                        print(f"    - {coupon.coupon_date.strftime('%d.%m.%Y')}: {coupon.coupon_value} ₽")
                else:
                    print("  ❌ Купонов не найдено")
            else:
                print("  ❌ Не удалось загрузить календарь")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    
    print("\n" + "="*60)
    print("🔄 Тест 2: Через MarketDataAggregator...")
    
    market_aggregator = MarketDataAggregator()
    
    for i, secid in enumerate(test_bonds):
        print(f"\n📊 Тестируем {secid} через агрегатор ({i+1}/{len(test_bonds)}):")
        try:
            calendar_data = await market_aggregator.get_bond_calendar(secid)
            if calendar_data:
                print(f"  ✅ Успешно загружен календарь")
                print(f"  📅 Купонов: {len(calendar_data.get('coupons', []))}")
                print(f"  🏦 Амортизаций: {len(calendar_data.get('amortizations', []))}")
                
                # Показываем ближайшие события
                from datetime import datetime
                upcoming_coupons = [c for c in calendar_data.get('coupons', []) if c.get('date') and c['date'] >= datetime.now()]
                if upcoming_coupons:
                    print("  💰 Ближайшие купоны:")
                    for coupon in sorted(upcoming_coupons, key=lambda x: x['date'])[:3]:
                        print(f"    - {coupon['date'].strftime('%d.%m.%Y')}: {coupon['value']} ₽")
                else:
                    print("  ❌ Купонов не найдено")
            else:
                print("  ❌ Не удалось загрузить календарь")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    
    print("\n" + "="*60)
    print("✅ Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_calendar_direct())
