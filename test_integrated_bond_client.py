#!/usr/bin/env python3
"""
Тест IntegratedBondClient с T-Bank интеграцией
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.utils.integrated_bond_client import IntegratedBondClient

async def test_integrated_bond_client():
    """Тест IntegratedBondClient с T-Bank"""
    print("🧪 Тестируем IntegratedBondClient с T-Bank...")
    
    try:
        client = IntegratedBondClient()
        
        # Тестируем с реальным ISIN
        test_isin = "RU000A10B2M3"  # Облигация из вашего портфеля
        print(f"🔍 Тестируем получение данных для {test_isin}...")
        
        bond_data = await client.get_bond_data(test_isin)
        
        if bond_data:
            print(f"✅ Получены данные облигации:")
            print(f"  - ISIN: {bond_data.isin}")
            print(f"  - Название: {bond_data.name}")
            print(f"  - Цена: {bond_data.price}")
            print(f"  - YTM: {bond_data.yield_to_maturity}")
            print(f"  - CorpBonds найдено: {bond_data.corpbonds_found}")
            print(f"  - T-Bank найдено: {bond_data.tbank_found}")
            print(f"  - MOEX найдено: {bond_data.moex_found}")
            print(f"  - Уверенность: {bond_data.confidence}")
        else:
            print("❌ Данные облигации не получены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_integrated_bond_client())
