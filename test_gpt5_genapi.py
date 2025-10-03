#!/usr/bin/env python3
"""
Тест gpt-5 через gen-api.ru
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

from bot.utils.genapi_client import GenAPIOpenAIAdapter
from dotenv import load_dotenv

load_dotenv()

async def test_gpt5_genapi():
    """Тестируем gpt-5 через gen-api.ru"""
    print("🧪 Тестируем gpt-5 через gen-api.ru...")
    
    # Получаем API ключ
    api_key = os.getenv("OPENAI_API_KEY", "sk-3lObctPRQiG7Pal1iDyiwQjdcipcvJRHDqvrbFGTmBeK735FUOS9sFevOBYa")
    print(f"🔑 API ключ: {api_key[:20]}...")
    
    # Создаем клиент
    client = GenAPIOpenAIAdapter(api_key)
    
    # Простой тест
    print("\n📝 Простой тест...")
    try:
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Ты помощник по инвестициям."},
                {"role": "user", "content": "Привет! Как дела?"}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"✅ Ответ: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Ошибка в простом тесте: {e}")
        return False
    
    # Тест с более сложным запросом
    print("\n📊 Тест анализа портфеля...")
    try:
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу инвестиционных портфелей. Анализируй данные и давай рекомендации."},
                {"role": "user", "content": "У меня в портфеле есть облигации Газпром БО-001Р-02 (RU000A0JX0S9) на сумму 100,000 рублей. Проанализируй риски и дай рекомендации."}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        print(f"✅ Анализ: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте анализа: {e}")
        return False
    
    print("\n🎉 Все тесты прошли успешно!")
    return True

if __name__ == "__main__":
    asyncio.run(test_gpt5_genapi())
