from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class SecurityInfo:
    secid: str
    shortname: str
    name: str
    isin: Optional[str] = None
    regnumber: Optional[str] = None
    type: Optional[str] = None
    group: Optional[str] = None
    primary_boardid: Optional[str] = None
    marketprice_boardid: Optional[str] = None


@dataclass
class ShareSnapshot:
    secid: str
    shortname: str
    last: Optional[float] = None
    change_day_pct: Optional[float] = None
    trading_status: Optional[str] = None
    sector: Optional[str] = None
    currency: Optional[str] = None
    board: Optional[str] = None
    market: Optional[str] = None
    volume: Optional[float] = None


@dataclass
class BondSnapshot:
    secid: str
    shortname: str
    last: Optional[float] = None
    change_day_pct: Optional[float] = None
    trading_status: Optional[str] = None
    ytm: Optional[float] = None
    duration: Optional[float] = None
    aci: Optional[float] = None
    next_coupon_date: Optional[datetime] = None
    maturity_date: Optional[datetime] = None
    coupon_value: Optional[float] = None
    currency: Optional[str] = None
    board: Optional[str] = None
    market: Optional[str] = None
    face_value: Optional[float] = None
    volume: Optional[float] = None


@dataclass
class CouponEvent:
    secid: str
    coupon_date: datetime
    coupon_value: float
    coupon_type: str = "coupon"


@dataclass
class AmortizationEvent:
    secid: str
    amort_date: datetime
    amort_value: float
    amort_type: str = "amortization"


@dataclass
class BondCalendar:
    secid: str
    coupons: List[CouponEvent] = None
    amortizations: List[AmortizationEvent] = None
    
    def __post_init__(self):
        if self.coupons is None:
            self.coupons = []
        if self.amortizations is None:
            self.amortizations = []


@dataclass
class SearchResult:
    secid: str
    shortname: str
    name: str
    isin: Optional[str] = None
    type: Optional[str] = None
    board: Optional[str] = None
    score: float = 0.0


@dataclass
class MarketData:
    secid: str
    last: Optional[float] = None
    change: Optional[float] = None
    change_pct: Optional[float] = None
    trading_status: Optional[str] = None
    currency: Optional[str] = None
    board: Optional[str] = None
    market: Optional[str] = None
    ytm: Optional[float] = None
    duration: Optional[float] = None
    aci: Optional[float] = None
    sector: Optional[str] = None