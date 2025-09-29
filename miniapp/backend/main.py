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
    elif telegram_id:
        user = db_manager.get_user_by_telegram_id(telegram_id)
    
    if not user and phone_number:
        user = db_manager.get_user_by_phone(phone_number)
    
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

    accounts_index: Dict[Optional[int], AccountResponse] = {}
    accounts_response: List[AccountResponse] = []

    for acc in summary["accounts"]:
        account_resp = AccountResponse(
            internal_id=acc["internal_id"],
            account_id=acc["account_id"] or "default",
            account_name=acc.get("account_name"),
            currency=acc.get("currency"),
            portfolio_value=acc.get("portfolio_value"),
            positions=[],
            cash=[]
        )
        accounts_response.append(account_resp)
        accounts_index[acc["internal_id"]] = account_resp

    # ensure default account exists for holdings without account
    if None not in accounts_index:
        default_account = AccountResponse(
            internal_id=None,
            account_id="default",
            account_name="Портфель",
            currency=None,
            portfolio_value=None,
            positions=[],
            cash=[]
        )
        accounts_index[None] = default_account
        accounts_response.append(default_account)

    for holding in summary["holdings"]:
        target_account = accounts_index.get(holding["account_internal_id"], accounts_index[None])
        name = holding.get("normalized_name") or holding.get("raw_name")
        provider_data = holding.get("provider_data") or {}
        position_resp = PortfolioPositionResponse(
            id=holding["id"],
            account_internal_id=holding.get("account_internal_id"),
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
        target_account.positions.append(position_resp)

    for cash in summary["cash_positions"]:
        target_account = accounts_index.get(cash.get("account_internal_id"), accounts_index[None])
        cash_resp = CashPositionResponse(
            id=cash["id"],
            account_internal_id=cash.get("account_internal_id"),
            raw_name=cash.get("raw_name"),
            amount=cash.get("amount"),
            currency=cash.get("currency"),
            created_at=cash.get("created_at"),
            updated_at=cash.get("updated_at"),
        )
        target_account.cash.append(cash_resp)

    user_info = UserInfo(phone=phone, telegram_id=telegram_id, username=username)
    return PortfolioResponse(user=user_info, accounts=accounts_response)


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
