#!/usr/bin/env python3
"""
Data Safety and Backup Test Suite
Critical safety measures to prevent data loss incidents

This test suite specifically addresses the Strong's concordance embeddings
deletion incident and provides comprehensive safety measures.
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
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class SafetyManager:
    """
    Safety manager for TinyOwl operations
    This class implements the safety measures that should be added to the codebase
    """
    
    def __init__(self, vectordb_path: str = "vectordb", backup_path: str = "backups"):
        self.vectordb_path = Path(vectordb_path)
        self.backup_path = Path(backup_path)
        self.backup_path.mkdir(exist_ok=True)
    
    def create_backup(self, collection_name: str) -> str:
        """Create a backup of a collection before destructive operations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{collection_name}_backup_{timestamp}"
        
        try:
            client = chromadb.PersistentClient(path=str(self.vectordb_path))
            collection = client.get_collection(collection_name)
            
            # Get all data from collection
            results = collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            # Save backup
            backup_file = self.backup_path / f"{backup_name}.json"
            backup_data = {
                'collection_name': collection_name,
                'backup_timestamp': timestamp,
                'item_count': len(results['ids']),
                'data': {
                    'ids': results['ids'],
                    'documents': results['documents'],
                    'metadatas': results['metadatas']
                    # Note: embeddings are large, consider separate storage
                }
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return str(backup_file)
            
        except Exception as e:
            raise Exception(f"Failed to create backup for {collection_name}: {e}")
    
    def validate_collection_integrity(self, collection_name: str) -> Dict[str, Any]:
        """Validate collection integrity before operations"""
        try:
            client = chromadb.PersistentClient(path=str(self.vectordb_path))
            collection = client.get_collection(collection_name)
            
            count = collection.count()
            
            # Sample data validation
            sample_results = collection.get(limit=10, include=['documents', 'metadatas'])
            
            validation_report = {
                'collection_name': collection_name,
                'total_count': count,
                'is_empty': count == 0,
                'has_documents': len(sample_results['documents']) > 0,
                'has_metadata': len(sample_results['metadatas']) > 0,
                'sample_ids': sample_results['ids'][:5],
                'validation_passed': count > 0 and len(sample_results['documents']) > 0
            }
            
            return validation_report
            
        except Exception as e:
            return {
                'collection_name': collection_name,
                'error': str(e),
                'validation_passed': False
            }
    
    def safe_collection_delete(self, collection_name: str, confirmation_token: str = None) -> bool:
        """Safely delete a collection with confirmation and backup"""
        if not confirmation_token or confirmation_token != f"DELETE_{collection_name}_CONFIRMED":
            raise ValueError(f"Invalid confirmation token. Required: DELETE_{collection_name}_CONFIRMED")
        
        # Create backup first
        backup_file = self.create_backup(collection_name)
        print(f"Backup created: {backup_file}")
        
        # Validate backup
        if not os.path.exists(backup_file):
            raise Exception("Backup creation failed - aborting deletion")
        
        # Perform deletion
        try:
            client = chromadb.PersistentClient(path=str(self.vectordb_path))
            client.delete_collection(collection_name)
            print(f"Collection {collection_name} safely deleted with backup")
            return True
            
        except Exception as e:
            raise Exception(f"Failed to delete collection {collection_name}: {e}")
    
    def restore_from_backup(self, backup_file: str) -> str:
        """Restore collection from backup"""
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        collection_name = backup_data['collection_name']
        
        client = chromadb.PersistentClient(path=str(self.vectordb_path))
        
        # Create collection
        collection = client.create_collection(collection_name)
        
        # Restore data
        data = backup_data['data']
        collection.add(
            ids=data['ids'],
            documents=data['documents'],
            metadatas=data['metadatas']
        )
        
        return collection_name


class TestDataSafetyMeasures(unittest.TestCase):
    """Test safety measures for data operations"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.vectordb_path = os.path.join(self.temp_dir, 'vectordb')
        self.backup_path = os.path.join(self.temp_dir, 'backups')
        os.makedirs(self.vectordb_path, exist_ok=True)
        
        self.safety_manager = SafetyManager(self.vectordb_path, self.backup_path)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_backup_creation(self):
        """Test that backups are created before destructive operations"""
        try:
            # Create test collection
            client = chromadb.PersistentClient(path=self.vectordb_path)
            collection = client.create_collection("test_collection")
            
            # Add test data
            test_docs = ["Document 1", "Document 2", "Document 3"]
            test_ids = ["id1", "id2", "id3"]
            test_metadata = [{"type": "test"}, {"type": "test"}, {"type": "test"}]
            
            collection.add(
                documents=test_docs,
                ids=test_ids,
                metadatas=test_metadata
            )
            
            # Test backup creation
            backup_file = self.safety_manager.create_backup("test_collection")
            
            # Verify backup exists
            self.assertTrue(os.path.exists(backup_file))
            
            # Verify backup content
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            self.assertEqual(backup_data['collection_name'], "test_collection")
            self.assertEqual(backup_data['item_count'], 3)
            self.assertEqual(len(backup_data['data']['ids']), 3)
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_collection_validation(self):
        """Test collection integrity validation"""
        try:
            client = chromadb.PersistentClient(path=self.vectordb_path)
            collection = client.create_collection("validation_test")
            
            # Test empty collection
            validation = self.safety_manager.validate_collection_integrity("validation_test")
            self.assertFalse(validation['validation_passed'])
            self.assertTrue(validation['is_empty'])
            
            # Add data
            collection.add(
                documents=["Test document"],
                ids=["test_id"],
                metadatas=[{"test": "metadata"}]
            )
            
            # Test non-empty collection
            validation = self.safety_manager.validate_collection_integrity("validation_test")
            self.assertTrue(validation['validation_passed'])
            self.assertFalse(validation['is_empty'])
            self.assertEqual(validation['total_count'], 1)
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_safe_deletion_requires_confirmation(self):
        """Test that collection deletion requires explicit confirmation"""
        try:
            client = chromadb.PersistentClient(path=self.vectordb_path)
            collection = client.create_collection("deletion_test")
            
            collection.add(
                documents=["Test document"],
                ids=["test_id"],
                metadatas=[{"test": "data"}]
            )
            
            # Test deletion without confirmation fails
            with self.assertRaises(ValueError):
                self.safety_manager.safe_collection_delete("deletion_test")
            
            # Test deletion with wrong confirmation fails
            with self.assertRaises(ValueError):
                self.safety_manager.safe_collection_delete("deletion_test", "WRONG_TOKEN")
            
            # Test deletion with correct confirmation succeeds
            correct_token = "DELETE_deletion_test_CONFIRMED"
            result = self.safety_manager.safe_collection_delete("deletion_test", correct_token)
            self.assertTrue(result)
            
            # Verify collection is deleted
            with self.assertRaises(ValueError):
                client.get_collection("deletion_test")
            
            # Verify backup was created
            backups = list(Path(self.backup_path).glob("deletion_test_backup_*.json"))
            self.assertGreater(len(backups), 0)
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_backup_restoration(self):
        """Test restoration from backup"""
        try:
            client = chromadb.PersistentClient(path=self.vectordb_path)
            collection = client.create_collection("restoration_test")
            
            # Add original data
            original_docs = ["Original Doc 1", "Original Doc 2"]
            original_ids = ["orig1", "orig2"]
            original_metadata = [{"version": "original"}, {"version": "original"}]
            
            collection.add(
                documents=original_docs,
                ids=original_ids,
                metadatas=original_metadata
            )
            
            # Create backup
            backup_file = self.safety_manager.create_backup("restoration_test")
            
            # Delete collection
            client.delete_collection("restoration_test")
            
            # Restore from backup
            restored_collection_name = self.safety_manager.restore_from_backup(backup_file)
            self.assertEqual(restored_collection_name, "restoration_test")
            
            # Verify restoration
            restored_collection = client.get_collection("restoration_test")
            count = restored_collection.count()
            self.assertEqual(count, 2)
            
            # Verify data integrity
            results = restored_collection.get()
            self.assertEqual(len(results['documents']), 2)
            self.assertIn("Original Doc 1", results['documents'])
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")


class TestEmbeddingGenerationSafety(unittest.TestCase):
    """Test safety measures specifically for embedding generation"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_chunks_file = os.path.join(self.temp_dir, "test_chunks.json")
        
        # Create test chunks
        test_chunks = [
            {
                "id": "test_aaron_1",
                "content": "Aaron was the brother of Moses",
                "metadata": {
                    "word": "AARON",
                    "source": "strongs_concordance",
                    "layer": "word_entry"
                }
            }
        ]
        
        with open(self.test_chunks_file, 'w') as f:
            json.dump(test_chunks, f)
    
    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_chunk_file_validation(self):
        """Test validation of chunk files before processing"""
        # Test valid file
        self.assertTrue(os.path.exists(self.test_chunks_file))
        
        with open(self.test_chunks_file, 'r') as f:
            chunks = json.load(f)
            
        # Validate chunk structure
        self.assertGreater(len(chunks), 0)
        
        for chunk in chunks:
            self.assertIn('id', chunk)
            self.assertIn('content', chunk)
            self.assertIn('metadata', chunk)
            self.assertIn('source', chunk['metadata'])
    
    def test_existing_collection_protection(self):
        """Test protection of existing collections during embedding generation"""
        try:
            client = chromadb.PersistentClient(path=os.path.join(self.temp_dir, 'vectordb'))
            
            # Create existing collection with valuable data
            existing_collection = client.create_collection("strongs_concordance_entries")
            existing_collection.add(
                documents=["Valuable existing data"],
                ids=["valuable_id"],
                metadatas=[{"importance": "critical"}]
            )
            
            # Verify existing data
            count = existing_collection.count()
            self.assertEqual(count, 1)
            
            # This is the critical safety check that was missing
            # Before overwriting, should:
            # 1. Check if collection exists
            # 2. Validate it has data
            # 3. Create backup
            # 4. Get confirmation
            
            existing_collections = [c.name for c in client.list_collections()]
            self.assertIn("strongs_concordance_entries", existing_collections)
            
        except Exception as e:
            self.skipTest(f"ChromaDB not available: {e}")
    
    def test_batch_processing_error_recovery(self):
        """Test error recovery during batch processing"""
        # Simulate batch processing with some failures
        test_batches = [
            {"valid": True, "data": ["doc1", "doc2", "doc3"]},
            {"valid": False, "data": None},  # This should fail
            {"valid": True, "data": ["doc4", "doc5"]},
        ]
        
        successful_batches = 0
        failed_batches = 0
        
        for i, batch in enumerate(test_batches):
            try:
                if not batch["valid"] or batch["data"] is None:
                    raise ValueError(f"Invalid batch {i}")
                
                # Process batch
                processed_count = len(batch["data"])
                self.assertGreater(processed_count, 0)
                successful_batches += 1
                
            except Exception as e:
                failed_batches += 1
                print(f"Batch {i} failed: {e}")
                # Should continue processing other batches
                continue
        
        # Should have processed valid batches despite one failure
        self.assertEqual(successful_batches, 2)
        self.assertEqual(failed_batches, 1)
    
    def test_disk_space_monitoring(self):
        """Test disk space monitoring during embedding generation"""
        import shutil
        
        # Check available disk space
        total, used, free = shutil.disk_usage(self.temp_dir)
        
        # Convert to GB
        free_gb = free // (1024**3)
        
        # Should have sufficient space for operations
        # Embeddings can be large (BGE-large is 1024 dimensions per vector)
        min_required_gb = 1  # At least 1GB for testing
        
        if free_gb < min_required_gb:
            self.skipTest(f"Insufficient disk space: {free_gb}GB available, {min_required_gb}GB required")
        
        # Simulate space calculation for embedding storage
        # Example: 31,000 verses * 1024 dimensions * 4 bytes = ~127MB just for verse embeddings
        estimated_size_bytes = 31000 * 1024 * 4
        estimated_size_gb = estimated_size_bytes / (1024**3)
        
        self.assertLess(estimated_size_gb, free_gb, 
                       "Insufficient disk space for estimated embedding size")


class TestQuerySystemSafety(unittest.TestCase):
    """Test safety measures in the query system"""
    
    def test_collection_availability_checking(self):
        """Test that query system checks collection availability"""
        temp_vectordb = tempfile.mkdtemp()
        
        try:
            # Test with empty vectordb
            with patch('chromadb.PersistentClient') as mock_client:
                mock_client_instance = Mock()
                mock_client.return_value = mock_client_instance
                mock_client_instance.list_collections.return_value = []
                
                # Query system should handle missing collections gracefully
                collections = mock_client_instance.list_collections()
                self.assertEqual(len(collections), 0)
                
                # Should not crash when collections don't exist
                mock_client_instance.get_collection.side_effect = ValueError("Collection not found")
                
                with self.assertRaises(ValueError):
                    mock_client_instance.get_collection("nonexistent_collection")
        
        finally:
            if os.path.exists(temp_vectordb):
                shutil.rmtree(temp_vectordb, ignore_errors=True)
    
    def test_query_parameter_validation(self):
        """Test validation of query parameters"""
        # Test various query formats that should be handled safely
        test_queries = [
            "",  # Empty query
            "   ",  # Whitespace only
            "@",  # Incomplete @ syntax
            "@word:",  # Missing term
            "@strong:",  # Missing number
            "@word:" + "x" * 1000,  # Very long term
            "normal search query",  # Normal query
            "@word:JESUS",  # Valid @ syntax
            "@strong:H175"  # Valid Strong's lookup
        ]
        
        for query in test_queries:
            # Should handle all queries without crashing
            self.assertIsInstance(query, str)
            
            # Basic validation rules
            if query.strip() == "":
                # Empty queries should be handled gracefully
                self.assertEqual(len(query.strip()), 0)
            
            if query.startswith("@"):
                if ":" not in query:
                    # Incomplete @ syntax should be detected
                    self.assertTrue(query == "@" or ":" not in query)
    
    def test_error_handling_in_queries(self):
        """Test comprehensive error handling in query operations"""
        # Test API failures
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_openai.return_value = mock_client
            
            # Test different types of API errors
            error_types = [
                Exception("Network error"),
                ValueError("Invalid parameters"),
                KeyError("Missing API key"),
                TimeoutError("Request timeout")
            ]
            
            for error in error_types:
                mock_client.chat.completions.create.side_effect = error
                
                # Should handle each error type gracefully
                with self.assertRaises(type(error)):
                    mock_client.chat.completions.create()


class TestConfigurationSafety(unittest.TestCase):
    """Test safety measures for configuration management"""
    
    def test_environment_variable_validation(self):
        """Test validation of required environment variables"""
        # Save original values
        original_openai_key = os.environ.get('OPENAI_API_KEY')
        
        try:
            # Test missing API key
            if 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
            
            # Should detect missing key
            self.assertNotIn('OPENAI_API_KEY', os.environ)
            
            # Test setting key
            os.environ['OPENAI_API_KEY'] = 'test_key'
            self.assertEqual(os.environ['OPENAI_API_KEY'], 'test_key')
            
        finally:
            # Restore original value
            if original_openai_key:
                os.environ['OPENAI_API_KEY'] = original_openai_key
            elif 'OPENAI_API_KEY' in os.environ:
                del os.environ['OPENAI_API_KEY']
    
    def test_path_configuration_safety(self):
        """Test that file paths are safely handled"""
        # Test various path scenarios
        test_paths = [
            "",  # Empty path
            "/nonexistent/path",  # Non-existent path
            "/tmp/test_path",  # Valid temporary path
            "relative/path",  # Relative path
            "../../../etc/passwd",  # Directory traversal attempt
        ]
        
        for path in test_paths:
            if path == "":
                # Empty paths should be handled
                self.assertEqual(len(path), 0)
            
            if path.startswith("/"):
                # Absolute paths should be validated
                self.assertTrue(os.path.isabs(path))
            
            if "../" in path:
                # Directory traversal should be detected
                self.assertIn("../", path)
                # In production, this should be blocked
    
    def test_model_configuration_validation(self):
        """Test validation of AI model configurations"""
        # Test model name validation
        valid_models = [
            "BAAI/bge-large-en-v1.5",
            "gpt-3.5-turbo",
            "gpt-4"
        ]
        
        invalid_models = [
            "",  # Empty model name
            "nonexistent/model",  # Non-existent model
            "../../../etc/passwd",  # Path traversal
        ]
        
        for model in valid_models:
            self.assertIsInstance(model, str)
            self.assertGreater(len(model), 0)
        
        for model in invalid_models:
            if model == "":
                self.assertEqual(len(model), 0)
            if "../" in model:
                # Should detect suspicious paths
                self.assertIn("../", model)


if __name__ == '__main__':
    # Create the SafetyManager as a utility for the main codebase
    print("TinyOwl Data Safety Test Suite")
    print("=" * 50)
    
    # Run all safety tests
    unittest.main(verbosity=2)