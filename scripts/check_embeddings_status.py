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

        counts = {}
        total_embedded = 0
        for collection in collections:
            try:
                count = collection.count()
                total_embedded += count
                counts[collection.name] = count
                print(f"   📚 {collection.name}: {count:,} embeddings")
            except Exception as e:
                print(f"   ❌ {collection.name}: Error - {e}")

        # KJV/WEB layer completeness
        expected_kjv = {'kjv_verses': 31102, 'kjv_pericopes': 9968, 'kjv_chapters': 1189}
        expected_web = {'web_verses': 31098, 'web_pericopes': 9967, 'web_chapters': 1189}

        print("\n📋 KJV status:")
        for k, exp in expected_kjv.items():
            act = counts.get(k, 0)
            status = "✅" if act == exp else ("⚠️" if act > 0 else "❌")
            print(f"   {status} {k}: {act:,}/{exp:,}")

        print("\n📋 WEB status:")
        for k, exp in expected_web.items():
            act = counts.get(k, 0)
            status = "✅" if act == exp else ("⚠️" if act > 0 else "❌")
            print(f"   {status} {k}: {act:,}/{exp:,}")

        print("\n📋 Strong's status:")
        for k in ('strongs_concordance_entries', 'strongs_numbers', 'strongs_word_summaries'):
            act = counts.get(k, 0)
            status = "✅" if act > 0 else "❌"
            print(f"   {status} {k}: {act:,}")

        print(f"\n📊 TOTAL EMBEDDED across all collections: {total_embedded:,}")

    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")

if __name__ == "__main__":
    check_embeddings_status()
