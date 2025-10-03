#!/usr/bin/env python3
"""
Тест различных вариантов URL для gen-api.ru
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

async def test_genapi_variants():
    """Тест различных вариантов URL для gen-api.ru"""
    print("🔍 Тест различных вариантов URL для gen-api.ru...")
    
    api_key = "sk-sYaKAn8J4zmc7NhbDmrSmO2hSwDZ0xS6g1JWtD8LM1CT7gla8fksbvUDFHsf"
    
    # Различные варианты URL
    test_urls = [
        "https://gen-api.ru/v1",
        "https://api.gen-api.ru/v1", 
        "https://gen-api.ru/api/v1",
        "https://api.gen-api.ru/api/v1",
        "https://gen-api.ru/openai/v1",
        "https://api.gen-api.ru/openai/v1",
        "https://gen-api.ru/chat/v1",
        "https://api.gen-api.ru/chat/v1",
        "https://gen-api.ru/gpt/v1",
        "https://api.gen-api.ru/gpt/v1",
        "https://gen-api.ru/ai/v1",
        "https://api.gen-api.ru/ai/v1"
    ]
    
    for url in test_urls:
        try:
            print(f"\n📋 Тестируем URL: {url}")
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=url,
                timeout=10.0
            )
            
            start_time = time.time()
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Привет, это тест."}
                ],
                max_tokens=50
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ УСПЕХ! URL: {url}")
            print(f"⏱️ Время ответа: {duration:.2f} сек")
            print(f"📝 Ответ: {response.choices[0].message.content}")
            return url
            
        except Exception as e:
            print(f"❌ Не работает: {url}")
            print(f"   Ошибка: {str(e)[:100]}...")
            continue
    
    print("\n❌ Ни один URL не работает")
    return None

if __name__ == "__main__":
    result = asyncio.run(test_genapi_variants())
    if result:
        print(f"\n🎉 Найден рабочий URL: {result}")
    else:
        print("\n💡 Рекомендации:")
        print("1. Проверьте правильность API ключа")
        print("2. Убедитесь, что сервис gen-api.ru существует")
        print("3. Обратитесь к документации провайдера")
        print("4. Рассмотрите альтернативные прокси-сервисы")
