#!/usr/bin/env python3
"""
Check current embedding status in ChromaDB
"""

import chromadb

def check_embeddings_status():
    """Check what's actually embedded in ChromaDB"""
    
    print("🔍 ChromaDB Embedding Status Check")
    print("=" * 50)
    
    try:
        client = chromadb.PersistentClient(path="vectordb")
        collections = client.list_collections()
        
        print(f"📊 Found {len(collections)} collections:")
        
        total_embedded = 0
        
        for collection in collections:
            try:
                count = collection.count()
                total_embedded += count
                print(f"   📚 {collection.name}: {count:,} embeddings")
            except Exception as e:
                print(f"   ❌ {collection.name}: Error - {e}")
        
        print(f"\n🎯 TOTAL EMBEDDED: {total_embedded:,} chunks")
        print(f"🎯 TARGET: 42,259 KJV chunks")
        print(f"📈 PROGRESS: {(total_embedded/42259)*100:.1f}% complete")
        
        # Expected breakdown
        expected = {
            'kjv_verses': 31102,
            'kjv_pericopes': 9968, 
            'kjv_chapters': 1189
        }
        
        print(f"\n📋 Expected vs Actual:")
        for name, exp_count in expected.items():
            try:
                actual_collection = client.get_collection(name)
                actual_count = actual_collection.count()
                status = "✅" if actual_count == exp_count else "⚠️"
                print(f"   {status} {name}: {actual_count:,}/{exp_count:,}")
            except Exception as e:
                print(f"   ❌ {name}: Not found or error")
        
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")

if __name__ == "__main__":
    check_embeddings_status()