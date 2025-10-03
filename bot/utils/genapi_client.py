"""
Адаптер для gen-api.ru API
"""
import asyncio
import aiohttp
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class GenAPIResponse:
    request_id: int
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

class GenAPIClient:
    """Клиент для работы с gen-api.ru API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.gen-api.ru/api/v1"
        self.network_id = "chat-gpt-3"  # ID для ChatGPT
        self.timeout = 300  # 5 минут максимум
        self.poll_interval = 2  # Проверяем каждые 2 секунды
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "gpt-4o-mini",
        max_tokens: int = 3000,
        temperature: float = 0.1
    ) -> str:
        """Отправляет запрос на генерацию и ждет результат"""
        
        # Формируем промпт из сообщений
        prompt = self._format_messages(messages)
        
        # Отправляем запрос на генерацию
        request_data = {
            "messages": messages,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with aiohttp.ClientSession() as session:
            # Шаг 1: Отправляем запрос на генерацию
            response = await self._send_generation_request(session, request_data)
            
            if not response:
                raise Exception("Не удалось отправить запрос на генерацию")
            
            # Шаг 2: Ждем завершения обработки
            result = await self._wait_for_completion(session, response.request_id)
            
            if result.error:
                raise Exception(f"Ошибка генерации: {result.error}")
            
            return result.result or ""
    
    async def _send_generation_request(self, session: aiohttp.ClientSession, data: Dict[str, Any]) -> Optional[GenAPIResponse]:
        """Отправляет запрос на генерацию"""
        url = f"{self.base_url}/networks/{self.network_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return GenAPIResponse(
                        request_id=result.get("request_id"),
                        status=result.get("status", "unknown")
                    )
                else:
                    error_text = await response.text()
                    print(f"Ошибка отправки запроса: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"Исключение при отправке запроса: {e}")
            return None
    
    async def _wait_for_completion(self, session: aiohttp.ClientSession, request_id: int) -> GenAPIResponse:
        """Ждет завершения обработки запроса"""
        url = f"{self.base_url}/request/get/{request_id}"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        status = result.get("status", "unknown")
                        
                        if status == "success":
                            return GenAPIResponse(
                                request_id=request_id,
                                status=status,
                                result=result.get("result", "")
                            )
                        elif status == "error":
                            return GenAPIResponse(
                                request_id=request_id,
                                status=status,
                                error=result.get("error", "Неизвестная ошибка")
                            )
                        else:
                            # Статус: starting, processing, etc.
                            print(f"Статус: {status}, ждем...")
                            await asyncio.sleep(self.poll_interval)
                    else:
                        print(f"Ошибка проверки статуса: {response.status}")
                        await asyncio.sleep(self.poll_interval)
            except Exception as e:
                print(f"Исключение при проверке статуса: {e}")
                await asyncio.sleep(self.poll_interval)
        
        # Таймаут
        return GenAPIResponse(
            request_id=request_id,
            status="timeout",
            error=f"Превышен таймаут {self.timeout} секунд"
        )
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """Форматирует сообщения в промпт"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                formatted.append(f"Система: {content}")
            elif role == "user":
                formatted.append(f"Пользователь: {content}")
            elif role == "assistant":
                formatted.append(f"Ассистент: {content}")
        
        return "\n\n".join(formatted)

# Адаптер для совместимости с OpenAI API
class GenAPIOpenAIAdapter:
    """Адаптер для совместимости с OpenAI API"""
    
    def __init__(self, api_key: str):
        self.client = GenAPIClient(api_key)
    
    class ChatCompletions:
        def __init__(self, client: GenAPIClient):
            self.client = client
        
        async def create(self, **kwargs):
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 4000)
            temperature = kwargs.get("temperature", 0.1)
            
            result = await self.client.chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Возвращаем объект, совместимый с OpenAI API
            class MockChoice:
                def __init__(self, content: str):
                    self.message = MockMessage(content)
            
            class MockMessage:
                def __init__(self, content: str):
                    self.content = content
            
            class MockResponse:
                def __init__(self, content: str):
                    self.choices = [MockChoice(content)]
            
            return MockResponse(result)
    
    @property
    def chat(self):
        return type('Chat', (), {
            'completions': self.ChatCompletions(self.client)
        })()
