#!/usr/bin/env python3
"""
Test script for simple_query.py
Tests the database connection and basic functionality without requiring API key.
"""

import os
import sys
import chromadb


def test_database_connection():
    """Test ChromaDB connection"""
    try:
        client = chromadb.PersistentClient(path="vectordb")
        collection = client.get_collection("theology")
        count = collection.count()
        print(f"✓ Database connection successful")
        print(f"✓ Theology collection found with {count} documents")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def test_database_search():
    """Test database search functionality"""
    try:
        client = chromadb.PersistentClient(path="vectordb")
        collection = client.get_collection("theology")
        
        # Test search
        results = collection.query(
            query_texts=["prayer"],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        if results["documents"][0]:
            print(f"✓ Database search successful")
            print(f"✓ Found {len(results['documents'][0])} relevant passages for 'prayer'")
            
            # Show first result as example
            first_doc = results["documents"][0][0]
            first_meta = results["metadatas"][0][0]
            title = first_meta.get("title", "Unknown")
            
            print(f"✓ Sample result from '{title}':")
            print(f"  {first_doc[:100]}...")
            return True
        else:
            print("✗ Database search returned no results")
            return False
            
    except Exception as e:
        print(f"✗ Database search failed: {e}")
        return False


def test_openai_client():
    """Test OpenAI client setup (without making API calls)"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("✗ OPENAI_API_KEY environment variable not set")
        print("  Set it with: export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        print("✓ OpenAI client initialized successfully")
        print("  (API key found and client created)")
        return True
    except ImportError:
        print("✗ OpenAI package not installed")
        print("  Install with: pip install openai")
        return False
    except Exception as e:
        print(f"✗ OpenAI client setup failed: {e}")
        return False


def main():
    """Run all tests"""
    print("Testing TinyOwl Simple Query System")
    print("=" * 40)
    
    tests = [
        test_database_connection,
        test_database_search, 
        test_openai_client
    ]
    
    passed = 0
    for test in tests:
        print()
        result = test()
        if result:
            passed += 1
    
    print()
    print("=" * 40)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("✓ All tests passed! The simple query system is ready to use.")
        print()
        print("Try it out:")
        print('  python simple_query.py "What is prayer?"')
        print("  or")
        print("  ./query.sh \"Tell me about the Sabbath\"")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)