#!/usr/bin/env python3
"""
Simple ChromaDB Query Script
A minimal interface to query the theology database and get AI-powered answers.

Usage:
    # Single query
    python simple_query.py "What does the Bible say about prayer?"
    
    # Interactive mode (no arguments)
    python simple_query.py
    
    # Using the launcher script
    ./query.sh "What is the Sabbath?"

Requirements:
    - OPENAI_API_KEY environment variable must be set
    - ChromaDB vectordb/ directory with 'theology' collection must exist
    - Virtual environment with required packages (openai, chromadb, etc.)

This script does exactly what you asked for:
1. Connects to existing ChromaDB collection "theology"
2. Takes a question as input  
3. Searches vector database for relevant passages
4. Sends passages + question to OpenAI GPT-3.5-turbo
5. Returns focused answer based on sources
6. Simple function-based approach without fancy UI
"""

import os
import sys
import chromadb
import openai
from typing import Optional


class SimpleTheologyQuery:
    """Simple interface to query ChromaDB and get OpenAI-powered answers"""
    
    def __init__(self, db_path: str = "vectordb", collection_name: str = None):
        """Initialize the query system"""
        self.db_path = db_path
        # Prefer live collections; fall back to legacy
        self.collection_name = collection_name
        self.collection = None
        self.client = None
        
        # Setup OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("ERROR: OPENAI_API_KEY environment variable not set")
            sys.exit(1)
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        
        # Connect to ChromaDB
        self._connect_to_database()
    
    def _connect_to_database(self):
        """Connect to the ChromaDB database"""
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            if not self.collection_name:
                # Try KJV/WEB verses first, then legacy 'theology'
                for cand in ("kjv_verses", "web_verses", "theology"):
                    try:
                        self.collection = self.client.get_collection(cand)
                        self.collection_name = cand
                        break
                    except Exception:
                        continue
                if not self.collection:
                    raise ValueError("No suitable collection found (kjv_verses/web_verses/theology)")
            else:
                self.collection = self.client.get_collection(self.collection_name)
            doc_count = self.collection.count()
            print(f"Connected to {self.collection_name} database ({doc_count} documents)")
        except Exception as e:
            print(f"ERROR: Failed to connect to database: {e}")
            sys.exit(1)
    
    def search_database(self, query: str, n_results: int = 5) -> str:
        """Search the vector database for relevant passages"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results["documents"][0]:
                return ""
            
            # Format the retrieved passages
            passages = []
            for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                title = metadata.get("title", "Unknown Source")
                author = metadata.get("author", "")
                
                # Create source citation
                source = f"{title}"
                if author:
                    source += f" by {author}"
                
                # Limit document length to prevent token overflow
                doc_text = doc[:500] + "..." if len(doc) > 500 else doc
                
                passages.append(f"Source {i+1} - [{source}]:\n{doc_text}")
            
            return "\n\n".join(passages)
            
        except Exception as e:
            print(f"ERROR: Database search failed: {e}")
            return ""
    
    def get_ai_answer(self, question: str, context: str, model: str = "gpt-3.5-turbo") -> str:
        """Get an AI-powered answer based on the context"""
        
        if not context:
            prompt = f"""You are a theological assistant. I couldn't find specific relevant passages in the database for this question. Please provide a helpful general response.

Question: {question}

Response:"""
        else:
            prompt = f"""You are a theological assistant specializing in Seventh-day Adventist doctrine and Biblical teachings.

INSTRUCTIONS:
- Answer the question based primarily on the provided source passages
- Cite which sources you're referencing in your answer
- If the sources don't fully address the question, mention that
- Keep your response focused and concise
- Use quotes from the sources when appropriate

RELEVANT PASSAGES:
{context}

QUESTION: {question}

ANSWER:"""

        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                return "ERROR: No response generated from OpenAI"
                
        except Exception as e:
            return f"ERROR: OpenAI API call failed: {e}"
    
    def query(self, question: str, n_results: int = 5) -> str:
        """Main query function: search database + get AI answer"""
        print(f"Searching for: {question}")
        print("=" * 50)
        
        # Search the database
        context = self.search_database(question, n_results)
        
        if context:
            print("✓ Found relevant passages in database")
        else:
            print("⚠ No relevant passages found in database")
        
        # Get AI answer
        print("Getting AI-powered answer...")
        answer = self.get_ai_answer(question, context)
        
        return answer


def main():
    """Simple command line interface"""
    if len(sys.argv) != 2:
        print("Usage: python simple_query.py \"Your theological question\"")
        print("Example: python simple_query.py \"What does the Bible say about prayer?\"")
        sys.exit(1)
    
    question = sys.argv[1]
    
    # Initialize the query system
    query_system = SimpleTheologyQuery()
    
    # Get the answer
    answer = query_system.query(question)
    
    # Print the result
    print("\nANSWER:")
    print("=" * 50)
    print(answer)
    print()


def interactive_mode():
    """Interactive mode for multiple queries"""
    print("TinyOwl Simple Query - Interactive Mode")
    print("Type 'quit' to exit\n")
    
    query_system = SimpleTheologyQuery()
    
    while True:
        try:
            question = input("Enter your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            print()
            answer = query_system.query(question)
            
            print("\nANSWER:")
            print("=" * 50)
            print(answer)
            print("\n" + "=" * 50 + "\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"ERROR: {e}")


if __name__ == "__main__":
    # If no arguments provided, run in interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
    else:
        main()
