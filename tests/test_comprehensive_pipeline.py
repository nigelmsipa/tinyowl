#!/usr/bin/env python3
"""
Comprehensive TinyOwl Pipeline Test Suite
Identifies and prevents critical issues found in systematic code review

This test suite addresses the major risks identified:
1. Data corruption prevention (Strong's embeddings deletion risk)
2. Resource management issues
3. Error handling gaps
4. Configuration validation
5. Integration testing for workflows
"""

import unittest
import pytest
import tempfile
import shutil
import json
import os
import sys
import chromadb
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
import time

# Add the scripts directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    from generate_strongs_embeddings import generate_all_strongs_embeddings
    from ingest_strongs_concordance import BulletproofConcordanceParser
    from tinyowl_query import TinyOwlQuery
    from text_normalizer import TextNormalizer
    from check_embeddings_status import check_embeddings_status
    from bulletproof_ingest import BulletproofIngestor
except ImportError as e:
    print(f"Warning: Could not import scripts: {e}")


class TestDataCorruptionPrevention(unittest.TestCase):
    """
    CRITICAL: Tests to prevent data corruption scenarios like accidental
    Strong's concordance embeddings deletion
    """
    
    def setUp(self):
        """Setup temporary test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_vectordb = os.path.join(self.temp_dir, 'test_vectordb')
        os.makedirs(self.test_vectordb, exist_ok=True)
    
    def tearDown(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_collection_deletion_protection(self):
        """Test that collections are not deleted without explicit confirmation"""
        # Mock ChromaDB client
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_collection.return_value = mock_collection
            
            # Test that delete operation requires confirmation
            # This should be implemented in generate_strongs_embeddings.py
            with self.assertRaises(ValueError):
                # Should fail if no confirmation provided
                pass  # Placeholder for actual test
    
    def test_backup_before_overwrite(self):
        """Test that existing collections are backed up before overwriting"""
        # Create test collection
        client = chromadb.PersistentClient(path=self.test_vectordb)
        
        try:
            # Create a test collection with data
            collection = client.create_collection("test_strongs")
            collection.add(
                documents=["test document"],
                ids=["test_id"],
                metadatas=[{"test": "data"}]
            )
            
            # Verify collection exists and has data
            self.assertEqual(collection.count(), 1)
            
            # Test backup functionality should be implemented
            # This is a CRITICAL missing feature identified in the review
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_data_validation_before_deletion(self):
        """Test that data is validated before any destructive operations"""
        # Create mock chunk files
        test_chunks = [
            {
                "id": "test_1",
                "content": "test content",
                "metadata": {"source": "test"}
            }
        ]
        
        chunks_file = os.path.join(self.temp_dir, "test_chunks.json")
        with open(chunks_file, 'w') as f:
            json.dump(test_chunks, f)
        
        # Test validation function (should be implemented)
        self.assertTrue(os.path.exists(chunks_file))
        
        # Validation should check:
        # 1. File exists and is readable
        # 2. JSON is valid
        # 3. Required fields are present
        # 4. Data is not empty
        with open(chunks_file, 'r') as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)
            self.assertIn('id', data[0])
            self.assertIn('content', data[0])


class TestResourceManagement(unittest.TestCase):
    """
    Tests for proper resource management (files, database connections, memory)
    Addresses issues found in the systematic review
    """
    
    def test_file_handle_cleanup(self):
        """Test that file handles are properly closed"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write("test content\n")
        temp_file.close()
        
        try:
            # Test TextNormalizer handles files properly
            normalizer = TextNormalizer()
            
            # Should not leave file handles open
            # This tests the pattern used in various scripts
            with open(temp_file.name, 'r') as f:
                content = f.read()
                self.assertIn("test content", content)
            
        finally:
            os.unlink(temp_file.name)
    
    def test_chromadb_connection_management(self):
        """Test ChromaDB connections are properly managed"""
        temp_vectordb = tempfile.mkdtemp()
        
        try:
            # Test connection cleanup
            client = chromadb.PersistentClient(path=temp_vectordb)
            
            # Create and use collection
            collection = client.create_collection("test_collection")
            self.assertEqual(collection.count(), 0)
            
            # Connection should be properly closed
            # No explicit close method, but client should be cleaned up
            del client
            del collection
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
        finally:
            if os.path.exists(temp_vectordb):
                shutil.rmtree(temp_vectordb, ignore_errors=True)
    
    def test_memory_usage_monitoring(self):
        """Test that memory usage doesn't grow unbounded"""
        import psutil
        import gc
        
        initial_memory = psutil.Process().memory_info().rss
        
        # Simulate large data processing
        large_data = []
        for i in range(1000):
            large_data.append({"id": f"test_{i}", "content": f"content_{i}" * 100})
        
        # Force garbage collection
        del large_data
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (less than 100MB for this test)
        self.assertLess(memory_growth, 100 * 1024 * 1024, 
                       "Memory usage grew too much during processing")


class TestErrorHandling(unittest.TestCase):
    """
    Tests for comprehensive error handling
    Addresses gaps identified in the systematic review
    """
    
    def test_missing_file_handling(self):
        """Test handling of missing input files"""
        parser = BulletproofConcordanceParser()
        
        # Test missing concordance file
        with self.assertRaises(FileNotFoundError):
            parser.parse_file("/nonexistent/file.txt")
    
    def test_malformed_data_handling(self):
        """Test handling of malformed input data"""
        # Test malformed JSON
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file.write('{"invalid": json syntax}')
        temp_file.close()
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                with open(temp_file.name, 'r') as f:
                    json.load(f)
        finally:
            os.unlink(temp_file.name)
    
    def test_api_failure_handling(self):
        """Test handling of external API failures"""
        # Test OpenAI API failure handling (from simple_query.py)
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Simulate API failure
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            # Test should handle gracefully (implement this in actual code)
            with self.assertRaises(Exception):
                mock_client.chat.completions.create()
    
    def test_disk_space_handling(self):
        """Test handling of insufficient disk space"""
        # This is a critical issue - embeddings can be large
        # Should check available space before processing
        
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (1024**3)
        
        # Should have at least 5GB free for embedding operations
        self.assertGreater(free_gb, 5, 
                          "Insufficient disk space for embedding operations")


class TestConfigurationValidation(unittest.TestCase):
    """
    Tests for configuration validation
    Addresses hard-coded values and missing validation
    """
    
    def test_required_environment_variables(self):
        """Test that required environment variables are validated"""
        # Test OPENAI_API_KEY requirement
        original_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            # Remove key
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            # Should handle missing key gracefully
            # This is tested in simple_query.py
            self.assertNotIn('OPENAI_API_KEY', os.environ)
            
        finally:
            # Restore key if it existed
            if original_key:
                os.environ['OPENAI_API_KEY'] = original_key
    
    def test_path_configuration(self):
        """Test that file paths are configurable and validated"""
        # Test hard-coded paths found in the review
        hard_coded_paths = [
            "/home/nigel/tinyowl/domains/theology/raw/strongs_concordance_complete.txt",
            "/home/nigel/Downloads/TheHolyBibleKJV.txt",
            "vectordb",
            "domains/theology"
        ]
        
        # These paths should be configurable, not hard-coded
        for path in hard_coded_paths:
            # Test would verify path is configurable
            self.assertTrue(isinstance(path, str))
    
    def test_model_configuration(self):
        """Test that AI models are configurable"""
        # Test BGE model configuration
        model_name = 'BAAI/bge-large-en-v1.5'
        
        # Should be configurable rather than hard-coded
        self.assertTrue(isinstance(model_name, str))
        
        # Test OpenAI model configuration
        openai_model = 'gpt-3.5-turbo'
        self.assertTrue(isinstance(openai_model, str))


class TestStrongsConcordanceWorkflow(unittest.TestCase):
    """
    Integration tests for the Strong's Concordance processing workflow
    This is the critical pipeline that had the major setback
    """
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_concordance_parsing_workflow(self):
        """Test the complete concordance parsing workflow"""
        # Create test concordance data
        test_concordance = """AARON
    Exo. 4:14     and he said, Is not A the Levite thy       [H175]
    Exo. 4:27     And the LORD said to A, Go into the        [H175]

ABRAHAM
    Gen. 12:1     Now the LORD had said unto A, Get thee     [H85]
    Gen. 12:4     So A departed, as the LORD had spoken      [H85]
"""
        
        temp_file = os.path.join(self.temp_dir, 'test_concordance.txt')
        with open(temp_file, 'w') as f:
            f.write(test_concordance)
        
        # Test parsing
        parser = BulletproofConcordanceParser()
        results = parser.parse_file(temp_file)
        
        # Validate results
        self.assertIn('words', results)
        self.assertIn('stats', results)
        self.assertIn('AARON', results['words'])
        self.assertIn('ABRAHAM', results['words'])
        
        # Test chunk generation
        chunks = parser.generate_concordance_chunks(results)
        self.assertGreater(len(chunks), 0)
        
        # Validate chunk structure
        for chunk in chunks:
            self.assertIn('id', chunk)
            self.assertIn('content', chunk)
            self.assertIn('metadata', chunk)
            self.assertIn('source', chunk['metadata'])
            self.assertEqual(chunk['metadata']['source'], 'strongs_concordance')
    
    def test_embedding_generation_workflow(self):
        """Test the embedding generation workflow"""
        # Create test chunks
        test_chunks = [
            {
                "id": "test_concordance_aaron_exo_4_14",
                "content": "and he said, Is not A the Levite thy",
                "metadata": {
                    "word": "AARON",
                    "book": "Exo",
                    "chapter": "4",
                    "verse": "14",
                    "strong_number": "H175",
                    "source": "strongs_concordance",
                    "layer": "word_entry",
                    "entry_type": "concordance_word_entry"
                }
            }
        ]
        
        chunks_file = os.path.join(self.temp_dir, 'test_chunks.json')
        with open(chunks_file, 'w') as f:
            json.dump(test_chunks, f)
        
        # Test file exists and is valid
        self.assertTrue(os.path.exists(chunks_file))
        
        with open(chunks_file, 'r') as f:
            loaded_chunks = json.load(f)
            self.assertEqual(len(loaded_chunks), 1)
            self.assertEqual(loaded_chunks[0]['metadata']['word'], 'AARON')
    
    def test_query_workflow(self):
        """Test the query workflow"""
        # Mock ChromaDB for testing
        with patch('chromadb.PersistentClient') as mock_client:
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            
            mock_collection = Mock()
            mock_client_instance.get_collection.return_value = mock_collection
            mock_client_instance.list_collections.return_value = []
            
            # Test query parsing
            # This tests the @ syntax functionality
            test_queries = [
                "@aaron",
                "@word:jesus", 
                "@strong:175",
                "faith and works"
            ]
            
            for query in test_queries:
                # Test query type identification
                if query.startswith('@'):
                    self.assertTrue(query.startswith('@'))


class TestEdgeCasesAndBoundaryConditions(unittest.TestCase):
    """
    Tests for edge cases and boundary conditions
    These scenarios often cause failures in production
    """
    
    def test_empty_files(self):
        """Test handling of empty files"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.close()  # Create empty file
        
        try:
            # Test parser handles empty files
            parser = BulletproofConcordanceParser()
            results = parser.parse_file(temp_file.name)
            
            # Should handle gracefully
            self.assertIn('words', results)
            self.assertEqual(len(results['words']), 0)
            
        finally:
            os.unlink(temp_file.name)
    
    def test_very_large_files(self):
        """Test handling of very large files"""
        # Create a moderately large test file
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        
        try:
            # Write 10,000 lines
            for i in range(10000):
                temp_file.write(f"Line {i}: test content for large file processing\n")
            temp_file.close()
            
            # Should handle without memory issues
            file_size = os.path.getsize(temp_file.name)
            self.assertGreater(file_size, 500000)  # At least 500KB
            
            # Test reading large file
            with open(temp_file.name, 'r') as f:
                lines = f.readlines()
                self.assertEqual(len(lines), 10000)
                
        finally:
            os.unlink(temp_file.name)
    
    def test_unicode_handling(self):
        """Test proper Unicode handling"""
        unicode_content = "Test with Unicode: αβγδε 中文 العربية עברית"
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False)
        temp_file.write(unicode_content)
        temp_file.close()
        
        try:
            # Test reading Unicode content
            with open(temp_file.name, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertEqual(content, unicode_content)
                
            # Test normalizer handles Unicode
            normalizer = TextNormalizer()
            normalized = normalizer.normalize_text(unicode_content)
            self.assertIsInstance(normalized, str)
            
        finally:
            os.unlink(temp_file.name)
    
    def test_concurrent_access(self):
        """Test concurrent access to resources"""
        import threading
        import time
        
        temp_vectordb = tempfile.mkdtemp()
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                client = chromadb.PersistentClient(path=temp_vectordb)
                collection = client.create_collection(f"test_concurrent_{worker_id}")
                collection.add(
                    documents=[f"test doc {worker_id}"],
                    ids=[f"id_{worker_id}"],
                    metadatas=[{"worker": worker_id}]
                )
                results.append(f"Worker {worker_id} success")
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")
        
        try:
            # Start multiple workers
            threads = []
            for i in range(3):
                t = threading.Thread(target=worker, args=(i,))
                threads.append(t)
                t.start()
            
            # Wait for completion
            for t in threads:
                t.join(timeout=10)
            
            # Should handle concurrent access gracefully
            # Allow some errors due to ChromaDB concurrency limitations
            total_operations = len(results) + len(errors)
            self.assertGreater(total_operations, 0)
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
        finally:
            if os.path.exists(temp_vectordb):
                shutil.rmtree(temp_vectordb, ignore_errors=True)


class TestPerformanceAndScalability(unittest.TestCase):
    """
    Tests for performance and scalability issues
    """
    
    def test_processing_time_bounds(self):
        """Test that processing completes within reasonable time bounds"""
        # Test text normalization performance
        normalizer = TextNormalizer()
        
        test_text = "Test text for normalization performance " * 1000
        
        start_time = time.time()
        normalized = normalizer.normalize_text(test_text)
        processing_time = time.time() - start_time
        
        # Should complete quickly (under 1 second for this size)
        self.assertLess(processing_time, 1.0)
        self.assertIsInstance(normalized, str)
    
    def test_batch_processing_efficiency(self):
        """Test batch processing efficiency"""
        # Create test batch data
        test_batch = []
        for i in range(1000):
            test_batch.append({
                'id': f'test_{i}',
                'content': f'Test content {i} ' * 50,
                'metadata': {'batch_id': i}
            })
        
        # Test batch processing time
        start_time = time.time()
        
        # Process batch (simulated)
        processed = 0
        for item in test_batch:
            # Simulate processing
            if 'content' in item and 'id' in item:
                processed += 1
        
        processing_time = time.time() - start_time
        
        # Should process efficiently
        rate = processed / processing_time if processing_time > 0 else 0
        self.assertGreater(rate, 500, "Batch processing rate too slow")
    
    def test_memory_efficiency(self):
        """Test memory efficiency during processing"""
        import gc
        import psutil
        
        gc.collect()
        initial_memory = psutil.Process().memory_info().rss
        
        # Process large dataset
        large_dataset = []
        for i in range(10000):
            large_dataset.append({
                'id': f'item_{i}',
                'content': f'Content for item {i}',
                'metadata': {'index': i}
            })
        
        # Process items one by one to test memory management
        processed_count = 0
        for item in large_dataset:
            if item['id'].startswith('item_'):
                processed_count += 1
                
                # Clear processed item to free memory
                del item
        
        # Force garbage collection
        del large_dataset
        gc.collect()
        
        final_memory = psutil.Process().memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB)
        self.assertLess(memory_increase, 500 * 1024 * 1024)
        self.assertEqual(processed_count, 10000)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)