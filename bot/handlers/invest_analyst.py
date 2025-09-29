import openai
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from bot.core.config import config
from bot.core.db import db_manager
from bot.analytics.portfolio_analyzer import PortfolioAnalyzer
from bot.sources.news_rss import NewsAggregator
from bot.utils.moex_client import MOEXClient
from bot.providers.aggregator import market_aggregator
from bot.core.logging import get_logger

logger = get_logger(__name__)


class InvestAnalyst:
    
    def __init__(self):
        self.openai_client = openai.OpenAI(
            base_url="https://neuroapi.host/v1",
            api_key=config.openai_api_key
        )
        self.portfolio_analyzer = PortfolioAnalyzer()
        self.news_aggregator = NewsAggregator()
        self.moex_client = MOEXClient()
        self.market_aggregator = market_aggregator
    
    async def chat_with_user(self, phone_number: str, message: str) -> str:
        try:
            portfolio_data = await self._get_user_portfolio_data(phone_number)
            
            market_context = await self._get_market_context()
            
            system_prompt = self._create_system_prompt(portfolio_data, market_context)
            
            response = await self._get_chatgpt_response(system_prompt, message)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in Invest chat: {e}")
            return "Извините, произошла ошибка. Попробуйте позже."
    
    async def _get_user_portfolio_data(self, phone_number: str) -> Dict[str, Any]:
        try:
            user = db_manager.get_user_by_phone(phone_number)
            if not user:
                return {"holdings": [], "analysis": None}

            holdings = db_manager.get_user_holdings(user.id, active_only=True)
            
            if not holdings:
                return {"holdings": [], "analysis": None}
            
            accounts = db_manager.get_user_accounts(user.id)
            cash_map: Dict[Optional[int], List[Dict[str, Any]]] = {}
            for account in accounts:
                cash_positions = db_manager.get_account_cash(user.id, account.id)
                cash_map[account.id] = [
                    {
                        "raw_name": cash.raw_name,
                        "amount": cash.amount,
                        "currency": cash.currency
                    }
                    for cash in cash_positions
                ]
            # separated cash not tied to конкретному account_internal_id
            detached_cash = db_manager.get_account_cash(user.id, None)
            if detached_cash:
                cash_map[None] = [
                    {
                        "raw_name": cash.raw_name,
                        "amount": cash.amount,
                        "currency": cash.currency
                    }
                    for cash in detached_cash
                ]

            analysis = await self.portfolio_analyzer.run_analysis(user.id)

            holdings_payload = [
                {
                    "name": h.normalized_name,
                    "ticker": h.ticker,
                    "isin": h.isin,
                    "quantity": h.raw_quantity or 0,
                    "security_type": h.security_type,
                    "account_id": h.account_internal_id
                }
                for h in holdings
            ]

            accounts_payload = [
                {
                    "id": acc.id,
                    "account_id": acc.account_id,
                    "name": acc.account_name,
                    "currency": acc.currency,
                    "portfolio_value": acc.portfolio_value,
                    "cash": cash_map.get(acc.id, []),
                    "daily_change_value": acc.daily_change_value,
                    "daily_change_percent": acc.daily_change_percent
                }
                for acc in accounts
            ]

            return {
                "holdings": holdings_payload,
                "accounts": accounts_payload,
                "detached_cash": cash_map.get(None, []),
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio data: {e}")
            return {"holdings": [], "analysis": None}
    
    async def _get_market_context(self) -> Dict[str, Any]:
        try:
            news_items = await self.news_aggregator.get_news_for_securities(
                tickers=["SBER", "GAZP", "LKOH", "ROSN", "NVTK", "MAGN", "YNDX", "TCSG", "VKCO", "AFLT"],
                issuers=["Сбербанк", "Газпром", "ЛУКОЙЛ", "Роснефть", "Новатэк", "Магнит", "Яндекс", "Тинькофф", "ВК", "Аэрофлот"],
                max_age_hours=24
            )
            
            moex_data = {}
            currency_rates = {}
            try:
                indices = ["IMOEX", "RTSI", "MOEXBC", "MOEXREAL"]
                for index in indices:
                    data = await self.moex_client.get_index_data(index)
                    if data:
                        moex_data[index] = data
            except Exception as e:
                logger.warning(f"Error getting MOEX data: {e}")

            try:
                currency_codes = ["USD000UTSTOM", "EUR_RUB__TOM", "CNYRUB_TOM"]
                snapshots = await self.market_aggregator.get_snapshot_for(currency_codes)
                for snapshot in snapshots:
                    ticker = snapshot.ticker or snapshot.secid
                    currency_rates[ticker] = {
                        "name": snapshot.name or ticker,
                        "price": snapshot.last_price,
                        "currency": snapshot.currency or "RUB",
                        "provider": snapshot.provider,
                        "data_freshness": getattr(snapshot, "data_freshness", None)
                    }

                if "EUR_RUB__TOM" not in currency_rates:
                    moex_currency = await self.moex_client.get_security_data(
                        "EURRUB_TOM", engine="currency", market="selt", board="CETS"
                    )
                    if moex_currency and moex_currency.get("last") is not None:
                        currency_rates["EUR_RUB__TOM"] = {
                            "name": moex_currency.get("name") or "EURRUB_TOM",
                            "price": moex_currency.get("last"),
                            "currency": moex_currency.get("currency") or "RUB",
                            "provider": "MOEX",
                            "data_freshness": None
                        }
            except Exception as e:
                logger.warning(f"Error getting currency data: {e}")
            
            return {
                "news": [
                    {
                        "title": item.title,
                        "source": item.source,
                        "published_at": item.published_at.strftime("%d.%m.%Y %H:%M") if item.published_at else None,
                        "related_tickers": item.related_tickers,
                        "related_issuers": item.related_issuers
                    }
                    for item in news_items[:5]
                ],
                "moex_indices": moex_data,
                "currency_rates": currency_rates
            }
            
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return {"news": [], "moex_indices": {}, "currency_rates": {}}
    
    def _create_system_prompt(self, portfolio_data: Dict[str, Any], market_context: Dict[str, Any]) -> str:
        holdings = portfolio_data.get("holdings", [])
        accounts = portfolio_data.get("accounts", [])
        detached_cash = portfolio_data.get("detached_cash", [])
        analysis = portfolio_data.get("analysis", {})
        news = market_context.get("news", [])
        moex_indices = market_context.get("moex_indices", {})
        currency_rates = market_context.get("currency_rates", {})
        
        portfolio_summary = ""
        if holdings:
            portfolio_summary = "Портфель пользователя:\n"
            for holding in holdings:
                ticker = holding.get('ticker') or '—'
                quantity = holding.get('quantity') or 0
                sec_type = holding.get('security_type') or 'инструмент'
                account_ref = ""
                if holding.get('account_id'):
                    account_ref = f" [счёт #{holding['account_id']}]."
                portfolio_summary += f"- {holding['name']} ({ticker}) - {quantity} шт. ({sec_type}){account_ref}\n"
        else:
            portfolio_summary = "Портфель пользователя пуст."

        accounts_summary = ""
        if accounts:
            accounts_summary = "Счета и балансы:\n"
            for account in accounts:
                display_name = account.get('name') or account.get('account_id') or f"ID {account.get('id')}"
                currency = account.get('currency') or 'RUB'
                value = account.get('portfolio_value')
                if value is not None:
                    if currency == 'RUB':
                        value_str = f"{value:,.2f} ₽"
                    elif currency == 'USD':
                        value_str = f"${value:,.2f}"
                    elif currency == 'EUR':
                        value_str = f"€{value:,.2f}"
                    else:
                        value_str = f"{value:,.2f} {currency}"
                else:
                    value_str = "—"
                accounts_summary += f"- {display_name}: {value_str}\n"

                daily_change_value = account.get('daily_change_value')
                daily_change_percent = account.get('daily_change_percent')
                change_parts = []
                if daily_change_value is not None:
                    if currency == 'RUB':
                        change_parts.append(f"{daily_change_value:+,.2f} ₽")
                    elif currency == 'USD':
                        change_parts.append(f"${daily_change_value:+,.2f}")
                    elif currency == 'EUR':
                        change_parts.append(f"€{daily_change_value:+,.2f}")
                    else:
                        change_parts.append(f"{daily_change_value:+,.2f} {currency}")
                if daily_change_percent is not None:
                    change_parts.append(f"{daily_change_percent:+.2f}%")
                if change_parts:
                    accounts_summary += f"  Δ {' / '.join(change_parts)}\n"

                cash_entries = account.get('cash') or []
                for cash in cash_entries:
                    cash_amount = cash.get('amount') or 0
                    cash_currency = cash.get('currency') or currency
                    if cash_currency == 'RUB':
                        cash_str = f"{cash_amount:,.2f} ₽"
                    elif cash_currency == 'USD':
                        cash_str = f"${cash_amount:,.2f}"
                    elif cash_currency == 'EUR':
                        cash_str = f"€{cash_amount:,.2f}"
                    else:
                        cash_str = f"{cash_amount:,.2f} {cash_currency}"
                    accounts_summary += f"  💵 {cash.get('raw_name') or 'Cash'}: {cash_str}\n"
        
        if detached_cash and not accounts:
            accounts_summary += "Денежные средства без привязки к счету:\n"
            for cash in detached_cash:
                cash_amount = cash.get('amount') or 0
                cash_currency = cash.get('currency') or 'RUB'
                if cash_currency == 'RUB':
                    cash_str = f"{cash_amount:,.2f} ₽"
                elif cash_currency == 'USD':
                    cash_str = f"${cash_amount:,.2f}"
                elif cash_currency == 'EUR':
                    cash_str = f"€{cash_amount:,.2f}"
                else:
                    cash_str = f"{cash_amount:,.2f} {cash_currency}"
                accounts_summary += f"- {cash.get('raw_name') or 'Cash'}: {cash_str}\n"
        
        news_summary = ""
        if news:
            news_summary = "Последние новости рынка:\n"
            for item in news:
                news_summary += f"- {item['title']} ({item['source']}, {item['published_at']})\n"
        else:
            news_summary = "Новости рынка недоступны."
        
        moex_summary = ""
        if moex_indices:
            moex_summary = "Индексы MOEX:\n"
            for index, data in moex_indices.items():
                if isinstance(data, dict) and data.get('last') is not None:
                    last = data.get('last')
                    change_pct = data.get('change_percent')
                    change_display = f"{change_pct}%" if change_pct is not None else "—"
                    moex_summary += f"- {index}: {last} ({change_display})\n"
        else:
            moex_summary = "Данные MOEX недоступны."

        currency_summary = ""
        if currency_rates:
            currency_summary = "Курсы валют (T-Bank/MOEX):\n"
            for code, data in currency_rates.items():
                price = data.get('price')
                currency = data.get('currency')
                if price is not None:
                    currency_summary += f"- {code}: {price} {currency}\n"
        else:
            currency_summary = "Курсы валют недоступны."
        
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        system_prompt = f"""Ты Invest - профессиональный финансовый аналитик и инвестиционный консультант. 

Твоя личность:
- Эксперт по российским и международным рынкам
- Специализируешься на облигациях, акциях и других ценных бумагах
- Говоришь профессионально, но доступно
- Всегда даешь обоснованные рекомендации
- Учитываешь риск-профиль клиента

Твои возможности:
- Анализируешь портфель пользователя
- Даешь рекомендации по инвестициям (включая конкретные покупки)
- Объясняешь рыночные события
- Помогаешь с выбором ценных бумаг
- Оцениваешь риски
- Анализируешь новости и их влияние на рынок
- Отслеживаешь индексы MOEX
- Подключен к Tinkoff Investments API (T-Bank) и MOEX ISS API: можешь запрашивать цены, справочные данные, календари купонов, курсы валют и т.п.
- Используешь объединенный маркет-агрегатор (MOEX + T-Bank + CorpBonds) для доступа к котировкам и характеристикам бумаг

Текущая дата: {current_date}

{portfolio_summary}

{accounts_summary}

{news_summary}

{moex_summary}

{currency_summary}

Правила общения:
1. Всегда представляйся как Invest
2. Отвечай на русском языке
3. Будь профессиональным, но дружелюбным
4. Используй эмодзи для лучшего восприятия
5. Можешь давать конкретные рекомендации по покупке акций/облигаций
6. ВСЕГДА добавляй к рекомендациям: "⚠️ Данные рекомендации носят развлекательный характер и не являются инвестиционными советами"
7. Всегда указывай на риски инвестиций
8. Используй новости и данные MOEX для обоснования рекомендаций
9. Если нужно больше информации о портфеле, можешь попросить пользователя запустить анализ

Отвечай как Invest - финансовый аналитик."""
        
        return system_prompt
    
    async def _get_chatgpt_response(self, system_prompt: str, user_message: str) -> str:
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error getting ChatGPT response: {e}")
            return "Извините, не могу обработать ваш запрос. Попробуйте позже."


invest_analyst = InvestAnalyst()