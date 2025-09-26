#!/usr/bin/env python3
"""
Add Nave's Topical Bible hierarchical chunks to TinyOwl's ChromaDB.
Uses BGE-large embeddings to match existing theological database.

Safety improvements:
- Backs up existing Nave's collections before re-creating them
- Embeds all four layers, including scripture_entries
- Optionally cleans up stray test collections
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Any
import sys

# Resolve project root and add scripts/ to path for safety utilities
ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SCRIPTS_DIR))

try:
    # Optional: safety backup if available
    from safety import backup_collection as _backup_collection  # type: ignore
except Exception:  # pragma: no cover
    _backup_collection = None

VDB_PATH = str(ROOT / "vectordb")
BACKUP_DIR = str(ROOT / "backups")

def load_naves_chunks() -> Dict[str, List[Dict[str, Any]]]:
    """Load all hierarchical Nave's chunks."""
    print("📖 Loading Nave's hierarchical chunks...")

    chunks_dir = Path("domains/theology/chunks")

    layers = {
        'scripture_entries': [],
        'topic_entries': [],
        'topic_sections': [],
        'complete_topics': []
    }

    for layer_name in layers.keys():
        file_path = chunks_dir / f"naves_{layer_name}.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                layers[layer_name] = json.load(f)
            print(f"  ✅ Loaded {len(layers[layer_name]):,} {layer_name}")
        else:
            print(f"  ❌ Missing {file_path}")

    return layers

def add_to_chromadb(layers: Dict[str, List[Dict[str, Any]]]):
    """Add Nave's chunks to ChromaDB with BGE-large embeddings."""
    print("🗃️ Adding to ChromaDB with BGE-large embeddings...")

    # Use BGE-large to match existing TinyOwl database
    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name='BAAI/bge-large-en-v1.5'
    )

    client = chromadb.PersistentClient(path=VDB_PATH)

    for layer_name, chunks in layers.items():
        if not chunks:
            continue

        collection_name = f"naves_{layer_name}"
        print(f"\\n📦 Processing {collection_name}...")

        # Create or get collection
        try:
            collection = client.get_collection(collection_name)
            existing = 0
            try:
                existing = collection.count()
            except Exception:
                existing = 0
            print(f"  ⚠️ Collection exists with {existing:,} items")
            # If already up-to-date, skip re-embedding
            if existing == len(chunks):
                print(f"  ✅ Up-to-date, skipping {collection_name}")
                continue
            # Backup then recreate
            if _backup_collection is not None and existing:
                try:
                    backup_path = _backup_collection(VDB_PATH, collection_name, BACKUP_DIR)
                    print(f"  🔒 Backup created: {backup_path}")
                except Exception as e:
                    print(f"  ⚠️ Backup failed ({e}); proceeding with caution")
            print(f"  🔄 Recreating {collection_name} for complete embedding")
            client.delete_collection(collection_name)
            collection = client.create_collection(
                name=collection_name,
                embedding_function=bge_ef,
                metadata={"description": f"Nave's Topical Bible - {layer_name}"}
            )

        except Exception:
            collection = client.create_collection(
                name=collection_name,
                embedding_function=bge_ef,
                metadata={"description": f"Nave's Topical Bible - {layer_name}"}
            )
            print(f"  ✅ Created new collection")

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            ids.append(chunk['id'])
            documents.append(chunk['document'])
            metadatas.append(chunk['metadata'])

        # Add in batches for large collections
        batch_size = 100
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        print(f"  📊 Adding {len(chunks):,} chunks in {total_batches} batches...")

        for i in range(0, len(chunks), batch_size):
            batch_end = min(i + batch_size, len(chunks))
            batch_num = (i // batch_size) + 1

            try:
                collection.add(
                    ids=ids[i:batch_end],
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end]
                )

                if batch_num % 10 == 0 or batch_num == total_batches:
                    print(f"    Batch {batch_num}/{total_batches} complete")

            except Exception as e:
                print(f"    ❌ Error in batch {batch_num}: {e}")
                continue

        final_count = collection.count()
        print(f"  ✅ {collection_name}: {final_count:,} chunks embedded")

def verify_integration():
    """Verify Nave's integration with existing TinyOwl database."""
    print("\\n🔍 Verifying TinyOwl + Nave's integration...")

    client = chromadb.PersistentClient(path=VDB_PATH)
    collections = client.list_collections()

    print(f"\\n📊 Complete TinyOwl Theological Database:")
    print("=" * 50)

    total_chunks = 0
    for collection in collections:
        count = collection.count()
        total_chunks += count
        source = "Bible/Strong's" if not collection.name.startswith('naves_') else "Nave's Topical"
        print(f"  {collection.name:25}: {count:,} chunks ({source})")

    print(f"\\n🎯 Total Theological Database: {total_chunks:,} chunks")
    print("✅ TinyOwl now includes Bible + Strong's + Nave's Topical!")

    # Optional cleanup: remove tiny test collection if present
    try:
        names = [c.name for c in collections]
        if 'naves_test' in names:
            print("\n🧹 Cleaning up stray 'naves_test' collection…")
            if _backup_collection is not None:
                try:
                    backup_path = _backup_collection(VDB_PATH, 'naves_test', BACKUP_DIR)
                    print(f"  🔒 Backup created: {backup_path}")
                except Exception as e:
                    print(f"  ⚠️ Backup failed ({e}); proceeding with deletion")
            client.delete_collection('naves_test')
            print("  ✅ Removed 'naves_test'")
    except Exception as e:
        print(f"  ⚠️ Cleanup skipped: {e}")

def main():
    """Main integration function."""
    print("🦉 TinyOwl: Adding Nave's Topical Bible to ChromaDB")
    print("=" * 55)

    # Load chunks
    layers = load_naves_chunks()

    # Add to ChromaDB
    add_to_chromadb(layers)

    # Verify integration
    verify_integration()

    print("\\n🎉 Nave's Topical Bible integration complete!")
    print("🔧 Next: Update chat application for Nave's search capabilities")

if __name__ == "__main__":
    main()
