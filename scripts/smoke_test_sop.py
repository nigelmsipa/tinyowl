#!/usr/bin/env python3
"""
Run quick smoke tests against SOP + Bible + Nave's layers.

Usage:
  python -u scripts/smoke_test_sop.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from chat_app.database_manager import DatabaseManager  # type: ignore


def run_query(db: DatabaseManager, q: str, n: int = 5) -> None:
    res = db.routed_search(q)
    print(f"\n> {q}  — results: {len(res)}")
    for r in res[:n]:
        md = r.get("metadata") or {}
        layer = r.get("source_layer")
        src = md.get("source") or md.get("translation") or ""
        book = md.get("book") or md.get("book_name") or ""
        snippet = (r.get("content") or "").replace("\n", " ")[:160]
        print(f"  - [{layer}] {src}:{book} | {snippet}")


def main() -> None:
    db = DatabaseManager()
    db.connect()
    tests: List[str] = [
        "According to Ellen White, Sabbath",
        "Spirit of Prophecy health principles",
        "Nave's: abomination",
        "investigative judgment",
        "ministry of angels",
    ]
    for q in tests:
        run_query(db, q)


if __name__ == "__main__":
    main()

