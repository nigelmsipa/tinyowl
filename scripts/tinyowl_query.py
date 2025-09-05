#!/usr/bin/env python3
"""
TinyOwl @ Feature Query Router
Lightning-fast theological lookups with @ syntax
"""

import chromadb
from sentence_transformers import SentenceTransformer
import re
import json
from typing import List, Dict, Any, Optional

class TinyOwlQuery:
    def __init__(self):
        """Initialize TinyOwl query system"""
        print("🦉 Initializing TinyOwl Query System...")
        
        # Initialize BGE model (same as used for embeddings)
        print("📖 Loading BGE-large-en-v1.5 model...")
        self.model = SentenceTransformer('BAAI/bge-large-en-v1.5')
        
        # Initialize ChromaDB
        print("💾 Connecting to ChromaDB...")
        self.client = chromadb.PersistentClient(path="vectordb")
        
        # Load collections
        self.collections = {}
        collection_names = [
            "strongs_concordance_entries",
            "strongs_numbers", 
            "strongs_word_summaries",
            "kjv_verses",
            "kjv_pericopes",
            "kjv_chapters"
        ]
        
        for name in collection_names:
            try:
                self.collections[name] = self.client.get_collection(name)
                print(f"✅ Loaded collection: {name}")
            except Exception as e:
                print(f"⚠️ Collection {name} not found: {e}")
        
        print("🎯 TinyOwl Query System ready!")
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse @ syntax queries"""
        query = query.strip()
        
        # @word:term - Concordance word lookup
        word_match = re.match(r'@word:(\w+)', query, re.IGNORECASE)
        if word_match:
            return {
                'type': 'word_lookup',
                'term': word_match.group(1).upper(),
                'original_query': query
            }
        
        # @strong:number - Strong's number lookup (H123 or G456 or just 123)
        strong_match = re.match(r'@strong:([HGhg]?\d+)', query, re.IGNORECASE)
        if strong_match:
            number = strong_match.group(1).upper()
            # Add H or G prefix if missing (default to Hebrew for ambiguous)
            if not number.startswith(('H', 'G')):
                number = 'H' + number
            return {
                'type': 'strong_lookup',
                'number': number,
                'original_query': query
            }
        
        # @term - Simple word concordance (shorthand for @word:term)
        simple_match = re.match(r'@(\w+)', query, re.IGNORECASE)
        if simple_match:
            return {
                'type': 'word_lookup',
                'term': simple_match.group(1).upper(),
                'original_query': query
            }
        
        # Regular semantic search
        return {
            'type': 'semantic_search',
            'query': query,
            'original_query': query
        }
    
    def word_lookup(self, term: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Lookup word in Strong's concordance"""
        if "strongs_concordance_entries" not in self.collections:
            return []
        
        collection = self.collections["strongs_concordance_entries"]
        
        # Try exact word match first using metadata filter
        try:
            # Use proper BGE embeddings instead of query_texts
            query_embedding = self.model.encode([term.lower()])
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=max_results,
                where={"word": term.upper()}
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0.0,
                    'source': 'concordance'
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error in word lookup: {e}")
            return []
    
    def strong_lookup(self, number: str, max_results: int = 10) -> Dict[str, Any]:
        """Lookup Strong's number definition and related verses"""
        if "strongs_numbers" not in self.collections:
            return {}
        
        collection = self.collections["strongs_numbers"]
        
        try:
            # Get Strong's number definition
            query_embedding = self.model.encode([number])
            definition_results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=1,
                where={"strong_number": number}
            )
            
            result = {
                'strong_number': number,
                'definition': None,
                'related_verses': []
            }
            
            if definition_results['ids'][0]:
                result['definition'] = {
                    'content': definition_results['documents'][0][0],
                    'metadata': definition_results['metadatas'][0][0]
                }
                
                # Get related concordance entries
                if "strongs_concordance_entries" in self.collections:
                    concordance_col = self.collections["strongs_concordance_entries"]
                    verse_query_embedding = self.model.encode([number])
                    verse_results = concordance_col.query(
                        query_embeddings=verse_query_embedding.tolist(),
                        n_results=max_results,
                        where={"strong_number": number}
                    )
                    
                    for i in range(len(verse_results['ids'][0])):
                        result['related_verses'].append({
                            'content': verse_results['documents'][0][i],
                            'metadata': verse_results['metadatas'][0][i],
                            'distance': verse_results['distances'][0][i] if 'distances' in verse_results else 0.0
                        })
            
            return result
            
        except Exception as e:
            print(f"Error in Strong's lookup: {e}")
            return {}
    
    def semantic_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Semantic search across all collections"""
        query_embedding = self.model.encode([query])
        
        all_results = []
        
        # Search concordance entries
        if "strongs_concordance_entries" in self.collections:
            try:
                results = self.collections["strongs_concordance_entries"].query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=max_results // 2
                )
                
                for i in range(len(results['ids'][0])):
                    all_results.append({
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'source': 'concordance'
                    })
            except Exception as e:
                print(f"Error searching concordance: {e}")
        
        # Search Bible verses
        if "kjv_verses" in self.collections:
            try:
                results = self.collections["kjv_verses"].query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=max_results // 2
                )
                
                for i in range(len(results['ids'][0])):
                    all_results.append({
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'source': 'bible'
                    })
            except Exception as e:
                print(f"Error searching Bible: {e}")
        
        # Sort by relevance (distance)
        all_results.sort(key=lambda x: x['distance'])
        return all_results[:max_results]
    
    def query(self, query_str: str, max_results: int = 20) -> Dict[str, Any]:
        """Main query interface"""
        parsed = self.parse_query(query_str)
        
        print(f"🔍 Query type: {parsed['type']}")
        
        if parsed['type'] == 'word_lookup':
            results = self.word_lookup(parsed['term'], max_results)
            return {
                'query': parsed['original_query'],
                'type': 'word_lookup',
                'term': parsed['term'],
                'results': results,
                'count': len(results)
            }
        
        elif parsed['type'] == 'strong_lookup':
            results = self.strong_lookup(parsed['number'], max_results)
            return {
                'query': parsed['original_query'],
                'type': 'strong_lookup',
                'number': parsed['number'],
                'results': results
            }
        
        elif parsed['type'] == 'semantic_search':
            results = self.semantic_search(parsed['query'], max_results)
            return {
                'query': parsed['original_query'],
                'type': 'semantic_search',
                'results': results,
                'count': len(results)
            }
        
        return {'error': 'Unknown query type'}

def format_result(result: Dict[str, Any]) -> str:
    """Format a single result for display"""
    if result['type'] == 'word_lookup':
        output = [f"🔍 Word Concordance: '{result['term']}' ({result['count']} results)\n"]
        
        for i, res in enumerate(result['results'][:10], 1):
            metadata = res['metadata']
            osis_id = metadata.get('osis_id', 'Unknown')
            strong_num = metadata.get('strong_number', '')
            strong_text = f" [{strong_num}]" if strong_num else ""
            
            output.append(f"{i:2d}. {osis_id}{strong_text}")
            output.append(f"    {res['content'][:100]}...")
            output.append("")
        
        return "\n".join(output)
    
    elif result['type'] == 'strong_lookup':
        output = [f"🔢 Strong's Number: {result['number']}\n"]
        
        if result['results'].get('definition'):
            defn = result['results']['definition']
            output.append(f"📖 Definition: {defn['content']}")
            output.append("")
        
        verses = result['results'].get('related_verses', [])
        if verses:
            output.append(f"📜 Related Verses ({len(verses)} found):")
            output.append("")
            
            for i, verse in enumerate(verses[:10], 1):
                metadata = verse['metadata']
                osis_id = metadata.get('osis_id', 'Unknown')
                output.append(f"{i:2d}. {osis_id}")
                output.append(f"    {verse['content'][:100]}...")
                output.append("")
        
        return "\n".join(output)
    
    elif result['type'] == 'semantic_search':
        output = [f"🧠 Semantic Search: '{result['query']}' ({result['count']} results)\n"]
        
        for i, res in enumerate(result['results'][:10], 1):
            source = res['source'].title()
            distance = res['distance']
            relevance = f"({distance:.3f})"
            
            output.append(f"{i:2d}. [{source}] {relevance}")
            output.append(f"    {res['content'][:100]}...")
            output.append("")
        
        return "\n".join(output)
    
    return str(result)

def main():
    """Interactive query testing"""
    print("🦉 TinyOwl @ Feature Testing")
    print("=" * 50)
    
    try:
        tinyowl = TinyOwlQuery()
        
        # Test queries (using words we know exist)
        test_queries = [
            "@jesus",
            "@word:old", 
            "@strong:175",
            "@strong:G4119",
            "faith and works"
        ]
        
        for query in test_queries:
            print(f"\n🎯 Testing: {query}")
            print("-" * 30)
            
            result = tinyowl.query(query)
            formatted = format_result(result)
            print(formatted)
            
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()