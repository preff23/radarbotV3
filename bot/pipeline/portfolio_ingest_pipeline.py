import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from bot.ai.vision import vision_processor, ExtractedPosition, OCRResult
from bot.utils.normalize import (
    normalize_security_name, is_security_name, extract_ticker_from_name,
    extract_isin_from_name, generate_normalized_key,
    deduplicate_securities, normalize_security_series, normalize_security_type
)
from bot.providers.aggregator import market_aggregator
from bot.core.db import db_manager, PortfolioHoldingV2, PortfolioCashPosition
from bot.core.logging import get_logger
from bot.utils.bond_reference import load_bond_reference
from typing import Set

logger = get_logger(__name__)


@dataclass
class IngestResult:
    added: int
    merged: int
    positions: List[Dict[str, Any]]
    reason: str
    raw_detected: int = 0
    normalized: int = 0
    resolved: int = 0


class PortfolioIngestPipeline:
    
    def __init__(self):
        self.vision_processor = vision_processor
        self.market_aggregator = market_aggregator
        self.db_manager = db_manager
        self._processing_locks = {}
        self._bond_reference = load_bond_reference()
    
    async def ingest_from_photo(self, phone_number: str, image_bytes: bytes) -> IngestResult:
        """Ingest portfolio from photo.

        Args:
            telegram_id: Telegram user ID
            image_bytes: Image bytes

        Returns:
            IngestResult with processing results
        """
        if phone_number not in self._processing_locks:
            self._processing_locks[phone_number] = asyncio.Lock()
        
        async with self._processing_locks[phone_number]:
            try:
                logger.info(f"Starting photo processing for user {phone_number}")
                
                user = self.db_manager.get_user_by_phone(phone_number)
                if not user:
                    logger.error(f"User with phone {phone_number} not found")
                    return IngestResult(
                        added=0,
                        merged=0,
                        positions=[],
                        reason="user_not_found",
                        raw_detected=0,
                        normalized=0,
                        resolved=0
                    )
                
                user_id = user.id
                
                ocr_result = await self._extract_positions(image_bytes)
                if not ocr_result or not getattr(ocr_result, "accounts", None):
                    logger.warning("OCR did not return accounts")
                    return IngestResult(added=0, merged=0, positions=[], reason="error", raw_detected=0, normalized=0, resolved=0)

                if getattr(ocr_result, "warnings", None):
                    logger.info(f"OCR returned warnings: {ocr_result.warnings}")

                processed_accounts, raw_detected = await self._prepare_accounts_payload(ocr_result)
                if not processed_accounts:
                    logger.warning("No valid accounts detected after OCR normalization")
                    return IngestResult(
                        added=0,
                        merged=0,
                        positions=[],
                        reason="no_valid_securities",
                        raw_detected=raw_detected,
                        normalized=0,
                        resolved=0
                    )

                resolve_result = await self._resolve_accounts(processed_accounts)
                normalized_count = resolve_result["normalized_count"]
                resolved_count = resolve_result["resolved_count"]

                save_result = await self._save_accounts(user_id, resolve_result)
                
                logger.info(f"Photo processing completed for user {phone_number}: added={save_result['added']}, merged={save_result['merged']}, total_active={save_result.get('total_active')}")

                # Save OCR portfolio meta for later analysis rendering
                try:
                    ocr_meta = {
                        "portfolio_name": getattr(ocr_result, "portfolio_name", None),
                        "portfolio_value": getattr(ocr_result, "portfolio_value", None),
                        "currency": getattr(ocr_result, "currency", None),
                        "positions_count": getattr(ocr_result, "positions_count", None),
                        "warnings": getattr(ocr_result, "warnings", None)
                    }
                    self.db_manager.set_portfolio_meta(user_id, ocr_meta)
                    logger.info(f"Saved OCR portfolio meta for user {phone_number}: {ocr_meta}")
                except Exception as meta_err:
                    logger.warning(f"Failed to save OCR portfolio meta: {meta_err}")

                return IngestResult(
                    added=save_result["added"],
                    merged=save_result["merged"],
                    positions=save_result["positions"],
                    reason="ok",
                    raw_detected=raw_detected,
                    normalized=normalized_count,
                    resolved=resolved_count
                )
                
            except Exception as e:
                logger.error(f"Portfolio ingest failed for user {phone_number}: {e}", exc_info=True)
                return IngestResult(
                    added=0,
                    merged=0,
                    positions=[],
                    reason="error",
                    raw_detected=raw_detected if 'raw_detected' in locals() else 0,
                    normalized=0,
                    resolved=0
                )
    
    async def _extract_positions(self, image_bytes: bytes) -> OCRResult:
        try:
            result = self.vision_processor.extract_positions_for_ingest(image_bytes)
            if not result or not getattr(result, "accounts", None):
                logger.error("OCR returned no accounts")
                return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)
            return result
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)
    
    async def _normalize_positions(self, positions: List[ExtractedPosition]) -> List[Dict[str, Any]]:
        normalized_positions = []
        filtered_count = 0
        
        for position in positions:
            hints = position.hints or {}
            
            if hints.get("norm_name"):
                normalized_name = hints["norm_name"]
            else:
                series_fixed_name = normalize_security_series(position.raw_name)
                normalized_name = normalize_security_name(series_fixed_name)
            
            if not normalized_name:
                logger.warning(f"Position filtered: no normalized name for '{position.raw_name}'")
                filtered_count += 1
                continue
            
            if not is_security_name(normalized_name):
                logger.warning(f"Position filtered: not a security name '{normalized_name}' (original: '{position.raw_name}')")
                filtered_count += 1
                continue
            
            ticker = hints.get("norm_ticker") or position.raw_ticker or extract_ticker_from_name(position.raw_name)
            isin = hints.get("norm_isin") or position.raw_isin or extract_isin_from_name(position.raw_name)
            
            normalized_type = normalize_security_type(position.raw_type)
            
            normalized_key = generate_normalized_key(normalized_name, ticker, isin)
            if not normalized_key:
                normalized_key = f"RAW:{position.raw_name}"
            
            normalized_position = {
                "raw_name": position.raw_name,
                "raw_ticker": position.raw_ticker,
                "raw_isin": position.raw_isin,
                "raw_type": position.raw_type,
                "raw_quantity": position.quantity,
                "raw_quantity_unit": position.quantity_unit,
                "confidence": position.confidence,
                "hints": hints,
                "normalized_name": normalized_name,
                "normalized_key": normalized_key,
                "ticker": ticker,
                "isin": isin,
                "security_type": normalized_type,
                "emitter_guess": hints.get("emitter_guess"),
                "detected_keywords": hints.get("detected_keywords", []),
                "series_fix_applied": hints.get("series_fix_applied", False)
            }

            if self._bond_reference:
                try:
                    if self._bond_reference.enrich_position(normalized_position):
                        logger.debug(
                            "Enriched position using bond reference: %s",
                            normalized_position.get("normalized_name") or normalized_position.get("isin")
                        )
                except Exception as enrich_err:
                    logger.warning(f"Failed to enrich position via bond reference: {enrich_err}")
            
            normalized_positions.append(normalized_position)
        
        logger.info(f"Normalized {len(normalized_positions)} positions, filtered {filtered_count}")
        
        deduplicated = deduplicate_securities(normalized_positions)
        logger.info(f"Deduplicated from {len(normalized_positions)} to {len(deduplicated)} positions")
        
        return deduplicated
    
    async def _resolve_securities(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        resolved_positions = []
        skipped_count = 0
        
        logger.info(f"Resolving {len(positions)} securities")
        
        tasks = [self._resolve_single_security(pos) for pos in positions]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to resolve position {i}: {result}")
                skipped_count += 1
            elif result is not None:
                resolved_positions.append(result)
                logger.info(f"Position {i+1} resolved successfully")
            else:
                skipped_count += 1
                logger.warning(f"Position {i+1} not found in any provider - SKIPPED")
        
        logger.info(f"Resolution complete: {len(resolved_positions)} resolved, {skipped_count} skipped")
        return resolved_positions
    
    async def _resolve_single_security(self, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            queries_to_try = []
            
            if position.get("raw_name"):
                queries_to_try.append(position["raw_name"])
            
            if position.get("ticker"):
                queries_to_try.append(position["ticker"])
            
            if position.get("isin"):
                queries_to_try.append(position["isin"])
            
            if position.get("normalized_name"):
                queries_to_try.append(position["normalized_name"])
            
            logger.info(f"Resolving '{position.get('raw_name', 'Unknown')}' with queries: {queries_to_try}")
            
            snapshot = None
            successful_query = None
            
            for query in queries_to_try:
                if not query:
                    continue
                    
                try:
                    snapshots = await self.market_aggregator.get_snapshot_for(query)
                    if snapshots and snapshots[0]:
                        snapshot = snapshots[0]
                        successful_query = query
                        logger.info(f"Found match for '{query}' via {snapshot.provider}")
                        break
                except Exception as e:
                    logger.warning(f"Query '{query}' failed: {e}")
                    continue
            
            if snapshot:
                security_type = snapshot.security_type
                
                # Force share type for known stock tickers
                ticker = snapshot.ticker or position.get("ticker", "").upper()
                if ticker in ["GAZP", "SBER", "LKOH", "ROSN", "NVTK", "MAGN", "YNDX", "TCSG", "VKCO", "AFLT"]:
                    security_type = "share"
                    logger.info(f"Force determined {ticker} as share based on ticker")
                
                if position.get("security_type") == "share" and snapshot.security_type == "bond":
                    security_type = "share"
                    logger.info(f"Keeping manual ticker '{position.get('raw_name')}' as share despite bond match")
                
                position.update({
                    "secid": snapshot.secid,
                    "ticker": snapshot.ticker or position.get("ticker"),
                    "isin": snapshot.isin or position.get("isin"),
                    "security_type": security_type,
                    "provider": snapshot.provider,
                    "provider_data": {
                        "last_price": snapshot.last_price,
                        "change_day_pct": snapshot.change_day_pct,
                        "trading_status": snapshot.trading_status,
                        "currency": snapshot.currency,
                        "ytm": snapshot.ytm,
                        "sector": snapshot.sector,
                        "resolved_query": successful_query
                    }
                })
                logger.info(f"Successfully resolved '{position.get('raw_name')}' -> {snapshot.name} ({snapshot.provider})")
                return position
            else:
                logger.warning(f"Could not resolve '{position.get('raw_name')}' with any query via providers")
                # fallback to bond reference data if available
                reference_entry = None
                try:
                    if self._bond_reference:
                        # Сначала пробуем точный поиск
                        reference_entry = self._bond_reference.match(
                            isin=position.get("isin"),
                            ticker=position.get("ticker"),
                            name=position.get("normalized_name") or position.get("raw_name")
                        )
                        
                        # Если не найдено, пробуем fuzzy поиск
                        if not reference_entry:
                            normalized_name = position.get("normalized_name") or position.get("raw_name")
                            if normalized_name:
                                reference_entry = self._bond_reference.match_fuzzy(normalized_name, threshold=0.75)
                                if reference_entry:
                                    logger.info(f"Fuzzy fallback match found for '{position.get('raw_name')}' -> '{reference_entry.name}'")
                except Exception as ref_err:
                    logger.warning(f"Reference lookup failed for '{position.get('raw_name')}': {ref_err}")

                if reference_entry:
                    logger.info(f"Fallback reference match used for '{position.get('raw_name')}' -> '{reference_entry.name}'")
                    position.update({
                        "secid": reference_entry.ticker or reference_entry.isin,
                        "ticker": reference_entry.ticker or position.get("ticker"),
                        "isin": reference_entry.isin or position.get("isin"),
                        "provider": position.get("provider") or "bond_reference",
                        "provider_data": {
                            "resolved_query": "bond_reference",
                            "source": reference_entry.sources,
                            "fallback": True,
                        }
                    })
                    return position

                logger.warning(f"Could not resolve '{position.get('raw_name')}' with any query - SKIPPING")
                logger.warning(f"Available queries were: {queries_to_try}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to resolve security '{position.get('raw_name', 'Unknown')}': {e}")
            return None
    
    async def _save_accounts(self, user_id: int, resolve_result: Dict[str, Any]) -> Dict[str, Any]:
        session = self.db_manager.SessionLocal()
        try:
            added_count = 0
            merged_count = 0
            saved_positions = []

            for account_payload in resolve_result["accounts"]:
                account_id = account_payload["account_id"]
                account_info = account_payload["account_info"]
                positions = account_payload["positions"]
                cash_entries = account_payload.get("cash", [])
                cash_balance = account_payload.get("cash_balance")

                logger.info("Saving account %s for user %s", account_id, user_id)
                db_account = self.db_manager.get_or_create_account(
                    user_id=user_id,
                    account_id=account_id,
                    session=session,
                    account_name=account_info.get("account_name"),
                    currency=account_info.get("currency"),
                    portfolio_value=account_info.get("portfolio_value")
                )

                if account_info.get("daily_change_value") is not None or account_info.get("daily_change_percent") is not None:
                    logger.info(
                        f"Account {account_id} change: value={account_info.get('daily_change_value')} percent={account_info.get('daily_change_percent')}"
                    )

                active_ids: Set[int] = set()

                for position in positions:
                    holding = self.db_manager.add_holding(
                        user_id=user_id,
                        raw_name=position["raw_name"],
                        normalized_name=position["normalized_name"],
                        normalized_key=position["normalized_key"],
                        account_internal_id=db_account.id,
                        session=session,
                        raw_ticker=position.get("raw_ticker"),
                        raw_isin=position.get("raw_isin"),
                        raw_type=position.get("raw_type"),
                        raw_quantity=position.get("raw_quantity"),
                        raw_quantity_unit=position.get("raw_quantity_unit"),
                        confidence=position.get("confidence"),
                        secid=position.get("secid"),
                        ticker=position.get("ticker"),
                        isin=position.get("isin"),
                        security_type=position.get("security_type"),
                        provider=position.get("provider"),
                        provider_data=position.get("provider_data")
                    )

                    active_ids.add(holding.id)

                    time_diff = abs((holding.created_at - holding.updated_at).total_seconds())
                    if time_diff < 1.0:
                        added_count += 1
                    else:
                        merged_count += 1

                    saved_positions.append({
                        "id": holding.id,
                        "name": holding.normalized_name,
                        "ticker": holding.ticker,
                        "isin": holding.isin,
                        "type": holding.security_type,
                        "provider": holding.provider,
                        "account_id": account_id
                    })

                self.db_manager.deactivate_missing_holdings(
                    user_id=user_id,
                    account_internal_id=db_account.id,
                    active_ids=active_ids,
                    session=session
                )

                self._apply_cash_updates(
                    session=session,
                    user_id=user_id,
                    account_internal_id=db_account.id,
                    cash_entries=cash_entries,
                    cash_balance=cash_balance
                )

            session.commit()

            total_active = session.query(PortfolioHoldingV2).filter(
                PortfolioHoldingV2.user_id == user_id,
                PortfolioHoldingV2.is_active == True
            ).count()

            return {
                "added": added_count,
                "merged": merged_count,
                "positions": saved_positions,
                "total_active": total_active
            }
        finally:
            session.close()

    async def add_manual_ticker(self, phone_number: str, ticker: str) -> IngestResult:
        """Add security manually by ticker.

        Args:
            user_id: User ID
            ticker: Security ticker

        Returns:
            IngestResult with processing results
        """
        try:
            position = {
                "raw_name": ticker,
                "raw_ticker": ticker,
                "raw_isin": None,
                "raw_type": "share",
                "confidence": 1.0,
                "normalized_name": normalize_security_name(ticker),
                "normalized_key": generate_normalized_key(ticker, ticker, None),
                "ticker": ticker,
                "isin": None,
                "security_type": "share"
            }
            resolved_positions = await self._resolve_securities([position])
            user = self.db_manager.get_user_by_phone(phone_number)
            if not user:
                logger.error(f"User with phone {phone_number} not found")
                return IngestResult(
                    added=0,
                    merged=0,
                    positions=[],
                    reason="user_not_found",
                    raw_detected=0,
                    normalized=0,
                    resolved=0
                )
 
            resolve_result = {
                "accounts": [{
                    "account_id": "manual",
                    "account_info": {
                        "account_name": "Manual",
                        "currency": None,
                        "portfolio_value": None
                    },
                    "positions": resolved_positions,
                    "cash": [],
                    "cash_balance": None
                }],
                "normalized_count": len(resolved_positions),
                "resolved_count": len(resolved_positions)
            }

            save_result = await self._save_accounts(user.id, resolve_result)
            
            return IngestResult(
                added=save_result["added"],
                merged=save_result["merged"],
                positions=save_result["positions"],
                reason="ok",
                raw_detected=1,
                normalized=len(resolved_positions),
                resolved=len(resolved_positions)
            )
            
        except Exception as e:
            logger.error(f"Manual ticker addition failed for user {phone_number}: {e}")
            return IngestResult(
                added=0,
                merged=0,
                positions=[],
                reason="error",
                raw_detected=0,
                normalized=0,
                resolved=0
            )

    async def _prepare_accounts_payload(self, ocr_result: OCRResult) -> Tuple[List[Dict[str, Any]], int]:
        prepared_accounts = []
        total_raw_detected = 0

        cash_by_account: Dict[str, List[Dict[str, Any]]] = {}
        for cash in getattr(ocr_result, "cash_positions", []) or []:
            account_id = cash.account_id or "default"
            cash_by_account.setdefault(account_id, []).append({
                "raw_name": cash.raw_name,
                "amount": cash.amount,
                "currency": cash.currency
            })

        for account in ocr_result.accounts:
            account_id = account.account_id or "default"
            positions_list = account.positions or []
            normalized_positions = await self._normalize_positions(positions_list)
            total_raw_detected += len(positions_list)

            cash_entries = cash_by_account.get(account_id, [])

            if not normalized_positions and not cash_entries:
                continue

            prepared_accounts.append({
                "account": account,
                "normalized_positions": normalized_positions,
                "cash_entries": cash_entries
            })

        return prepared_accounts, total_raw_detected

    async def _resolve_accounts(self, accounts_payload: List[Dict[str, Any]]) -> Dict[str, Any]:
        resolved_accounts = []
        normalized_count = 0
        resolved_count = 0

        for payload in accounts_payload:
            account = payload["account"]
            normalized_positions = payload["normalized_positions"]
            normalized_count += len(normalized_positions)

            resolved_positions = await self._resolve_securities(normalized_positions)
            resolved_count += len(resolved_positions)

            account_id = getattr(account, "account_id", None) or "default"
            account_info = {
                "account_name": getattr(account, "account_name", None),
                "currency": getattr(account, "currency", None),
                "portfolio_value": getattr(account, "portfolio_value", None),
                "daily_change_value": getattr(account, "daily_change_value", None),
                "daily_change_percent": getattr(account, "daily_change_percent", None)
            }

            resolved_accounts.append({
                "account_id": account_id,
                "account_info": account_info,
                "positions": resolved_positions,
                "cash": payload.get("cash_entries", []),
                "cash_balance": account.cash_balance
            })

        return {
            "accounts": resolved_accounts,
            "normalized_count": normalized_count,
            "resolved_count": resolved_count
        }

    def _apply_cash_updates(self, session: Any, user_id: int, account_internal_id: Optional[int], cash_entries: List[Dict[str, Any]], cash_balance: Optional[Any]):
        self.db_manager.delete_account_cash(user_id, account_internal_id, session)

        normalized_entries = list(cash_entries)
        if cash_balance:
            normalized_entries.append({
                "raw_name": cash_balance.raw_name,
                "amount": cash_balance.amount,
                "currency": cash_balance.currency
            })

        for entry in normalized_entries:
            cash = PortfolioCashPosition(
                user_id=user_id,
                account_internal_id=account_internal_id,
                raw_name=entry.get("raw_name") or "cash",
                amount=entry.get("amount"),
                currency=entry.get("currency")
            )
            session.add(cash)


ingest_pipeline = PortfolioIngestPipeline()