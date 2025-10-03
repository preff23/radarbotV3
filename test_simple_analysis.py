#!/usr/bin/env python3
"""
Простой тест AI анализа
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

async def test_simple_analysis():
    """Простой тест AI анализа"""
    print("🧪 Простой тест AI анализа...")
    
    try:
        # Создаем клиент
        api_key = os.getenv("OPENAI_API_KEY", "sk-3lObctPRQiG7Pal1iDyiwQjdcipcvJRHDqvrbFGTmBeK735FUOS9sFevOBYa")
        client = GenAPIOpenAIAdapter(api_key)
        
        print("🔄 Отправляем запрос...")
        
        # Простой тест
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу инвестиций."},
                {"role": "user", "content": "Проанализируй облигации Газпром на 100,000 рублей. Кратко."}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        
        print(f"✅ Ответ получен: {response.choices[0].message.content[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_simple_analysis())
