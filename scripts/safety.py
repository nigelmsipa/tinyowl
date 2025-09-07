#!/usr/bin/env python3
"""
Safety utilities for ChromaDB operations (backup, safe delete, restore)
Non-destructive helpers to prevent accidental data loss.
"""

import json
from pathlib import Path
from datetime import datetime
import argparse
import chromadb


def backup_collection(vectordb_path: str, collection_name: str, backup_dir: str) -> Path:
    client = chromadb.PersistentClient(path=vectordb_path)
    col = client.get_collection(collection_name)
    result = col.get(include=["documents", "metadatas"])  # ids always returned
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(backup_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{collection_name}_backup_{ts}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "collection": collection_name,
            "timestamp": ts,
            "count": len(result.get("ids", [])),
            "data": {
                "ids": result.get("ids", []),
                "documents": result.get("documents", []),
                "metadatas": result.get("metadatas", []),
            }
        }, f, indent=2)
    return out_file


def safe_delete_collection(vectordb_path: str, collection_name: str, confirmation: str, backup_dir: str) -> None:
    required = f"DELETE_{collection_name}_CONFIRMED"
    if confirmation != required:
        raise ValueError(f"Invalid confirmation token. Required: {required}")
    backup_file = backup_collection(vectordb_path, collection_name, backup_dir)
    client = chromadb.PersistentClient(path=vectordb_path)
    client.delete_collection(collection_name)
    print(f"Deleted {collection_name}. Backup: {backup_file}")


def restore_collection(vectordb_path: str, backup_file: str) -> None:
    with open(backup_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    name = data["collection"]
    client = chromadb.PersistentClient(path=vectordb_path)
    col = client.create_collection(name)
    payload = data["data"]
    col.add(ids=payload["ids"], documents=payload["documents"], metadatas=payload["metadatas"])
    print(f"Restored {name} from {backup_file} ({data.get('count', 0)} items)")


def main():
    ap = argparse.ArgumentParser(description="ChromaDB safety utilities")
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("backup", help="Backup a collection")
    b.add_argument("collection")
    b.add_argument("--vectordb", default="vectordb")
    b.add_argument("--out", default="backups")

    d = sub.add_parser("delete", help="Safely delete a collection (with backup)")
    d.add_argument("collection")
    d.add_argument("--confirm", required=True)
    d.add_argument("--vectordb", default="vectordb")
    d.add_argument("--out", default="backups")

    r = sub.add_parser("restore", help="Restore from a backup file")
    r.add_argument("backup_file")
    r.add_argument("--vectordb", default="vectordb")

    args = ap.parse_args()

    if args.cmd == "backup":
        out = backup_collection(args.vectordb, args.collection, args.out)
        print(out)
    elif args.cmd == "delete":
        safe_delete_collection(args.vectordb, args.collection, args.confirm, args.out)
    elif args.cmd == "restore":
        restore_collection(args.vectordb, args.backup_file)


if __name__ == "__main__":
    main()
