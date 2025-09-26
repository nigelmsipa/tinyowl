#!/usr/bin/env python3
"""
Monitor TinyOwl embedding progress and print a simple dashboard.

Usage:
  python -u scripts/monitor_progress.py --interval 60

Outputs:
  - Console dashboard with counts
  - Writes logs/progress.log with timestamped snapshots
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict

import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "vectordb/chroma.sqlite3"
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT = LOG_DIR / "progress.log"


def query_counts(cur) -> Dict[str, int]:
    q = (
        "SELECT c.name, COUNT(e.id) "
        "FROM embeddings e "
        "JOIN segments s ON e.segment_id = s.id "
        "JOIN collections c ON s.collection = c.id "
        "GROUP BY c.name"
    )
    res = cur.execute(q).fetchall()
    return {name: int(cnt) for name, cnt in res}


def bar(value: int, total: int, width: int = 20) -> str:
    if total <= 0:
        return "[{}]".format("-" * width)
    pct = min(1.0, max(0.0, value / total))
    filled = int(pct * width)
    return "[{}{}] {:>5.1f}%".format("#" * filled, "-" * (width - filled), pct * 100)


def main() -> None:
    ap = argparse.ArgumentParser(description="Monitor embedding counts")
    ap.add_argument("--interval", type=int, default=60, help="Refresh interval seconds")
    ap.add_argument("--expect-coa-paragraphs", type=int, default=14738, help="Expected COA paragraph total")
    ap.add_argument("--expect-coa-chapters", type=int, default=315, help="Expected COA chapter total")
    args = ap.parse_args()

    conn = sqlite3.connect(str(DB))
    cur = conn.cursor()

    try:
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            counts = query_counts(cur)
            sop_p = counts.get("sop_paragraphs", 0)
            sop_c = counts.get("sop_chapters", 0)
            kjv_v = counts.get("kjv_verses", 0)
            web_v = counts.get("web_verses", 0)
            naves_e = counts.get("naves_topic_entries", 0)

            dash = (
                f"\n[{now}]\n"
                f"  SOP paragraphs: {sop_p:>6} {bar(sop_p, args.expect_coa_paragraphs)} (COA target)\n"
                f"  SOP chapters  : {sop_c:>6} {bar(sop_c, args.expect_coa_chapters)} (COA target)\n"
                f"  Nave's entries: {naves_e:>6}\n"
                f"  KJV verses    : {kjv_v:>6} | WEB verses: {web_v:>6}\n"
            )
            print(dash, end="")
            with OUT.open("a", encoding="utf-8") as f:
                f.write(dash)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

