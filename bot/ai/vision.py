import base64
import io
import json
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from bot.core.config import config
from bot.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractedPosition:
    raw_name: str
    raw_ticker: Optional[str] = None
    raw_isin: Optional[str] = None
    raw_type: Optional[str] = None
    quantity: Optional[float] = None
    quantity_unit: Optional[str] = None
    confidence: float = 0.0
    hints: Optional[Dict[str, Any]] = None


@dataclass
class OCRAccount:
    account_id: str
    account_name: Optional[str]
    portfolio_value: Optional[float]
    currency: Optional[str]
    positions: List[ExtractedPosition]
    positions_count: Optional[int] = None
    daily_change_value: Optional[float] = None
    daily_change_percent: Optional[float] = None
    cash_balance: Optional["CashPosition"] = None


@dataclass
class CashPosition:
    account_id: str
    raw_name: str
    amount: Optional[float]
    currency: Optional[str]


@dataclass
class OCRResult:
    accounts: List[OCRAccount]
    cash_positions: List[CashPosition]
    reason: str
    is_portfolio: bool = True
    portfolio_name: Optional[str] = None
    portfolio_value: Optional[float] = None
    currency: Optional[str] = None
    positions_count: Optional[int] = None
    warnings: Optional[List[str]] = None


class VisionProcessor:
    
    def __init__(self):
        self.client = openai.OpenAI(
            base_url="https://neuroapi.host/v1",
            api_key=config.openai_api_key
        )
        self.model = config.vision_model
    
    def extract_positions_for_ingest(self, image_bytes: bytes) -> OCRResult:
        """Extract positions from portfolio image for ingest only.

        Args:
            image_bytes: Image bytes

        Returns:
            OCRResult with extracted positions
        """
        try:
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            if config.feature_ocr_v3:
                prompt = self._load_ocr_prompt_v3()
                parser = self._parse_ocr_response_v3
            elif config.feature_ocr_v2:
                prompt = self._load_ocr_prompt_v2()
                parser = self._parse_ocr_response_v2
            else:
                prompt = self._load_ocr_prompt_v1()
                parser = self._parse_ocr_response_v1

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )

            content = response.choices[0].message.content
            return parser(content)

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)
    
    def _get_ocr_prompt(self) -> str:
        if config.feature_ocr_v3:
            return self._load_ocr_prompt_v3()
        elif config.feature_ocr_v2:
            return self._load_ocr_prompt_v2()
        else:
            return self._load_ocr_prompt_v1()
    
    def _load_ocr_prompt_v1(self) -> str:
        return """
Ты — эксперт по распознаванию инвестиционных портфелей. Проанализируй изображение и извлеки структурированные данные портфеля.

ЗАДАЧА:
1) Определить, является ли изображение скриншотом инвестиционного портфеля.
2) Извлечь список ценных бумаг (акции, облигации, фонды) с максимально возможными атрибутами.
3) Извлечь метаданные портфеля: название/имя портфеля (если указано), общую стоимость портфеля и валюту, количество бумаг.

ФОРМАТ ОТВЕТА (строго JSON):
{
  "is_portfolio": true/false,
  "portfolio_name": "Имя портфеля, если видно, иначе null",
  "portfolio_value": 123456.78,  // число, если видно, иначе null
  "currency": "RUB",           // валютный код, если видно, иначе null
  "positions_count": 12,        // целое число (если не видно, укажи длину массива positions)
  "positions": [
    {
      "raw_name": "полное название бумаги",
      "raw_ticker": "тикер если виден",
      "raw_isin": "ISIN если виден",
      "raw_type": "акция/облигация/фонд если понятно",
      "quantity": 10,                 // если видно, иначе null
      "quantity_unit": "шт"/"лоты"/null,
      "confidence": 0.95
    }
  ],
  "reason": "ok" или "not_portfolio"
}

ПРАВИЛА:
1. is_portfolio = false, если это НЕ портфель (золото, валюта, депозиты, недвижимость и т.п.)
2. Извлекай ТОЛЬКО ценные бумаги (акции, облигации, ETF, ПИФы)
3. portfolio_name — заголовок/имя счёта/портфеля, если присутствует (например, «Брокерский счёт», «Инвесткопилка», собственное название).
4. portfolio_value — общая стоимость портфеля в числовом виде; currency — код валюты (RUB, USD, EUR).
5. Если явно не указано количество бумаг, positions_count = длина массива positions.
6. raw_name — полное название как видно на изображении; raw_ticker — в верхнем регистре; raw_isin — как на изображении.
7. quantity/quantity_unit указывать только если они видны.
8. reason = "not_portfolio" если не портфель, иначе "ok".

 АДАПТИВНОСТЬ ПО БРОКЕРАМ (обязательно учесть разные UI):
 - Tinkoff (Тинькофф): ключевые слова «Тинькофф», «Инвестиции», «Итог по счёту», «Портфель»; сумма часто с пробелами как разделителями тысяч и символом «₽».
 - ВТБ: «ВТБ Мои инвестиции», «Стоимость портфеля», «Итого», «Брокерский счёт»; может быть «₽», «$», «€».
 - Сбер: «СберИнвест», «Портфель», «Итого по счёту», «Счёт»; сумма в формате «1 234 567 ₽».
 - Другие: ищи заголовки разделов «Портфель», «Счёт», «Итого», «Баланс», «Стоимость портфеля».

 ВЫДЕЛЕНИЕ НАЗВАНИЯ ПОРТФЕЛЯ:
 - Брать ближайший к верхней части экрана заголовок/подпись счёта: «Брокерский счёт», «Инвесткопилка», пользовательские имена (например, «Пассивный»).
 - Если явно указано имя счёта — вернуть его. Если нет — вернуть null.

 ВЫДЕЛЕНИЕ ОБЩЕЙ СТОИМОСТИ:
 - Ищем подписи: «Итог по счёту», «Стоимость портфеля», «Итого», «Баланс».
 - Нормализуй число: убрать пробелы/неразрывные пробелы, заменить запятую на точку в дробной части.
 - currency вернуть как «RUB», «USD» или «EUR» по символу (₽ → RUB, $ → USD, € → EUR). Если буквенный код (RUB/USD/EUR) — использовать его.

 ТИКЕРЫ И КОЛИЧЕСТВА:
 - raw_ticker — только буквенно-цифровой идентификатор (например, SBER, GAZP, LKOH, TCSG). Не включать доп. символы.
 - Количество: распознавать форматы «10 шт», «2 лота», «1,5 шт», «x10»; quantity — число, quantity_unit — "шт" или "лоты".
 - Если количество/единицы не видны — оставить null.

ПРИМЕРЫ НЕ-ПОРТФЕЛЕЙ:
- Золото, серебро, драгметаллы
- Валюты (рубли, доллары, евро)
- Депозиты, вклады
- Недвижимость
- Криптовалюты
- Товары (нефть, газ)

ПРИМЕРЫ ПОРТФЕЛЕЙ:
- Акции компаний
- Облигации (государственные, корпоративные)
- ETF, ПИФы
- Депозитарные расписки

Отвечай ТОЛЬКО валидным JSON без дополнительного текста.
"""
    
    def _load_ocr_prompt_v3(self) -> str:
        try:
            with open("bot/ai/ocr_prompt_portfolio_v3.txt", "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            logger.warning("OCR prompt v3 not found, falling back to v2")
            return self._load_ocr_prompt_v2()
    
    def _load_ocr_prompt_v2(self) -> str:
        try:
            import os
            prompt_path = os.path.join(os.path.dirname(__file__), "ocr_prompt_portfolio_v2.txt")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to load OCR prompt v2: {e}")
            return self._load_ocr_prompt_v1()
    
    def _parse_ocr_response_v2(self, content: str) -> OCRResult:
        try:
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                    except json.JSONDecodeError:
                        logger.error("Failed to parse JSON even with regex extraction")
                        return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)
                else:
                    logger.error("No JSON block found in response")
                    return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)
            
            required_keys = ["accounts", "reason"]
            for key in required_keys:
                if key not in data:
                    logger.warning(f"Missing required key '{key}' in OCR response, using defaults")
                    if key == "accounts":
                        data[key] = []
                    elif key == "reason":
                        data[key] = "ok"
 
            accounts = []
            for acc in data.get('accounts', []):
                positions = []
                for pos_data in acc.get('positions', []):
                    positions.append(ExtractedPosition(
                        raw_name=pos_data.get('raw_name', ''),
                        raw_ticker=pos_data.get('raw_ticker'),
                        raw_isin=pos_data.get('raw_isin'),
                        raw_type=pos_data.get('raw_type'),
                        quantity=pos_data.get('quantity'),
                        quantity_unit=pos_data.get('quantity_unit'),
                        confidence=pos_data.get('confidence', 0.0),
                        hints=pos_data.get('hints')
                    ))
                account = OCRAccount(
                    account_id=acc.get('account_id') or 'default',
                    account_name=acc.get('account_name'),
                    portfolio_value=acc.get('portfolio_value'),
                    currency=acc.get('currency'),
                    positions=positions,
                    positions_count=acc.get('positions_count') or len(positions)
                )
                accounts.append(account)

            cash_positions = []
            for cash in data.get('cash_positions', []):
                cash_positions.append(CashPosition(
                    account_id=cash.get('account_id') or 'default',
                    raw_name=cash.get('raw_name', ''),
                    amount=cash.get('amount'),
                    currency=cash.get('currency')
                ))

            return OCRResult(
                accounts=accounts,
                cash_positions=cash_positions,
                reason=data.get('reason', 'ok'),
                is_portfolio=data.get('is_portfolio', bool(accounts)),
                portfolio_name=data.get('portfolio_name'),
                portfolio_value=data.get('portfolio_value'),
                currency=data.get('currency'),
                positions_count=sum(acc.positions_count or len(acc.positions) for acc in accounts)
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OCR response v2: {e}")
            return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)
    
    def _parse_ocr_response(self, content: str) -> OCRResult:
        if config.feature_ocr_v3:
            return self._parse_ocr_response_v3(content)
        elif config.feature_ocr_v2:
            return self._parse_ocr_response_v2(content)
        else:
            return self._parse_ocr_response_v1(content)
    
    def _parse_ocr_response_v3(self, content: str) -> OCRResult:
        try:
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            # Log the raw content for debugging
            logger.info(f"OCR v3 raw content length: {len(content)}")
            logger.info(f"OCR v3 content preview: {content[:500]}...")
            
            # Save full content to file for debugging
            with open("/tmp/ocr_debug.json", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Full OCR content saved to /tmp/ocr_debug.json")

            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OCR v3 response: {e}")
                logger.error(f"Content around error position: {content[max(0, e.pos-50):e.pos+50]}")
                
                # Try to find JSON in the content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        data = json.loads(json_match.group())
                        logger.info("Successfully parsed JSON after regex extraction")
                    except json.JSONDecodeError as e2:
                        logger.error(f"Failed to parse extracted JSON: {e2}")
                        return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False, warnings=["json_parse_failed"])
                else:
                    logger.error("No valid JSON found in OCR response")
                    return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False, warnings=["json_parse_failed"])

            required_keys = ["accounts", "reason"]
            if not all(key in data for key in required_keys):
                logger.error("Missing required keys in OCR response")
                return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False, warnings=["missing_required_keys"])

            warnings = data.get("warnings") or []

            accounts = []
            for acc in data.get("accounts", []):
                extracted = []
                for pos_data in acc.get("positions", []):
                    try:
                        extracted.append(ExtractedPosition(
                            raw_name=pos_data.get("raw_name", ""),
                            raw_ticker=pos_data.get("raw_ticker"),
                            raw_isin=pos_data.get("raw_isin"),
                            raw_type=pos_data.get("raw_type"),
                            quantity=pos_data.get("quantity"),
                            quantity_unit=pos_data.get("quantity_unit"),
                            confidence=pos_data.get("confidence", 0.0),
                            hints=pos_data.get("hints")
                        ))
                    except Exception as e:
                        logger.warning(f"Failed to parse position: {e}")
                account_id = acc.get("account_id") or "default"
                account = OCRAccount(
                    account_id=account_id,
                    account_name=acc.get("account_name"),
                    portfolio_value=acc.get("portfolio_value"),
                    currency=acc.get("currency"),
                    positions=extracted,
                    positions_count=acc.get("positions_count") or len(extracted),
                    daily_change_value=acc.get("daily_change_value"),
                    daily_change_percent=acc.get("daily_change_percent"),
                    cash_balance=self._parse_cash_balance(acc.get("cash_balance"), account_id)
                )
                accounts.append(account)

            cash_positions = []
            for cash in data.get('cash_positions', []):
                cash_positions.append(CashPosition(
                    account_id=cash.get('account_id') or 'default',
                    raw_name=cash.get('raw_name', ''),
                    amount=cash.get('amount'),
                    currency=cash.get('currency')
                ))

            total_positions = data.get("positions_count")
            if total_positions is None:
                total_positions = sum(acc.positions_count or len(acc.positions) for acc in accounts)

            return OCRResult(
                accounts=accounts,
                cash_positions=cash_positions,
                reason=data.get("reason", "ok"),
                is_portfolio=data.get("is_portfolio", bool(accounts)),
                portfolio_name=data.get("portfolio_name"),
                portfolio_value=data.get("portfolio_value"),
                currency=data.get("currency"),
                positions_count=total_positions,
                warnings=warnings
            )
        except Exception as e:
            logger.error(f"Failed to parse OCR v3 response: {e}")
            return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False, warnings=["parse_exception"])

    def _parse_cash_balance(self, cash_payload: Optional[Dict[str, Any]], account_id: str) -> Optional[CashPosition]:
        if not cash_payload or not isinstance(cash_payload, dict):
            return None
        return CashPosition(
            account_id=account_id,
            raw_name=cash_payload.get("raw_name", "Cash"),
            amount=cash_payload.get("amount"),
            currency=cash_payload.get("currency")
        )
    
    def _parse_ocr_response_v1(self, content: str) -> OCRResult:
        try:
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            data = json.loads(content)

            accounts = []
            for acc in data.get('accounts', []):
                extracted = []
                for pos_data in acc.get('positions', []):
                    extracted.append(ExtractedPosition(
                        raw_name=pos_data.get('raw_name', ''),
                        raw_ticker=pos_data.get('raw_ticker'),
                        raw_isin=pos_data.get('raw_isin'),
                        raw_type=pos_data.get('raw_type'),
                        quantity=pos_data.get('quantity'),
                        quantity_unit=pos_data.get('quantity_unit'),
                        confidence=pos_data.get('confidence', 0.0),
                        hints=pos_data.get('hints')
                    ))
                accounts.append(OCRAccount(
                    account_id=acc.get('account_id') or 'default',
                    account_name=acc.get('account_name'),
                    portfolio_value=acc.get('portfolio_value'),
                    currency=acc.get('currency'),
                    positions=extracted,
                    positions_count=acc.get('positions_count') or len(extracted)
                ))

            cash_positions = []
            for cash in data.get('cash_positions', []):
                cash_positions.append(CashPosition(
                    account_id=cash.get('account_id') or 'default',
                    raw_name=cash.get('raw_name', ''),
                    amount=cash.get('amount'),
                    currency=cash.get('currency')
                ))

            return OCRResult(
                accounts=accounts,
                cash_positions=cash_positions,
                reason=data.get('reason', 'ok'),
                is_portfolio=data.get('is_portfolio', bool(accounts)),
                portfolio_name=data.get('portfolio_name'),
                portfolio_value=data.get('portfolio_value'),
                currency=data.get('currency'),
                positions_count=sum(acc.positions_count or len(acc.positions) for acc in accounts)
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OCR response: {e}")
            return OCRResult(accounts=[], cash_positions=[], reason="error", is_portfolio=False)


vision_processor = VisionProcessor()