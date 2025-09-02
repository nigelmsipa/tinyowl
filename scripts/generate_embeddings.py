#!/usr/bin/env python3
"""
Generate BGE-large embeddings for hierarchical KJV chunks
"""

import json
import chromadb
from sentence_transformers import SentenceTransformer
import time
import os

def generate_embeddings():
    """Generate embeddings for all KJV chunk layers"""
    
    print("🚀 BGE-Large Embedding Generation Pipeline")
    print("=" * 60)
    
    # Initialize BGE model
    print("📖 Loading BGE-large-en-v1.5 model...")
    model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    print(f"✅ Model loaded (dim: {model.get_sentence_embedding_dimension()})")
    
    # Initialize ChromaDB
    print("\n💾 Initializing ChromaDB...")
    client = chromadb.PersistentClient(path="vectordb")
    
    # Process only chapters (verses and pericopes already complete)
    layers = [
        ("chapters", "kjv_chapters_chunks.json", "broad themes")
    ]
    
    total_embedded = 0
    start_time = time.time()
    
    for layer_name, filename, description in layers:
        print(f"\n📚 Processing {layer_name} layer ({description})")
        
        # Load chunks
        chunk_path = f"domains/theology/chunks/{filename}"
        if not os.path.exists(chunk_path):
            print(f"❌ Chunk file not found: {chunk_path}")
            continue
            
        with open(chunk_path, 'r') as f:
            chunk_data = json.load(f)
        
        chunks = chunk_data['chunks']  # Extract nested chunks
        print(f"   📄 Loaded {len(chunks):,} chunks")
        
        # Create/get collection
        collection_name = f"kjv_{layer_name}"
        try:
            client.delete_collection(collection_name)  # Clear existing
        except:
            pass
        
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": f"KJV {layer_name} with BGE-large embeddings"}
        )
        
        # Batch process embeddings
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            # Extract texts and metadata
            texts = [chunk['content'] for chunk in batch]
            metadatas = []
            ids = []
            
            for chunk in batch:
                # Extract metadata from nested structure
                chunk_metadata = chunk['metadata']
                
                # Handle different ID structures (verses vs pericopes vs chapters)
                if 'osis_id' in chunk:
                    chunk_id = chunk['osis_id']
                    metadata = {'osis_id': chunk['osis_id']}
                elif 'osis_id_start' in chunk:
                    chunk_id = chunk['id']  # Use the generated ID for pericopes/chapters
                    metadata = {'osis_id_start': chunk['osis_id_start']}
                    # Only add osis_id_end if it exists (pericopes have it, chapters might not)
                    if 'osis_id_end' in chunk:
                        metadata['osis_id_end'] = chunk['osis_id_end']
                else:
                    chunk_id = chunk['id']
                    metadata = {}
                
                # Common metadata
                metadata.update({
                    'book_id': chunk_metadata['book_id'],
                    'layer': chunk_metadata['layer'],
                    'translation': chunk_metadata.get('translation', 'kjv'),
                    'authority_level': chunk_metadata.get('authority_level', 'scripture')
                })
                
                if 'chapter' in chunk_metadata:
                    metadata['chapter'] = str(chunk_metadata['chapter'])
                if 'verse' in chunk_metadata:
                    metadata['verse'] = str(chunk_metadata['verse'])
                if 'verses' in chunk_metadata:
                    if isinstance(chunk_metadata['verses'], list):
                        metadata['verses'] = ','.join(map(str, chunk_metadata['verses']))
                    else:
                        metadata['verses'] = str(chunk_metadata['verses'])
                if 'verse_count' in chunk_metadata:
                    metadata['verse_count'] = str(chunk_metadata['verse_count'])
                
                metadatas.append(metadata)
                ids.append(chunk_id)
            
            # Generate embeddings
            embeddings = model.encode(texts, convert_to_tensor=False)
            
            # Add to collection
            collection.add(
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                documents=texts,
                ids=ids
            )
            
            processed = min(i + batch_size, len(chunks))
            print(f"   ⚡ Embedded {processed:,}/{len(chunks):,} chunks", end='\r')
        
        print(f"\n   ✅ {layer_name} layer complete: {len(chunks):,} embeddings")
        total_embedded += len(chunks)
    
    # Final summary
    elapsed = time.time() - start_time
    print(f"\n🎉 EMBEDDING GENERATION COMPLETE!")
    print(f"⏱️  Total time: {elapsed:.1f} seconds") 
    print(f"📊 Total embedded: {total_embedded:,} chunks")
    print(f"🚀 Rate: {total_embedded/elapsed:.0f} chunks/second")
    print(f"💾 Collections: kjv_verses, kjv_pericopes, kjv_chapters")

if __name__ == "__main__":
    generate_embeddings()