#!/usr/bin/env python3
"""
Тест gen-api.ru с правильным API
"""
import asyncio
import os
import sys
import time
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.utils.genapi_client import GenAPIClient, GenAPIOpenAIAdapter

async def test_genapi_real():
    """Тест gen-api.ru с правильным API"""
    print("🔍 Тест gen-api.ru с правильным API...")
    
    api_key = "sk-sYaKAn8J4zmc7NhbDmrSmO2hSwDZ0xS6g1JWtD8LM1CT7gla8fksbvUDFHsf"
    
    try:
        # Тест 1: Прямой API
        print("📋 Тест 1: Прямой API gen-api.ru...")
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
        print("\n📋 Тест 2: Адаптер OpenAI...")
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
        
        # Тест 3: Большой промпт
        print("\n📋 Тест 3: Большой промпт...")
        big_messages = [
            {"role": "system", "content": "Ты эксперт по анализу портфелей облигаций. Дай детальный анализ."},
            {"role": "user", "content": f"""
Проанализируй портфель:

ДАННЫЕ ПОРТФЕЛЯ:
{{
    "positions": [
        {{"name": "Облигация А", "ticker": "BOND001", "type": "bond", "price": 100.0, "ytm": 10.0, "quantity": 10}},
        {{"name": "Облигация Б", "ticker": "BOND002", "type": "bond", "price": 105.0, "ytm": 12.0, "quantity": 15}},
        {{"name": "Облигация В", "ticker": "BOND003", "type": "bond", "price": 95.0, "ytm": 8.0, "quantity": 20}}
    ],
    "total_value": 5000.0,
    "bond_count": 3
}}

Дай полный анализ портфеля с рекомендациями.
"""}
        ]
        
        start_time = time.time()
        response = await adapter.chat.completions.create(
            model="gpt-4o-mini",
            messages=big_messages,
            max_tokens=2000
        )
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Большой промпт: {duration:.2f} сек")
        print(f"📝 Ответ: {response.choices[0].message.content[:300]}...")
        
        print("\n🎉 Все тесты gen-api.ru прошли успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста gen-api.ru: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_genapi_real())
