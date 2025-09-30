#!/usr/bin/env python3
"""
Тест загрузки календаря выплат для облигаций
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from bot.providers.aggregator import MarketDataAggregator
from bot.providers.moex_iss.client import MOEXISSClient
from bot.core.config import config

async def test_calendar():
    print("🔍 Тестирование загрузки календаря выплат...")
    
    # Тестовые ISIN облигаций из вашего портфеля
    test_bonds = [
        "RU000A10B2M3",  # БДеньг-2P8
        "RU000A105SK4",  # Роделен1P4
        "RU000A107PW1",  # БДеньг-2P5
        "RU000A1082K7",  # ВЭББНКР 06
        "RU000A10CKZ0",  # ЕврХол3P04
        "RU000A109K40",  # ФосАгро П2
        "RU000A10BL99",  # Сбер SbD6R
        "RU000A10CT33",  # Атомэнпр08
        "RU000A104B46",  # ГПБ001P21P
        "RU000A106P97",  # sСОПФДОМ6
    ]
    
    print(f"📋 Тестируем {len(test_bonds)} облигаций:")
    for bond in test_bonds:
        print(f"  - {bond}")
    
    print("\n" + "="*60)
    
    # Тест 1: Прямой запрос к MOEX
    print("🌐 Тест 1: Прямой запрос к MOEX ISS...")
    moex_client = MOEXISSClient()
    
    for i, bond in enumerate(test_bonds[:3]):  # Тестируем первые 3
        print(f"\n📊 Тестируем {bond} ({i+1}/3):")
        try:
            calendar = await moex_client.get_bond_calendar(bond, days_ahead=30)
            if calendar:
                print(f"  ✅ Успешно загружен календарь")
                print(f"  📅 Купонов: {len(calendar.coupons)}")
                print(f"  🏦 Амортизаций: {len(calendar.amortizations)}")
                
                if calendar.coupons:
                    print(f"  💰 Ближайшие купоны:")
                    for coupon in calendar.coupons[:3]:  # Показываем первые 3
                        print(f"    - {coupon.coupon_date.strftime('%d.%m.%Y')}: {coupon.coupon_value} ₽")
                else:
                    print(f"  ❌ Купонов не найдено")
                    
            else:
                print(f"  ❌ Календарь не загружен")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    
    print("\n" + "="*60)
    
    # Тест 2: Через MarketDataAggregator
    print("🔄 Тест 2: Через MarketDataAggregator...")
    aggregator = MarketDataAggregator()
    
    for i, bond in enumerate(test_bonds[:3]):  # Тестируем первые 3
        print(f"\n📊 Тестируем {bond} через агрегатор ({i+1}/3):")
        try:
            calendar_data = await aggregator.get_bond_calendar(bond)
            if calendar_data:
                print(f"  ✅ Успешно загружен календарь")
                print(f"  📅 Купонов: {len(calendar_data.get('coupons', []))}")
                print(f"  🏦 Амортизаций: {len(calendar_data.get('amortizations', []))}")
                
                coupons = calendar_data.get('coupons', [])
                if coupons:
                    print(f"  💰 Ближайшие купоны:")
                    for coupon in coupons[:3]:  # Показываем первые 3
                        date_str = coupon['date'].strftime('%d.%m.%Y') if hasattr(coupon['date'], 'strftime') else str(coupon['date'])
                        print(f"    - {date_str}: {coupon['value']} ₽")
                else:
                    print(f"  ❌ Купонов не найдено")
                    
            else:
                print(f"  ❌ Календарь не загружен")
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    
    print("\n" + "="*60)
    print("✅ Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_calendar())
