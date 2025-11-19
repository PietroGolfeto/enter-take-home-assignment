"""
Cache Manager Module

Handles all caching logic including PDF hashing and result caching.
This module follows the Single Responsibility Principle (SRP) by only managing cache operations.
"""

import functools
import hashlib
import json
import sys
from typing import Dict, Any, Optional

from src.config import PDF_CHUNK_SIZE
from src.utils.error_handler import CacheError


# Global cache for storing extraction results
GLOBAL_CACHE: Dict[str, Dict[str, Any]] = {}


def get_pdf_hash(pdf_path: str) -> str:
    """
    Calculate SHA-256 hash of a PDF file in a memory-efficient manner.
    
    This function reads the PDF file in chunks to handle large files
    without loading the entire file into memory.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Hexadecimal string representation of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the PDF file cannot be found
        IOError: If there's an error reading the file
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(pdf_path, 'rb') as f:
            # Read the file in chunks for memory efficiency
            while True:
                chunk = f.read(PDF_CHUNK_SIZE)
                if not chunk:
                    break
                sha256_hash.update(chunk)
    except (FileNotFoundError, PermissionError):
        # Let these errors pass through for compatibility
        raise
    except IOError as e:
        raise CacheError(f"Failed to read PDF file '{pdf_path}': {e}")
    
    return sha256_hash.hexdigest()


@functools.cache
def get_pdf_hash_cached(pdf_path: str) -> str:
    """
    Calculate SHA-256 hash of a PDF file with caching enabled.
    
    This function uses functools.cache to cache hash results based on the pdf_path.
    Subsequent calls with the same pdf_path will return the cached hash
    without re-reading the PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Hexadecimal string representation of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the PDF file cannot be found
        IOError: If there's an error reading the file
    """
    return get_pdf_hash(pdf_path)


def create_cache_key(pdf_path: str, schema_dict: Dict[str, str]) -> str:
    """
    Create a unique cache key combining PDF content hash and schema hash.
    
    This function generates a cache key that uniquely identifies the combination
    of a PDF file and an extraction schema. The key changes if either the PDF
    content or the schema changes.
    
    Args:
        pdf_path: Path to the PDF file
        schema_dict: Dictionary containing the extraction schema
        
    Returns:
        Combined cache key in format 'pdf_hash:schema_hash'
        
    Raises:
        FileNotFoundError: If the PDF file cannot be found
        IOError: If there's an error reading the file
    """
    # Get the hash of the PDF file (cached)
    pdf_hash = get_pdf_hash_cached(pdf_path)
    
    # Convert schema to canonical JSON string (sorted keys for consistency)
    schema_json = json.dumps(schema_dict, sort_keys=True)
    
    # Calculate SHA-256 hash of the schema
    schema_hash = hashlib.sha256(schema_json.encode('utf-8')).hexdigest()
    
    # Return combined key
    return f"{pdf_hash}:{schema_hash}"


def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a cached extraction result.
    
    Args:
        cache_key: The cache key to lookup
        
    Returns:
        Cached result dictionary if found, None otherwise
    """
    return GLOBAL_CACHE.get(cache_key)


def set_cached_result(cache_key: str, result: Dict[str, Any]) -> None:
    """
    Store an extraction result in the cache.
    
    Args:
        cache_key: The cache key to store under
        result: The extraction result to cache
    """
    GLOBAL_CACHE[cache_key] = result


def clear_cache() -> None:
    """Clear all cached results."""
    GLOBAL_CACHE.clear()
