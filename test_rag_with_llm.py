#!/usr/bin/env python3
"""
Test TinyOwl RAG with a local LLM
Simple test with one model to see how well it works
"""

import sys
import time
import json
import requests
import chromadb

def test_rag_with_llm(model="mistral:latest"):
    """Test RAG retrieval + LLM generation"""
    print(f"🦉 Testing TinyOwl RAG + {model}")
    print("=" * 60)
    
    # Connect to database
    client = chromadb.PersistentClient(path="vectordb")
    collection = client.get_collection("theology")
    
    print(f"📚 Connected to theology collection: {collection.count()} documents\n")
    
    # Test questions
    questions = [
        "What does the Bible say about the Sabbath?",
        "Who was Ellen G. White?",
        "What is the Great Controversy about?",
        "What does the Bible teach about health and diet?",
        "What is the sanctuary doctrine in Adventist theology?"
    ]
    
    for i, question in enumerate(questions):
        print(f"🔍 Question {i+1}: {question}")
        print("-" * 50)
        
        # Step 1: Retrieve context
        print("📖 Retrieving relevant context...")
        start_time = time.time()
        
        results = collection.query(
            query_texts=[question],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        retrieval_time = time.time() - start_time
        print(f"   ⏱️ Retrieval time: {retrieval_time:.3f} seconds")
        
        # Format context
        context = ""
        if results["documents"][0]:
            context = "Based on the following religious texts:\n\n"
            for j, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                title = metadata.get("title", "Unknown")
                author = metadata.get("author", "")
                context += f"[Source {j+1}] {title}"
                if author:
                    context += f" by {author}"
                context += f":\n{doc}\n\n"
        
        if not context:
            print("❌ No relevant context found, skipping...")
            continue
            
        # Step 2: Generate answer with LLM
        print("🤖 Generating answer with LLM...")
        
        prompt = f"""{context}

Question: {question}

Please provide a comprehensive answer based on the sources above. Focus on what the religious texts actually say about this topic."""

        try:
            start_llm = time.time()
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            llm_time = time.time() - start_llm
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "No response generated")
                
                print(f"   ⏱️ LLM response time: {llm_time:.3f} seconds")
                print(f"   📊 Total time: {retrieval_time + llm_time:.3f} seconds")
                
                print(f"\n💬 Answer:")
                print(f"{answer}")
                
                # Show which sources were used
                print(f"\n📚 Sources used:")
                for j, metadata in enumerate(results["metadatas"][0]):
                    title = metadata.get("title", "Unknown")
                    author = metadata.get("author", "")
                    similarity = 1 - results["distances"][0][j]
                    print(f"   [{j+1}] {title} {'by ' + author if author else ''} (similarity: {similarity:.3f})")
                    
            else:
                print(f"❌ LLM error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error calling LLM: {e}")
        
        print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    # You can change the model here
    model = "mistral:latest" if len(sys.argv) < 2 else sys.argv[1]
    test_rag_with_llm(model)