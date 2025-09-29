import asyncio
import json
import openai
from typing import List, Dict, Any, Optional
from datetime import datetime
from bot.core.db import db_manager, PortfolioHoldingV2, PortfolioAccount, PortfolioCashPosition
from bot.core.config import config
from bot.providers.aggregator import market_aggregator
from bot.sources.news_rss import get_news_for_portfolio
from bot.utils.integrated_bond_client import IntegratedBondClient
from bot.analytics.payment_history import PaymentHistoryAnalyzer
from bot.utils.render import (
    render_signals_as_cards, render_calendar_30d, render_news_summary,
    render_portfolio_summary, render_recommendations, render_payment_history
)
from bot.core.logging import get_logger

logger = get_logger(__name__)


class IntegratedSnapshot:
    
    def __init__(self, data: dict):
        self.isin = data.get('isin')
        self.name = data.get('name')
        self.issuer_name = data.get('issuer_name')
        self.price = data.get('price')
        self.yield_to_maturity = data.get('yield_to_maturity')
        self.duration = data.get('duration')
        self.face_value = data.get('face_value')
        self.sector = data.get('sector')
        self.security_type = data.get('security_type')
        self.confidence = data.get('confidence')
        self.corpbonds_found = data.get('corpbonds_found')
        self.tbank_found = data.get('tbank_found')
        self.moex_found = data.get('moex_found')
        self.holding_id = data.get('holding_id')
        self.raw_name = data.get('raw_name')
        self.raw_quantity = data.get('raw_quantity')
        
        self.ticker = self.isin
        self.last_price = self.price
        self.change_day_pct = 0.0
        self.volume = 0.0
        self.currency = 'RUB'
        self.secid = self.isin
        self.trading_status = 'NormalTrading'
        self.shortname = self.name
        self.board = 'TQCB'
        self.aci = 0.0
        self.ytm = self.yield_to_maturity
        self.next_coupon_date = None
        self.provider = 'integrated'
        self.last_update = datetime.now()
        self.maturity_date = None
        self.coupon_rate = 0.0
        self.coupon_frequency = 0
        self.issue_date = None
        self.issue_size = 0.0
        self.rating = None
        self.rating_agency = None


class PortfolioAnalyzer:
    
    def __init__(self):
        self.db_manager = db_manager
        self.market_aggregator = market_aggregator
        self.payment_history_analyzer = PaymentHistoryAnalyzer()
        self.openai_client = openai.OpenAI(
            base_url="https://neuroapi.host/v1",
            api_key=config.openai_api_key
        )
    
    async def run_analysis(self, user_id: int) -> Dict[str, Any]:
        """Run comprehensive portfolio analysis.

        Args:
            user_id: User ID

        Returns:
            Analysis results with all components
        """
        try:
            holdings = await self._load_user_holdings(user_id)
            if not holdings:
                return {
                    "error": "Портфель пуст",
                    "summary": "Добавьте позиции для анализа"
                }

            accounts = await self._load_user_accounts(user_id)
            cash_by_account = await self._load_account_cash(user_id, accounts)

            bond_holdings = [h for h in holdings if h.security_type == "bond" or (h.isin and h.isin.startswith('RU'))]
            share_holdings = [h for h in holdings if h.security_type == "share"]
            
            integrated_bond_data = await self._get_integrated_bond_data(bond_holdings)
            
            share_snapshots = []
            if share_holdings:
                share_snapshots = await self._get_market_data(share_holdings)
            
            all_snapshots = integrated_bond_data + share_snapshots
            
            bonds_with_data = {snapshot.holding_id for snapshot in integrated_bond_data if hasattr(snapshot, 'holding_id')}
            bonds_without_data = [h for h in bond_holdings if h.id not in bonds_with_data]
            
            if bonds_without_data:
                basic_bond_snapshots = await self._create_basic_snapshots(bonds_without_data)
                all_snapshots.extend(basic_bond_snapshots)
            
            if not all_snapshots:
                all_snapshots = await self._create_basic_snapshots(holdings)
            
            bond_calendar = await self._get_bond_calendar(all_snapshots)
            
            news_items = await self._get_news(all_snapshots)
            
            payment_history = await self._get_payment_history(all_snapshots)
            
            has_shares = len(share_holdings) > 0
            try:
                ocr_meta = self.db_manager.get_portfolio_meta(user_id)
            except Exception:
                ocr_meta = {}
            analysis = await self._generate_analysis(
                all_snapshots,
                bond_calendar,
                news_items,
                payment_history,
                has_shares,
                holdings,
                accounts,
                cash_by_account,
                ocr_meta
            )
            
            if config.feature_analysis_v14:
                ai_analysis = await self._generate_ai_analysis(
                    all_snapshots,
                    bond_calendar,
                    news_items,
                    ocr_meta,
                    payment_history,
                    accounts,
                    cash_by_account
                )
                analysis["ai_analysis"] = ai_analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Portfolio analysis failed for user {user_id}: {e}")
            return {
                "error": "Ошибка анализа",
                "summary": f"Не удалось выполнить анализ: {str(e)}"
            }
    
    async def _load_user_holdings(self, user_id: int) -> List[PortfolioHoldingV2]:
        try:
            return self.db_manager.get_user_holdings(user_id, active_only=True)
        except Exception as e:
            logger.error(f"Failed to load holdings for user {user_id}: {e}")
            return []

    async def _load_user_accounts(self, user_id: int) -> List[PortfolioAccount]:
        try:
            return self.db_manager.get_user_accounts(user_id)
        except Exception as e:
            logger.error(f"Failed to load accounts for user {user_id}: {e}")
            return []

    async def _load_account_cash(self, user_id: int, accounts: List[PortfolioAccount]) -> Dict[int, List[PortfolioCashPosition]]:
        cash_map: Dict[int, List[PortfolioCashPosition]] = {}
        try:
            for account in accounts:
                cash_map[account.id] = self.db_manager.get_account_cash(user_id, account.id)
            cash_map[None] = self.db_manager.get_account_cash(user_id, None)
        except Exception as e:
            logger.error(f"Failed to load cash positions for user {user_id}: {e}")
        return cash_map
    
    async def _get_payment_history(self, snapshots: List[Any]) -> Dict[str, Any]:
        try:
            bond_snapshots = [
                snapshot for snapshot in snapshots 
                if snapshot.security_type == "bond" and snapshot.secid
            ]
            
            if not bond_snapshots:
                return {}
            
            logger.info(f"Getting payment history for {len(bond_snapshots)} bonds")
            
            history_tasks = [
                self.payment_history_analyzer.get_payment_history(snapshot.secid, months_back=12)
                for snapshot in bond_snapshots
            ]
            history_results = await asyncio.gather(*history_tasks, return_exceptions=True)
            
            payment_history = {}
            risk_signals = []
            
            for i, result in enumerate(history_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to get payment history for {bond_snapshots[i].secid}: {result}")
                    continue
                
                if result:
                    secid = bond_snapshots[i].secid
                    payment_history[secid] = result
                    
                    signals = self.payment_history_analyzer.get_risk_signals(result)
                    if signals:
                        risk_signals.extend([f"{secid}: {signal}" for signal in signals])
            
            return {
                "history": payment_history,
                "risk_signals": risk_signals,
                "total_bonds_analyzed": len(bond_snapshots),
                "bonds_with_history": len(payment_history)
            }
            
        except Exception as e:
            logger.error(f"Failed to get payment history: {e}")
            return {}
    
    async def _create_basic_snapshots(self, holdings: List[PortfolioHoldingV2]) -> List[Any]:
        from bot.providers.aggregator import MarketSnapshot
        
        snapshots = []
        for holding in holdings:
            security_type = holding.security_type or "bond"
            
            if security_type == "fund" and holding.isin and holding.isin.startswith('RU'):
                security_type = "bond"
            elif security_type == "fund" and not holding.isin and holding.ticker and holding.ticker.startswith('RU') and len(holding.ticker) == 12:
                security_type = "bond"
            elif holding.security_type == "bond":
                security_type = "bond"
            
            snapshot = MarketSnapshot(
                name=holding.normalized_name,
                ticker=holding.ticker,
                isin=holding.isin,
                secid=holding.secid,
                security_type=security_type,
                last_price=None,
                change_day_pct=None,
                currency="RUB",
                trading_status="T",
                provider="UNKNOWN",
                sector=None,
                ytm=None,
                next_coupon_date=None,
                coupon_value=None,
                maturity_date=None,
                next_dividend_date=None,
                dividend_value=None
            )
            snapshots.append(snapshot)
        
        return snapshots
    
    async def _get_market_data(self, holdings: List[PortfolioHoldingV2]) -> List[Any]:
        try:
            queries = []
            for holding in holdings:
                query = holding.ticker or holding.isin or holding.raw_name or holding.normalized_name
                if query:
                    queries.append(query)
            
            if not queries:
                return []
            
            snapshots = await self.market_aggregator.get_snapshot_for(queries)
            
            enriched_snapshots = []
            for i, snapshot in enumerate(snapshots):
                if i < len(holdings):
                    holding = holdings[i]
                    snapshot.holding_id = holding.id
                    snapshot.raw_name = holding.raw_name
                    snapshot.raw_quantity = holding.raw_quantity
                    enriched_snapshots.append(snapshot)
            
            return enriched_snapshots
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return []

    async def _get_integrated_bond_data(self, holdings: List[PortfolioHoldingV2]) -> List[Any]:
        try:
            bond_holdings = []
            for h in holdings:
                if h.isin and h.isin.startswith('RU'):
                    bond_holdings.append(h)
                elif not h.isin and h.ticker and h.ticker.startswith('RU') and len(h.ticker) == 12:
                    bond_holdings.append(h)
                elif h.security_type == "bond":
                    bond_holdings.append(h)
            
            if not bond_holdings:
                logger.info("No bond holdings found for integrated analysis")
                return []
            
            logger.info(f"Getting integrated data for {len(bond_holdings)} bond holdings")
            
            async with IntegratedBondClient() as client:
                await client._load_corpbonds_data()
                
                integrated_data = []
                for holding in bond_holdings:
                    try:
                        isin_to_use = holding.isin if holding.isin else holding.ticker
                        
                        bond_data = await client.get_bond_data(isin_to_use, holding.ticker)
                        if bond_data:
                            snapshot_data = {
                                'isin': bond_data.isin,
                                'name': bond_data.name,
                                'issuer_name': bond_data.issuer_name,
                                'price': bond_data.price,
                                'yield_to_maturity': bond_data.yield_to_maturity,
                                'duration': bond_data.duration,
                                'face_value': bond_data.face_value,
                                'sector': bond_data.sector,
                                'security_type': bond_data.security_type,
                                'confidence': bond_data.confidence,
                                'corpbonds_found': bond_data.corpbonds_found,
                                'tbank_found': bond_data.tbank_found,
                                'moex_found': bond_data.moex_found,
                                'holding_id': holding.id,
                                'raw_name': holding.raw_name,
                                'raw_quantity': holding.raw_quantity
                            }
                            snapshot = IntegratedSnapshot(snapshot_data)
                            integrated_data.append(snapshot)
                        else:
                            logger.warning(f"No integrated data found for {isin_to_use}")
                            
                    except Exception as e:
                        logger.error(f"Failed to get integrated data for {isin_to_use}: {e}")
                
                logger.info(f"Retrieved integrated data for {len(integrated_data)} bonds")
                return integrated_data
                
        except Exception as e:
            logger.error(f"Failed to get integrated bond data: {e}")
            return []
    
    async def _get_bond_calendar(self, snapshots: List[Any]) -> List[Dict[str, Any]]:
        try:
            bond_secids = [
                snapshot.secid for snapshot in snapshots
                if snapshot.security_type == "bond" and snapshot.secid
            ]
            
            if not bond_secids:
                return []
            
            calendar_tasks = [
                self.market_aggregator.get_bond_calendar(secid)
                for secid in bond_secids
            ]
            calendar_results = await asyncio.gather(*calendar_tasks, return_exceptions=True)
            
            all_events = []
            for i, result in enumerate(calendar_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to get calendar for {bond_secids[i]}: {result}")
                    continue
                
                if result:
                    bond_secid = bond_secids[i]
                    bond_snapshot = next(
                        (s for s in snapshots if s.secid == bond_secid), None
                    )
                    bond_name = bond_snapshot.name if bond_snapshot else bond_secid
                    
                    for coupon in result.get("coupons", []):
                        event = coupon.copy()
                        event["secid"] = bond_secid
                        event["name"] = bond_name
                        all_events.append(event)
                    
                    for amort in result.get("amortizations", []):
                        event = amort.copy()
                        event["secid"] = bond_secid
                        event["name"] = bond_name
                        all_events.append(event)
            
            return all_events
            
        except Exception as e:
            logger.error(f"Failed to get bond calendar: {e}")
            return []
    
    async def _get_news(self, snapshots: List[Any]) -> List[Dict[str, Any]]:
        try:
            tickers = [s.ticker for s in snapshots if s.ticker]
            issuers = [s.name for s in snapshots if s.name]
            
            logger.info(f"Getting news for portfolio with {len(tickers)} tickers and {len(issuers)} issuers")
            logger.info(f"Tickers: {tickers}")
            logger.info(f"Issuers: {issuers}")
            
            if not tickers and not issuers:
                logger.warning("No tickers or issuers found for news search")
                return []
            
            news_items = await get_news_for_portfolio(tickers, issuers, max_age_hours=24)
            
            logger.info(f"Found {len(news_items)} relevant news items for current portfolio")
            
            news_dicts = []
            for item in news_items:
                news_dicts.append({
                    "title": item.title,
                    "link": item.link,
                    "description": item.description,
                    "source": item.source,
                    "published_at": item.published_at,
                    "related_tickers": item.related_tickers,
                    "related_issuers": item.related_issuers,
                    "matched_terms": getattr(item, 'matched_terms', [])
                })
            
            return news_dicts
            
        except Exception as e:
            logger.error(f"Failed to get news: {e}")
            return []
    
    async def _generate_analysis(self,
                               snapshots: List[Any],
                               bond_calendar: List[Dict[str, Any]],
                               news_items: List[Dict[str, Any]],
                               payment_history: Dict[str, Any],
                               has_shares: bool = False,
                               holdings: List[Any] = None,
                               accounts: List[PortfolioAccount] = None,
                               cash_by_account: Dict[int, List[PortfolioCashPosition]] = None,
                               ocr_meta: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            summary = render_portfolio_summary(snapshots, ocr_meta, accounts, cash_by_account)
            
            signals_table = await render_signals_as_cards(snapshots, has_shares)
            
            calendar_text = render_calendar_30d(bond_calendar)
            
            news_summary = render_news_summary(news_items, holdings)
            
            payment_history_summary = render_payment_history(payment_history)
            
            recommendations = render_recommendations(snapshots)
            
            metrics = self._calculate_metrics(snapshots)
            
            return {
                "summary": summary,
                "signals_table": signals_table,
                "signals": snapshots,
                "calendar_30d": calendar_text,
                "news_summary": news_summary,
                "news": news_items,
                "payment_history_summary": payment_history_summary,
                "recommendations": recommendations,
                "metrics": metrics,
                "payment_history": payment_history,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate analysis: {e}")
            return {
                "error": "Ошибка генерации анализа",
                "summary": f"Не удалось сгенерировать анализ: {str(e)}"
            }
    
    def _calculate_metrics(self, snapshots: List[Any]) -> Dict[str, Any]:
        try:
            total_value = 0
            total_change = 0
            high_risk_count = 0
            monitor_count = 0
            low_risk_count = 0
            
            for snapshot in snapshots:
                if snapshot.last_price:
                    total_value += snapshot.last_price
                
                if snapshot.change_day_pct is not None:
                    total_change += snapshot.change_day_pct
                
                risk_level = self._get_risk_level(snapshot)
                if "🔴" in risk_level or "🚨" in risk_level:
                    high_risk_count += 1
                elif "🟠" in risk_level:
                    monitor_count += 1
                else:
                    low_risk_count += 1
            
            return {
                "total_value": total_value,
                "total_change": total_change,
                "high_risk_count": high_risk_count,
                "monitor_count": monitor_count,
                "low_risk_count": low_risk_count,
                "total_positions": len(snapshots)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {}
    
    def _get_risk_level(self, snapshot: Any) -> str:
        if snapshot.security_type == "bond":
            if snapshot.trading_status and snapshot.trading_status != "T":
                return "🚨 критический (торги ограничены)"
            
            if snapshot.ytm is None:
                return "🟡 умеренный (нет YTM)"
            
            if snapshot.ytm > 20:
                return "🔴 высокий"
            elif snapshot.ytm >= 12:
                return "🟠 мониторинг"
            else:
                return "🟢 низкий"
        
        elif snapshot.security_type == "share":
            if snapshot.change_day_pct is None:
                return "🟡 умеренный (нет данных)"
            
            if snapshot.change_day_pct > 5:
                return "🟡 умеренный (событие/волатильность)"
            elif snapshot.change_day_pct < -5:
                return "🟠 мониторинг"
            else:
                return "🟢 низкий"
        
        elif snapshot.security_type == "fund":
            return "🟢 низкий (фонд)"
        
        return "—"
    
    async def _generate_ai_analysis(self,
                                  snapshots: List[Any],
                                  bond_calendar: List[Dict[str, Any]],
                                  news_items: List[Dict[str, Any]],
                                  ocr_meta: Dict[str, Any],
                                  payment_history: Optional[Dict[str, Any]] = None,
                                  accounts: Optional[List[PortfolioAccount]] = None,
                                  cash_by_account: Optional[Dict[int, List[PortfolioCashPosition]]] = None) -> str:
        try:
            prompt_path = "bot/ai/prompts/portfolio_analyze_v14.txt"
            with open(prompt_path, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
            
            # Build payload for AI
            metrics = self._calculate_metrics(snapshots)
            portfolio_data = {
                "positions": [],
                "bond_calendar": bond_calendar,
                "news": news_items,
                "ocr_meta": ocr_meta,
                "metrics": metrics,
                "top_positions": [],
                "accounts": [],
            }
            if payment_history:
                portfolio_data["payment_history"] = payment_history

            if accounts:
                for account in accounts:
                    account_cash = [
                        {
                            "raw_name": cash.raw_name,
                            "amount": cash.amount,
                            "currency": cash.currency
                        }
                        for cash in (cash_by_account or {}).get(account.id, [])
                    ]
                    portfolio_data["accounts"].append({
                        "account_name": account.account_name,
                        "account_id": account.account_id,
                        "currency": account.currency,
                        "portfolio_value": account.portfolio_value,
                        "cash_positions": account_cash
                    })
 
            weighted_positions = []
            for snapshot in snapshots:
                quantity = getattr(snapshot, "raw_quantity", None)
                quantity_unit = getattr(snapshot, "raw_quantity_unit", None)
                notional_estimate = None
                if quantity is not None and snapshot.last_price is not None:
                    try:
                        notional_estimate = float(quantity) * float(snapshot.last_price)
                    except Exception:
                        notional_estimate = None
                position = {
                    "name": snapshot.name or snapshot.ticker or snapshot.secid,
                    "raw_name": getattr(snapshot, "raw_name", None),
                    "ticker": snapshot.ticker,
                    "isin": snapshot.isin,
                    "secid": getattr(snapshot, "secid", None),
                    "type": snapshot.security_type,
                    "currency": snapshot.currency,
                    "last_price": snapshot.last_price,
                    "price_kind": "percent_of_nominal" if snapshot.security_type == "bond" else "absolute",
                    "change_pct": snapshot.change_day_pct,
                    "trading_status": snapshot.trading_status,
                    "quantity": quantity,
                    "quantity_unit": quantity_unit,
                    "issuer": getattr(snapshot, "issuer_name", None),
                    "sector": snapshot.sector,
                    "ytm": getattr(snapshot, "ytm", None),
                    "duration": getattr(snapshot, "duration", None),
                    "face_value": getattr(snapshot, "face_value", None),
                    "provider": getattr(snapshot, "provider", None),
                    "data_freshness": getattr(snapshot, "data_freshness", None),
                    "notional_estimate": notional_estimate
                }
                portfolio_data["positions"].append(position)
                weighted_positions.append(position)
 
            weighted_positions = [p for p in weighted_positions if p.get("notional_estimate")]
            weighted_positions.sort(key=lambda x: x["notional_estimate"], reverse=True)
            portfolio_data["top_positions"] = weighted_positions[:5]
 
            meta_block = ""
            if ocr_meta:
                meta_block = (
                    "МЕТАДАННЫЕ ПОРТФЕЛЯ (OCR):\n"
                    f"- Название: {ocr_meta.get('portfolio_name') or '—'}\n"
                    f"- Общая стоимость: {ocr_meta.get('portfolio_value') if ocr_meta.get('portfolio_value') is not None else '—'} {ocr_meta.get('currency') or ''}\n"
                    f"- Количество позиций: {ocr_meta.get('positions_count') or '—'}\n"
                )
 
            from bot.utils.simple_time import get_time_context
            time_context = get_time_context()
            portfolio_payload = json.dumps(portfolio_data, ensure_ascii=False, indent=2, default=str)
            requirements = (
                "ТРЕБОВАНИЯ К ОТВЕТУ:\n"
                "1. Сделай насыщенное резюме (стоимость, распределение, доли ТОП-5, суммарная YTM, дюрация).\n"
                "2. Проанализируй ключевые позиции: количество, цена (объясни, что это % номинала, если так), YTM, сектор, статус торгов, доля в портфеле.\n"
                "3. Используй календарь выплат: ближайшие купоны/амортизации, суммарные потоки, возможные кассовые риски и рекомендации.\n"
                "4. Приведи важные новости и их влияние на портфель/конкретные бумаги.\n"
                "5. Дай конкретные действия (держать/сократить/докупать) с обоснованием и рисками.\n"
                "6. Пиши по-русски, опирайся только на JSON, отмечай, если данных нет.\n"
            )
 
            user_message = f"""
 Проанализируй портфель строго по промту v16 (файл portfolio_analyze_v14.txt).
 
 КОНТЕКСТ ВРЕМЕНИ:
 {time_context}
 
-{meta_block}СТРУКТУРИРОВАННЫЕ ДАННЫЕ ПОРТФЕЛЯ:
-{portfolio_data}
-
-Требования:
-- следуй всем инструкциям промта v16;
-- обязательно укажи в ответе название портфеля, его общую стоимость и количество бумаг, если значения присутствуют в OCR-метаданных;
-- начни ответ с текущего времени из блока времени.
+{meta_block}{requirements}
 
 СТРУКТУРИРОВАННЫЕ ДАННЫЕ ПОРТФЕЛЯ (JSON):
 {portfolio_payload}
 
 Используй все доступные цифры, поясняй выводы и делай рекомендации, полезные инвестору.
            """
 
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=3000,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to generate AI analysis: {e}")
            return "Ошибка при генерации AI анализа"


portfolio_analyzer = PortfolioAnalyzer()