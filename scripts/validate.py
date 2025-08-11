#!/usr/bin/env python3
"""
TinyOwl Validation Script

Tests retrieval quality using predefined domain-specific questions.
Helps evaluate and improve the RAG system performance.

Usage:
    python validate.py --domain theology
"""

import os
import sys
import argparse
import yaml
import json
import logging
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional
import time
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("tinyowl-validate")

# Define base paths
BASE_DIR = Path(__file__).parent.parent.absolute()

# Sample theology questions for testing
THEOLOGY_QUESTIONS = [
    "What happened on the seventh day of creation?",
    "Who was the first person to build an ark?",
    "What are the Ten Commandments?",
    "What happened at the tower of Babel?",
    "How did Jesus respond to the woman caught in adultery?",
    "What is the Great Controversy about?",
    "Who was Ellen G. White?",
    "What is the significance of the Sanctuary doctrine?",
    "What does the Bible say about the Sabbath?",
    "What are the main themes in the book of Revelation?"
]


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def load_questions(domain: str) -> List[str]:
    """Load test questions for a specific domain"""
    # First check for domain-specific questions in tests directory
    test_file = BASE_DIR / "tests" / f"{domain}_questions.py"
    
    if test_file.exists():
        # Load questions from the test file
        spec = importlib.util.spec_from_file_location(f"{domain}_questions", test_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Get questions from the module
        questions_var = f"{domain.upper()}_QUESTIONS"
        if hasattr(module, questions_var):
            return getattr(module, questions_var)
    
    # Fall back to built-in questions for theology or return empty list
    if domain == "theology":
        return THEOLOGY_QUESTIONS
    
    logger.warning(f"No questions found for domain: {domain}")
    return []


class ValidationResult:
    """Stores results of validation tests"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.timestamp = datetime.now().isoformat()
        self.results = []
        self.summary = {
            "total_questions": 0,
            "avg_retrieval_time": 0,
            "avg_chunks_retrieved": 0,
        }
    
    def add_result(self, question: str, chunks: List[Dict[str, Any]], retrieval_time: float):
        """Add a test result"""
        result = {
            "question": question,
            "retrieval_time": retrieval_time,
            "chunks_retrieved": len(chunks),
            "chunks": [{
                "id": chunk["id"],
                "text_snippet": chunk["text"][:100] + "..." if len(chunk["text"]) > 100 else chunk["text"],
                "source": chunk["metadata"].get("title", "Unknown"),
                "similarity": 1 - chunk["distance"]  # Convert distance to similarity score
            } for chunk in chunks]
        }
        self.results.append(result)
    
    def calculate_summary(self):
        """Calculate summary statistics"""
        self.summary["total_questions"] = len(self.results)
        
        if self.results:
            self.summary["avg_retrieval_time"] = sum(r["retrieval_time"] for r in self.results) / len(self.results)
            self.summary["avg_chunks_retrieved"] = sum(r["chunks_retrieved"] for r in self.results) / len(self.results)
    
    def save_report(self, output_dir: Path = None):
        """Save validation report to file"""
        self.calculate_summary()
        
        if output_dir is None:
            output_dir = BASE_DIR / "tests" / "results"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"validation_{self.domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file = output_dir / filename
        
        with open(output_file, 'w') as f:
            json.dump({
                "domain": self.domain,
                "timestamp": self.timestamp,
                "summary": self.summary,
                "results": self.results
            }, f, indent=2)
        
        logger.info(f"Validation report saved to {output_file}")
    
    def print_summary(self):
        """Print summary of validation results"""
        self.calculate_summary()
        
        print("\n" + "=" * 50)
        print(f"TinyOwl Validation Results: {self.domain}")
        print("=" * 50)
        print(f"Total questions: {self.summary['total_questions']}")
        print(f"Average retrieval time: {self.summary['avg_retrieval_time']:.3f} seconds")
        print(f"Average chunks retrieved: {self.summary['avg_chunks_retrieved']:.1f}")
        print("=" * 50)
        
        for i, result in enumerate(self.results):
            print(f"\nQuestion {i+1}: {result['question']}")
            print(f"  Retrieval time: {result['retrieval_time']:.3f} seconds")
            print(f"  Top result: {result['chunks'][0]['text_snippet']}")
            print(f"  Source: {result['chunks'][0]['source']}")
            print(f"  Similarity score: {result['chunks'][0]['similarity']:.3f}")
        
        print("\n" + "=" * 50)


class TinyOwlValidator:
    """Validates the retrieval quality of the TinyOwl system"""
    
    def __init__(self, domain: str):
        """Initialize the validator for a specific domain"""
        self.domain = domain
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
        
        # Load collection
        collection_name = self.models_config["vector_db"]["collections"].get(domain, {}).get("name", domain)
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to load collection '{collection_name}': {e}")
            sys.exit(1)
    
    def retrieve(self, query: str, n_results: int = 5) -> (List[Dict[str, Any]], float):
        """Retrieve relevant chunks and measure retrieval time"""
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })
        
        retrieval_time = time.time() - start_time
        
        return formatted_results, retrieval_time
    
    def validate(self, questions: List[str]) -> ValidationResult:
        """Run validation on a list of test questions"""
        if not questions:
            logger.error(f"No validation questions found for domain: {self.domain}")
            sys.exit(1)
        
        logger.info(f"Starting validation with {len(questions)} questions for domain: {self.domain}")
        
        result = ValidationResult(self.domain)
        
        for question in questions:
            logger.info(f"Testing question: {question}")
            
            retrieved_chunks, retrieval_time = self.retrieve(question)
            result.add_result(question, retrieved_chunks, retrieval_time)
        
        return result


def main():
    parser = argparse.ArgumentParser(description="TinyOwl Validation Script")
    parser.add_argument("--domain", default="theology", help="Domain to validate")
    parser.add_argument("--save-report", action="store_true", help="Save validation report to file")
    args = parser.parse_args()
    
    # Load test questions for the domain
    questions = load_questions(args.domain)
    
    # Run validation
    validator = TinyOwlValidator(args.domain)
    results = validator.validate(questions)
    
    # Print results summary
    results.print_summary()
    
    # Save report if requested
    if args.save_report:
        results.save_report()


if __name__ == "__main__":
    main()
