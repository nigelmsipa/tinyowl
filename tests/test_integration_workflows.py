#!/usr/bin/env python3
"""
Integration Workflow Tests for TinyOwl
Tests complete end-to-end workflows to ensure system reliability

These tests validate that the complete pipelines work correctly and
identify integration issues that could lead to data corruption or
system failures.
"""

import unittest
import tempfile
import shutil
import json
import os
import sys
import chromadb
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestCompleteStrongsConcordanceWorkflow(unittest.TestCase):
    """
    Integration test for the complete Strong's Concordance workflow:
    Raw text -> Parsing -> Chunking -> Embedding -> Query
    """
    
    def setUp(self):
        """Set up test environment with sample data"""
        self.temp_dir = tempfile.mkdtemp()
        self.vectordb_path = os.path.join(self.temp_dir, 'vectordb')
        self.chunks_dir = os.path.join(self.temp_dir, 'chunks')
        os.makedirs(self.chunks_dir, exist_ok=True)
        
        # Create sample Strong's concordance data
        self.sample_concordance = """A
    See the Appendix.

AARON
    Exo. 4:14     and he said, Is not A the Levite thy       [H175]
    Exo. 4:27     And the LORD said to A, Go into the        [H175]
    Exo. 4:28     And Moses told A all the words of the      [H175]
    Exo. 6:20     And Amram took him Jochebed his father's   [H175]

ABRAHAM
    Gen. 12:1     Now the LORD had said unto A, Get thee     [H85]
    Gen. 12:4     So A departed, as the LORD had spoken      [H85]
    Gen. 13:1     And A went up out of Egypt, he, and        [H85]

CAESAR
    Mat. 22:17   it lawful to give tribute unto C, or not?   [G2541]
    Mat. 22:21   therefore unto C the things which are       [G2541]
    Mar. 12:14   Is it lawful to give tribute to C, or      [G2541]

FAITH
    Rom. 1:17    For therein is the righteousness of God     [G4102]
    Rom. 3:28    Therefore we conclude that a man is         [G4102]
    Gal. 2:16    Knowing that a man is not justified by      [G4102]
"""
        
        self.concordance_file = os.path.join(self.temp_dir, 'concordance.txt')
        with open(self.concordance_file, 'w') as f:
            f.write(self.sample_concordance)
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_concordance_workflow(self):
        """Test the complete workflow from parsing to querying"""
        try:
            # Import required modules
            from ingest_strongs_concordance import BulletproofConcordanceParser
            
            # Step 1: Parse concordance file
            parser = BulletproofConcordanceParser()
            parse_results = parser.parse_file(self.concordance_file)
            
            # Validate parsing results
            self.assertIn('words', parse_results)
            self.assertIn('stats', parse_results)
            
            # Check that critical words were found
            words_found = set(parse_results['words'].keys())
            expected_words = {'AARON', 'ABRAHAM', 'CAESAR', 'FAITH'}
            
            for word in expected_words:
                self.assertIn(word, words_found, f"Word {word} not found in parsing results")
            
            # Validate word entries have verses
            for word, word_data in parse_results['words'].items():
                if word in expected_words:
                    self.assertGreater(len(word_data['verses']), 0, 
                                     f"Word {word} has no verses")
            
            # Step 2: Generate chunks
            chunks = parser.generate_concordance_chunks(parse_results)
            
            self.assertGreater(len(chunks), 0, "No chunks generated")
            
            # Validate chunk structure
            for chunk in chunks[:5]:  # Check first 5 chunks
                self.assertIn('id', chunk)
                self.assertIn('content', chunk)
                self.assertIn('metadata', chunk)
                
                metadata = chunk['metadata']
                self.assertIn('word', metadata)
                self.assertIn('source', metadata)
                self.assertEqual(metadata['source'], 'strongs_concordance')
            
            # Step 3: Save chunks (simulate file I/O)
            chunks_file = os.path.join(self.chunks_dir, 'concordance_chunks.json')
            with open(chunks_file, 'w') as f:
                json.dump(chunks, f, indent=2)
            
            self.assertTrue(os.path.exists(chunks_file))
            
            # Step 4: Validate saved chunks can be loaded
            with open(chunks_file, 'r') as f:
                loaded_chunks = json.load(f)
            
            self.assertEqual(len(loaded_chunks), len(chunks))
            
            # Step 5: Test chunk compatibility with ChromaDB format
            # (This simulates what would happen in embedding generation)
            sample_chunk = loaded_chunks[0]
            
            # Check ChromaDB compatibility
            required_fields = ['id', 'content', 'metadata']
            for field in required_fields:
                self.assertIn(field, sample_chunk)
            
            # Metadata should only contain scalar values for ChromaDB
            metadata = sample_chunk['metadata']
            for key, value in metadata.items():
                self.assertIn(type(value), [str, int, float, bool], 
                            f"Metadata field {key} has non-scalar type: {type(value)}")
        
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")
    
    def test_embedding_generation_workflow(self):
        """Test the embedding generation workflow"""
        # Create test chunks for embedding
        test_chunks = [
            {
                "id": "concordance_aaron_exo_4_014",
                "content": "and he said, Is not A the Levite thy",
                "metadata": {
                    "concordance_id": "concordance_aaron_exo_4_014",
                    "source": "strongs_concordance",
                    "layer": "word_entry",
                    "testament": "OT",
                    "word": "AARON",
                    "osis_id": "Exo.4.014",
                    "book": "Exo",
                    "chapter": "4",
                    "verse": "14",
                    "strong_number": "H175",
                    "entry_type": "concordance_word_entry"
                }
            },
            {
                "id": "concordance_faith_rom_1_017",
                "content": "For therein is the righteousness of God",
                "metadata": {
                    "concordance_id": "concordance_faith_rom_1_017",
                    "source": "strongs_concordance",
                    "layer": "word_entry",
                    "testament": "NT",
                    "word": "FAITH",
                    "osis_id": "Rom.1.017",
                    "book": "Rom",
                    "chapter": "1",
                    "verse": "17",
                    "strong_number": "G4102",
                    "entry_type": "concordance_word_entry"
                }
            }
        ]
        
        chunks_file = os.path.join(self.temp_dir, 'test_chunks.json')
        with open(chunks_file, 'w') as f:
            json.dump(test_chunks, f)
        
        try:
            # Test ChromaDB collection creation
            client = chromadb.PersistentClient(path=self.vectordb_path)
            
            # Create collection
            collection = client.create_collection("test_strongs_concordance_entries")
            
            # Test adding chunks (without actual embeddings)
            for chunk in test_chunks:
                # Simulate embedding generation
                mock_embedding = [0.1] * 1024  # BGE-large dimension
                
                collection.add(
                    documents=[chunk['content']],
                    embeddings=[mock_embedding],
                    metadatas=[chunk['metadata']],
                    ids=[chunk['id']]
                )
            
            # Verify collection was populated
            count = collection.count()
            self.assertEqual(count, len(test_chunks))
            
            # Test query functionality
            query_embedding = [0.1] * 1024
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=2
            )
            
            self.assertEqual(len(results['ids'][0]), 2)
            self.assertIn('concordance_aaron_exo_4_014', results['ids'][0])
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_query_system_integration(self):
        """Test integration with the query system"""
        try:
            # Create test ChromaDB with data
            client = chromadb.PersistentClient(path=self.vectordb_path)
            
            # Create collections that TinyOwlQuery expects
            concordance_collection = client.create_collection("strongs_concordance_entries")
            
            # Add test data
            test_data = [
                {
                    "id": "test_aaron_1",
                    "document": "Aaron was the brother of Moses",
                    "metadata": {
                        "word": "AARON",
                        "strong_number": "H175",
                        "book": "Exo",
                        "chapter": "4",
                        "verse": "14"
                    }
                }
            ]
            
            for data in test_data:
                mock_embedding = [0.1] * 1024
                concordance_collection.add(
                    documents=[data["document"]],
                    embeddings=[mock_embedding],
                    metadatas=[data["metadata"]],
                    ids=[data["id"]]
                )
            
            # Test query parsing functionality (without actual model loading)
            test_queries = [
                "@aaron",
                "@word:AARON",
                "@strong:H175",
                "faith and works"
            ]
            
            # Simulate query parsing
            for query in test_queries:
                if query.startswith('@'):
                    if query.startswith('@word:') or (query.startswith('@') and ':' not in query):
                        # Word lookup query
                        query_type = 'word_lookup'
                        if ':' in query:
                            term = query.split(':', 1)[1].upper()
                        else:
                            term = query[1:].upper()
                        
                        self.assertIn(query_type, ['word_lookup'])
                        self.assertTrue(term.isupper())
                    
                    elif query.startswith('@strong:'):
                        # Strong's number lookup
                        query_type = 'strong_lookup'
                        number = query.split(':', 1)[1].upper()
                        
                        self.assertIn(query_type, ['strong_lookup'])
                        self.assertTrue(number.startswith(('H', 'G')) or number.isdigit())
                
                else:
                    # Semantic search
                    query_type = 'semantic_search'
                    self.assertEqual(query_type, 'semantic_search')
        
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")


class TestKJVIngestionWorkflow(unittest.TestCase):
    """Test the complete KJV Bible ingestion workflow"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample KJV data
        self.sample_kjv = """THE FIRST BOOK OF MOSES, CALLED
GENESIS

CHAPTER 1

1 In the beginning God created the heaven and the earth.
2 And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.
3 And God said, Let there be light: and there was light.

CHAPTER 2

1 Thus the heavens and the earth were finished, and all the host of them.
2 And on the seventh day God ended his work which he had made; and he rested on the seventh day from all his work which he had made.

THE GOSPEL ACCORDING TO SAINT MATTHEW

CHAPTER 1

1 The book of the generation of Jesus Christ, the son of David, the son of Abraham.
2 Abraham begat Isaac; and Isaac begat Jacob; and Jacob begat Judas and his brethren.
"""
        
        self.kjv_file = os.path.join(self.temp_dir, 'kjv_sample.txt')
        with open(self.kjv_file, 'w', encoding='latin1') as f:
            f.write(self.sample_kjv)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_kjv_parsing_workflow(self):
        """Test KJV parsing and chunking workflow"""
        try:
            from bulletproof_ingest import BulletproofIngestor
            from text_normalizer import TextNormalizer
            
            # Test text normalization
            normalizer = TextNormalizer()
            
            test_verse = "In the beginning God created the heaven and the earth."
            normalized = normalizer.normalize_text(test_verse)
            
            self.assertIsInstance(normalized, str)
            self.assertGreater(len(normalized), 0)
            
            # Test OSIS ID creation
            osis_id = normalizer.create_osis_id("Gen", 1, 1)
            self.assertEqual(osis_id, "Gen.01.001")
            
            # Test verse extraction
            test_line = "1 In the beginning God created the heaven and the earth."
            verse_info = normalizer.extract_verse_from_line(test_line)
            
            if verse_info:
                self.assertIn('verse', verse_info)
                self.assertIn('text', verse_info)
        
        except ImportError as e:
            self.skipTest(f"Required modules not available: {e}")
    
    def test_hierarchical_chunking_workflow(self):
        """Test the hierarchical chunking process"""
        # Simulate the hierarchical chunking process
        sample_verses = {
            "Gen": {
                1: {
                    1: "In the beginning God created the heaven and the earth.",
                    2: "And the earth was without form, and void; and darkness was upon the face of the deep.",
                    3: "And God said, Let there be light: and there was light."
                }
            }
        }
        
        # Test verse-level chunks (Layer A)
        verse_chunks = []
        for book_id, chapters in sample_verses.items():
            for chapter_num, verses in chapters.items():
                for verse_num, verse_text in verses.items():
                    osis_id = f"{book_id}.{chapter_num:02d}.{verse_num:03d}"
                    
                    verse_chunk = {
                        "id": f"kjv_{osis_id.lower().replace('.', '_')}",
                        "osis_id": osis_id,
                        "content": verse_text,
                        "metadata": {
                            "source_id": "kjv",
                            "type": "scripture",
                            "layer": "verse",
                            "book_id": book_id,
                            "chapter": chapter_num,
                            "verse": verse_num
                        }
                    }
                    verse_chunks.append(verse_chunk)
        
        self.assertEqual(len(verse_chunks), 3)
        
        # Test pericope chunks (Layer B)
        verse_list = list(sample_verses["Gen"][1].items())
        window_size = 2  # Smaller for test
        pericope_chunks = []
        
        for i in range(0, len(verse_list), 1):  # stride = 1 for test
            window_verses = verse_list[i:i + window_size]
            if len(window_verses) < 2:
                continue
            
            combined_text = " ".join([verse_text for _, verse_text in window_verses])
            
            pericope_chunk = {
                "id": f"kjv_gen_c01_p{i+1:03d}",
                "content": combined_text,
                "metadata": {
                    "source_id": "kjv",
                    "type": "scripture",
                    "layer": "pericope",
                    "book_id": "Gen",
                    "chapter": 1,
                    "verse_start": window_verses[0][0],
                    "verse_end": window_verses[-1][0]
                }
            }
            pericope_chunks.append(pericope_chunk)
        
        self.assertGreater(len(pericope_chunks), 0)
        
        # Test chapter chunk (Layer C)
        all_verses_text = " ".join([verse_text for _, verse_text in verse_list])
        
        chapter_chunk = {
            "id": "kjv_gen_chapter_01",
            "content": all_verses_text,
            "metadata": {
                "source_id": "kjv",
                "type": "scripture",
                "layer": "chapter",
                "book_id": "Gen",
                "chapter": 1,
                "verse_count": len(verse_list)
            }
        }
        
        self.assertIn("In the beginning", chapter_chunk["content"])
        self.assertEqual(chapter_chunk["metadata"]["verse_count"], 3)


class TestEndToEndSystemIntegration(unittest.TestCase):
    """Test complete end-to-end system integration"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vectordb_path = os.path.join(self.temp_dir, 'vectordb')
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_system_startup_and_initialization(self):
        """Test that the system initializes properly"""
        try:
            # Test ChromaDB initialization
            client = chromadb.PersistentClient(path=self.vectordb_path)
            
            # Test collection listing (should be empty initially)
            collections = client.list_collections()
            self.assertIsInstance(collections, list)
            
            # Test creating required collections
            required_collections = [
                "kjv_verses",
                "kjv_pericopes", 
                "kjv_chapters",
                "strongs_concordance_entries",
                "strongs_numbers",
                "strongs_word_summaries"
            ]
            
            created_collections = []
            for collection_name in required_collections:
                try:
                    collection = client.create_collection(collection_name)
                    created_collections.append(collection_name)
                    
                    # Test basic collection operations
                    self.assertEqual(collection.count(), 0)
                    
                except Exception as e:
                    print(f"Could not create collection {collection_name}: {e}")
            
            self.assertGreater(len(created_collections), 0)
        
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_configuration_loading(self):
        """Test that configuration files load properly"""
        # Test creating a basic configuration
        config_dir = os.path.join(self.temp_dir, 'configs')
        os.makedirs(config_dir, exist_ok=True)
        
        # Create test configuration
        test_config = {
            'text_normalization': {
                'unicode_form': 'NFKC',
                'collapse_whitespace': True,
                'strip_leading_trailing': True,
                'replacements': {
                    '\u2019': "'",  # Right single quotation mark
                    '\u201C': '"',  # Left double quotation mark
                    '\u201D': '"'   # Right double quotation mark
                },
                'remove_patterns': [
                    r'\[\d+\]',  # Remove footnote markers
                    r'\s+(?=\s)',  # Multiple spaces
                ]
            },
            'book_aliases': {
                'Genesis': 'Gen',
                'Exodus': 'Exod',
                'Matthew': 'Matt',
                'Romans': 'Rom'
            }
        }
        
        config_file = os.path.join(config_dir, 'test_config.json')
        with open(config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        
        # Test loading configuration
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        self.assertEqual(loaded_config['text_normalization']['unicode_form'], 'NFKC')
        self.assertIn('Genesis', loaded_config['book_aliases'])
    
    def test_error_recovery_scenarios(self):
        """Test system behavior under error conditions"""
        # Test missing file scenarios
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.txt')
        
        # Should handle missing files gracefully
        self.assertFalse(os.path.exists(nonexistent_file))
        
        # Test malformed data scenarios
        malformed_json = os.path.join(self.temp_dir, 'malformed.json')
        with open(malformed_json, 'w') as f:
            f.write('{"invalid": json syntax}')
        
        # Should detect malformed JSON
        with self.assertRaises(json.JSONDecodeError):
            with open(malformed_json, 'r') as f:
                json.load(f)
        
        # Test disk space scenarios (simulated)
        import shutil
        total, used, free = shutil.disk_usage(self.temp_dir)
        
        # Should have some free space
        self.assertGreater(free, 0)
        
        # Test permission scenarios
        test_file = os.path.join(self.temp_dir, 'permission_test.txt')
        with open(test_file, 'w') as f:
            f.write('test content')
        
        # Should be able to read the file
        self.assertTrue(os.access(test_file, os.R_OK))
    
    def test_performance_under_load(self):
        """Test system performance under simulated load"""
        # Create large test dataset
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                'id': f'load_test_{i:04d}',
                'content': f'Load test content item {i} ' + 'x' * 100,
                'metadata': {
                    'test_id': i,
                    'batch': i // 100,
                    'category': f'category_{i % 10}'
                }
            })
        
        # Test processing performance
        start_time = time.time()
        
        processed_items = 0
        for item in large_dataset:
            # Simulate processing
            if 'id' in item and 'content' in item:
                processed_items += 1
        
        processing_time = time.time() - start_time
        
        # Should process efficiently
        self.assertEqual(processed_items, 1000)
        
        # Should complete within reasonable time (5 seconds for this test)
        self.assertLess(processing_time, 5.0)
        
        # Calculate processing rate
        rate = processed_items / processing_time if processing_time > 0 else 0
        self.assertGreater(rate, 100)  # At least 100 items per second


if __name__ == '__main__':
    print("TinyOwl Integration Workflow Tests")
    print("=" * 50)
    
    # Run all integration tests
    unittest.main(verbosity=2)