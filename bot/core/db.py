import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.sqlite import JSON
from bot.core.config import config

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(32), unique=True, nullable=False)
    country_code = Column(String(8), nullable=True)
    telegram_id = Column(Integer, unique=True, nullable=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    holdings = relationship("PortfolioHoldingV2", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("PortfolioAccount", back_populates="user", cascade="all, delete-orphan")
    cash_positions = relationship("PortfolioCashPosition", back_populates="user", cascade="all, delete-orphan")


class PortfolioAccount(Base):
    __tablename__ = "portfolio_accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(String(128), nullable=False)
    account_name = Column(String(255), nullable=True)
    portfolio_value = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint('user_id', 'account_id', name='uq_user_account'),)

    user = relationship("User", back_populates="accounts")
    holdings = relationship("PortfolioHoldingV2", back_populates="account", cascade="all, delete-orphan")
    cash_positions = relationship("PortfolioCashPosition", back_populates="account", cascade="all, delete-orphan")


class PortfolioHoldingV2(Base):
    __tablename__ = "portfolio_holdings_v2"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_internal_id = Column(Integer, ForeignKey("portfolio_accounts.id"), nullable=True)
    
    raw_name = Column(String(500), nullable=False)
    raw_ticker = Column(String(50), nullable=True)
    raw_isin = Column(String(50), nullable=True)
    raw_type = Column(String(50), nullable=True)
    raw_quantity = Column(Float, nullable=True)
    raw_quantity_unit = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    
    normalized_name = Column(String(500), nullable=False)
    normalized_key = Column(String(500), nullable=False)
    
    secid = Column(String(50), nullable=True)
    ticker = Column(String(50), nullable=True)
    isin = Column(String(50), nullable=True)
    security_type = Column(String(50), nullable=True)
    
    provider = Column(String(50), nullable=True)
    provider_data = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="holdings")
    account = relationship("PortfolioAccount", back_populates="holdings")


class PortfolioCashPosition(Base):
    __tablename__ = "portfolio_cash_positions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_internal_id = Column(Integer, ForeignKey("portfolio_accounts.id"), nullable=True)
    raw_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=True)
    currency = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cash_positions")
    account = relationship("PortfolioAccount", back_populates="cash_positions")


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    
    id = Column(Integer, primary_key=True)
    secid = Column(String(50), nullable=False)
    ticker = Column(String(50), nullable=True)
    isin = Column(String(50), nullable=True)
    
    last_price = Column(Float, nullable=True)
    change_day_pct = Column(Float, nullable=True)
    trading_status = Column(String(50), nullable=True)
    currency = Column(String(10), nullable=True)
    
    ytm = Column(Float, nullable=True)
    duration = Column(Float, nullable=True)
    aci = Column(Float, nullable=True)
    next_coupon_date = Column(DateTime, nullable=True)
    maturity_date = Column(DateTime, nullable=True)
    coupon_value = Column(Float, nullable=True)
    
    sector = Column(String(100), nullable=True)
    
    provider = Column(String(50), nullable=False)
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


class NewsItem(Base):
    __tablename__ = "news_items"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=False)
    source = Column(String(100), nullable=False)
    
    related_secids = Column(JSON, nullable=True)
    related_tickers = Column(JSON, nullable=True)
    
    cached_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)


engine = create_engine(config.database_url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        pass


class DatabaseManager:
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        self._portfolio_meta_cache: Dict[int, Dict[str, Any]] = {}

    @staticmethod
    def normalize_phone(phone_number: str) -> Optional[str]:
        if not phone_number:
            return None
        digits = ''.join(ch for ch in str(phone_number) if ch.isdigit())
        if not digits:
            return None
        if digits.startswith("00"):
            digits = digits[2:]
        if not digits.startswith("+"):
            digits = "+" + digits
        return digits
 
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        db = self.SessionLocal()
        try:
            normalized = self.normalize_phone(phone_number)
            if not normalized:
                return None
            return db.query(User).filter(User.phone_number == normalized).first()
        finally:
            db.close()

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        if telegram_id in (None, 0):
            return None
        db = self.SessionLocal()
        try:
            return db.query(User).filter(User.telegram_id == telegram_id).first()
        finally:
            db.close()

    def create_user(self, phone_number: str, country_code: str = None,
                   telegram_id: int = None, username: str = None,
                   first_name: str = None, last_name: str = None) -> User:
        db = self.SessionLocal()
        try:
            normalized = self.normalize_phone(phone_number)
            if not normalized:
                raise ValueError("Invalid phone number")

            user = db.query(User).filter(User.phone_number == normalized).first()
            if user:
                if telegram_id and user.telegram_id != telegram_id:
                    user.telegram_id = telegram_id
                if username is not None:
                    user.username = username
                if first_name is not None:
                    user.first_name = first_name
                if last_name is not None:
                    user.last_name = last_name
                if country_code is not None:
                    user.country_code = country_code
                user.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(user)
                return user

            user = User(
                phone_number=normalized,
                country_code=country_code,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        finally:
            db.close()

    def update_user(self, user_id: int, **fields) -> Optional[User]:
        if not fields:
            return None
        db = self.SessionLocal()
        try:
            update_data = {}
            for key, value in fields.items():
                if value is None:
                    continue
                if key == "phone_number":
                    normalized = self.normalize_phone(value)
                    if not normalized:
                        continue
                    update_data[key] = normalized
                else:
                    update_data[key] = value
            if not update_data:
                return None
            db.query(User).filter(User.id == user_id).update(update_data)
            db.commit()
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()

    def ensure_user(self, phone_number: str, **kwargs) -> User:
        user = self.get_user_by_phone(phone_number)
        if user:
            if kwargs:
                update_fields = {}
                for key, value in kwargs.items():
                    if value is not None and getattr(user, key, None) != value:
                        update_fields[key] = value
                if update_fields:
                    return self.update_user(user.id, **update_fields) or user
            return user
        return self.create_user(phone_number=phone_number, **kwargs)
 
    def get_user_holdings(self, user_id: int, active_only: bool = True) -> List[PortfolioHoldingV2]:
        db = self.SessionLocal()
        try:
            query = db.query(PortfolioHoldingV2).filter(PortfolioHoldingV2.user_id == user_id)
            if active_only:
                query = query.filter(PortfolioHoldingV2.is_active == True)
            return query.all()
        finally:
            db.close()
    
    def add_holding(self, user_id: int, raw_name: str, normalized_name: str,
                    normalized_key: str, account_internal_id: Optional[int] = None,
                    session: Session = None, **kwargs) -> PortfolioHoldingV2:
        db = session or self.SessionLocal()
        own_session = session is None
        try:
            query = db.query(PortfolioHoldingV2).filter(
                PortfolioHoldingV2.user_id == user_id,
                PortfolioHoldingV2.normalized_key == normalized_key,
                PortfolioHoldingV2.is_active == True
            )

            if account_internal_id is not None:
                query = query.filter(PortfolioHoldingV2.account_internal_id == account_internal_id)
            else:
                query = query.filter(PortfolioHoldingV2.account_internal_id.is_(None))

            existing = query.first()

            if existing:
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                if account_internal_id is not None and existing.account_internal_id != account_internal_id:
                    existing.account_internal_id = account_internal_id
                existing.updated_at = datetime.utcnow()

                if own_session:
                    db.commit()
                    db.refresh(existing)
                else:
                    db.flush()
                    db.refresh(existing)
                return existing

            holding = PortfolioHoldingV2(
                user_id=user_id,
                account_internal_id=account_internal_id,
                raw_name=raw_name,
                normalized_name=normalized_name,
                normalized_key=normalized_key,
                **kwargs
            )
            db.add(holding)

            if own_session:
                db.commit()
                db.refresh(holding)
            else:
                db.flush()
                db.refresh(holding)
            return holding
        finally:
            if own_session:
                db.close()
    
    def clear_user_holdings(self, user_id: int, session: Session = None) -> int:
        db = session or self.SessionLocal()
        own_session = session is None
        try:
            count = db.query(PortfolioHoldingV2).filter(
                PortfolioHoldingV2.user_id == user_id
            ).update({"is_active": False})
            if own_session:
                db.commit()
            return count
        finally:
            if own_session:
                db.close()

    # -------- Portfolio meta (in-memory cache) --------
    def set_portfolio_meta(self, user_id: int, meta: Dict[str, Any]) -> None:
        safe_meta = {
            "portfolio_name": meta.get("portfolio_name"),
            "portfolio_value": meta.get("portfolio_value"),
            "currency": meta.get("currency"),
            "positions_count": meta.get("positions_count"),
            "updated_at": datetime.utcnow().isoformat()
        }
        self._portfolio_meta_cache[user_id] = safe_meta

    def get_portfolio_meta(self, user_id: int) -> Dict[str, Any]:
        return self._portfolio_meta_cache.get(user_id, {})

    def clear_portfolio_meta(self, user_id: int) -> None:
        if user_id in self._portfolio_meta_cache:
            self._portfolio_meta_cache.pop(user_id, None)

    def deactivate_missing_holdings(self, user_id: int, account_internal_id: Optional[int], active_ids: Set[int], session: Session) -> int:
        query = session.query(PortfolioHoldingV2).filter(
            PortfolioHoldingV2.user_id == user_id,
            PortfolioHoldingV2.is_active == True
        )
        if account_internal_id is not None:
            query = query.filter(PortfolioHoldingV2.account_internal_id == account_internal_id)
        else:
            query = query.filter(PortfolioHoldingV2.account_internal_id.is_(None))

        if active_ids:
            query = query.filter(~PortfolioHoldingV2.id.in_(active_ids))

        count = query.update({"is_active": False}, synchronize_session=False)
        return count

    def delete_account_holdings(self, user_id: int, account_internal_id: Optional[int], session: Session) -> int:
        query = session.query(PortfolioHoldingV2).filter(
            PortfolioHoldingV2.user_id == user_id
        )
        if account_internal_id is not None:
            query = query.filter(PortfolioHoldingV2.account_internal_id == account_internal_id)
        else:
            query = query.filter(PortfolioHoldingV2.account_internal_id.is_(None))
        count = query.delete(synchronize_session=False)
        return count

    def delete_account_cash(self, user_id: int, account_internal_id: Optional[int], session: Session) -> int:
        query = session.query(PortfolioCashPosition).filter(
            PortfolioCashPosition.user_id == user_id
        )
        if account_internal_id is not None:
            query = query.filter(PortfolioCashPosition.account_internal_id == account_internal_id)
        else:
            query = query.filter(PortfolioCashPosition.account_internal_id.is_(None))
        count = query.delete(synchronize_session=False)
        return count

    def get_or_create_account(self, user_id: int, account_id: str, session: Session,
                              account_name: Optional[str] = None,
                              currency: Optional[str] = None,
                              portfolio_value: Optional[float] = None) -> PortfolioAccount:
        account = session.query(PortfolioAccount).filter(
            PortfolioAccount.user_id == user_id,
            PortfolioAccount.account_id == account_id
        ).first()

        if account:
            updated = False
            if account_name is not None and account.account_name != account_name:
                account.account_name = account_name
                updated = True
            if currency is not None and account.currency != currency:
                account.currency = currency
                updated = True
            if portfolio_value is not None and account.portfolio_value != portfolio_value:
                account.portfolio_value = portfolio_value
                updated = True
            if updated:
                account.updated_at = datetime.utcnow()
                session.flush()
            return account

        account = PortfolioAccount(
            user_id=user_id,
            account_id=account_id,
            account_name=account_name,
            currency=currency,
            portfolio_value=portfolio_value
        )
        session.add(account)
        session.flush()
        return account

    def get_user_accounts(self, user_id: int) -> List[PortfolioAccount]:
        db = self.SessionLocal()
        try:
            return db.query(PortfolioAccount).filter(PortfolioAccount.user_id == user_id).all()
        finally:
            db.close()

    def get_account_cash(self, user_id: int, account_internal_id: Optional[int]) -> List[PortfolioCashPosition]:
        db = self.SessionLocal()
        try:
            query = db.query(PortfolioCashPosition).filter(PortfolioCashPosition.user_id == user_id)
            if account_internal_id is not None:
                query = query.filter(PortfolioCashPosition.account_internal_id == account_internal_id)
            else:
                query = query.filter(PortfolioCashPosition.account_internal_id.is_(None))
            return query.all()
        finally:
            db.close()

    def get_user_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        db = self.SessionLocal()
        try:
            accounts = db.query(PortfolioAccount).filter(PortfolioAccount.user_id == user_id).all()
            holdings = db.query(PortfolioHoldingV2).filter(
                PortfolioHoldingV2.user_id == user_id,
                PortfolioHoldingV2.is_active == True
            ).all()
            cash_positions = db.query(PortfolioCashPosition).filter(
                PortfolioCashPosition.user_id == user_id
            ).all()

            def serialize_account(acc: PortfolioAccount) -> Dict[str, Any]:
                return {
                    "internal_id": acc.id,
                    "account_id": acc.account_id,
                    "account_name": acc.account_name,
                    "currency": acc.currency,
                    "portfolio_value": acc.portfolio_value,
                    "created_at": acc.created_at.isoformat() if acc.created_at else None,
                    "updated_at": acc.updated_at.isoformat() if acc.updated_at else None,
                }

            def serialize_holding(h: PortfolioHoldingV2) -> Dict[str, Any]:
                provider_data = h.provider_data or {}
                return {
                    "id": h.id,
                    "account_internal_id": h.account_internal_id,
                    "raw_name": h.raw_name,
                    "normalized_name": h.normalized_name,
                    "ticker": h.ticker,
                    "isin": h.isin,
                    "security_type": h.security_type,
                    "quantity": h.raw_quantity,
                    "quantity_unit": h.raw_quantity_unit,
                    "provider": h.provider,
                    "provider_data": provider_data,
                    "fallback": bool(provider_data.get("fallback")),
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                    "updated_at": h.updated_at.isoformat() if h.updated_at else None,
                }

            def serialize_cash(c: PortfolioCashPosition) -> Dict[str, Any]:
                return {
                    "id": c.id,
                    "account_internal_id": c.account_internal_id,
                    "raw_name": c.raw_name,
                    "amount": c.amount,
                    "currency": c.currency,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                }

            return {
                "accounts": [serialize_account(acc) for acc in accounts],
                "holdings": [serialize_holding(h) for h in holdings],
                "cash_positions": [serialize_cash(c) for c in cash_positions],
            }
        finally:
            db.close()


db_manager = DatabaseManager()