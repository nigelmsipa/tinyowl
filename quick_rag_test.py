#!/usr/bin/env python3
"""
Quick RAG test with shorter prompts
"""

import sys
import time
import json
import requests
import chromadb

def quick_rag_test():
    """Quick test with one question"""
    print("🦉 Quick TinyOwl RAG Test")
    print("=" * 40)
    
    # Connect to database
    client = chromadb.PersistentClient(path="vectordb")
    collection = client.get_collection("theology")
    
    print(f"📚 Collection: {collection.count()} documents")
    
    # One simple question
    question = "Who was Ellen G. White?"
    print(f"\n🔍 Question: {question}")
    
    # Retrieve context (just 1 result to keep it fast)
    results = collection.query(
        query_texts=[question],
        n_results=1,
        include=["documents", "metadatas", "distances"]
    )
    
    if results["documents"][0]:
        doc = results["documents"][0][0][:300]  # Limit to 300 chars
        title = results["metadatas"][0][0].get("title", "Unknown")
        
        print(f"📖 Found context from: {title}")
        print(f"📝 Context: {doc}...")
        
        # Simple prompt
        prompt = f"Based on this text: {doc}\n\nWho was Ellen G. White? Answer in 2-3 sentences."
        
        print(f"\n🤖 Asking mistral...")
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 100}  # Limit response length
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "No response")
                print(f"💬 Answer: {answer}")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("❌ No context found")

if __name__ == "__main__":
    quick_rag_test()