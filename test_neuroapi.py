#!/usr/bin/env python3
"""
Тест NeuroAPI
"""
import asyncio
import sys
import os
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent))

import openai
from dotenv import load_dotenv

load_dotenv()

async def test_neuroapi():
    """Тест NeuroAPI"""
    print("🧪 Тест NeuroAPI...")
    
    try:
        # Создаем клиент
        api_key = os.getenv("OPENAI_API_KEY", "sk-3lObctPRQiG7Pal1iDyiwQjdcipcvJRHDqvrbFGTmBeK735FUOS9sFevOBYa")
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://neuroapi.host/v1",
            timeout=120.0,
            max_retries=3
        )
        
        print("🔄 Отправляем запрос...")
        
        # Простой тест
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
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
    asyncio.run(test_neuroapi())
