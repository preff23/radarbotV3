#!/usr/bin/env python3
"""
Тест нового T-Bank API токена
"""
import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.providers.tbank_rest import TBankRestClient

async def test_tbank_token():
    """Тест нового T-Bank токена"""
    print("🧪 Тестируем новый T-Bank API токен...")
    
    try:
        # Создаем клиент
        tbank = TBankRestClient()
        
        # Тестируем поиск инструмента
        print("🔍 Тестируем поиск инструмента 'SBER'...")
        instruments = await tbank.find_instrument("SBER")
        
        if instruments and len(instruments) > 0:
            print(f"✅ Найдено {len(instruments)} инструментов")
            for i, instrument in enumerate(instruments[:3]):  # Показываем первые 3
                print(f"  {i+1}. {instrument.name} - {instrument.ticker}")
        else:
            print("❌ Инструменты не найдены")
        
        # Тестируем получение котировок
        print("\n📊 Тестируем получение котировок для SBER...")
        if instruments:
            figi = instruments[0].figi
            if figi:
                quotes = await tbank.get_last_prices([figi])
                if quotes:
                    print(f"✅ Получены котировки: {quotes}")
                else:
                    print("❌ Котировки не получены")
            else:
                print("❌ FIGI не найден")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_tbank_token())
