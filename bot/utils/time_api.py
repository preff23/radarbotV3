"""Client for retrieving current time from various APIs with fallbacks."""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TimeAPIClient:
    
    def __init__(self):
        self.session = None
        self.apis = [
            {
                "name": "WorldTimeAPI",
                "url": "https://worldtimeapi.org/api/timezone/Europe/Moscow",
                "free": True,
                "rate_limit": "1000/day"
            },
            {
                "name": "TimeAPI.io",
                "url": "https://timeapi.io/api/Time/current/zone?timeZone=Europe/Moscow",
                "free": True,
                "rate_limit": "1000/day"
            },
            {
                "name": "HTTPBin",
                "url": "https://httpbin.org/json",
                "free": True,
                "rate_limit": "unlimited",
                "test_only": True
            }
        ]
    
    async def __aenter__(self):
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_current_time(self) -> Optional[Dict[str, Any]]:
        
        for api in self.apis:
            try:
                logger.info(f"Trying {api['name']} API...")
                
                async with self.session.get(api["url"], timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        parsed_time = self._parse_time_data(api["name"], data)
                        if parsed_time:
                            logger.info(f"Successfully got time from {api['name']}")
                            return parsed_time
                    else:
                        logger.warning(f"{api['name']} returned status {response.status}")
                        
            except Exception as e:
                logger.warning(f"Failed to get time from {api['name']}: {e}")
                continue
        
        logger.warning("All APIs failed, using system time")
        return self._get_system_time()
    
    def _parse_time_data(self, api_name: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        
        try:
            if api_name == "WorldTimeAPI":
                datetime_str = data.get("datetime")
                if datetime_str:
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    return {
                        "datetime": dt,
                        "date": dt.strftime("%Y-%m-%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "timezone": "Europe/Moscow",
                        "source": "WorldTimeAPI",
                        "timestamp": dt.timestamp()
                    }
            
            elif api_name == "Aimylogic":
                time_str = data.get("time", "")
                if time_str:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    dt = dt.replace(tzinfo=timezone.utc)
                    return {
                        "datetime": dt,
                        "date": dt.strftime("%Y-%m-%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "timezone": "Europe/Moscow",
                        "source": "Aimylogic",
                        "timestamp": dt.timestamp()
                    }
            
            elif api_name == "TimeAPI.io":
                datetime_str = data.get("dateTime")
                if datetime_str:
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                    return {
                        "datetime": dt,
                        "date": dt.strftime("%Y-%m-%d"),
                        "time": dt.strftime("%H:%M:%S"),
                        "timezone": "Europe/Moscow",
                        "source": "TimeAPI.io",
                        "timestamp": dt.timestamp()
                    }
        
        except Exception as e:
            logger.error(f"Failed to parse time data from {api_name}: {e}")
            return None
        
        return None
    
    def _get_system_time(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "datetime": now,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timezone": "UTC",
            "source": "System",
            "timestamp": now.timestamp()
        }
    
    async def get_formatted_time(self, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        time_data = await self.get_current_time()
        if time_data:
            return time_data["datetime"].strftime(format_str)
        return datetime.now().strftime(format_str)
    
    async def get_time_for_chatgpt(self) -> str:
        time_data = await self.get_current_time()
        if time_data:
            return f"Текущее время: {time_data['date']} {time_data['time']} ({time_data['timezone']})"
        return f"Текущее время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)"


time_client = TimeAPIClient()


async def get_current_time() -> Optional[Dict[str, Any]]:
    async with time_client as client:
        return await client.get_current_time()


async def get_formatted_time(format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    async with time_client as client:
        return await client.get_formatted_time(format_str)


async def get_time_for_chatgpt() -> str:
    async with time_client as client:
        return await client.get_time_for_chatgpt()


async def test_time_apis():
    print("Testing Time APIs...")
    
    async with time_client as client:
        time_data = await client.get_current_time()
        
        if time_data:
            print(f"✅ Success: {time_data['source']}")
            print(f"   Date: {time_data['date']}")
            print(f"   Time: {time_data['time']}")
            print(f"   Timezone: {time_data['timezone']}")
            print(f"   Timestamp: {time_data['timestamp']}")
        else:
            print("❌ Failed to get time from any API")
        
        chatgpt_time = await client.get_time_for_chatgpt()
        print(f"📝 ChatGPT format: {chatgpt_time}")


if __name__ == "__main__":
    asyncio.run(test_time_apis())