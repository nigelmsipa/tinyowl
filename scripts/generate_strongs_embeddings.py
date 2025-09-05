#!/usr/bin/env python3
"""
Generate BGE-large embeddings for Strong's Concordance chunks
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer
import time
import os
import argparse
from pathlib import Path

STATE_PATH = Path("domains/theology/chunks/embedding_state.json")


def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except Exception:
            return {}
    return {}


def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def generate_all_strongs_embeddings(force: bool = False, only: str = None, resume: bool = False, batch_limit: int = None):
    """Generate embeddings for all Strong's concordance chunk files"""
    
    print("🦉 TinyOwl Strong's Concordance Embedding Pipeline")
    print("=" * 60)
    
    # Initialize BGE model
    print("\n📖 Loading BGE-large-en-v1.5 model...")
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    print(f"✅ Model loaded (dim: {model.get_sentence_embedding_dimension()})")
    
    # Initialize ChromaDB
    print("\n💾 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="vectordb")
    
    # Strong's files to process
    files_to_process = [
        ("domains/theology/chunks/strongs_concordance_entries_chunks.json", "strongs_concordance_entries"),
        ("domains/theology/chunks/strongs_strongs_numbers_chunks.json", "strongs_numbers"),
        ("domains/theology/chunks/strongs_word_summaries_chunks.json", "strongs_word_summaries")
    ]

    if only:
        files_to_process = [t for t in files_to_process if t[1] == only]
    
    total_processed = 0
    overall_start = time.time()
    
    state = load_state() if resume else {}

    for chunks_file, collection_name in files_to_process:
        print(f"\n📚 Processing {collection_name}...")
        
        # Load chunks (flat JSON array format)
        # Prefer enriched numbers with definitions if present
        if collection_name == "strongs_numbers":
            enriched = "domains/theology/chunks/strongs_strongs_numbers_chunks_with_defs.json"
            if os.path.exists(enriched):
                chunks_file = enriched

        if not os.path.exists(chunks_file):
            print(f"❌ Chunk file not found: {chunks_file}")
            continue
            
        with open(chunks_file, 'r') as f:
            chunks = json.load(f)  # Direct JSON array, not nested
        
        # Full production mode - process all chunks
        
        print(f"   📄 Loaded {len(chunks):,} chunks")
        
        # Create/get collection with safety
        existing = None
        existing_count = 0
        try:
            existing = client.get_collection(collection_name)
            try:
                existing_count = existing.count()
            except Exception:
                existing_count = 0
        except Exception:
            existing = None

        # Resume path: allow adding more even if non-empty
        if existing and existing_count > 0 and not force and not resume:
            print(f"⚠️  Collection '{collection_name}' already has {existing_count} items. Skipping (use --force or --resume).")
            continue

        if existing and existing_count > 0 and force:
            try:
                client.delete_collection(collection_name)
                print(f"🗑️ Cleared existing collection: {collection_name}")
            except Exception as e:
                print(f"❌ Failed to clear collection {collection_name}: {e}")
                continue

        if existing and existing_count >= 0:
            collection = existing
            print(f"📂 Using existing collection: {collection_name} (count: {existing_count})")
        else:
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": f"Strong's Concordance with BGE-large embeddings"}
            )
            print(f"📂 Created new collection: {collection_name}")
        
        # Batch process embeddings
        batch_size = 100
        # Determine start index for resume
        start_index = 0
        if resume:
            start_index = int(state.get(collection_name, {}).get("next_index", 0))
            if start_index >= len(chunks):
                print(f"✅ Resume: nothing left to do for {collection_name}")
                continue

        file_embedded = 0
        start_time = time.time()

        print(f"⚡ Processing {len(chunks):,} chunks in batches of {batch_size} (starting at {start_index})")

        batches_done = 0
        for i in range(start_index, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            # Extract texts and metadata for ChromaDB
            texts = [chunk['content'] for chunk in batch]
            metadatas = []
            ids = []
            
            for idx, chunk in enumerate(batch):
                # Create unique ChromaDB ID by adding batch position
                chromadb_id = f"{chunk['id']}_doc_{file_embedded + idx}"
                ids.append(chromadb_id)

                # Start with chunk metadata to preserve upgrade flags and fields
                chunk_meta = chunk.get('metadata', {})
                metadata = dict(chunk_meta)

                # Normalize some common fields to strings
                for key in ("chapter", "verse", "total_verses", "ot_count", "nt_count", "verse_count", "word_count"):
                    if key in metadata:
                        try:
                            metadata[key] = str(metadata[key])
                        except Exception:
                            metadata[key] = str(metadata[key])

                # Ensure required keys exist
                if 'concordance_id' not in metadata:
                    metadata['concordance_id'] = chunk.get('id', '')

                metadatas.append(metadata)
            
            # Generate embeddings for batch
            print(f"   🔢 Batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size} ({len(batch)} chunks)...", end="", flush=True)
            
            embeddings = model.encode(texts)
            
            # Add to ChromaDB
            collection.add(
                documents=texts,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            file_embedded += len(batch)
            elapsed = time.time() - start_time
            rate = file_embedded / elapsed
            print(f" ✅ ({rate:.1f}/sec)")

            # Save resume state
            if resume:
                state.setdefault(collection_name, {})["next_index"] = i + batch_size
                state[collection_name]["total"] = len(chunks)
                save_state(state)

            batches_done += 1
            if resume and batch_limit and batches_done >= batch_limit:
                print(f"⏸️  Pausing after {batches_done} batches for {collection_name}")
                break
        
        print(f"   ✅ {collection_name} complete: {file_embedded:,} chunks")
        total_processed += file_embedded
    
    overall_elapsed = time.time() - overall_start
    print(f"\n🎉 ALL STRONG'S CONCORDANCE EMBEDDING COMPLETE!")
    print(f"   📊 Total chunks embedded: {total_processed:,}")
    print(f"   ⏱️ Total time: {overall_elapsed:.1f}s")
    print(f"   ⚡ Overall rate: {total_processed/overall_elapsed:.1f} chunks/sec")
    print(f"   🗂️ Collections: strongs_concordance_entries, strongs_numbers, strongs_word_summaries")
    print(f"   🎯 Ready for @strong: and @word: hotkey lookups!")


def main():
    parser = argparse.ArgumentParser(description="Generate Strong's embeddings safely")
    parser.add_argument("--force", action="store_true", help="Overwrite existing non-empty collections")
    parser.add_argument("--only", choices=["strongs_concordance_entries", "strongs_numbers", "strongs_word_summaries"], help="Process only this collection")
    parser.add_argument("--resume", action="store_true", help="Resume mode; continue from last batch and allow partial runs")
    parser.add_argument("--batch-limit", type=int, help="In resume mode, process at most this many batches then pause")
    args = parser.parse_args()
    generate_all_strongs_embeddings(force=args.force, only=args.only, resume=args.resume, batch_limit=args.batch_limit)


if __name__ == "__main__":
    main()
