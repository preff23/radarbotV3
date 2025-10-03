#!/usr/bin/env python3
"""
Тест доступных моделей в gen-api.ru
"""
import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_genapi_models():
    """Тестируем доступные модели в gen-api.ru"""
    print("🔍 Проверяем доступные модели в gen-api.ru...")
    
    api_key = os.getenv("OPENAI_API_KEY", "sk-3lObctPRQiG7Pal1iDyiwQjdcipcvJRHDqvrbFGTmBeK735FUOS9sFevOBYa")
    base_url = "https://api.gen-api.ru/api/v1"
    
    # Список возможных network_id для тестирования
    possible_networks = [
        "chat-gpt-3",
        "chat-gpt-4", 
        "chat-gpt-4o",
        "chat-gpt-5",
        "gpt-4",
        "gpt-4o",
        "gpt-5",
        "openai-gpt-4",
        "openai-gpt-5"
    ]
    
    async with aiohttp.ClientSession() as session:
        for network_id in possible_networks:
            print(f"\n🧪 Тестируем network_id: {network_id}")
            
            try:
                # Отправляем тестовый запрос
                url = f"{base_url}/networks/{network_id}"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "messages": [
                        {"role": "user", "content": "Привет! Как дела?"}
                    ],
                    "prompt": "Привет! Как дела?",
                    "max_tokens": 50,
                    "temperature": 0.7
                }
                
                async with session.post(url, headers=headers, json=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ {network_id}: Работает! Статус: {result.get('status', 'unknown')}")
                        
                        # Если есть request_id, проверим результат
                        if 'request_id' in result:
                            request_id = result['request_id']
                            print(f"   📝 Request ID: {request_id}")
                            
                            # Проверим статус запроса
                            status_url = f"{base_url}/request/get/{request_id}"
                            async with session.get(status_url, headers=headers, timeout=10) as status_response:
                                if status_response.status == 200:
                                    status_result = await status_response.json()
                                    print(f"   📊 Статус: {status_result.get('status', 'unknown')}")
                                    if status_result.get('result'):
                                        print(f"   💬 Ответ: {status_result['result'][:100]}...")
                    else:
                        print(f"❌ {network_id}: Ошибка {response.status}")
                        
            except Exception as e:
                print(f"❌ {network_id}: Исключение - {e}")

if __name__ == "__main__":
    asyncio.run(test_genapi_models())
