from types import SimpleNamespace

from bot.utils.render import render_portfolio_summary
from bot.providers.aggregator import MarketSnapshot


def test_render_portfolio_summary_includes_accounts_and_cash():
    snapshots = [
        MarketSnapshot(
            secid="TQBR",
            name="Сбербанк",
            security_type="share",
            last_price=123.45,
            change_day_pct=1.23,
        )
    ]

    account = SimpleNamespace(
        id=1,
        account_id="broker_1",
        account_name="Брокерский счёт",
        currency="RUB",
        portfolio_value=150000.0,
        daily_change_value=1234.56,
        daily_change_percent=1.23,
    )

    cash_item = SimpleNamespace(raw_name="Рубли", amount=10000.0, currency="RUB")

    summary = render_portfolio_summary(
        snapshots,
        ocr_meta={"portfolio_name": "Портфель", "positions_count": 1},
        accounts=[account],
        cash_by_account={1: [cash_item]},
    )

    assert "Брокерский счёт" in summary
    assert "150,000.00 ₽" in summary or "150000.00 ₽" in summary
    assert "Δ" in summary
    assert "+1.23%" in summary
    assert "💵" in summary
    assert "10,000.00 ₽" in summary or "10000.00 ₽" in summary


def test_render_portfolio_summary_detached_cash_without_accounts():
    snapshots = []

    cash_item = SimpleNamespace(raw_name="USD", amount=500.0, currency="USD")

    summary = render_portfolio_summary(
        snapshots,
        ocr_meta={"warnings": ["partial"]},
        accounts=None,
        cash_by_account={None: [cash_item]},
    )

    assert "⚠️ **Предупреждения OCR:**" in summary
    assert "Денежные средства" in summary
    assert "$500.00" in summary

