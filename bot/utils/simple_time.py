"""Simple Time API client for getting real-time data.
Uses system time with proper timezone handling.
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SimpleTimeClient:
    
    def __init__(self):
        self.moscow_offset = timedelta(hours=3)
    
    def get_current_time(self) -> Dict[str, Any]:
        utc_now = datetime.now(timezone.utc)
        
        moscow_time = utc_now + self.moscow_offset
        
        return {
            "datetime": moscow_time,
            "date": moscow_time.strftime("%Y-%m-%d"),
            "time": moscow_time.strftime("%H:%M:%S"),
            "timezone": "Europe/Moscow",
            "source": "System",
            "timestamp": moscow_time.timestamp(),
            "utc_datetime": utc_now,
            "utc_timestamp": utc_now.timestamp()
        }
    
    def get_formatted_time(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        time_data = self.get_current_time()
        return time_data["datetime"].strftime(format_str)
    
    def get_time_for_chatgpt(self) -> str:
        time_data = self.get_current_time()
        return f"Текущее время: {time_data['date']} {time_data['time']} ({time_data['timezone']})"
    
    def get_time_context(self) -> str:
        time_data = self.get_current_time()
        
        day_names = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        day_name = day_names[time_data["datetime"].weekday()]
        
        month_names = ["января", "февраля", "марта", "апреля", "мая", "июня",
                      "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        month_name = month_names[time_data["datetime"].month - 1]
        
        return f"""Текущая дата и время: {time_data['datetime'].day} {month_name} {time_data['datetime'].year} года, {day_name}, {time_data['time']} по московскому времени (UTC+3).
Временная зона: {time_data['timezone']}
Unix timestamp: {int(time_data['timestamp'])}"""


time_client = SimpleTimeClient()


def get_current_time() -> Dict[str, Any]:
    return time_client.get_current_time()


def get_formatted_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    return time_client.get_formatted_time(format_str)


def get_time_for_chatgpt() -> str:
    return time_client.get_time_for_chatgpt()


def get_time_context() -> str:
    return time_client.get_time_context()


def test_time_client():
    print("Testing Simple Time Client...")
    
    time_data = time_client.get_current_time()
    
    print(f"✅ Success: {time_data['source']}")
    print(f"   Date: {time_data['date']}")
    print(f"   Time: {time_data['time']}")
    print(f"   Timezone: {time_data['timezone']}")
    print(f"   Timestamp: {time_data['timestamp']}")
    
    chatgpt_time = time_client.get_time_for_chatgpt()
    print(f"📝 ChatGPT format: {chatgpt_time}")
    
    context = time_client.get_time_context()
    print(f"📋 Detailed context:")
    print(f"   {context}")


if __name__ == "__main__":
    test_time_client()