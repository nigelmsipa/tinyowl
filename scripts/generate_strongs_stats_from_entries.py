#!/usr/bin/env python3
"""
Generate Strong's numbers and word summaries chunks from existing concordance entries.

This does NOT include dictionary definitions; it builds statistics-only layers that
improve @strong:<num> and word summaries until dictionary text is available.

Inputs:
  - domains/theology/chunks/strongs_concordance_entries_chunks.json

Outputs:
  - domains/theology/chunks/strongs_strongs_numbers_chunks.json
  - domains/theology/chunks/strongs_word_summaries_chunks.json

All metadata fields are scalars (strings) to be Chroma-compatible.
"""

import json
from collections import defaultdict, Counter
from pathlib import Path

ENTRIES_PATH = Path("domains/theology/chunks/strongs_concordance_entries_chunks.json")
NUMBERS_OUT = Path("domains/theology/chunks/strongs_strongs_numbers_chunks.json")
WORDS_OUT = Path("domains/theology/chunks/strongs_word_summaries_chunks.json")


def load_entries():
    with ENTRIES_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    entries = load_entries()
    print(f"Loaded {len(entries):,} concordance entries")

    by_number = defaultdict(list)
    by_word = defaultdict(list)

    for e in entries:
        meta = e.get("metadata", {})
        snum = meta.get("strong_number")
        word = meta.get("word")
        if snum:
            by_number[snum].append(e)
        if word:
            by_word[word].append(e)

    # Build numbers chunks (stats only)
    numbers_chunks = []
    for snum, lst in by_number.items():
        testament_counts = Counter((e.get("metadata", {}).get("testament") or "").upper() for e in lst)
        words = [e.get("metadata", {}).get("word") for e in lst if e.get("metadata", {}).get("word")]
        top_words = ", ".join([w for w, _ in Counter(words).most_common(5)])
        verse_count = len(lst)
        stype = "Hebrew" if snum.startswith("H") else ("Greek" if snum.startswith("G") else "Unknown")

        content = (
            f"Strong's {snum} ({stype}) — {verse_count} verses. "
            f"Top words: {top_words if top_words else 'n/a'}. "
            f"Definitions not yet available."
        )

        chunk = {
            "id": f"strongs_{snum}",
            "content": content,
            "metadata": {
                "concordance_id": f"strongs_{snum}",
                "source": "strongs_stats",
                "layer": "strongs_number",
                "strong_number": snum,
                "type": stype,
                "verse_count": str(verse_count),
                "word_count": str(len(set(words))),
                "entry_type": "strongs_number"
            }
        }
        numbers_chunks.append(chunk)

    # Build word summaries
    word_chunks = []
    for w, lst in by_word.items():
        total_verses = len(lst)
        testament_counts = Counter((e.get("metadata", {}).get("testament") or "").upper() for e in lst)
        ot = testament_counts.get("OT", 0)
        nt = testament_counts.get("NT", 0)
        nums = [e.get("metadata", {}).get("strong_number") for e in lst if e.get("metadata", {}).get("strong_number")]
        top_nums = ", ".join([n for n, _ in Counter(nums).most_common(5)])

        content = (
            f"Word '{w}' — {total_verses} verses (OT {ot}, NT {nt}). "
            f"Top Strong's: {top_nums if top_nums else 'n/a'}."
        )

        chunk = {
            "id": f"strongs_word_{w.lower()}",
            "content": content,
            "metadata": {
                "concordance_id": f"strongs_word_{w.lower()}",
                "source": "strongs_stats",
                "layer": "word_summary",
                "word": w,
                "total_verses": str(total_verses),
                "ot_count": str(ot),
                "nt_count": str(nt),
                "entry_type": "word_summary"
            }
        }
        word_chunks.append(chunk)

    # Save
    with NUMBERS_OUT.open("w", encoding="utf-8") as f:
        json.dump(numbers_chunks, f, indent=2)
    with WORDS_OUT.open("w", encoding="utf-8") as f:
        json.dump(word_chunks, f, indent=2)

    print(f"Wrote {len(numbers_chunks):,} numbers chunks → {NUMBERS_OUT}")
    print(f"Wrote {len(word_chunks):,} word summaries → {WORDS_OUT}")


if __name__ == "__main__":
    main()

