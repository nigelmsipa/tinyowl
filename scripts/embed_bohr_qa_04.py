#!/usr/bin/env python3
"""
Generate BGE-large-en-v1.5 embeddings for Stephen Bohr Q&A 04 chunks
and add them to ChromaDB collection
"""

import json
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Paths
TINYOWL_ROOT = Path("/home/nigel/tinyowl")
CHUNKS_FILE = TINYOWL_ROOT / "domains/theology/chunks/stephen_bohr_qa_04_chunks.json"
VECTORDB_DIR = TINYOWL_ROOT / "vectordb"
COLLECTION_NAME = "stephen_bohr_qa"

# Model
MODEL_NAME = "BAAI/bge-large-en-v1.5"

def main():
    print("=" * 60)
    print("Embedding Stephen Bohr Q&A 04 Chunks")
    print("=" * 60)

    # Load chunks
    print(f"\nLoading chunks from: {CHUNKS_FILE}")
    with open(CHUNKS_FILE, 'r') as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks")

    # Initialize embedding model
    print(f"\nLoading embedding model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded successfully")

    # Initialize ChromaDB client
    print(f"\nConnecting to ChromaDB at: {VECTORDB_DIR}")
    client = chromadb.PersistentClient(
        path=str(VECTORDB_DIR),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )

    # Get or create collection
    try:
        collection = client.get_collection(name=COLLECTION_NAME)
        existing_count = collection.count()
        print(f"Found existing collection '{COLLECTION_NAME}' with {existing_count} documents")
    except:
        print(f"Creating new collection: {COLLECTION_NAME}")
        collection = client.create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Stephen Bohr I'd Like to Know Q&A responses"}
        )

    # Generate embeddings and add to ChromaDB
    print(f"\nGenerating embeddings for {len(chunks)} chunks...")

    batch_size = 100
    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
        batch = chunks[i:i+batch_size]

        # Extract texts
        texts = [chunk["text"] for chunk in batch]

        # Generate embeddings
        embeddings = model.encode(texts, show_progress_bar=False)

        # Prepare data for ChromaDB
        ids = [chunk["id"] for chunk in batch]
        metadatas = [
            {
                "source": chunk.get("source", ""),
                "pair_num": chunk.get("pair_num", 0),
                "chunk_type": chunk.get("chunk_type", ""),
                "main_topic": chunk.get("main_topic", ""),
                "section": chunk.get("section", "")
            }
            for chunk in batch
        ]

        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas
        )

    # Final statistics
    final_count = collection.count()
    print(f"\n✓ Embedding complete!")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Total documents: {final_count}")
    print(f"  New documents added: {len(chunks)}")

if __name__ == "__main__":
    main()
