#!/usr/bin/env python3
"""
Прямой тест календаря выплат в PortfolioAnalyzer
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append('/Users/goretofff/Desktop/radar3.0')

from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.core.logging import get_logger

logger = get_logger(__name__)

async def test_calendar_direct():
    """Прямой тест календаря выплат"""
    print("🔍 Прямой тест календаря выплат...")
    
    analyzer = PortfolioAnalyzer()
    
    # Создаем тестовые снапшоты с облигациями
    from bot.providers.moex_iss.models import BondSnapshot
    from datetime import datetime
    
    test_snapshots = [
        BondSnapshot(
            secid="RU000A10B2M3",
            shortname="Быстроденьги МФК",
            last=102.88,
            change_day_pct=0.5,
            trading_status="NormalTrading",
            ytm=25.07,
            duration=162.0,
            currency="RUB",
            board="TQCB",
            market="bonds",
            face_value=1000.0,
            volume=1000.0,
            security_type="bond"
        ),
        BondSnapshot(
            secid="RU000A10CT33",
            shortname="Атомэнергопром",
            last=99.5,
            change_day_pct=-0.2,
            trading_status="NormalTrading",
            ytm=15.69,
            duration=1313.0,
            currency="RUB",
            board="TQCB",
            market="bonds",
            face_value=1000.0,
            volume=500.0,
            security_type="bond"
        ),
        BondSnapshot(
            secid="RU000A104B46",
            shortname="Банк ГПБ",
            last=103.58,
            change_day_pct=0.8,
            trading_status="NormalTrading",
            ytm=15.5,
            duration=1044.0,
            currency="RUB",
            board="TQCB",
            market="bonds",
            face_value=1000.0,
            volume=250.0,
            security_type="bond"
        )
    ]
    
    print(f"📋 Создано {len(test_snapshots)} тестовых снапшотов")
    for snapshot in test_snapshots:
        print(f"  - {snapshot.shortname} ({snapshot.security_type}) - SECID: {snapshot.secid}")
    
    # Тестируем календарь выплат напрямую
    print(f"\n🔍 Тестируем _get_bond_calendar...")
    calendar = await analyzer._get_bond_calendar(test_snapshots)
    
    print(f"📅 Результат календаря выплат:")
    print(f"  - Событий: {len(calendar)}")
    
    if calendar:
        print(f"  🎉 Календарь выплат работает!")
        for i, event in enumerate(calendar[:5]):  # Показываем первые 5 событий
            print(f"    {i+1}. {event.get('name', 'Unknown')}: {event.get('date', 'No date')} - {event.get('value', 'No value')} ₽ ({event.get('type', 'unknown')})")
    else:
        print(f"  ❌ Календарь выплат пуст!")
    
    print(f"\n✅ Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_calendar_direct())
