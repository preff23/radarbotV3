import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any

import sys
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from bot.utils.corpbonds_client import CorpBondsClient
from bot.providers.tbank_rest import TBankRestClient


async def fetch_corpbonds() -> List[Dict[str, Any]]:
    async with CorpBondsClient() as client:
        bonds = await client.get_all_bonds()
        return [
            {
                "source": "corpbonds",
                "isin": bond.isin,
                "name": bond.bond_short_name,
                "full_name": bond.bond_full_name,
                "issuer_name": bond.issuer_name,
            }
            for bond in bonds
            if bond.isin
        ]


async def fetch_tbank_bonds() -> List[Dict[str, Any]]:
    client = TBankRestClient()
    try:
        instruments = await client.get_all_bonds_base()
        entries = []
        for item in instruments:
            isin = item.get("isin")
            if not isin:
                continue
            entries.append(
                {
                    "source": "tbank",
                    "isin": isin,
                    "name": item.get("name"),
                    "ticker": item.get("ticker"),
                    "issuer_name": item.get("issuer"),
                }
            )
        return entries
    finally:
        await client.client.aclose()


async def main():
    corpbonds, tbank = await asyncio.gather(fetch_corpbonds(), fetch_tbank_bonds())

    combined: Dict[str, Dict[str, Any]] = {}

    def merge(entries: List[Dict[str, Any]]):
        for entry in entries:
            isin = entry.get("isin")
            if not isin:
                continue
            combined.setdefault(isin, {"isin": isin, "sources": []})
            combined[isin]["sources"].append(entry.get("source"))
            for key, value in entry.items():
                if key in ("isin", "source"):
                    continue
                if value and key not in combined[isin]:
                    combined[isin][key] = value

    merge(corpbonds)
    merge(tbank)

    records = list(combined.values())

    output_dir = ROOT_DIR / "data"
    output_dir.mkdir(exist_ok=True)

    json_path = output_dir / "bonds_reference.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"Combined {len(corpbonds)} CorpBonds + {len(tbank)} TBank => {len(records)} unique records")
    print(f"Saved to {json_path}")


if __name__ == "__main__":
    asyncio.run(main())
