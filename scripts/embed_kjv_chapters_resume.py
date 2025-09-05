#!/usr/bin/env python3
"""
Embed only missing KJV chapter chunks into ChromaDB (resume-safe).

Requirements:
  - Chunk file: domains/theology/chunks/kjv_chapters_chunks.json
  - Collection: kjv_chapters (existing 0..N items)
  - Model: BAAI/bge-large-en-v1.5 (will use cache if available)

Behavior:
  - Reads all chapter chunks, checks existing IDs in kjv_chapters
  - Embeds and adds only the missing IDs in batches
  - Does NOT delete or overwrite existing items
"""

import json
import os
import time
from typing import List, Dict, Set

import chromadb
from sentence_transformers import SentenceTransformer


CHUNKS_PATH = "domains/theology/chunks/kjv_chapters_chunks.json"
COLLECTION = "kjv_chapters"
DB_PATH = "vectordb"


def load_chunks(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    chunks = data.get("chunks", [])
    return chunks


def get_existing_ids(col) -> Set[str]:
    # Chroma get() returns 'ids' even if include omits documents
    got = col.get(include=["metadatas"])  # lightweight fetch
    return set(got.get("ids", []) or [])


def embed_missing():
    print("🦉 Resume KJV Chapters Embedding (add-only)")
    print("=" * 60)

    # Load chunks
    if not os.path.exists(CHUNKS_PATH):
        raise FileNotFoundError(f"Chunk file not found: {CHUNKS_PATH}")
    chunks = load_chunks(CHUNKS_PATH)
    print(f"📄 Loaded {len(chunks)} chapter chunks from {CHUNKS_PATH}")

    # Init DB
    client = chromadb.PersistentClient(path=DB_PATH)
    try:
        col = client.get_collection(COLLECTION)
        print(f"📚 Using existing collection: {COLLECTION}")
    except Exception:
        col = client.create_collection(COLLECTION)
        print(f"📂 Created new collection: {COLLECTION}")

    existing_ids = get_existing_ids(col)
    print(f"🔎 Existing items: {len(existing_ids)}")

    # Determine missing
    missing = [c for c in chunks if c.get("id") not in existing_ids]
    if not missing:
        print("✅ No missing chapters. Nothing to do.")
        return

    print(f"🧩 Missing chapters to embed: {len(missing)}")

    # Load model (should use cache if previously loaded)
    print("📖 Loading embedding model: BAAI/bge-large-en-v1.5 ...")
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    print(f"✅ Model ready (dim: {model.get_sentence_embedding_dimension()})")

    # Batch add
    batch_size = 100
    start = time.time()
    added = 0

    for i in range(0, len(missing), batch_size):
        batch = missing[i:i+batch_size]
        texts = [c["content"] for c in batch]
        ids = [c["id"] for c in batch]
        metadatas = []
        for c in batch:
            m = c.get("metadata", {}).copy()
            # Normalize a few fields to strings
            for k in ("chapter", "verse_count"):
                if k in m:
                    m[k] = str(m[k])
            metadatas.append(m)

        embeddings = model.encode(texts, convert_to_tensor=False)
        col.add(ids=ids, documents=texts, metadatas=metadatas, embeddings=[e.tolist() for e in embeddings])
        added += len(batch)
        print(f"   ⚡ Embedded {added}/{len(missing)} ...")

    elapsed = time.time() - start
    rate = added / elapsed if elapsed > 0 else added
    print(f"\n🎉 Completed. Added {added} chapters in {elapsed:.1f}s ({rate:.1f}/s)")


if __name__ == "__main__":
    embed_missing()
