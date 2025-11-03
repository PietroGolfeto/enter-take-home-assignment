"""
Comprehensive unit tests for caching functionality.
Tests cover create_cache_key, extract_text_from_pdf_cached, and integration scenarios.
"""

import pytest
import hashlib
import json
from unittest.mock import Mock, patch, call
import tempfile

from src.cache_manager import (
    create_cache_key,
    get_pdf_hash_cached,
    GLOBAL_CACHE
)
from src.pdf_parser import (
    extract_text_from_pdf_cached,
    extract_text_from_pdf
)


class TestCreateCacheKey:
    """Test suite for create_cache_key function."""
    
    def setup_method(self):
        """Clear caches before each test."""
        get_pdf_hash_cached.cache_clear()
    
    def test_cache_key_format(self, tmp_path):
        """Test that cache key has correct format: pdf_hash:schema_hash."""
        # Create a test PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test PDF content")
        
        # Create a test schema
        schema = {"field1": "value1", "field2": "value2"}
        
        # Generate cache key
        cache_key = create_cache_key(str(pdf_file), schema)
        
        # Verify format (should have exactly one colon separator)
        assert cache_key.count(':') == 1
        parts = cache_key.split(':')
        assert len(parts) == 2
        
        # Both parts should be hex strings (SHA-256 = 64 chars)
        assert len(parts[0]) == 64
        assert len(parts[1]) == 64
        assert all(c in '0123456789abcdef' for c in parts[0])
        assert all(c in '0123456789abcdef' for c in parts[1])
    
    def test_same_pdf_same_schema_same_key(self, tmp_path):
        """Test that same PDF and schema produce same cache key."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Same schema
        schema = {"name": "John", "age": 30}
        
        # Generate keys multiple times
        key1 = create_cache_key(str(pdf_file), schema)
        key2 = create_cache_key(str(pdf_file), schema)
        key3 = create_cache_key(str(pdf_file), schema)
        
        # All should be identical
        assert key1 == key2 == key3
    
    def test_different_pdf_different_key(self, tmp_path):
        """Test that different PDFs produce different cache keys."""
        # Create two different PDFs
        pdf_file1 = tmp_path / "test1.pdf"
        pdf_file2 = tmp_path / "test2.pdf"
        pdf_file1.write_bytes(b"Content A")
        pdf_file2.write_bytes(b"Content B")
        
        # Same schema
        schema = {"field": "value"}
        
        # Generate keys
        key1 = create_cache_key(str(pdf_file1), schema)
        key2 = create_cache_key(str(pdf_file2), schema)
        
        # Keys should be different
        assert key1 != key2
    
    def test_different_schema_different_key(self, tmp_path):
        """Test that different schemas produce different cache keys."""
        # Same PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Different schemas
        schema1 = {"field1": "value1"}
        schema2 = {"field2": "value2"}
        
        # Generate keys
        key1 = create_cache_key(str(pdf_file), schema1)
        key2 = create_cache_key(str(pdf_file), schema2)
        
        # Keys should be different
        assert key1 != key2
    
    def test_schema_key_order_independence(self, tmp_path):
        """Test that schema dict key order doesn't affect cache key (sort_keys=True)."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Same schema content, different key order
        schema1 = {"z": 3, "a": 1, "m": 2}
        schema2 = {"a": 1, "m": 2, "z": 3}
        schema3 = {"m": 2, "z": 3, "a": 1}
        
        # Generate keys
        key1 = create_cache_key(str(pdf_file), schema1)
        key2 = create_cache_key(str(pdf_file), schema2)
        key3 = create_cache_key(str(pdf_file), schema3)
        
        # All keys should be identical (sort_keys ensures consistent ordering)
        assert key1 == key2 == key3
    
    def test_schema_value_changes_affect_key(self, tmp_path):
        """Test that changing schema values produces different keys."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Same structure, different values
        schema1 = {"name": "Alice", "age": 25}
        schema2 = {"name": "Bob", "age": 25}
        schema3 = {"name": "Alice", "age": 30}
        
        # Generate keys
        key1 = create_cache_key(str(pdf_file), schema1)
        key2 = create_cache_key(str(pdf_file), schema2)
        key3 = create_cache_key(str(pdf_file), schema3)
        
        # All keys should be different
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
    
    def test_nested_schema(self, tmp_path):
        """Test cache key generation with nested schema dictionaries."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Nested schema
        schema = {
            "person": {
                "name": "John",
                "address": {
                    "street": "123 Main St",
                    "city": "Boston"
                }
            },
            "metadata": {
                "version": 1
            }
        }
        
        # Should generate valid cache key
        cache_key = create_cache_key(str(pdf_file), schema)
        assert ':' in cache_key
        assert len(cache_key.split(':')[0]) == 64
        assert len(cache_key.split(':')[1]) == 64
    
    def test_empty_schema(self, tmp_path):
        """Test cache key generation with empty schema."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Empty schema
        schema = {}
        
        # Should still generate valid cache key
        cache_key = create_cache_key(str(pdf_file), schema)
        assert ':' in cache_key
        
        # Schema part should be hash of empty dict JSON
        expected_schema_hash = hashlib.sha256(
            json.dumps({}, sort_keys=True).encode('utf-8')
        ).hexdigest()
        assert cache_key.endswith(':' + expected_schema_hash) or cache_key.split(':')[1] == expected_schema_hash
    
    def test_schema_with_special_characters(self, tmp_path):
        """Test schema with special characters and unicode."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        # Schema with special characters
        schema = {
            "name": "José García",
            "description": "Test with émojis 🎉 and symbols: @#$%",
            "unicode": "日本語"
        }
        
        # Should generate valid cache key
        cache_key = create_cache_key(str(pdf_file), schema)
        assert ':' in cache_key
        assert len(cache_key.split(':')[0]) == 64
        assert len(cache_key.split(':')[1]) == 64
    
    def test_uses_cached_pdf_hash(self, tmp_path):
        """Test that create_cache_key uses the cached PDF hash function."""
        # Create a test PDF
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"Test content")
        
        schema = {"field": "value"}
        
        # Clear cache and check initial state
        get_pdf_hash_cached.cache_clear()
        initial_misses = get_pdf_hash_cached.cache_info().misses
        
        # First call to create_cache_key
        key1 = create_cache_key(str(pdf_file), schema)
        
        # Should have one cache miss (PDF hash was calculated)
        assert get_pdf_hash_cached.cache_info().misses == initial_misses + 1
        
        # Second call with same PDF
        key2 = create_cache_key(str(pdf_file), schema)
        
        # Should have one cache hit (PDF hash was retrieved from cache)
        assert get_pdf_hash_cached.cache_info().hits >= 1
        
        # Keys should be identical
        assert key1 == key2


class TestExtractTextFromPdfCached:
    """Test suite for extract_text_from_pdf_cached function."""
    
    def setup_method(self):
        """Clear caches before each test."""
        extract_text_from_pdf_cached.cache_clear()
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_cached_returns_same_result(self, mock_pymupdf_open):
        """Test that cached version returns same result as uncached."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_page = Mock()
        mock_page.get_text.return_value = 'Test text'
        mock_doc.load_page.return_value = mock_page
        mock_pymupdf_open.return_value = mock_doc
        
        # Get text using both functions
        uncached_text = extract_text_from_pdf('test.pdf')
        
        # Reset mock call count
        mock_pymupdf_open.reset_mock()
        mock_doc.reset_mock()
        
        cached_text = extract_text_from_pdf_cached('test.pdf')
        
        # Results should match
        assert uncached_text == cached_text
        assert cached_text == 'Test text'
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_cache_prevents_reopening(self, mock_pymupdf_open):
        """Test that cache prevents re-opening the PDF file."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_page = Mock()
        mock_page.get_text.return_value = 'Cached text'
        mock_doc.load_page.return_value = mock_page
        mock_pymupdf_open.return_value = mock_doc
        
        # First call - should open PDF
        text1 = extract_text_from_pdf_cached('test.pdf')
        assert mock_pymupdf_open.call_count == 1
        
        # Second call - should use cache (no additional open)
        text2 = extract_text_from_pdf_cached('test.pdf')
        assert mock_pymupdf_open.call_count == 1  # Still just 1
        
        # Results should match
        assert text1 == text2
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_cache_per_pdf_path(self, mock_pymupdf_open):
        """Test that cache is keyed by PDF path."""
        # Setup mock to return different text for different files
        def mock_open_side_effect(path):
            mock_doc = Mock()
            mock_doc.page_count = 1
            mock_page = Mock()
            mock_page.get_text.return_value = f'Text from {path}'
            mock_doc.load_page.return_value = mock_page
            return mock_doc
        
        mock_pymupdf_open.side_effect = mock_open_side_effect
        
        # Extract from two different PDFs
        text1 = extract_text_from_pdf_cached('file1.pdf')
        text2 = extract_text_from_pdf_cached('file2.pdf')
        
        # Should be different
        assert text1 == 'Text from file1.pdf'
        assert text2 == 'Text from file2.pdf'
        
        # Extract again - should use cache
        text1_again = extract_text_from_pdf_cached('file1.pdf')
        text2_again = extract_text_from_pdf_cached('file2.pdf')
        
        assert text1 == text1_again
        assert text2 == text2_again
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_cache_statistics(self, mock_pymupdf_open):
        """Test cache hit/miss statistics."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_page = Mock()
        mock_page.get_text.return_value = 'Test'
        mock_doc.load_page.return_value = mock_page
        mock_pymupdf_open.return_value = mock_doc
        
        # Clear cache
        extract_text_from_pdf_cached.cache_clear()
        
        # First call - cache miss
        extract_text_from_pdf_cached('test.pdf')
        info1 = extract_text_from_pdf_cached.cache_info()
        assert info1.misses == 1
        assert info1.hits == 0
        
        # Second call - cache hit
        extract_text_from_pdf_cached('test.pdf')
        info2 = extract_text_from_pdf_cached.cache_info()
        assert info2.misses == 1
        assert info2.hits == 1
        
        # Multiple more calls - all cache hits
        for _ in range(5):
            extract_text_from_pdf_cached('test.pdf')
        
        info3 = extract_text_from_pdf_cached.cache_info()
        assert info3.misses == 1
        assert info3.hits == 6


class TestIntegrationCaching:
    """Integration tests for caching functionality working together."""
    
    def setup_method(self):
        """Clear all caches before each test."""
        get_pdf_hash_cached.cache_clear()
        extract_text_from_pdf_cached.cache_clear()
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_full_workflow_with_caching(self, mock_pymupdf_open, tmp_path):
        """Test complete workflow: hash PDF, create cache key, extract text."""
        # Create a real PDF file
        pdf_file = tmp_path / "workflow.pdf"
        pdf_file.write_bytes(b"PDF content for workflow test")
        
        # Setup mock for text extraction
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_page = Mock()
        mock_page.get_text.return_value = 'Extracted workflow text'
        mock_doc.load_page.return_value = mock_page
        mock_pymupdf_open.return_value = mock_doc
        
        # Step 1: Create cache key
        schema1 = {"field1": "value1"}
        cache_key1 = create_cache_key(str(pdf_file), schema1)
        
        # Step 2: Extract text (first time)
        text1 = extract_text_from_pdf_cached(str(pdf_file))
        
        # Step 3: Create same cache key again (should use cached hash)
        cache_key2 = create_cache_key(str(pdf_file), schema1)
        assert cache_key1 == cache_key2
        
        # Step 4: Extract text again (should use cached text)
        text2 = extract_text_from_pdf_cached(str(pdf_file))
        assert text1 == text2
        
        # Verify PDF was only opened once
        assert mock_pymupdf_open.call_count == 1
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_different_schemas_same_pdf(self, mock_pymupdf_open, tmp_path):
        """Test that different schemas produce different cache keys for same PDF."""
        # Create a PDF file
        pdf_file = tmp_path / "multi_schema.pdf"
        pdf_file.write_bytes(b"PDF content")
        
        # Setup mock
        mock_doc = Mock()
        mock_doc.page_count = 1
        mock_page = Mock()
        mock_page.get_text.return_value = 'Text'
        mock_doc.load_page.return_value = mock_page
        mock_pymupdf_open.return_value = mock_doc
        
        # Create cache keys with different schemas
        schema1 = {"extraction": "type1"}
        schema2 = {"extraction": "type2"}
        schema3 = {"extraction": "type3"}
        
        key1 = create_cache_key(str(pdf_file), schema1)
        key2 = create_cache_key(str(pdf_file), schema2)
        key3 = create_cache_key(str(pdf_file), schema3)
        
        # All keys should be different
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3
        
        # All should share the same PDF hash part
        pdf_hash1 = key1.split(':')[0]
        pdf_hash2 = key2.split(':')[0]
        pdf_hash3 = key3.split(':')[0]
        assert pdf_hash1 == pdf_hash2 == pdf_hash3
    
    def test_cache_invalidation_scenario(self, tmp_path):
        """Test scenario where PDF content changes and cache needs invalidation."""
        # Create initial PDF
        pdf_file = tmp_path / "changing.pdf"
        pdf_file.write_bytes(b"Original content")
        
        schema = {"field": "value"}
        
        # Get initial hash and cache key
        hash1 = get_pdf_hash_cached(str(pdf_file))
        key1 = create_cache_key(str(pdf_file), schema)
        
        # Simulate PDF content change
        pdf_file.write_bytes(b"Modified content")
        
        # Without clearing cache, hash and key would be stale
        hash2 = get_pdf_hash_cached(str(pdf_file))
        key2 = create_cache_key(str(pdf_file), schema)
        
        # Cache returns old values
        assert hash1 == hash2  # Stale!
        assert key1 == key2    # Stale!
        
        # Clear cache to detect change
        get_pdf_hash_cached.cache_clear()
        
        # Now get fresh values
        hash3 = get_pdf_hash_cached(str(pdf_file))
        key3 = create_cache_key(str(pdf_file), schema)
        
        # Should reflect the change
        assert hash3 != hash1
        assert key3 != key1
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_multiple_pdfs_multiple_schemas(self, mock_pymupdf_open, tmp_path):
        """Test caching with multiple PDFs and multiple schemas."""
        # Create multiple PDF files
        pdf_files = []
        for i in range(3):
            pdf_file = tmp_path / f"doc{i}.pdf"
            pdf_file.write_bytes(f"Content {i}".encode())
            pdf_files.append(str(pdf_file))
        
        # Setup mock
        def mock_open_side_effect(path):
            mock_doc = Mock()
            mock_doc.page_count = 1
            mock_page = Mock()
            mock_page.get_text.return_value = f'Text from {path}'
            mock_doc.load_page.return_value = mock_page
            return mock_doc
        
        mock_pymupdf_open.side_effect = mock_open_side_effect
        
        # Create multiple schemas
        schemas = [
            {"type": "A"},
            {"type": "B"},
            {"type": "C"}
        ]
        
        # Generate all combinations of cache keys
        cache_keys = {}
        for pdf in pdf_files:
            for schema in schemas:
                key = create_cache_key(pdf, schema)
                cache_keys[(pdf, json.dumps(schema, sort_keys=True))] = key
        
        # Should have 9 unique cache keys (3 PDFs × 3 schemas)
        assert len(cache_keys) == 9
        assert len(set(cache_keys.values())) == 9  # All unique
        
        # Extract text from all PDFs (should cache)
        texts = {}
        for pdf in pdf_files:
            texts[pdf] = extract_text_from_pdf_cached(pdf)
        
        # Extract again - should use cache
        for pdf in pdf_files:
            text_again = extract_text_from_pdf_cached(pdf)
            assert texts[pdf] == text_again
