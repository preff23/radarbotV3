import json
from pathlib import Path

from bot.utils.bond_reference import load_bond_reference


def test_load_bond_reference(tmp_path):
    test_path = tmp_path / "bonds_reference.json"
    sample_data = [
        {
            "isin": "RU000A100001",
            "name": "Компания 001Р-01",
            "full_name": "Компания 001Р-01 2026",
            "ticker": "RU000A100001",
            "issuer_name": "Компания",
            "sources": ["tbank"],
        },
        {
            "isin": "RU000A100002",
            "name": "Компания 001P-02",
            "full_name": "Компания 001P-02 2027",
            "ticker": "RU000A100002",
            "issuer_name": "Компания",
            "sources": ["corpbonds"],
        }
    ]
    with test_path.open("w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False)

    reference = load_bond_reference(test_path)
    assert reference is not None

    entry = reference.match(isin="ru000a100002", ticker=None, name=None)
    assert entry is not None
    assert entry.full_name == "Компания 001P-02 2027"

    fuzzy_entry = reference.match_fuzzy("Компания001Р02")
    assert fuzzy_entry is not None
    assert fuzzy_entry.isin == "RU000A100002"
