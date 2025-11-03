"""
Comprehensive unit tests for PDF hashing functionality.
Tests cover get_pdf_hash, get_pdf_hash_cached, and edge cases.
"""

import pytest
import hashlib
import tempfile
import os
from unittest.mock import patch, mock_open
from pathlib import Path

from src.cache_manager import get_pdf_hash, get_pdf_hash_cached


class TestGetPdfHash:
    """Test suite for get_pdf_hash function."""
    
    def test_hash_small_file(self, tmp_path):
        """Test hashing a small PDF file."""
        # Create a temporary PDF file with known content
        pdf_file = tmp_path / "test.pdf"
        test_content = b"Small PDF content"
        pdf_file.write_bytes(test_content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Get hash using function
        result = get_pdf_hash(str(pdf_file))
        
        # Verify
        assert result == expected_hash
        assert len(result) == 64  # SHA-256 produces 64 hex characters
    
    def test_hash_large_file(self, tmp_path):
        """Test hashing a large file (>4096 bytes) to verify chunked reading."""
        # Create a file larger than one chunk (4096 bytes)
        pdf_file = tmp_path / "large.pdf"
        test_content = b"X" * 10000  # 10KB file
        pdf_file.write_bytes(test_content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Get hash using function
        result = get_pdf_hash(str(pdf_file))
        
        # Verify
        assert result == expected_hash
    
    def test_hash_empty_file(self, tmp_path):
        """Test hashing an empty file (0 bytes)."""
        # Create an empty file
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b"")
        
        # Calculate expected hash of empty content
        expected_hash = hashlib.sha256(b"").hexdigest()
        
        # Get hash using function
        result = get_pdf_hash(str(pdf_file))
        
        # Verify
        assert result == expected_hash
    
    def test_hash_exact_chunk_size(self, tmp_path):
        """Test hashing a file that is exactly 4096 bytes (one chunk)."""
        # Create a file exactly 4096 bytes
        pdf_file = tmp_path / "exact.pdf"
        test_content = b"A" * 4096
        pdf_file.write_bytes(test_content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Get hash using function
        result = get_pdf_hash(str(pdf_file))
        
        # Verify
        assert result == expected_hash
    
    def test_hash_multiple_chunks(self, tmp_path):
        """Test hashing a file that requires multiple chunks (e.g., 3.5 chunks)."""
        # Create a file that's 14336 bytes (3.5 * 4096)
        pdf_file = tmp_path / "multiple.pdf"
        test_content = b"M" * 14336
        pdf_file.write_bytes(test_content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        # Get hash using function
        result = get_pdf_hash(str(pdf_file))
        
        # Verify
        assert result == expected_hash
    
    def test_hash_file_not_found(self, capsys):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_pdf_hash("nonexistent_file.pdf")
        
        # Note: In the refactored version, library code doesn't print to stderr
        # Error handling is done through exceptions only
    
    def test_hash_permission_error(self, tmp_path, capsys):
        """Test handling of permission errors when reading file."""
        # Create a file
        pdf_file = tmp_path / "noperm.pdf"
        pdf_file.write_bytes(b"test content")
        
        # Mock open to raise PermissionError
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                get_pdf_hash(str(pdf_file))
        
        # Note: In the refactored version, library code doesn't print to stderr
        # Error handling is done through exceptions only
    
    def test_hash_different_content_different_hash(self, tmp_path):
        """Test that different content produces different hashes."""
        # Create two files with different content
        pdf_file1 = tmp_path / "file1.pdf"
        pdf_file2 = tmp_path / "file2.pdf"
        pdf_file1.write_bytes(b"Content A")
        pdf_file2.write_bytes(b"Content B")
        
        # Get hashes
        hash1 = get_pdf_hash(str(pdf_file1))
        hash2 = get_pdf_hash(str(pdf_file2))
        
        # Verify they are different
        assert hash1 != hash2
    
    def test_hash_same_content_same_hash(self, tmp_path):
        """Test that same content produces same hash."""
        # Create two files with identical content
        pdf_file1 = tmp_path / "file1.pdf"
        pdf_file2 = tmp_path / "file2.pdf"
        content = b"Identical content in both files"
        pdf_file1.write_bytes(content)
        pdf_file2.write_bytes(content)
        
        # Get hashes
        hash1 = get_pdf_hash(str(pdf_file1))
        hash2 = get_pdf_hash(str(pdf_file2))
        
        # Verify they are identical
        assert hash1 == hash2
    
    def test_hash_binary_content(self, tmp_path):
        """Test hashing file with binary content (not just ASCII)."""
        # Create a file with binary content
        pdf_file = tmp_path / "binary.pdf"
        binary_content = bytes(range(256))  # All byte values 0-255
        pdf_file.write_bytes(binary_content)
        
        # Calculate expected hash
        expected_hash = hashlib.sha256(binary_content).hexdigest()
        
        # Get hash using function
        result = get_pdf_hash(str(pdf_file))
        
        # Verify
        assert result == expected_hash
    
    def test_hash_consistency_multiple_calls(self, tmp_path):
        """Test that hashing the same file multiple times gives consistent results."""
        # Create a file
        pdf_file = tmp_path / "consistent.pdf"
        pdf_file.write_bytes(b"Test consistency")
        
        # Hash it multiple times
        hash1 = get_pdf_hash(str(pdf_file))
        hash2 = get_pdf_hash(str(pdf_file))
        hash3 = get_pdf_hash(str(pdf_file))
        
        # All should be identical
        assert hash1 == hash2 == hash3


class TestGetPdfHashCached:
    """Test suite for get_pdf_hash_cached function with caching behavior."""
    
    def setup_method(self):
        """Clear the cache before each test."""
        get_pdf_hash_cached.cache_clear()
    
    def test_cached_returns_same_result(self, tmp_path):
        """Test that cached version returns same result as uncached."""
        # Create a file
        pdf_file = tmp_path / "test.pdf"
        content = b"Test caching"
        pdf_file.write_bytes(content)
        
        # Get hash using both functions
        uncached_hash = get_pdf_hash(str(pdf_file))
        cached_hash = get_pdf_hash_cached(str(pdf_file))
        
        # Verify they match
        assert uncached_hash == cached_hash
    
    def test_cache_is_used(self, tmp_path):
        """Test that cache actually prevents re-reading the file."""
        # Create a file
        pdf_file = tmp_path / "cache_test.pdf"
        pdf_file.write_bytes(b"Original content")
        
        # First call - should read the file
        hash1 = get_pdf_hash_cached(str(pdf_file))
        
        # Modify the file
        pdf_file.write_bytes(b"Modified content - should not be reflected!")
        
        # Second call - should return cached result (not re-read)
        hash2 = get_pdf_hash_cached(str(pdf_file))
        
        # Hashes should be the same (cache was used)
        assert hash1 == hash2
        
        # Verify cache was actually used by checking the hash matches original
        expected_hash = hashlib.sha256(b"Original content").hexdigest()
        assert hash1 == expected_hash
    
    def test_cache_per_file_path(self, tmp_path):
        """Test that cache is keyed by file path."""
        # Create two different files
        pdf_file1 = tmp_path / "file1.pdf"
        pdf_file2 = tmp_path / "file2.pdf"
        pdf_file1.write_bytes(b"Content A")
        pdf_file2.write_bytes(b"Content B")
        
        # Hash both files
        hash1 = get_pdf_hash_cached(str(pdf_file1))
        hash2 = get_pdf_hash_cached(str(pdf_file2))
        
        # They should be different
        assert hash1 != hash2
        
        # Hash them again - should use cache
        hash1_again = get_pdf_hash_cached(str(pdf_file1))
        hash2_again = get_pdf_hash_cached(str(pdf_file2))
        
        # Should match original hashes
        assert hash1 == hash1_again
        assert hash2 == hash2_again
    
    def test_cache_info(self, tmp_path):
        """Test cache statistics to verify caching behavior."""
        # Create a file
        pdf_file = tmp_path / "stats.pdf"
        pdf_file.write_bytes(b"Cache stats test")
        
        # Clear cache and check initial state
        get_pdf_hash_cached.cache_clear()
        initial_info = get_pdf_hash_cached.cache_info()
        assert initial_info.hits == 0
        assert initial_info.misses == 0
        
        # First call - should be a cache miss
        get_pdf_hash_cached(str(pdf_file))
        info_after_first = get_pdf_hash_cached.cache_info()
        assert info_after_first.misses == 1
        assert info_after_first.hits == 0
        
        # Second call - should be a cache hit
        get_pdf_hash_cached(str(pdf_file))
        info_after_second = get_pdf_hash_cached.cache_info()
        assert info_after_second.misses == 1
        assert info_after_second.hits == 1
        
        # Multiple more calls - all cache hits
        for _ in range(5):
            get_pdf_hash_cached(str(pdf_file))
        
        info_final = get_pdf_hash_cached.cache_info()
        assert info_final.misses == 1
        assert info_final.hits == 6
    
    def test_cache_clear(self, tmp_path):
        """Test that cache_clear() forces re-reading."""
        # Create a file
        pdf_file = tmp_path / "clear_test.pdf"
        pdf_file.write_bytes(b"Original")
        
        # Get hash
        hash1 = get_pdf_hash_cached(str(pdf_file))
        
        # Modify file
        pdf_file.write_bytes(b"Modified")
        
        # Hash again - should use cache (old hash)
        hash2 = get_pdf_hash_cached(str(pdf_file))
        assert hash1 == hash2
        
        # Clear cache
        get_pdf_hash_cached.cache_clear()
        
        # Hash again - should re-read file (new hash)
        hash3 = get_pdf_hash_cached(str(pdf_file))
        assert hash3 != hash1
        
        # Verify new hash is correct
        expected_hash = hashlib.sha256(b"Modified").hexdigest()
        assert hash3 == expected_hash
    
    def test_cached_file_not_found(self, capsys):
        """Test that cached version also handles file not found."""
        with pytest.raises(FileNotFoundError):
            get_pdf_hash_cached("nonexistent_cached.pdf")
        
        # Note: In the refactored version, library code doesn't print to stderr
        # Error handling is done through exceptions only
    
    def test_cache_with_many_files(self, tmp_path):
        """Test caching behavior with multiple different files."""
        # Create 10 different files
        files = []
        hashes = []
        for i in range(10):
            pdf_file = tmp_path / f"file{i}.pdf"
            pdf_file.write_bytes(f"Content {i}".encode())
            files.append(str(pdf_file))
        
        # Hash all files
        for file_path in files:
            hashes.append(get_pdf_hash_cached(file_path))
        
        # Verify all hashes are different
        assert len(set(hashes)) == 10
        
        # Hash all files again - should all be cache hits
        cache_info_before = get_pdf_hash_cached.cache_info()
        hits_before = cache_info_before.hits
        
        for file_path in files:
            get_pdf_hash_cached(file_path)
        
        cache_info_after = get_pdf_hash_cached.cache_info()
        hits_after = cache_info_after.hits
        
        # Should have 10 more cache hits
        assert hits_after - hits_before == 10
