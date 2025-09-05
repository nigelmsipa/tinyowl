#!/usr/bin/env python3
"""
Parse Strong's Greek/Hebrew dictionary text (from OCR/text extraction) and
merge definitions into existing numbers stats chunks.

Inputs (created by pdftotext -layout):
  domains/theology/raw/strongs_pd/strongs_greek.txt
  domains/theology/raw/strongs_pd/strongs_hebrew.txt

Stats file to enrich:
  domains/theology/chunks/strongs_strongs_numbers_chunks.json

Output (review file):
  domains/theology/chunks/strongs_strongs_numbers_chunks_with_defs.json

This script does not write to the DB. Review the output then embed.
"""

import re
import json
from pathlib import Path
from typing import Dict, List

GREEK_TXT = Path("domains/theology/raw/strongs_pd/strongs_greek.txt")
HEBREW_TXT = Path("domains/theology/raw/strongs_pd/strongs_hebrew.txt")
NUMBERS_STATS = Path("domains/theology/chunks/strongs_strongs_numbers_chunks.json")
NUMBERS_WITH_DEFS = Path("domains/theology/chunks/strongs_strongs_numbers_chunks_with_defs.json")


def parse_dictionary(txt_path: Path, header_prefix: str) -> Dict[str, str]:
    """Parse dictionary blocks. header_prefix: 'SG' or 'SH'"""
    content = txt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    entries: Dict[str, List[str]] = {}

    # Header lines like 'SG123' or 'SH456'
    header_re = re.compile(rf"^\s*{re.escape(header_prefix)}(\d+)\s*$")

    current_key = None
    buffer: List[str] = []

    def flush():
        nonlocal current_key, buffer
        if current_key is not None:
            # Clean trailing blank lines
            while buffer and not buffer[-1].strip():
                buffer.pop()
            entries.setdefault(current_key, []).append("\n".join(buffer))
        buffer = []

    for line in content:
        m = header_re.match(line)
        if m:
            # New entry
            flush()
            num = m.group(1)
            current_key = ("G" if header_prefix == "SG" else "H") + num
            # Start fresh buffer
            buffer = []
            continue
        # Accumulate lines
        buffer.append(line)

    flush()

    # Join multiple segments per key if any
    resolved = {k: "\n".join(v).strip() for k, v in entries.items()}
    return resolved


def merge_definitions(stats_file: Path, defs: Dict[str, str]) -> List[dict]:
    stats = json.loads(stats_file.read_text(encoding="utf-8"))
    out: List[dict] = []
    for chunk in stats:
        snum = chunk.get("metadata", {}).get("strong_number")
        definition = defs.get(snum)
        meta = chunk.get("metadata", {})
        # Mark schema and definition flags for upgrade path
        meta["schema_version"] = "1"
        if definition:
            meta["has_definition"] = "true"
            meta["definition_source"] = "pd_pdf"
            content = (
                f"Strong's {snum} — Definition\n\n" + definition.strip() +
                "\n\n---\n" + chunk.get("content", "")
            )
            chunk["content"] = content
        else:
            meta["has_definition"] = "false"
            meta["definition_source"] = "none"
        chunk["metadata"] = meta
        out.append(chunk)
    return out


def main():
    greek = parse_dictionary(GREEK_TXT, "SG") if GREEK_TXT.exists() else {}
    hebrew = parse_dictionary(HEBREW_TXT, "SH") if HEBREW_TXT.exists() else {}
    defs = {**greek, **hebrew}
    print(f"Parsed definitions: Greek {len(greek)}, Hebrew {len(hebrew)}, total {len(defs)}")

    enriched = merge_definitions(NUMBERS_STATS, defs)
    NUMBERS_WITH_DEFS.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
    print(f"Wrote enriched numbers → {NUMBERS_WITH_DEFS}")


if __name__ == "__main__":
    main()

