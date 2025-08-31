#!/usr/bin/env python3
"""
TinyOwl Chat Interface

A simple chat interface that uses RAG (Retrieval Augmented Generation)
to answer questions based on the ingested knowledge base.

Usage:
    python chat.py [--model MODEL_NAME]
"""

import os
import sys
import argparse
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time

import chromadb
import requests
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("tinyowl-chat")

# Define base paths
BASE_DIR = Path(__file__).parent.parent.absolute()


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class TinyOwlChat:
    """RAG-based chat interface for TinyOwl knowledge system"""
    
    def __init__(self, model_name: str = None):
        """Initialize the chat interface"""
        self.models_config = load_config(BASE_DIR / "configs" / "models.yaml")
        
        # Set up embedding model
        emb_model = self.models_config["embeddings"]["default"]["name"]
        logger.info(f"Loading embedding model: {emb_model}")
        self.embedding_model = SentenceTransformer(emb_model)
        
        # Set up ChromaDB client
        db_path = BASE_DIR / "vectordb"
        if not db_path.exists():
            logger.error(f"Vector database not found at {db_path}. Run ingest.py first.")
            sys.exit(1)
            
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collections = {}  # Will be loaded on demand
        
        # Set up LLM
        self.model_name = model_name or self.models_config["llms"]["rag"]["name"]
        logger.info(f"Using LLM: {self.model_name}")
        
        # History for conversation context
        self.history = []
    
    def load_collection(self, domain: str):
        """Load a collection for a specific domain"""
        if domain not in self.collections:
            collection_name = self.models_config["vector_db"]["collections"].get(domain, {}).get("name", domain)
            try:
                self.collections[domain] = self.client.get_collection(name=collection_name)
                logger.info(f"Loaded collection: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to load collection '{collection_name}': {e}")
                return None
        return self.collections[domain]
    
    def get_adjacent_chunks(self, collection, chunk_id: str, n: int = 1) -> List[Dict[str, Any]]:
        """Get n adjacent chunks before and after the given chunk_id"""
        try:
            # Extract the numeric part of the chunk ID (e.g., "bible_geneva_00123" -> 123)
            chunk_num = int(chunk_id.split('_')[-1])
            adjacent_chunks = []
            
            # Get the chunk and its metadata
            chunk_data = collection.get(ids=[chunk_id], include=["metadatas", "documents"])
            if not chunk_data['ids']:
                return []
                
            base_metadata = chunk_data['metadatas'][0]
            base_source = base_metadata.get('source_id', '')
            
            # Get n chunks before and after
            for offset in range(-n, n + 1):
                if offset == 0:
                    continue  # Skip the original chunk
                    
                adjacent_num = chunk_num + offset
                if adjacent_num < 0:
                    continue  # Skip negative chunk numbers
                    
                # Format the adjacent chunk ID with leading zeros
                adjacent_id = f"{'_'.join(chunk_id.split('_')[:-1])}_{adjacent_num:05d}"
                
                try:
                    # Try to get the adjacent chunk
                    adj_data = collection.get(
                        ids=[adjacent_id],
                        include=["metadatas", "documents"]
                    )
                    
                    if adj_data['ids'] and adj_data['metadatas'][0].get('source_id') == base_source:
                        adjacent_chunks.append({
                            'id': adjacent_id,
                            'text': adj_data['documents'][0],
                            'metadata': adj_data['metadatas'][0],
                            'score': 0.9  # Slightly lower score for adjacent chunks
                        })
                except Exception as e:
                    logger.debug(f"Error fetching adjacent chunk {adjacent_id}: {e}")
            
            return adjacent_chunks
            
        except (ValueError, IndexError, AttributeError) as e:
            logger.warning(f"Error processing adjacent chunks for {chunk_id}: {e}")
            return []
    
    def retrieve(self, query: str, domain: str = None, n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant chunks from the knowledge base with neighbor expansion"""
        domains = [domain] if domain else list(self.models_config["vector_db"]["collections"].keys())
        
        all_results = []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search across all specified domains
        for d in domains:
            collection = self.load_collection(d)
            if not collection:
                continue
                
            try:
                # First, get the top-k results
                # Get n_results * 2 to have more candidates before neighbor expansion
                base_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results * 2,
                    include=["metadatas", "documents", "distances"]
                )
                
                # Process base results
                seen_chunks = set()
                for i in range(len(base_results['ids'][0])):
                    chunk_id = base_results['ids'][0][i]
                    if chunk_id in seen_chunks:
                        continue
                        
                    metadata = base_results['metadatas'][0][i]
                    text = base_results['documents'][0][i]
                    distance = base_results['distances'][0][i]
                    
                    # Add the main result
                    all_results.append({
                        'id': chunk_id,
                        'text': text,
                        'metadata': metadata,
                        'score': 1.0 - distance,  # Convert distance to similarity score
                        'domain': d
                    })
                    seen_chunks.add(chunk_id)
                    
                    # Get adjacent chunks (±1) for this result
                    adjacent_chunks = self.get_adjacent_chunks(collection, chunk_id, n=1)
                    
                    # Add adjacent chunks if not already in results
                    for adj in adjacent_chunks:
                        if adj['id'] not in seen_chunks:
                            all_results.append({
                                **adj,
                                'domain': d,
                                'is_neighbor': True  # Mark as neighbor for display
                            })
                            seen_chunks.add(adj['id'])
            except Exception as e:
                logger.error(f"Error querying collection for domain '{d}': {e}")
        
        # Sort by distance (similarity)
        all_results = sorted(all_results, key=lambda x: x["score"], reverse=True)

        def fetch_by_id(col, cid: str) -> Optional[Dict[str, Any]]:
            try:
                got = col.get(ids=[cid], include=["documents", "metadatas"])
                if got and got.get("ids") and got["ids"][0]:
                    return {
                        "id": got["ids"][0],
                        "text": got["documents"][0],
                        "metadata": got["metadatas"][0],
                        "distance": None,
                    }
            except Exception:
                return None
            return None

        expanded: List[Dict[str, Any]] = []
        seen_ids = set()
        max_context = max(n_results * 2, n_results)  # cap context to avoid bloat
        for hit in all_results[:n_results]:
            expanded.append(hit)
            seen_ids.add(hit["id"])
            # Try to fetch neighbors from same collection/domain
            col = self.load_collection(hit["domain"]) if isinstance(hit.get("domain"), str) else None
            prefix, num = parse_id(hit["id"])
            if col and num is not None:
                for delta in (-1, 1):
                    neighbor_id = f"{prefix}_{num+delta:06d}"
                    if neighbor_id in seen_ids:
                        continue
                    nb = fetch_by_id(col, neighbor_id)
                    if nb and nb.get("metadata", {}).get("source_id") == hit["metadata"].get("source_id"):
                        expanded.append({**nb, "domain": hit["domain"]})
                        seen_ids.add(neighbor_id)
                        if len(expanded) >= max_context:
                            break
            if len(expanded) >= max_context:
                break

        return expanded
    
    def format_context(self, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into context for the LLM"""
        context = "Information from the knowledge base:\n\n"
        
        for i, chunk in enumerate(retrieved_chunks):
            metadata = chunk["metadata"]
            # Prefer scripture reference when available
            ref = metadata.get("verse_reference")
            if ref:
                source_info = f"{metadata.get('title', 'Unknown')} — {ref}"
            else:
                source_info = f"{metadata.get('title', 'Unknown')}"

            if "page_reference" in metadata and not ref:
                source_info += f", page {metadata['page_reference']}"
            if "author" in metadata:
                source_info += f" by {metadata['author']}"

            context += f"[{i+1}] {chunk['text']}\n"
            context += f"Source: {source_info}\n\n"
        
        return context
    
    def generate_response(self, query: str, context: str) -> str:
        """Generate a response using the configured LLM"""
        llm_config = self.models_config["llms"]["rag"]
        
        # For a local model
        if llm_config["provider"] == "local":
            # Placeholder for local model inference
            # In a real implementation, this would use a local model API
            response = "This is a placeholder response. In a real implementation, this would come from a local LLM like LlamaCpp."
            return response
        
        # For OpenAI API (example)
        elif llm_config["provider"] == "openai":
            # Check if API key is set
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return "Error: OpenAI API key not found in environment variables (OPENAI_API_KEY)"
            
            # Format prompt
            system_prompt = llm_config.get("system_prompt", "You are a helpful assistant.")
            
            # Simple text completion prompt (would use Chat API in real implementation)
            prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
            
            # This is a placeholder for the actual API call
            # In a real implementation, use the OpenAI Python client
            response = "This is a placeholder for an OpenAI API response. Set up your API key to get real responses."
            
            return response
            
        else:
            return "Error: Unsupported LLM provider specified in config"
    
    def answer(self, query: str, domain: str = None) -> str:
        """Answer a question using RAG"""
        # Add query to history
        self.history.append({"role": "user", "content": query})
        
        # Retrieve relevant chunks
        retrieved_chunks = self.retrieve(query, domain=domain)
        
        if not retrieved_chunks:
            response = "I couldn't find any relevant information in the knowledge base."
            self.history.append({"role": "assistant", "content": response})
            return response
        
        # Format context for the LLM
        context = self.format_context(retrieved_chunks)
        
        # Generate response
        response = self.generate_response(query, context)
        
        # Add response to history
        self.history.append({"role": "assistant", "content": response})
        
        return response
    
    def run_interactive(self):
        """Run an interactive chat session"""
        print("TinyOwl Chat Interface")
        print("Type 'exit' or 'quit' to end the session")
        print("Type 'domain:theology' to set a specific domain")
        
        current_domain = None
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                # Check for domain command
                if user_input.startswith("domain:"):
                    current_domain = user_input[7:].strip()
                    print(f"Domain set to: {current_domain}")
                    continue
                
                # Process query
                start_time = time.time()
                response = self.answer(user_input, domain=current_domain)
                end_time = time.time()
                
                print(f"\nTinyOwl: {response}")
                print(f"\n[Answered in {end_time - start_time:.2f}s]")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="TinyOwl Chat Interface")
    parser.add_argument("--model", help="Model name to use for responses")
    args = parser.parse_args()
    
    chat = TinyOwlChat(model_name=args.model)
    chat.run_interactive()


if __name__ == "__main__":
    main()
