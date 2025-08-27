#!/usr/bin/env python3
"""
Test TinyOwl RAG with different local LLMs
Compares performance and quality across multiple local models
"""

import sys
import os
import time
import json
from pathlib import Path
import chromadb
import subprocess
import requests
from typing import List, Dict, Any

# Test questions for theology domain
TEST_QUESTIONS = [
    "What does the Bible say about the Sabbath?",
    "Who was Ellen G. White and what did she write?",
    "What is the Great Controversy about?",
    "What happened on the seventh day of creation?",
    "What are the main themes in the book of Revelation?",
    "What does the Bible teach about health and diet?",
    "What is the significance of the sanctuary doctrine?",
    "How should Christians approach education?",
    "What does the Bible say about the second coming of Christ?",
    "What are the characteristics of true Christian leadership?"
]

class RAGTester:
    def __init__(self, db_path: str = "vectordb"):
        """Initialize the RAG tester"""
        print("🦉 Initializing TinyOwl RAG Tester")
        
        # Connect to ChromaDB
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_collection("theology")
        
        print(f"📚 Connected to theology collection: {self.collection.count()} documents")
        
        # Available local LLM endpoints (assuming Ollama is running)
        self.local_models = {
            "llama3.2": {"url": "http://localhost:11434", "model": "llama3.2"},
            "qwen2.5": {"url": "http://localhost:11434", "model": "qwen2.5"},
            "mistral": {"url": "http://localhost:11434", "model": "mistral"},
            "phi3": {"url": "http://localhost:11434", "model": "phi3"},
        }
    
    def retrieve_context(self, query: str, n_results: int = 5) -> List[Dict]:
        """Retrieve relevant context from ChromaDB"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        return formatted_results
    
    def format_context(self, context_chunks: List[Dict]) -> str:
        """Format retrieved chunks for LLM prompt"""
        context = "Relevant information from the knowledge base:\n\n"
        
        for i, chunk in enumerate(context_chunks):
            title = chunk["metadata"].get("title", "Unknown")
            author = chunk["metadata"].get("author", "")
            
            context += f"[Source {i+1}] {title}"
            if author:
                context += f" by {author}"
            context += f"\n{chunk['text']}\n\n"
        
        return context
    
    def query_ollama(self, model_config: Dict, prompt: str) -> Dict:
        """Query a local Ollama model"""
        try:
            payload = {
                "model": model_config["model"],
                "prompt": prompt,
                "stream": False
            }
            
            start_time = time.time()
            response = requests.post(
                f"{model_config['url']}/api/generate",
                json=payload,
                timeout=60
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "response": result.get("response", ""),
                    "time": end_time - start_time,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "response": "",
                    "time": end_time - start_time,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "time": 0,
                "error": str(e)
            }
    
    def test_model(self, model_name: str, model_config: Dict, questions: List[str]) -> Dict:
        """Test a specific model with all questions"""
        print(f"\n🤖 Testing model: {model_name}")
        print("=" * 50)
        
        results = {
            "model": model_name,
            "config": model_config,
            "test_results": [],
            "summary": {
                "total_questions": len(questions),
                "successful_responses": 0,
                "failed_responses": 0,
                "avg_response_time": 0,
                "avg_retrieval_quality": 0
            }
        }
        
        for i, question in enumerate(questions):
            print(f"\n📝 Question {i+1}/{len(questions)}: {question}")
            
            # Retrieve context
            start_retrieval = time.time()
            context_chunks = self.retrieve_context(question)
            retrieval_time = time.time() - start_retrieval
            
            if not context_chunks:
                print("❌ No relevant context found")
                continue
            
            # Format prompt
            context = self.format_context(context_chunks)
            prompt = f"""Based on the following information from religious texts, please answer the question comprehensively and accurately.

{context}

Question: {question}

Answer:"""
            
            # Query the model
            result = self.query_ollama(model_config, prompt)
            
            # Store result
            test_result = {
                "question": question,
                "retrieval_time": retrieval_time,
                "context_chunks": len(context_chunks),
                "avg_similarity": 1 - sum(c["distance"] for c in context_chunks) / len(context_chunks),
                "llm_response": result
            }
            results["test_results"].append(test_result)
            
            # Print results
            if result["success"]:
                print(f"✅ Response time: {result['time']:.2f}s")
                print(f"📊 Context: {len(context_chunks)} chunks, avg similarity: {test_result['avg_similarity']:.3f}")
                print(f"💬 Response: {result['response'][:200]}...")
                results["summary"]["successful_responses"] += 1
            else:
                print(f"❌ Failed: {result['error']}")
                results["summary"]["failed_responses"] += 1
        
        # Calculate summary statistics
        successful_tests = [r for r in results["test_results"] if r["llm_response"]["success"]]
        if successful_tests:
            results["summary"]["avg_response_time"] = sum(r["llm_response"]["time"] for r in successful_tests) / len(successful_tests)
            results["summary"]["avg_retrieval_quality"] = sum(r["avg_similarity"] for r in successful_tests) / len(successful_tests)
        
        return results
    
    def check_available_models(self) -> List[str]:
        """Check which models are available in Ollama"""
        available = []
        
        try:
            # Check if Ollama is running
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model["name"].split(":")[0] for model in models_data.get("models", [])]
                
                # Filter to only include models we want to test
                for model_key, config in self.local_models.items():
                    if config["model"] in available_models:
                        available.append(model_key)
                
            print(f"🔍 Available models: {available}")
            
        except Exception as e:
            print(f"⚠️  Could not check Ollama models: {e}")
            print("Make sure Ollama is running: ollama serve")
        
        return available
    
    def run_comparison(self, questions: List[str] = None) -> Dict:
        """Run comparison across all available models"""
        if questions is None:
            questions = TEST_QUESTIONS
        
        print("🧪 Starting RAG + LLM Comparison Test")
        print(f"📋 Testing {len(questions)} questions")
        
        # Check available models
        available_models = self.check_available_models()
        
        if not available_models:
            print("❌ No models available. Make sure Ollama is running and models are installed.")
            return {}
        
        # Test each model
        all_results = {}
        for model_name in available_models:
            model_config = self.local_models[model_name]
            results = self.test_model(model_name, model_config, questions)
            all_results[model_name] = results
        
        # Print comparison summary
        self.print_comparison_summary(all_results)
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"rag_llm_comparison_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        return all_results
    
    def print_comparison_summary(self, results: Dict):
        """Print a summary comparison of all models"""
        print("\n" + "=" * 70)
        print("🏆 MODEL COMPARISON SUMMARY")
        print("=" * 70)
        
        # Print header
        print(f"{'Model':<15} {'Success Rate':<12} {'Avg Time':<10} {'Avg Quality':<12}")
        print("-" * 70)
        
        # Sort models by success rate
        sorted_models = sorted(results.items(), 
                             key=lambda x: x[1]["summary"]["successful_responses"], 
                             reverse=True)
        
        for model_name, model_results in sorted_models:
            summary = model_results["summary"]
            success_rate = summary["successful_responses"] / summary["total_questions"] * 100
            avg_time = summary["avg_response_time"]
            avg_quality = summary["avg_retrieval_quality"]
            
            print(f"{model_name:<15} {success_rate:>8.1f}%    {avg_time:>6.1f}s     {avg_quality:>8.3f}")
        
        print("=" * 70)

def main():
    print("🦉 TinyOwl RAG + Local LLM Tester")
    
    # Initialize tester
    tester = RAGTester()
    
    # Run the comparison
    results = tester.run_comparison()
    
    if results:
        print("\n🎉 Testing completed! Check the JSON file for detailed results.")
    else:
        print("\n❌ Testing failed. Make sure Ollama is running with some models installed.")
        print("Example setup:")
        print("  ollama serve")
        print("  ollama pull llama3.2")
        print("  ollama pull qwen2.5")

if __name__ == "__main__":
    main()