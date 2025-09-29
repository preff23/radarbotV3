from types import SimpleNamespace

import pytest

from bot.handlers.invest_analyst import InvestAnalyst


@pytest.mark.asyncio
async def test_create_system_prompt_includes_accounts_and_cash(monkeypatch):
    analyst = InvestAnalyst()

    portfolio_data = {
        "holdings": [
            {
                "name": "Сбербанк",
                "ticker": "SBER",
                "quantity": 10,
                "security_type": "share",
                "account_id": 1,
            }
        ],
        "accounts": [
            {
                "id": 1,
                "account_id": "broker_1",
                "name": "Брокерский счёт",
                "currency": "RUB",
                "portfolio_value": 150000.0,
                "cash": [{"raw_name": "Рубли", "amount": 10000.0, "currency": "RUB"}],
                "daily_change_value": 1234.56,
                "daily_change_percent": 1.23,
            }
        ],
        "detached_cash": [],
        "analysis": {},
    }

    market_context = {
        "news": [],
        "moex_indices": {},
        "currency_rates": {},
    }

    prompt = analyst._create_system_prompt(portfolio_data, market_context)

    assert "Счета и балансы" in prompt
    assert "Брокерский счёт" in prompt
    assert "10,000.00 ₽" in prompt or "10000.00 ₽" in prompt
    assert "+1.23%" in prompt or "+1,23%" in prompt
    assert "Δ" in prompt


@pytest.mark.asyncio
async def test_create_system_prompt_no_accounts_but_cash(monkeypatch):
    analyst = InvestAnalyst()

    portfolio_data = {
        "holdings": [],
        "accounts": [],
        "detached_cash": [{"raw_name": "USD", "amount": 500.0, "currency": "USD"}],
        "analysis": {},
    }

    market_context = {
        "news": [],
        "moex_indices": {},
        "currency_rates": {},
    }

    prompt = analyst._create_system_prompt(portfolio_data, market_context)

    assert "Денежные средства без привязки" in prompt
    assert "$500.00" in prompt

