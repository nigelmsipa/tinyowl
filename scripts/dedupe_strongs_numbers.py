#!/usr/bin/env python3
"""
Deduplicate strongs_numbers collection: keep one doc per strong_number, preferring
entries with definitions (has_definition=true). Backup before delete is recommended.
"""

import chromadb
import json
from collections import defaultdict

DB_PATH = "vectordb"
COLLECTION = "strongs_numbers"


def main():
    client = chromadb.PersistentClient(path=DB_PATH)
    col = client.get_collection(COLLECTION)
    print("Fetching collection...")
    got = col.get(include=["documents", "metadatas"])  # ids are returned regardless
    ids = got.get("ids", [])
    docs = got.get("documents", [])
    metas = got.get("metadatas", [])
    print(f"Total items: {len(ids)}")

    groups = defaultdict(list)
    for i, cid in enumerate(ids):
        meta = metas[i] if i < len(metas) else {}
        snum = meta.get("strong_number")
        if not snum:
            # fallback attempt to parse from id
            snum = meta.get("concordance_id") or cid
        groups[snum].append(i)

    to_keep = set()
    to_delete = []
    kept = 0
    for snum, idxs in groups.items():
        if not idxs:
            continue
        # pick the one with definition if available, else the first
        best = idxs[0]
        for j in idxs:
            m = metas[j]
            if str(m.get("has_definition", "false")).lower() == "true":
                best = j
                break
        to_keep.add(ids[best])
        for j in idxs:
            if ids[j] not in to_keep:
                to_delete.append(ids[j])
        kept += 1

    print(f"Unique strong_numbers: {kept}")
    print(f"Duplicates to delete: {len(to_delete)}")
    if not to_delete:
        print("Nothing to delete.")
        return

    # Delete in chunks
    B = 200
    for i in range(0, len(to_delete), B):
        batch = to_delete[i:i+B]
        print(f"Deleting {i+len(batch)}/{len(to_delete)}...")
        col.delete(ids=batch)

    print("Done. Recount:")
    print(col.count())


if __name__ == "__main__":
    main()
