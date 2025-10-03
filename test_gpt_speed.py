#!/usr/bin/env python3
"""
Тест скорости GPT API через NeuroAPI
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

async def test_gpt_speed():
    """Тест скорости GPT API"""
    print("🔍 Тест скорости GPT API через NeuroAPI...")
    
    try:
        # Инициализируем клиент
        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://neuroapi.host/v1"
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
        
        # Читаем оригинальный промпт
        with open("bot/ai/prompts/portfolio_analyze_v14.txt", 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
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
                for i in range(20)  # 20 облигаций
            ],
            "total_value": 50000.0,
            "bond_count": 20,
            "share_count": 0,
            "accounts": [],
            "macro_data": {
                "timestamp": "2024-10-03 15:40:00 МСК",
                "usd_rub": "USD/RUB: 95.50",
                "imoex": "IMOEX: 2800"
            },
            "news": [
                {"title": f"Новость {i}", "description": f"Описание новости {i}"}
                for i in range(10)  # 10 новостей
            ],
            "bond_calendar": [
                {"date": f"2024-10-{i+1:02d}", "event": f"Событие {i}"}
                for i in range(15)  # 15 событий
            ]
        }
        
        user_message = f"""
Проанализируй портфель строго по промпту v14.5.

МАКРО-ДАННЫЕ:
- Время: {portfolio_data['macro_data']['timestamp']}
- USD/RUB: {portfolio_data['macro_data']['usd_rub']}
- IMOEX: {portfolio_data['macro_data']['imoex']}

ДАННЫЕ ПОРТФЕЛЯ:
{portfolio_data}

Дай полный анализ портфеля.
"""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=2000
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Большой промпт: {duration:.2f} сек")
        print(f"📝 Ответ: {response.choices[0].message.content[:200]}...")
        
        # Тест с gpt-4o (если доступен)
        print("\n📋 Тест 3: GPT-4o (если доступен)...")
        try:
            start_time = time.time()
            
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Ты помощник по анализу портфелей."},
                    {"role": "user", "content": "Проанализируй портфель из 3 облигаций: А, Б, В. Дай краткий анализ."}
                ],
                max_tokens=500
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ GPT-4o: {duration:.2f} сек")
            print(f"📝 Ответ: {response.choices[0].message.content[:100]}...")
            
        except Exception as e:
            print(f"❌ GPT-4o недоступен: {e}")
        
        print("\n🎉 Тест завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_gpt_speed())
