#!/usr/bin/env python3
"""
Тест скорости NeuroAPI
"""
import asyncio
import sys
import os
import time
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

import openai
from dotenv import load_dotenv

load_dotenv()

async def test_neuroapi_speed():
    """Тест скорости NeuroAPI"""
    print("🧪 Тест скорости NeuroAPI...")
    
    try:
        # Создаем клиент
        api_key = os.getenv("OPENAI_API_KEY", "sk-ljmNZVQv5Fjdom5CMlelMKjbZtpjRDYeqjdtzFJXJSZtWsx8")
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://neuroapi.host/v1",
            timeout=120.0,
            max_retries=3
        )
        
        # Тест 1: Простой запрос
        print("🔄 Тест 1: Простой запрос...")
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу инвестиций."},
                {"role": "user", "content": "Проанализируй облигации Газпром на 100,000 рублей. Кратко."}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        end_time = time.time()
        duration1 = end_time - start_time
        print(f"✅ Тест 1 завершен за {duration1:.2f} секунд")
        print(f"📝 Ответ: {response.choices[0].message.content[:100]}...")
        
        # Тест 2: Более сложный запрос
        print("\n🔄 Тест 2: Сложный запрос...")
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу инвестиций. Дай подробный анализ портфеля."},
                {"role": "user", "content": "Проанализируй портфель: 10 облигаций Газпрома на 500,000 руб, 5 облигаций Сбербанка на 300,000 руб, 3 облигации ВТБ на 200,000 руб. Оцени риски, доходность, диверсификацию."}
            ],
            max_tokens=2000,
            temperature=0.1
        )
        
        end_time = time.time()
        duration2 = end_time - start_time
        print(f"✅ Тест 2 завершен за {duration2:.2f} секунд")
        print(f"📝 Ответ: {response.choices[0].message.content[:100]}...")
        
        # Тест 3: Максимальный запрос
        print("\n🔄 Тест 3: Максимальный запрос...")
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу инвестиций. Дай максимально подробный анализ портфеля с рекомендациями."},
                {"role": "user", "content": "Проанализируй портфель: 15 облигаций Газпрома на 1,000,000 руб, 10 облигаций Сбербанка на 800,000 руб, 8 облигаций ВТБ на 600,000 руб, 5 облигаций Лукойла на 400,000 руб, 3 облигации Роснефти на 300,000 руб. Оцени риски, доходность, диверсификацию, дай рекомендации по оптимизации."}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        end_time = time.time()
        duration3 = end_time - start_time
        print(f"✅ Тест 3 завершен за {duration3:.2f} секунд")
        print(f"📝 Ответ: {response.choices[0].message.content[:100]}...")
        
        # Итоги
        print(f"\n📊 Итоги скорости:")
        print(f"   Простой запрос: {duration1:.2f} сек")
        print(f"   Сложный запрос: {duration2:.2f} сек")
        print(f"   Максимальный запрос: {duration3:.2f} сек")
        print(f"   Средняя скорость: {(duration1 + duration2 + duration3) / 3:.2f} сек")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_neuroapi_speed())
