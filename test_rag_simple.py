#!/usr/bin/env python3
"""
Simple RAG test for TinyOwl database
Tests retrieval quality and shows relevant passages
"""

import sys
import time
import chromadb
from pathlib import Path

# Test questions
TEST_QUESTIONS = [
    "What does the Bible say about the Sabbath?",
    "Who was Ellen G. White?",
    "What is the Great Controversy about?",
    "What happened on the seventh day of creation?",
    "What are the Ten Commandments?",
    "What does the Bible teach about health?",
    "What is the sanctuary doctrine?",
    "How should Christians approach education?",
    "What does the Bible say about the second coming?",
    "What are characteristics of good leadership?"
]

def test_rag_retrieval():
    """Test RAG retrieval quality"""
    print("🦉 TinyOwl RAG Retrieval Test")
    print("=" * 50)
    
    try:
        # Connect to database
        client = chromadb.PersistentClient(path="vectordb")
        collection = client.get_collection("theology")
        
        print(f"📚 Connected to theology collection: {collection.count()} documents\n")
        
        # Test each question
        for i, question in enumerate(TEST_QUESTIONS):
            print(f"🔍 Question {i+1}: {question}")
            print("-" * 40)
            
            # Retrieve relevant passages
            start_time = time.time()
            results = collection.query(
                query_texts=[question],
                n_results=3,
                include=["documents", "metadatas", "distances"]
            )
            retrieval_time = time.time() - start_time
            
            # Display results
            print(f"⏱️  Retrieval time: {retrieval_time:.3f} seconds")
            
            if results["documents"][0]:
                avg_similarity = 1 - (sum(results["distances"][0]) / len(results["distances"][0]))
                print(f"📊 Average similarity: {avg_similarity:.3f}")
                
                print(f"\n📖 Top 3 relevant passages:")
                for j, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0], 
                    results["metadatas"][0], 
                    results["distances"][0]
                )):
                    title = metadata.get("title", "Unknown")
                    author = metadata.get("author", "")
                    similarity = 1 - distance
                    
                    print(f"\n[{j+1}] 📚 {title} {'by ' + author if author else ''}")
                    print(f"    🎯 Similarity: {similarity:.3f}")
                    print(f"    📝 {doc[:200]}...")
            else:
                print("❌ No relevant passages found")
            
            print("\n" + "=" * 50 + "\n")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you're in the tinyowl directory with the vectordb folder")

if __name__ == "__main__":
    test_rag_retrieval()