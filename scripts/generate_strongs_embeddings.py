#!/usr/bin/env python3
"""
Generate BGE-large embeddings for Strong's Concordance chunks
Adapted for the flat JSON array format used by Strong's concordance data
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer
import time
import os
import argparse

def generate_strongs_embeddings(chunks_file: str, collection_name: str):
    """Generate embeddings for Strong's concordance chunks"""
    
    print("🦉 TinyOwl Strong's Concordance Embedding Pipeline")
    print("=" * 60)
    print(f"📁 Input: {chunks_file}")
    print(f"🗂️ Collection: {collection_name}")
    
    # Initialize BGE model
    print("\n📖 Loading BGE-large-en-v1.5 model...")
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    print(f"✅ Model loaded (dim: {model.get_sentence_embedding_dimension()})")
    
    # Initialize ChromaDB
    print("\n💾 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="vectordb")
    
    # Load chunks (flat JSON array format)
    print(f"\n📚 Loading chunks from {chunks_file}...")
    if not os.path.exists(chunks_file):
        print(f"❌ Chunk file not found: {chunks_file}")
        return
        
    with open(chunks_file, 'r') as f:
        chunks = json.load(f)  # Direct JSON array, not nested
    
    print(f"   📄 Loaded {len(chunks):,} chunks")
    
    # Create/get collection
    try:
        client.delete_collection(collection_name)  # Clear existing
        print(f"🗑️ Cleared existing collection: {collection_name}")
    except:
        print(f"📂 Creating new collection: {collection_name}")
        pass
    
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": f"Strong's Concordance with BGE-large embeddings"}
    )
    
    # Batch process embeddings
    batch_size = 100
    total_embedded = 0
    start_time = time.time()
    
    print(f"\n⚡ Processing {len(chunks):,} chunks in batches of {batch_size}")
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        
        # Extract texts and metadata for ChromaDB
        texts = [chunk['content'] for chunk in batch]
        metadatas = []
        ids = []
        
        for idx, chunk in enumerate(batch):
            # Create unique ChromaDB ID by adding batch position
            # This preserves the logical ID in metadata while ensuring ChromaDB uniqueness
            chromadb_id = f"{chunk['id']}_doc_{total_embedded + idx}"
            ids.append(chromadb_id)
            
            # Prepare metadata for ChromaDB (scalars only, no lists/dicts)
            # Keep original Strong's ID structure in metadata for proper retrieval
            metadata = {
                'concordance_id': chunk['id'],  # Preserve Strong's logical ID
                'source': chunk['source'],
                'layer': chunk['layer'],
                'testament': chunk.get('testament', 'unknown')
            }
            
            # Add type-specific metadata
            if chunk['layer'] == 'word_entry':
                metadata.update({
                    'word': chunk['word'],
                    'osis_id': chunk['osis_id'],
                    'book': chunk['book'],
                    'chapter': str(chunk['chapter']),
                    'verse': str(chunk['verse']),
                    'strong_number': chunk.get('strong_number') or '',  # Convert None to empty string
                    'entry_type': 'concordance_word_entry'
                })
            elif chunk['layer'] == 'strongs_number':
                metadata.update({
                    'strong_number': chunk['strong_number'],
                    'type': chunk['type'],
                    'verse_count': str(chunk['verse_count']),
                    'word_count': str(len(chunk['word_entries'])),
                    'entry_type': 'strongs_number'
                })
            elif chunk['layer'] == 'word_summary':
                metadata.update({
                    'word': chunk['word'],
                    'total_verses': str(chunk['total_verses']),
                    'ot_count': str(chunk['ot_count']),
                    'nt_count': str(chunk['nt_count']),
                    'entry_type': 'word_summary'
                })
            
            metadatas.append(metadata)
        
        # Generate embeddings for batch
        print(f"   🔢 Embedding batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size} ({len(batch)} chunks)...", end="", flush=True)
        
        embeddings = model.encode(texts)
        
        # Add to ChromaDB
        collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=ids
        )
        
        total_embedded += len(batch)
        elapsed = time.time() - start_time
        rate = total_embedded / elapsed
        print(f" ✅ ({rate:.1f} chunks/sec)")
    
    elapsed = time.time() - start_time
    print(f"\n🎉 Embedding complete!")
    print(f"   📊 Total chunks: {total_embedded:,}")
    print(f"   ⏱️ Total time: {elapsed:.1f}s")
    print(f"   ⚡ Average rate: {total_embedded/elapsed:.1f} chunks/sec")
    print(f"   🗂️ Collection: {collection_name}")


def main():
    parser = argparse.ArgumentParser(description='Generate BGE-large embeddings for Strong\'s Concordance')
    parser.add_argument('--chunks_file', required=True, help='Path to JSON chunks file')
    parser.add_argument('--collection_name', required=True, help='ChromaDB collection name')
    
    args = parser.parse_args()
    
    generate_strongs_embeddings(args.chunks_file, args.collection_name)


if __name__ == "__main__":
    main()