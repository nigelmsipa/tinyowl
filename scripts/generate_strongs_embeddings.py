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

def generate_all_strongs_embeddings(force: bool = False):
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
    
    total_processed = 0
    overall_start = time.time()
    
    for chunks_file, collection_name in files_to_process:
        print(f"\n📚 Processing {collection_name}...")
        
        # Load chunks (flat JSON array format)
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

        if existing and existing_count > 0 and not force:
            print(f"⚠️  Collection '{collection_name}' already has {existing_count} items. Skipping (use --force to overwrite).")
            continue

        if existing and existing_count > 0 and force:
            try:
                client.delete_collection(collection_name)
                print(f"🗑️ Cleared existing collection: {collection_name}")
            except Exception as e:
                print(f"❌ Failed to clear collection {collection_name}: {e}")
                continue

        if existing and existing_count == 0:
            collection = existing
            print(f"📂 Using existing empty collection: {collection_name}")
        else:
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": f"Strong's Concordance with BGE-large embeddings"}
            )
            print(f"📂 Created new collection: {collection_name}")
        
        # Batch process embeddings
        batch_size = 100
        file_embedded = 0
        start_time = time.time()
        
        print(f"⚡ Processing {len(chunks):,} chunks in batches of {batch_size}")
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            # Extract texts and metadata for ChromaDB
            texts = [chunk['content'] for chunk in batch]
            metadatas = []
            ids = []
            
            for idx, chunk in enumerate(batch):
                # Create unique ChromaDB ID by adding batch position
                chromadb_id = f"{chunk['id']}_doc_{file_embedded + idx}"
                ids.append(chromadb_id)
                
                # Prepare metadata for ChromaDB (scalars only) - bulletproof parser format
                chunk_meta = chunk['metadata']
                metadata = {
                    'concordance_id': chunk['id'],
                    'source': chunk_meta['source'],
                    'layer': chunk_meta['layer'],
                    'testament': chunk_meta.get('testament', 'unknown')
                }
                
                # Add type-specific metadata
                if chunk_meta['layer'] == 'word_entry':
                    metadata.update({
                        'word': chunk_meta['word'],
                        'osis_id': chunk_meta['osis_id'],
                        'book': chunk_meta['book'],
                        'chapter': str(chunk_meta['chapter']),
                        'verse': str(chunk_meta['verse']),
                        'strong_number': chunk_meta.get('strong_number') or '',
                        'entry_type': 'concordance_word_entry'
                    })
                elif chunk_meta['layer'] == 'strongs_number':
                    metadata.update({
                        'strong_number': chunk_meta['strong_number'],
                        'type': chunk_meta['type'],
                        'verse_count': str(chunk_meta['verse_count']),
                        'word_count': str(len(chunk_meta['word_entries'])),
                        'entry_type': 'strongs_number'
                    })
                elif chunk_meta['layer'] == 'word_summary':
                    metadata.update({
                        'word': chunk_meta['word'],
                        'total_verses': str(chunk_meta['total_verses']),
                        'ot_count': str(chunk_meta['ot_count']),
                        'nt_count': str(chunk_meta['nt_count']),
                        'entry_type': 'word_summary'
                    })
                
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
    args = parser.parse_args()
    generate_all_strongs_embeddings(force=args.force)


if __name__ == "__main__":
    main()
