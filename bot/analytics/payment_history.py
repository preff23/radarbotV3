"""Модуль для анализа истории выплат облигаций.
Отслеживает прошедшие выплаты для выявления отмен, задержек и дефолтов.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from bot.providers.moex_iss.client import MOEXISSClient
from bot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PaymentEvent:
    secid: str
    bond_name: str
    event_type: str
    scheduled_date: datetime
    actual_date: Optional[datetime] = None
    amount: float = 0.0
    status: str = "scheduled"
    delay_days: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class PaymentHistory:
    secid: str
    bond_name: str
    total_events: int = 0
    paid_events: int = 0
    cancelled_events: int = 0
    delayed_events: int = 0
    average_delay_days: float = 0.0
    reliability_score: float = 0.0
    events: List[PaymentEvent] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []


class PaymentHistoryAnalyzer:
    
    def __init__(self):
        self.moex_client = MOEXISSClient()
    
    async def get_payment_history(self, secid: str, months_back: int = 24) -> Optional[PaymentHistory]:
        """Получить историю выплат за последние N месяцев.

        Args:
            secid: Идентификатор облигации
            months_back: Количество месяцев назад для анализа (по умолчанию 24)
        """
        try:
            logger.info(f"Getting payment history for {secid} (last {months_back} months)")
            
            calendar = await self.moex_client.get_bond_calendar(secid, days_ahead=365*2)
            
            if not calendar:
                logger.warning(f"No calendar data found for {secid}")
                return None
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months_back * 30)
            
            all_events = []
            
            for coupon in calendar.coupons:
                if start_date <= coupon.coupon_date <= end_date:
                    event = PaymentEvent(
                        secid=secid,
                        bond_name=calendar.secid,
                        event_type="coupon",
                        scheduled_date=coupon.coupon_date,
                        amount=coupon.coupon_value or 0.0,
                        status="scheduled"
                    )
                    all_events.append(event)
            
            for amort in calendar.amortizations:
                if start_date <= amort.amort_date <= end_date:
                    event = PaymentEvent(
                        secid=secid,
                        bond_name=calendar.secid,
                        event_type="amortization",
                        scheduled_date=amort.amort_date,
                        amount=amort.amort_value or 0.0,
                        status="scheduled"
                    )
                    all_events.append(event)
            
            all_events.sort(key=lambda x: x.scheduled_date)
            
            for event in all_events:
                await self._analyze_event_status(event)
            
            history = PaymentHistory(
                secid=secid,
                bond_name=calendar.secid,
                events=all_events
            )
            
            self._calculate_statistics(history)
            
            logger.info(f"Payment history for {secid}: {len(all_events)} events, "
                       f"reliability: {history.reliability_score:.1f}%")
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get payment history for {secid}: {e}")
            return None
    
    async def _analyze_event_status(self, event: PaymentEvent):
        try:
            
            current_date = datetime.now()
            
            if event.scheduled_date < current_date:
                if event.scheduled_date + timedelta(days=7) < current_date:
                    event.status = "delayed"
                    event.delay_days = (current_date - event.scheduled_date).days
                    event.notes = f"Задержка на {event.delay_days} дней"
                else:
                    event.status = "paid"
            else:
                event.status = "scheduled"
                
        except Exception as e:
            logger.error(f"Failed to analyze event status: {e}")
            event.status = "unknown"
    
    def _calculate_statistics(self, history: PaymentHistory):
        if not history.events:
            history.total_events = 0
            history.paid_events = 0
            history.cancelled_events = 0
            history.delayed_events = 0
            history.average_delay_days = 0.0
            history.reliability_score = 50.0
            return
        
        history.total_events = len(history.events)
        
        paid_count = 0
        cancelled_count = 0
        delayed_count = 0
        total_delay_days = 0
        
        for event in history.events:
            if event.status == "paid":
                paid_count += 1
            elif event.status == "cancelled":
                cancelled_count += 1
            elif event.status == "delayed":
                delayed_count += 1
                if event.delay_days:
                    total_delay_days += event.delay_days
        
        history.paid_events = paid_count
        history.cancelled_events = cancelled_count
        history.delayed_events = delayed_count
        
        if delayed_count > 0:
            history.average_delay_days = total_delay_days / delayed_count
        
        if history.total_events > 0:
            reliability = (paid_count / history.total_events) * 100
            penalty = (cancelled_count * 20) + (delayed_count * 5)
            history.reliability_score = max(0, reliability - penalty)
        else:
            history.reliability_score = 50.0
    
    def get_reliability_assessment(self, history: PaymentHistory) -> str:
        if history.reliability_score >= 95:
            return "🟢 Высокая надежность"
        elif history.reliability_score >= 85:
            return "🟡 Умеренная надежность"
        elif history.reliability_score >= 70:
            return "🟠 Пониженная надежность"
        else:
            return "🔴 Низкая надежность"
    
    def get_risk_signals(self, history: PaymentHistory) -> List[str]:
        signals = []
        
        if history.total_events == 0:
            return signals
        
        if history.cancelled_events > 0:
            signals.append(f"❗ Отменено выплат: {history.cancelled_events}")
        
        if history.delayed_events > 0:
            signals.append(f"⚠️ Задержек выплат: {history.delayed_events}")
        
        if history.average_delay_days > 30:
            signals.append(f"🚨 Средняя задержка: {history.average_delay_days:.0f} дней")
        
        if history.reliability_score < 80:
            signals.append(f"📉 Коэффициент надежности: {history.reliability_score:.1f}%")
        
        return signals


async def analyze_payment_history(secid: str, months_back: int = 24) -> Optional[PaymentHistory]:
    analyzer = PaymentHistoryAnalyzer()
    return await analyzer.get_payment_history(secid, months_back)


if __name__ == "__main__":
    async def test():
        analyzer = PaymentHistoryAnalyzer()
        
        test_secid = "RU000A108C17"
        
        print(f"🧪 Тестирование анализа истории выплат для {test_secid}...")
        
        history = await analyzer.get_payment_history(test_secid, months_back=12)
        
        if history:
            print(f"\n📊 Результаты анализа:")
            print(f"   • Всего событий: {history.total_events}")
            print(f"   • Выплачено: {history.paid_events}")
            print(f"   • Отменено: {history.cancelled_events}")
            print(f"   • Задержек: {history.delayed_events}")
            print(f"   • Средняя задержка: {history.average_delay_days:.1f} дней")
            print(f"   • Коэффициент надежности: {history.reliability_score:.1f}%")
            print(f"   • Оценка: {analyzer.get_reliability_assessment(history)}")
            
            signals = analyzer.get_risk_signals(history)
            if signals:
                print(f"\n⚠️ Сигналы риска:")
                for signal in signals:
                    print(f"   • {signal}")
            
            print(f"\n📅 Детали событий:")
            for event in history.events[:5]:
                date_str = event.scheduled_date.strftime("%d.%m.%Y")
                print(f"   • {date_str} - {event.event_type} - {event.amount}₽ - {event.status}")
        else:
            print("❌ Не удалось получить историю выплат")
    
    asyncio.run(test())