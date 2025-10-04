#!/usr/bin/env python3
"""
Тест GPT-5 через NeuroAPI
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

async def test_gpt5_neuroapi():
    """Тест GPT-5 через NeuroAPI"""
    print("🧪 Тест GPT-5 через NeuroAPI...")
    
    try:
        # Создаем клиент
        api_key = os.getenv("OPENAI_API_KEY", "sk-ljmNZVQv5Fjdom5CMlelMKjbZtpjRDYeqjdtzFJXJSZtWsx8")
        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://neuroapi.host/v1",
            timeout=120.0,
            max_retries=3
        )
        
        print("🔄 Тестируем GPT-5...")
        
        # Тест GPT-5
        response = await client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Ты эксперт по анализу инвестиций."},
                {"role": "user", "content": "Проанализируй облигации Газпром на 100,000 рублей. Кратко."}
            ],
            max_tokens=1000,
            temperature=0.1
        )
        
        print(f"✅ GPT-5 работает! Ответ: {response.choices[0].message.content[:200]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка с GPT-5: {e}")
        
        # Попробуем GPT-4o-mini как fallback
        print("🔄 Пробуем GPT-4o-mini как fallback...")
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты эксперт по анализу инвестиций."},
                    {"role": "user", "content": "Проанализируй облигации Газпром на 100,000 рублей. Кратко."}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            print(f"✅ GPT-4o-mini работает как fallback: {response.choices[0].message.content[:200]}...")
            return False
        except Exception as e2:
            print(f"❌ И GPT-4o-mini не работает: {e2}")
            return False

if __name__ == "__main__":
    asyncio.run(test_gpt5_neuroapi())
