#!/usr/bin/env python3
"""
Add Nave's Topical Bible hierarchical chunks to TinyOwl's ChromaDB.
Uses BGE-large embeddings to match existing theological database.
"""

import json
import chromadb
from chromadb.utils import embedding_functions
from pathlib import Path
from typing import List, Dict, Any

def load_naves_chunks() -> Dict[str, List[Dict[str, Any]]]:
    """Load all hierarchical Nave's chunks."""
    print("📖 Loading Nave's hierarchical chunks...")

    chunks_dir = Path("domains/theology/chunks")

    layers = {
        'scripture_entries': [],
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

    client = chromadb.PersistentClient(path='./vectordb')

    for layer_name, chunks in layers.items():
        if not chunks:
            continue

        collection_name = f"naves_{layer_name}"
        print(f"\\n📦 Processing {collection_name}...")

        # Create or get collection
        try:
            collection = client.get_collection(collection_name)
            print(f"  ⚠️ Collection exists with {collection.count():,} items")

            # Ask user if they want to recreate
            response = input(f"  🤔 Recreate {collection_name}? (y/n): ").strip().lower()
            if response == 'y':
                client.delete_collection(collection_name)
                collection = client.create_collection(
                    name=collection_name,
                    embedding_function=bge_ef,
                    metadata={"description": f"Nave's Topical Bible - {layer_name}"}
                )
                print(f"  🔄 Recreated collection")
            else:
                print(f"  ⏭️ Skipping {collection_name}")
                continue

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

    client = chromadb.PersistentClient(path='./vectordb')
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