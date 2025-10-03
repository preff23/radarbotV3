#!/usr/bin/env python3
"""
Тест скорости GPT API через gen-api.ru
"""
import asyncio
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from openai import AsyncOpenAI

async def test_genapi_speed():
    """Тест скорости GPT API через gen-api.ru"""
    print("🔍 Тест скорости GPT API через gen-api.ru...")
    
    try:
        # Инициализируем клиент для gen-api.ru
        client = AsyncOpenAI(
            api_key="sk-sYaKAn8J4zmc7NhbDmrSmO2hSwDZ0xS6g1JWtD8LM1CT7gla8fksbvUDFHsf",
            base_url="https://gen-api.ru/v1"  # Попробуем стандартный путь
        )
        
        # Простой тест
        print("📋 Тест 1: Простой запрос...")
        start_time = time.time()
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник по анализу портфелей."},
                {"role": "user", "content": "Проанализируй портфель из 3 облигаций: А, Б, В. Дай краткий анализ."}
            ],
            max_tokens=500
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Простой запрос: {duration:.2f} сек")
        print(f"📝 Ответ: {response.choices[0].message.content[:100]}...")
        
        # Тест с большим промптом
        print("\n📋 Тест 2: Большой промпт...")
        start_time = time.time()
        
        # Создаем большой JSON с данными портфеля
        portfolio_data = {
            "positions": [
                {
                    "name": f"Облигация {i}",
                    "ticker": f"BOND{i:03d}",
                    "isin": f"RU000A{i:010d}",
                    "type": "bond",
                    "price": 100.0 + i,
                    "ytm": 10.0 + i,
                    "quantity": 10 + i,
                    "value": (100.0 + i) * (10 + i)
                }
                for i in range(10)  # 10 облигаций
            ],
            "total_value": 25000.0,
            "bond_count": 10,
            "share_count": 0
        }
        
        user_message = f"""
Проанализируй портфель:

ДАННЫЕ ПОРТФЕЛЯ:
{portfolio_data}

Дай полный анализ портфеля.
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу портфелей облигаций. Дай детальный анализ."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Большой промпт: {duration:.2f} сек")
        print(f"📝 Ответ: {response.choices[0].message.content[:200]}...")
        
        print("\n🎉 Тест gen-api.ru завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста gen-api.ru: {e}")
        
        # Попробуем альтернативные URL
        print("\n🔄 Пробуем альтернативные URL...")
        
        alternative_urls = [
            "https://api.gen-api.ru/v1",
            "https://gen-api.ru/api/v1",
            "https://api.gen-api.ru/api/v1"
        ]
        
        for url in alternative_urls:
            try:
                print(f"📋 Пробуем URL: {url}")
                client = AsyncOpenAI(
                    api_key="sk-sYaKAn8J4zmc7NhbDmrSmO2hSwDZ0xS6g1JWtD8LM1CT7gla8fksbvUDFHsf",
                    base_url=url
                )
                
                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "user", "content": "Привет, это тест."}
                    ],
                    max_tokens=100
                )
                
                print(f"✅ Успешно! URL: {url}")
                print(f"📝 Ответ: {response.choices[0].message.content}")
                return True
                
            except Exception as url_error:
                print(f"❌ Не работает: {url} - {url_error}")
                continue
        
        print("❌ Ни один URL не работает")
        return False

if __name__ == "__main__":
    asyncio.run(test_genapi_speed())
