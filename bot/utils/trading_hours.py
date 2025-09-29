"""Модуль для определения торговых часов и актуальности данных."""

from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from enum import Enum

class TradingStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"

class TradingHoursManager:
    
    def __init__(self):
        self.moex_start = (10, 0)
        self.moex_end = (18, 45)
        
        self.tbank_start = (10, 0)
        self.tbank_end = (18, 45)
    
    def get_moscow_time(self) -> datetime:
        utc_now = datetime.now(timezone.utc)
        moscow_tz = timezone(timedelta(hours=3))
        return utc_now.astimezone(moscow_tz)
    
    def is_trading_hours(self, provider: str = "moex") -> Tuple[bool, TradingStatus]:
        """Проверить, открыты ли торги.

        Args:
            provider: Провайдер данных ("moex" или "tbank")

        Returns:
            Tuple[bool, TradingStatus]: (открыты ли торги, статус торгов)
        """
        moscow_time = self.get_moscow_time()
        current_time = moscow_time.time()
        
        if provider.lower() == "moex":
            start_hour, start_minute = self.moex_start
            end_hour, end_minute = self.moex_end
        else:
            start_hour, start_minute = self.tbank_start
            end_hour, end_minute = self.tbank_end
        
        trading_start = datetime.strptime(f"{start_hour:02d}:{start_minute:02d}", "%H:%M").time()
        trading_end = datetime.strptime(f"{end_hour:02d}:{end_minute:02d}", "%H:%M").time()
        
        weekday = moscow_time.weekday()
        is_weekend = weekday >= 5
        
        if is_weekend:
            return False, TradingStatus.CLOSED
        
        if trading_start <= current_time <= trading_end:
            return True, TradingStatus.OPEN
        elif current_time < trading_start:
            return False, TradingStatus.PRE_MARKET
        else:
            return False, TradingStatus.AFTER_HOURS
    
    def get_trading_status_info(self, provider: str = "moex") -> dict:
        """Получить подробную информацию о статусе торгов.

        Args:
            provider: Провайдер данных

        Returns:
            dict: Информация о статусе торгов
        """
        moscow_time = self.get_moscow_time()
        is_open, status = self.is_trading_hours(provider)
        
        info = {
            "is_trading_open": is_open,
            "status": status,
            "current_time_moscow": moscow_time,
            "provider": provider
        }
        
        if provider.lower() == "moex":
            info["trading_hours"] = "10:00 - 18:45 МСК"
            info["next_open"] = self._get_next_trading_open(moscow_time)
            info["last_close"] = self._get_last_trading_close(moscow_time)
        else:
            info["trading_hours"] = "10:00 - 18:45 МСК"
            info["next_open"] = self._get_next_trading_open(moscow_time)
            info["last_close"] = self._get_last_trading_close(moscow_time)
        
        return info
    
    def _get_next_trading_open(self, moscow_time: datetime) -> Optional[datetime]:
        current_date = moscow_time.date()
        
        for days_ahead in range(1, 8):
            next_date = current_date + timedelta(days=days_ahead)
            if next_date.weekday() < 5:
                next_open = datetime.combine(next_date, datetime.strptime("10:00", "%H:%M").time())
                return next_open.replace(tzinfo=moscow_time.tzinfo)
        
        return None
    
    def _get_last_trading_close(self, moscow_time: datetime) -> Optional[datetime]:
        current_date = moscow_time.date()
        
        if moscow_time.weekday() < 5:
            today_close = datetime.combine(current_date, datetime.strptime("18:45", "%H:%M").time())
            today_close = today_close.replace(tzinfo=moscow_time.tzinfo)
            
            if moscow_time.time() > datetime.strptime("18:45", "%H:%M").time():
                return today_close
        
        for days_back in range(1, 8):
            prev_date = current_date - timedelta(days=days_back)
            if prev_date.weekday() < 5:
                last_close = datetime.combine(prev_date, datetime.strptime("18:45", "%H:%M").time())
                return last_close.replace(tzinfo=moscow_time.tzinfo)
        
        return None

trading_hours_manager = TradingHoursManager()

def get_trading_status(provider: str = "moex") -> dict:
    return trading_hours_manager.get_trading_status_info(provider)

def is_trading_open(provider: str = "moex") -> bool:
    is_open, _ = trading_hours_manager.is_trading_hours(provider)
    return is_open

if __name__ == "__main__":
    print("🕐 ТЕСТ ТОРГОВЫХ ЧАСОВ")
    print("=" * 40)
    
    moex_status = get_trading_status("moex")
    print(f"🏛️ MOEX:")
    print(f"   Торги открыты: {moex_status['is_trading_open']}")
    print(f"   Статус: {moex_status['status'].value}")
    print(f"   Время в Москве: {moex_status['current_time_moscow']}")
    print(f"   Торговые часы: {moex_status['trading_hours']}")
    
    if moex_status['next_open']:
        print(f"   Следующее открытие: {moex_status['next_open']}")
    if moex_status['last_close']:
        print(f"   Последнее закрытие: {moex_status['last_close']}")
    
    print()
    
    tbank_status = get_trading_status("tbank")
    print(f"🏦 T-Bank:")
    print(f"   Торги открыты: {tbank_status['is_trading_open']}")
    print(f"   Статус: {tbank_status['status'].value}")
    print(f"   Время в Москве: {tbank_status['current_time_moscow']}")
    print(f"   Торговые часы: {tbank_status['trading_hours']}")