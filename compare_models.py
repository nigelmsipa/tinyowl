#!/usr/bin/env python3
"""
Compare different local LLMs with TinyOwl RAG
Tests multiple models on the same questions
"""

import sys
import time
import json
import requests
import chromadb
from datetime import datetime

class ModelComparison:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="vectordb")
        self.collection = self.client.get_collection("theology")
        
        # Available models (you can modify this list)
        self.models = [
            "mistral:latest",
            "phi3:mini", 
            "qwen2.5:7b",
            "qwen2.5-coder:3b"
        ]
        
        # Test questions
        self.questions = [
            "Who was Ellen G. White?",
            "What does the Bible say about the Sabbath?",
            "What is the Great Controversy about?",
            "What does the Bible teach about health?"
        ]
        
        self.results = {}
    
    def get_context(self, question, n_results=2):
        """Get context from RAG database"""
        results = self.collection.query(
            query_texts=[question],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        if not results["documents"][0]:
            return ""
        
        # Format context (keep it short)
        context_parts = []
        for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
            title = metadata.get("title", "Unknown")
            # Limit each source to 200 characters
            short_doc = doc[:200] + "..." if len(doc) > 200 else doc
            context_parts.append(f"{title}: {short_doc}")
        
        return "\\n\\n".join(context_parts)
    
    def test_model(self, model_name, question, context):
        """Test a specific model with a question"""
        prompt = f"Context: {context}\\n\\nQuestion: {question}\\n\\nAnswer briefly (2-3 sentences):"
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 150  # Limit response length
                    }
                },
                timeout=45  # 45 second timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "No response").strip()
                
                return {
                    "success": True,
                    "answer": answer,
                    "time": elapsed_time,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "answer": "",
                    "time": elapsed_time,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "answer": "",
                "time": 0,
                "error": str(e)
            }
    
    def run_comparison(self):
        """Run comparison across all models and questions"""
        print("🦉 TinyOwl RAG Model Comparison")
        print("=" * 50)
        print(f"📚 Database: {self.collection.count()} documents")
        print(f"🤖 Models: {', '.join(self.models)}")
        print(f"❓ Questions: {len(self.questions)}")
        print("=" * 50)
        
        # Test each question
        for q_idx, question in enumerate(self.questions):
            print(f"\\n🔍 Question {q_idx + 1}: {question}")
            print("-" * 40)
            
            # Get context once for this question
            context = self.get_context(question)
            if not context:
                print("❌ No context found, skipping question")
                continue
            
            print(f"📖 Context sources found: {len(context.split('\\n\\n'))} documents")
            
            question_results = {}
            
            # Test each model
            for model in self.models:
                print(f"  🤖 Testing {model}...", end=" ", flush=True)
                
                result = self.test_model(model, question, context)
                question_results[model] = result
                
                if result["success"]:
                    print(f"✅ {result['time']:.1f}s")
                else:
                    print(f"❌ {result['error']}")
            
            self.results[question] = {
                "context": context,
                "model_results": question_results
            }
            
            # Show best answers for this question
            successful_results = [(model, res) for model, res in question_results.items() if res["success"]]
            if successful_results:
                # Sort by response time
                successful_results.sort(key=lambda x: x[1]["time"])
                print(f"\\n  🏆 Fastest: {successful_results[0][0]} ({successful_results[0][1]['time']:.1f}s)")
                print(f"      Answer: {successful_results[0][1]['answer'][:100]}...")
        
        self.print_summary()
        self.save_results()
    
    def print_summary(self):
        """Print overall summary"""
        print("\\n" + "=" * 60)
        print("📊 SUMMARY")
        print("=" * 60)
        
        # Calculate stats for each model
        model_stats = {}
        
        for model in self.models:
            successful = 0
            total_time = 0
            total_questions = 0
            
            for question_data in self.results.values():
                model_result = question_data["model_results"].get(model)
                if model_result:
                    total_questions += 1
                    if model_result["success"]:
                        successful += 1
                        total_time += model_result["time"]
            
            success_rate = (successful / total_questions * 100) if total_questions > 0 else 0
            avg_time = (total_time / successful) if successful > 0 else 0
            
            model_stats[model] = {
                "success_rate": success_rate,
                "avg_time": avg_time,
                "successful": successful,
                "total": total_questions
            }
        
        # Print table
        print(f"{'Model':<20} {'Success Rate':<12} {'Avg Time':<10} {'Status'}")
        print("-" * 60)
        
        # Sort by success rate, then by time
        sorted_models = sorted(model_stats.items(), 
                             key=lambda x: (x[1]["success_rate"], -x[1]["avg_time"]), 
                             reverse=True)
        
        for model, stats in sorted_models:
            success_rate = stats["success_rate"]
            avg_time = stats["avg_time"]
            successful = stats["successful"]
            total = stats["total"]
            
            print(f"{model:<20} {success_rate:>8.1f}%     {avg_time:>6.1f}s     {successful}/{total}")
        
        print("=" * 60)
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_comparison_{timestamp}.json"
        
        output_data = {
            "timestamp": timestamp,
            "models_tested": self.models,
            "questions": self.questions,
            "results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\\n💾 Results saved to: {filename}")

def main():
    comparison = ModelComparison()
    comparison.run_comparison()

if __name__ == "__main__":
    main()