import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from bot.core.db import (
    db_manager,
    PortfolioHoldingV2,
    PortfolioAccount,
    PortfolioCashPosition,
)
from bot.utils.normalize import normalize_security_name, generate_normalized_key, normalize_security_type
from bot.providers.aggregator import market_aggregator, MarketSnapshot
from bot.utils.bond_reference import load_bond_reference
from bot.core.logging import get_logger

logger = get_logger(__name__)


class UserContext(BaseModel):
    id: int
    phone_number: str
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    username: Optional[str] = None


class TelegramInitData(BaseModel):
    telegram_id: Optional[int] = None
    phone_number: Optional[str] = None


class PortfolioPositionResponse(BaseModel):
    id: int
    account_internal_id: Optional[int]
    name: str
    ticker: Optional[str]
    isin: Optional[str]
    security_type: Optional[str]
    quantity: Optional[float]
    quantity_unit: Optional[str]
    provider: Optional[str]
    provider_data: Dict[str, Any] = Field(default_factory=dict)
    fallback: bool = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class CashPositionResponse(BaseModel):
    id: int
    account_internal_id: Optional[int]
    raw_name: str
    amount: Optional[float]
    currency: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class AccountResponse(BaseModel):
    internal_id: Optional[int]
    account_id: str
    account_name: Optional[str]
    currency: Optional[str]
    portfolio_value: Optional[float]
    positions: List[PortfolioPositionResponse]
    cash: List[CashPositionResponse]


class UserInfo(BaseModel):
    phone: Optional[str]
    telegram_id: Optional[int]
    username: Optional[str]


class PortfolioResponse(BaseModel):
    user: UserInfo
    accounts: List[AccountResponse]


class SearchResult(BaseModel):
    name: Optional[str]
    ticker: Optional[str]
    isin: Optional[str]
    description: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]


class UpdatePositionRequest(BaseModel):
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    security_type: Optional[str] = None


class CreatePositionRequest(BaseModel):
    account_id: str
    account_name: Optional[str] = None
    currency: Optional[str] = None
    name: Optional[str] = None
    ticker: Optional[str] = None
    isin: Optional[str] = None
    security_type: Optional[str] = None
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None


app = FastAPI(title="Radar MiniApp Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def get_current_user(
    request: Request,
    telegram_id: Optional[int] = Header(None, alias="X-Telegram-Id"),
    phone_number: Optional[str] = Header(None, alias="X-User-Phone")
) -> UserContext:
    user = None
    # Fallback: allow tg_id and phone query parameters when headers are stripped by a proxy (e.g., Vercel rewrites)
    tg_q = request.query_params.get("tg_id")
    phone_q = request.query_params.get("phone")
    
    try:
        if telegram_id in (None, 0) and tg_q and tg_q.isdigit():
            telegram_id = int(tg_q)
    except Exception:
        pass
    
    # Use phone from query params if header is not available
    if not phone_number and phone_q:
        phone_number = phone_q
    
    # Handle special case for offline_test user
    if tg_q == 'offline_test':
        user = db_manager.get_user_by_username('offline_test')
        if user:
            print(f'Found offline_test user: ID={user.id}, phone={user.phone_number}')
    elif phone_number:
        # Priority 1: Search by phone number (most reliable for multi-user)
        user = db_manager.get_user_by_phone(phone_number)
        print(f'Searching by phone: {phone_number}')
    elif telegram_id:
        # Priority 2: Search by telegram_id (fallback)
        user = db_manager.get_user_by_telegram_id(telegram_id)
        print(f'Searching by telegram_id: {telegram_id}')
    
    if not user:
        raise HTTPException(status_code=401, detail="User is not authorized")
    if not getattr(user, "phone_number", None):
        raise HTTPException(status_code=403, detail="Phone number required")
    
    print(f'Found user: ID={user.id}, phone={user.phone_number}, telegram_id={user.telegram_id}')
    return UserContext(
        id=user.id,
        phone_number=user.phone_number,
        phone=user.phone_number,
        telegram_id=user.telegram_id,
        username=user.username
    )


def build_portfolio_response(user_id: int, phone: Optional[str] = None, telegram_id: Optional[int] = None, username: Optional[str] = None) -> PortfolioResponse:
    summary = db_manager.get_user_portfolio_summary(user_id)

    # Создаем только один manual аккаунт
    manual_account = AccountResponse(
            internal_id=None,
        account_id="manual",
            account_name="Портфель",
        currency="RUB",
        portfolio_value=0.0,
            positions=[],
            cash=[]
        )

    # Добавляем все позиции в manual аккаунт
    for holding in summary["holdings"]:
        name = holding.get("normalized_name") or holding.get("raw_name")
        provider_data = holding.get("provider_data") or {}
        position_resp = PortfolioPositionResponse(
            id=holding["id"],
            account_internal_id=None,  # Все позиции в manual аккаунте
            name=name,
            ticker=holding.get("ticker"),
            isin=holding.get("isin"),
            security_type=holding.get("security_type"),
            quantity=holding.get("quantity"),
            quantity_unit=holding.get("quantity_unit"),
            provider=holding.get("provider"),
            provider_data=provider_data,
            fallback=bool(provider_data.get("fallback")),
            created_at=holding.get("created_at"),
            updated_at=holding.get("updated_at"),
        )
        manual_account.positions.append(position_resp)

    # Добавляем все денежные средства в manual аккаунт
    for cash in summary["cash_positions"]:
        cash_resp = CashPositionResponse(
            id=cash["id"],
            account_internal_id=None,  # Все денежные средства в manual аккаунте
            raw_name=cash.get("raw_name"),
            amount=cash.get("amount"),
            currency=cash.get("currency"),
            created_at=cash.get("created_at"),
            updated_at=cash.get("updated_at"),
        )
        manual_account.cash.append(cash_resp)

    # Вычисляем общую стоимость портфеля
    total_value = sum(acc.get("portfolio_value", 0) or 0 for acc in summary["accounts"])
    manual_account.portfolio_value = total_value

    user_info = UserInfo(phone=phone, telegram_id=telegram_id, username=username)
    return PortfolioResponse(user=user_info, accounts=[manual_account])


@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio(user: UserContext = Depends(get_current_user)) -> PortfolioResponse:
    return build_portfolio_response(user.id, user.phone, user.telegram_id, user.username)


def build_search_result(snapshot: MarketSnapshot) -> SearchResult:
    description_parts = []
    if snapshot.security_type:
        description_parts.append(snapshot.security_type)
    if snapshot.currency:
        description_parts.append(snapshot.currency)
    if snapshot.provider:
        description_parts.append(f"{snapshot.provider.upper()}")
    description = " · ".join(description_parts) if description_parts else None
    return SearchResult(
        name=snapshot.name or snapshot.secid,
        ticker=snapshot.ticker,
        isin=snapshot.isin,
        description=description,
    )


@app.get("/api/portfolio/search", response_model=SearchResponse)
async def search_securities(
    query: str,
    user: UserContext = Depends(get_current_user)
) -> SearchResponse:
    if not query or len(query.strip()) < 2:
        raise HTTPException(status_code=400, detail="Query too short")

    normalized_query = query.strip()

    snapshots: List[MarketSnapshot] = []
    try:
        snapshots = await market_aggregator.get_snapshot_for(normalized_query)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    results: List[SearchResult] = []
    seen_pairs = set()
    for snapshot in snapshots:
        if not snapshot:
            continue
        key = (snapshot.isin or "", snapshot.ticker or "", snapshot.secid or "")
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        results.append(build_search_result(snapshot))

    # Allow direct ISIN lookup via local bond reference if market data providers miss it
    compact_query = re.sub(r"[^A-Za-z0-9]", "", normalized_query).upper()
    if len(compact_query) == 12 and compact_query.isalnum():
        existing_isins = {res.isin.upper() for res in results if res.isin}
        if compact_query not in existing_isins:
            bond_reference = load_bond_reference()
            if bond_reference:
                entry = bond_reference.match(isin=compact_query, ticker=None, name=None)
                if entry:
                    results.append(
                        SearchResult(
                            name=entry.name or entry.full_name or entry.isin,
                            ticker=entry.ticker,
                            isin=entry.isin,
                            description="Справочник облигаций",
                        )
                    )

    return SearchResponse(results=results)


@app.get("/api/portfolio/security/{isin}/details")
async def get_security_details(
    isin: str,
    user: UserContext = Depends(get_current_user)
):
    """Get detailed information about a security by ISIN."""
    try:
        # Get market data for the security
        snapshots = await market_aggregator.get_snapshot_for(isin)
        
        if not snapshots:
            raise HTTPException(status_code=404, detail="Security not found")
        
        snapshot = snapshots[0]  # Get the first (most relevant) snapshot
        
        # Log the snapshot data for debugging
        logger.info(f"Security details for {isin}: duration={snapshot.duration}, face_value={snapshot.face_value}, provider={snapshot.provider}")
        
        # Build detailed response
        details = {
            "isin": snapshot.isin,
            "ticker": snapshot.ticker,
            "name": snapshot.name,
            "shortname": snapshot.shortname,
            "security_type": snapshot.security_type,
            "provider": snapshot.provider,
            
            # Price information
            "price": {
                "last": snapshot.last_price,
                "change_day_pct": snapshot.change_day_pct,
                "currency": snapshot.currency,
                "trading_status": snapshot.trading_status
            },
            
            # Bond-specific information
            "bond_info": {
                "ytm": snapshot.ytm,
                "duration": snapshot.duration,
                "aci": snapshot.aci,
                "face_value": snapshot.face_value,
                "coupon_value": snapshot.coupon_value,
                "coupon_rate": snapshot.coupon_rate,
                "coupon_frequency": snapshot.coupon_frequency,
                "next_coupon_date": snapshot.next_coupon_date.isoformat() if snapshot.next_coupon_date else None,
                "maturity_date": snapshot.maturity_date.isoformat() if snapshot.maturity_date else None,
                "issue_date": snapshot.issue_date.isoformat() if snapshot.issue_date else None,
                "issue_size": snapshot.issue_size
            } if snapshot.security_type == "bond" else None,
            
            # Share-specific information
            "share_info": {
                "sector": snapshot.sector,
                "next_dividend_date": snapshot.next_dividend_date.isoformat() if snapshot.next_dividend_date else None,
                "dividend_value": snapshot.dividend_value
            } if snapshot.security_type == "share" else None,
            
            # Rating information
            "rating": {
                "rating": snapshot.rating,
                "rating_agency": snapshot.rating_agency
            } if snapshot.rating else None,
            
            # Trading information
            "trading": {
                "volume": snapshot.volume,
                "board": snapshot.board,
                "is_trading_open": snapshot.is_trading_open,
                "data_freshness": snapshot.data_freshness
            },
            
            # Metadata
            "metadata": {
                "cached_at": snapshot.cached_at.isoformat() if snapshot.cached_at else None,
                "last_update": snapshot.last_update.isoformat() if snapshot.last_update else None
            }
        }
        
        return details
        
    except Exception as exc:
        logger.error(f"Failed to get security details for {isin}: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/portfolio/calendar")
async def get_payment_calendar(
    period: str = "30",  # "30", "90", "all"
    user: UserContext = Depends(get_current_user)
):
    """Get payment calendar for user's portfolio."""
    try:
        from datetime import datetime, timedelta
        now = datetime.now()
        
        # Calculate date range based on period
        if period == "30":
            start_date = now
            end_date = now + timedelta(days=30)
        elif period == "90":
            start_date = now
            end_date = now + timedelta(days=90)
        else:  # "all"
            start_date = now
            end_date = now + timedelta(days=3650)  # 10 years
        
        logger.info(f"Calendar request: period={period}, start_date={start_date.isoformat()}, end_date={end_date.isoformat()}")
        
        # Get user's portfolio
        session: Session = db_manager.SessionLocal()
        try:
            holdings = session.query(PortfolioHoldingV2).filter(
                PortfolioHoldingV2.user_id == user.id,
                PortfolioHoldingV2.is_active == True
            ).all()
            
            if not holdings:
                return {"events": [], "month": month, "year": year}
            
            events = []
            
            # Process each holding to get payment events
            for holding in holdings:
                # Get detailed security information and calendar data
                try:
                    # First get basic snapshot data
                    snapshots = await market_aggregator.get_snapshot_for(holding.isin)
                    if not snapshots:
                        continue
                    snapshot = snapshots[0]
                    
                    # Get calendar data based on security type
                    if holding.security_type == "bond":
                        # Try to get coupon data from T-Bank if available
                        if hasattr(snapshot, 'figi') and snapshot.figi:
                            from bot.providers.tbank_rest import TBankRestClient
                            async with TBankRestClient() as tbank_client:
                                try:
                                    # Get future coupons
                                    from datetime import datetime, timedelta
                                    now = datetime.now()
                                    
                                    logger.info(f"Requesting T-Bank coupons for {holding.isin} (FIGI: {snapshot.figi}) from {start_date.isoformat()} to {end_date.isoformat()}")
                                    coupons = await tbank_client.get_bond_coupons(
                                        snapshot.figi, 
                                        from_date=start_date, 
                                        to_date=end_date
                                    )
                                    logger.info(f"T-Bank returned {len(coupons)} coupons for {holding.isin}")
                                    
                                    if coupons:
                                        # Add all coupons in range as events
                                        for coupon in coupons:
                                            events.append({
                                                "date": coupon.coupon_date.isoformat(),
                                                "type": "coupon",
                                                "security_name": snapshot.name or snapshot.shortname or holding.ticker or holding.isin,
                                                "ticker": holding.ticker or snapshot.ticker or holding.isin,
                                                "isin": holding.isin,
                                                "amount": coupon.coupon_value or 0,
                                                "currency": snapshot.currency or "RUB",
                                                "quantity": holding.raw_quantity or 0,
                                                "total_amount": (coupon.coupon_value or 0) * (holding.raw_quantity or 0),
                                                "provider": "T-Bank"
                                            })
                                        
                                        logger.info(f"Found T-Bank calendar data for {holding.isin}: {len(coupons)} coupons")
                                    
                                except Exception as e:
                                    logger.error(f"Failed to get T-Bank coupons for {holding.isin}: {e}")
                        
                        # If no T-Bank data, try MOEX
                        if not snapshot.next_coupon_date:
                            from bot.providers.moex_iss.client import MOEXISSClient
                            async with MOEXISSClient() as moex_client:
                                try:
                                    moex_results = await moex_client.search_securities(holding.isin)
                                    if moex_results:
                                        moex_secid = moex_results[0].secid
                                        logger.info(f"Requesting MOEX calendar for {holding.isin} (SECID: {moex_secid})")
                                        # Calculate days ahead based on period
                                        days_ahead = (end_date - start_date).days
                                        calendar_data = await moex_client.get_bond_calendar(moex_secid, days_ahead=days_ahead)
                                        if calendar_data:
                                            if calendar_data.coupons:
                                                # Filter coupons by date range
                                                from datetime import datetime
                                                future_coupons = [c for c in calendar_data.coupons if start_date <= c.coupon_date <= end_date]
                                                logger.info(f"MOEX calendar for {holding.isin}: {len(calendar_data.coupons)} total coupons, {len(future_coupons)} in date range")
                                                
                                                if future_coupons:
                                                    # Add all coupons in range as events
                                                    for coupon in future_coupons:
                                                        events.append({
                                                            "date": coupon.coupon_date.isoformat(),
                                                            "type": "coupon",
                                                            "security_name": snapshot.name or snapshot.shortname or holding.ticker or holding.isin,
                                                            "ticker": holding.ticker or snapshot.ticker or holding.isin,
                                                            "isin": holding.isin,
                                                            "amount": coupon.coupon_value or 0,
                                                            "currency": snapshot.currency or "RUB",
                                                            "quantity": holding.raw_quantity or 0,
                                                            "total_amount": (coupon.coupon_value or 0) * (holding.raw_quantity or 0),
                                                            "provider": "MOEX"
                                                        })
                                            
                                            # Add amortizations in range
                                            if calendar_data.amortizations:
                                                future_amorts = [a for a in calendar_data.amortizations if start_date <= a.amort_date <= end_date]
                                                for amort in future_amorts:
                                                    events.append({
                                                        "date": amort.amort_date.isoformat(),
                                                        "type": "maturity",
                                                        "security_name": snapshot.name or snapshot.shortname or holding.ticker or holding.isin,
                                                        "ticker": holding.ticker or snapshot.ticker or holding.isin,
                                                        "isin": holding.isin,
                                                        "amount": amort.amort_value or 0,
                                                        "currency": snapshot.currency or "RUB",
                                                        "quantity": holding.raw_quantity or 0,
                                                        "total_amount": (amort.amort_value or 0) * (holding.raw_quantity or 0),
                                                        "provider": "MOEX"
                                                    })
                                            
                                            logger.info(f"Found MOEX calendar data for {holding.isin}: {len(future_coupons) if 'future_coupons' in locals() else 0} coupons, {len(future_amorts) if 'future_amorts' in locals() else 0} amortizations")
                                
                                except Exception as e:
                                    logger.error(f"Failed to get MOEX calendar for {holding.isin}: {e}")
                    
                    elif holding.security_type == "share":
                        # Try to get dividend data from T-Bank
                        if hasattr(snapshot, 'figi') and snapshot.figi:
                            from bot.providers.tbank_rest import TBankRestClient
                            async with TBankRestClient() as tbank_client:
                                try:
                                    from datetime import datetime, timedelta
                                    now = datetime.now()
                                    
                                    logger.info(f"Requesting T-Bank dividends for {holding.isin} (FIGI: {snapshot.figi}) from {start_date.isoformat()} to {end_date.isoformat()}")
                                    dividends = await tbank_client.get_dividends(
                                        snapshot.figi,
                                        from_date=start_date,
                                        to_date=end_date
                                    )
                                    logger.info(f"T-Bank returned {len(dividends)} dividends for {holding.isin}")
                                    
                                    if dividends:
                                        # Add all dividends in range as events
                                        for dividend in dividends:
                                            events.append({
                                                "date": dividend.payment_date.isoformat(),
                                                "type": "dividend",
                                                "security_name": snapshot.name or snapshot.shortname or holding.ticker or holding.isin,
                                                "ticker": holding.ticker or snapshot.ticker or holding.isin,
                                                "isin": holding.isin,
                                                "amount": dividend.dividend_net or 0,
                                                "currency": snapshot.currency or "RUB",
                                                "quantity": holding.raw_quantity or 0,
                                                "total_amount": (dividend.dividend_net or 0) * (holding.raw_quantity or 0),
                                                "provider": "T-Bank"
                                            })
                                        
                                        logger.info(f"Found T-Bank dividend data for {holding.isin}: {len(dividends)} dividends")
                                
                                except Exception as e:
                                    logger.error(f"Failed to get T-Bank dividends for {holding.isin}: {e}")
                    
                
                except Exception as e:
                    logger.error(f"Failed to process holding {holding.isin}: {e}")
                    continue
            
            # Log debug information
            logger.info(f"Calendar request: period={period}, start_date={start_date}, end_date={end_date}, holdings_count={len(holdings)}")
            
            # Debug: log details about each holding
            for holding in holdings:
                logger.info(f"Holding: {holding.ticker or holding.isin} ({holding.isin}) - {holding.raw_quantity or 0} шт")
                logger.info(f"  Security type: {holding.security_type}")
                logger.info(f"  Provider: {holding.provider}")
                
                # Try to get snapshot for this holding
                try:
                    snapshots = await market_aggregator.get_snapshot_for(holding.isin)
                    if snapshots:
                        snapshot = snapshots[0]
                        logger.info(f"  Snapshot: provider={snapshot.provider}, next_coupon={snapshot.next_coupon_date}, maturity={snapshot.maturity_date}")
                    else:
                        logger.info(f"  No snapshot found for {holding.isin}")
                except Exception as e:
                    logger.error(f"  Error getting snapshot for {holding.isin}: {e}")
            
            logger.info(f"Found {len(events)} events for user {user.id} in period {period}")
            for event in events[:10]:  # Log first 10 events
                logger.info(f"Event: {event['date']} - {event['type']} - {event['security_name']} - {event['amount']} {event['currency']} (provider: {event.get('provider', 'unknown')})")
            
            # Sort events by date
            events.sort(key=lambda x: x["date"])
            
            return {
                "events": events,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_events": len(events)
            }
            
        finally:
            session.close()
        
    except Exception as exc:
        logger.error(f"Failed to get payment calendar: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.patch("/api/portfolio/position/{position_id}", response_model=PortfolioResponse)
def update_position(
    position_id: int,
    payload: UpdatePositionRequest,
    user: UserContext = Depends(get_current_user)
) -> PortfolioResponse:
    session: Session = db_manager.SessionLocal()
    try:
        holding: Optional[PortfolioHoldingV2] = session.query(PortfolioHoldingV2).filter(
            PortfolioHoldingV2.id == position_id,
            PortfolioHoldingV2.user_id == user.id,
            PortfolioHoldingV2.is_active == True
        ).first()
        if not holding:
            raise HTTPException(status_code=404, detail="Position not found")

        if payload.quantity is not None:
            holding.raw_quantity = payload.quantity
        if payload.quantity_unit is not None:
            holding.raw_quantity_unit = payload.quantity_unit
        if payload.security_type is not None:
            holding.security_type = normalize_security_type(payload.security_type)

        holding.updated_at = datetime.utcnow()
        session.commit()
        return build_portfolio_response(user.id)
    finally:
        session.close()


@app.delete("/api/portfolio/position/{position_id}", response_model=PortfolioResponse)
def delete_position(
    position_id: int,
    user: UserContext = Depends(get_current_user)
) -> PortfolioResponse:
    session: Session = db_manager.SessionLocal()
    try:
        holding: Optional[PortfolioHoldingV2] = session.query(PortfolioHoldingV2).filter(
            PortfolioHoldingV2.id == position_id,
            PortfolioHoldingV2.user_id == user.id,
            PortfolioHoldingV2.is_active == True
        ).first()
        if not holding:
            raise HTTPException(status_code=404, detail="Position not found")

        holding.is_active = False
        holding.updated_at = datetime.utcnow()
        session.commit()
        return build_portfolio_response(user.id)
    finally:
        session.close()


@app.post("/api/portfolio/position", response_model=PortfolioResponse)
def create_position(
    payload: CreatePositionRequest,
    user: UserContext = Depends(get_current_user)
) -> PortfolioResponse:
    session: Session = db_manager.SessionLocal()
    try:
        account = db_manager.get_or_create_account(
            user_id=user.id,
            account_id=payload.account_id,
            session=session,
            account_name=payload.account_name,
            currency=payload.currency
        )

        name = payload.name or payload.ticker or payload.isin
        if not name:
            raise HTTPException(status_code=400, detail="Name or ticker is required")

        normalized_name = normalize_security_name(name)
        normalized_key = generate_normalized_key(normalized_name, payload.ticker or "", payload.isin or "")

        holding = db_manager.add_holding(
            user_id=user.id,
            raw_name=name,
            normalized_name=normalized_name,
            normalized_key=normalized_key,
            account_internal_id=account.id,
            session=session,
            raw_ticker=payload.ticker,
            raw_isin=payload.isin,
            raw_type=payload.security_type,
            raw_quantity=payload.quantity,
            raw_quantity_unit=payload.quantity_unit,
            ticker=payload.ticker,
            isin=payload.isin,
            security_type=normalize_security_type(payload.security_type),
            provider="manual",
            provider_data={"fallback": True, "source": "manual"}
        )

        holding.updated_at = datetime.utcnow()
        session.commit()
        return build_portfolio_response(user.id)
    finally:
        session.close()


@app.get("/api/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
