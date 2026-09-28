"""Write-through index of records live in the current demo run (instant UI lists, clean resets)."""
import json
import threading

from .config import LEDGER_PATH, seed_records
from .records import record_id

_lock = threading.Lock()


def _write(data):
    LEDGER_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def _read() -> dict:
    if not LEDGER_PATH.exists():
        return reset()
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def reset() -> dict:
    data = {"records": {record_id(r): r for r in seed_records()}, "demo_ids": []}
    with _lock:
        _write(data)
    return data


def upsert(r: dict, demo: bool = True):
    with _lock:
        data = _read()
        data["records"][record_id(r)] = r
        if demo and record_id(r) not in data["demo_ids"]:
            data["demo_ids"].append(record_id(r))
        _write(data)


def get(rid):
    return _read()["records"].get(rid)


def all_records() -> list[dict]:
    return list(_read()["records"].values())


def demo_ids() -> list[str]:
    return list(_read()["demo_ids"])


def known_ids() -> set[str]:
    return set(_read()["records"])
