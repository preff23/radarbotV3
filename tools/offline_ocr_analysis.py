import asyncio
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bot.pipeline.portfolio_ingest_pipeline import ingest_pipeline
from bot.analytics.portfolio_analyzer import portfolio_analyzer
from bot.core.db import db_manager
from bot.utils.corpbonds_client import CorpBondsClient  # подготовка к скачиванию справочников

TEST_PHOTO_DIR = Path("photo")
TEST_PHONE = "+7000000999"


async def ensure_test_user():
    return db_manager.ensure_user(TEST_PHONE, username="offline_test")


def load_photo_bytes(filename: str) -> bytes:
    photo_path = TEST_PHOTO_DIR / filename
    if not photo_path.exists():
        raise FileNotFoundError(f"Файл {photo_path} не найден")
    with open(photo_path, "rb") as f:
        return f.read()


async def process_photo(filename: str):
    user = await ensure_test_user()
    image_bytes = load_photo_bytes(filename)
    ingest_result = await ingest_pipeline.ingest_from_photo(TEST_PHONE, image_bytes)
    user = db_manager.get_user_by_phone(TEST_PHONE)
    ocr_meta = db_manager.get_portfolio_meta(user.id) if user else {}
    return ingest_result, ocr_meta


def clear_user_state():
    user = db_manager.get_user_by_phone(TEST_PHONE)
    if user:
        db_manager.clear_user_holdings(user.id)
        db_manager.clear_portfolio_meta(user.id)


async def run_analysis():
    user = db_manager.get_user_by_phone(TEST_PHONE)
    if not user:
        raise RuntimeError("Тестовый пользователь не найден")
    analysis = await portfolio_analyzer.run_analysis(user.id)
    return analysis


async def main():
    files = sorted([p.name for p in TEST_PHOTO_DIR.glob("*.jpeg")])
    if not files:
        print("В каталоге photo нет jpeg-файлов для теста")
        return

    clear_user_state()

    last_meta = {}

    for filename in files:
        print(f"\n=== Обработка {filename} ===")
        ingest_result, ocr_meta = await process_photo(filename)
        print(json.dumps({
            "reason": ingest_result.reason,
            "added": ingest_result.added,
            "merged": ingest_result.merged,
            "positions": ingest_result.positions
        }, ensure_ascii=False, indent=2, default=str))
        print("OCR meta:", json.dumps(ocr_meta, ensure_ascii=False, default=str))
        if ocr_meta.get("portfolio_value"):
            last_meta = ocr_meta

    print("\n=== Запуск анализа ===")

    if last_meta:
        print("Используем OCR-мета для анализа:", json.dumps(last_meta, ensure_ascii=False, default=str))
    else:
        print("OCR-мета не обнаружена, анализ будет без дополнительных метаданных")

    analysis = await run_analysis()
    print(json.dumps(analysis, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
