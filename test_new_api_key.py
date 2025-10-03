#!/usr/bin/env python3
"""
Тест нового API ключа для gen-api.ru
"""
import asyncio
import os
import sys
import time
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.utils.genapi_client import GenAPIClient, GenAPIOpenAIAdapter

async def test_new_api_key():
    """Тест нового API ключа"""
    print("🔍 Тест нового API ключа для gen-api.ru...")
    
    # Новый API ключ
    api_key = "sk-3lObctPRQiG7Pal1iDyiwQjdcipcvJRHDqvrbFGTmBeK735FUOS9sFevOBYa"
    
    try:
        # Тест 1: Прямой API
        print("📋 Тест 1: Прямой API с новым ключом...")
        client = GenAPIClient(api_key)
        
        messages = [
            {"role": "system", "content": "Ты помощник по анализу портфелей."},
            {"role": "user", "content": "Проанализируй портфель из 3 облигаций: А, Б, В. Дай краткий анализ."}
        ]
        
        start_time = time.time()
        result = await client.chat_completion(messages, max_tokens=500)
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Прямой API: {duration:.2f} сек")
        print(f"📝 Ответ: {result[:200]}...")
        
        # Тест 2: Адаптер OpenAI
        print("\n📋 Тест 2: Адаптер OpenAI с новым ключом...")
        adapter = GenAPIOpenAIAdapter(api_key)
        
        start_time = time.time()
        response = await adapter.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Адаптер OpenAI: {duration:.2f} сек")
        print(f"📝 Ответ: {response.choices[0].message.content[:200]}...")
        
        # Тест 3: Большой промпт для анализа портфеля
        print("\n📋 Тест 3: Большой промпт анализа портфеля...")
        big_messages = [
            {"role": "system", "content": "Ты эксперт по анализу портфелей облигаций. Дай детальный анализ с рекомендациями."},
            {"role": "user", "content": f"""
Проанализируй портфель:

ДАННЫЕ ПОРТФЕЛЯ:
{{
    "positions": [
        {{"name": "Быстроденьги 002Р-08", "ticker": "Быстроденьги 002Р-08", "isin": "RU000A103ZJ0", "type": "bond", "price": 1025.0, "ytm": 10.0, "quantity": 5, "value": 5125.0}},
        {{"name": "КЛС-Трейд БО-03", "ticker": "КЛС-Трейд БО-03", "isin": "RU000A0JXTS8", "type": "bond", "price": 237.76, "ytm": 12.0, "quantity": 25, "value": 5944.0}},
        {{"name": "Полипласт ПО2-БО-11", "ticker": "Полипласт ПО2-БО-11", "isin": "RU000A10CTH9", "type": "bond", "price": 1133.51, "ytm": 8.0, "quantity": 88, "value": 9999.28}}
    ],
    "total_value": 21068.28,
    "bond_count": 3,
    "share_count": 0,
    "macro_data": {{
        "timestamp": "2024-10-03 16:30:00 МСК",
        "usd_rub": "USD/RUB: 95.50",
        "imoex": "IMOEX: 2800"
    }}
}}

Дай полный анализ портфеля с рекомендациями по каждой позиции.
"""}
        ]
        
        start_time = time.time()
        response = await adapter.chat.completions.create(
            model="gpt-4o-mini",
            messages=big_messages,
            max_tokens=3000
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Большой промпт: {duration:.2f} сек")
        print(f"📝 Ответ: {response.choices[0].message.content[:400]}...")
        
        print("\n🎉 Новый API ключ работает отлично!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка с новым API ключом: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_new_api_key())
