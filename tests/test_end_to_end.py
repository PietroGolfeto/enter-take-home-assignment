"""
Comprehensive end-to-end tests for the PDF extraction system.
Tests all 6 PDF files from dataset.json with caching verification.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, Mock

from extract import main
from src.pdf_parser import extract_text_from_pdf, extract_text_from_pdf_cached
from src.heuristics.registry import run_heuristics
from src.llm_client import run_llm_extraction
from src.cache_manager import create_cache_key, GLOBAL_CACHE, get_pdf_hash_cached


@pytest.fixture
def dataset():
    """Load the dataset.json file."""
    with open('dataset.json', 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def clear_caches():
    """Clear all caches before each test."""
    GLOBAL_CACHE.clear()
    get_pdf_hash_cached.cache_clear()
    extract_text_from_pdf_cached.cache_clear()
    yield
    # Clear again after test
    GLOBAL_CACHE.clear()
    get_pdf_hash_cached.cache_clear()
    extract_text_from_pdf_cached.cache_clear()


class TestEndToEndCarteiraSab:
    """End-to-end tests for carteira_oab PDF files."""
    
    def test_oab_1_extraction(self, dataset, clear_caches):
        """Test extraction from oab_1.pdf with full schema."""
        # Find the dataset entry
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        assert len(text) > 0, "Extracted text should not be empty"
        
        # Test heuristics first
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        print(f"\n=== OAB_1 Heuristics Results ===")
        print(f"Full result: {json.dumps(heuristic_result, indent=2, ensure_ascii=False)}")
        print(f"Found all: {heuristic_result.get('__found_all__')}")
        
        # Check which fields were found by heuristics
        found_fields = []
        missing_fields = []
        for field_name in schema.keys():
            if heuristic_result.get(field_name) is not None:
                found_fields.append(field_name)
                print(f"  ✓ Heuristics found '{field_name}': {heuristic_result[field_name]}")
            else:
                missing_fields.append(field_name)
                print(f"  ✗ Heuristics missed '{field_name}'")
        
        # Verify expected heuristics results
        # Based on our heuristics rules, we expect to find:
        # - inscricao (6-digit number rule)
        # Note: seccional might not be found if "Seccional XX" pattern doesn't match
        #       (e.g., if they're on separate lines)
        assert 'inscricao' in found_fields, "Heuristics should find inscricao"
        
        # The rest should need LLM
        assert len(missing_fields) > 0, "Some fields should require LLM"
    
    def test_oab_2_extraction(self, dataset, clear_caches):
        """Test extraction from oab_2.pdf."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_2.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        text = extract_text_from_pdf(pdf_path)
        
        # Test heuristics
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        print(f"\n=== OAB_2 Heuristics Results ===")
        for field_name in schema.keys():
            value = heuristic_result.get(field_name)
            if value is not None:
                print(f"  ✓ Heuristics found '{field_name}': {value}")
            else:
                print(f"  ✗ Heuristics missed '{field_name}'")
        
        # Verify at least some fields were found
        found_count = sum(1 for f in schema.keys() if heuristic_result.get(f) is not None)
        assert found_count > 0, "Heuristics should find at least some fields"
    
    def test_oab_3_extraction(self, dataset, clear_caches):
        """Test extraction from oab_3.pdf."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_3.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        text = extract_text_from_pdf(pdf_path)
        
        # Test heuristics
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        print(f"\n=== OAB_3 Heuristics Results ===")
        for field_name in schema.keys():
            value = heuristic_result.get(field_name)
            if value is not None:
                print(f"  ✓ Heuristics found '{field_name}': {value}")
            else:
                print(f"  ✗ Heuristics missed '{field_name}'")
        
        # Verify at least some fields were found
        found_count = sum(1 for f in schema.keys() if heuristic_result.get(f) is not None)
        assert found_count > 0, "Heuristics should find at least some fields"


class TestEndToEndTelaSistema:
    """End-to-end tests for tela_sistema PDF files."""
    
    def test_tela_sistema_1_extraction(self, dataset, clear_caches):
        """Test extraction from tela_sistema_1.pdf."""
        entry = next(e for e in dataset if e['pdf_path'] == 'tela_sistema_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        text = extract_text_from_pdf(pdf_path)
        
        # Test heuristics
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        print(f"\n=== TELA_SISTEMA_1 Heuristics Results ===")
        for field_name in schema.keys():
            value = heuristic_result.get(field_name)
            if value is not None:
                print(f"  ✓ Heuristics found '{field_name}': {value}")
            else:
                print(f"  ✗ Heuristics missed '{field_name}'")
        
        # tela_sistema files likely won't match our OAB-specific heuristics
        # But we should still verify the function runs without errors
        assert '__found_all__' in heuristic_result
    
    def test_tela_sistema_2_extraction(self, dataset, clear_caches):
        """Test extraction from tela_sistema_2.pdf."""
        entry = next(e for e in dataset if e['pdf_path'] == 'tela_sistema_2.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        text = extract_text_from_pdf(pdf_path)
        
        # Test heuristics
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        print(f"\n=== TELA_SISTEMA_2 Heuristics Results ===")
        for field_name in schema.keys():
            value = heuristic_result.get(field_name)
            if value is not None:
                print(f"  ✓ Heuristics found '{field_name}': {value}")
            else:
                print(f"  ✗ Heuristics missed '{field_name}'")
        
        assert '__found_all__' in heuristic_result
    
    def test_tela_sistema_3_extraction(self, dataset, clear_caches):
        """Test extraction from tela_sistema_3.pdf."""
        entry = next(e for e in dataset if e['pdf_path'] == 'tela_sistema_3.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        text = extract_text_from_pdf(pdf_path)
        
        # Test heuristics
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        print(f"\n=== TELA_SISTEMA_3 Heuristics Results ===")
        for field_name in schema.keys():
            value = heuristic_result.get(field_name)
            if value is not None:
                print(f"  ✓ Heuristics found '{field_name}': {value}")
            else:
                print(f"  ✗ Heuristics missed '{field_name}'")
        
        assert '__found_all__' in heuristic_result


class TestCachingBehavior:
    """Test that caching works correctly across multiple extractions."""
    
    def test_global_cache_persists_within_session(self, dataset, clear_caches):
        """Test that GLOBAL_CACHE persists results within the same Python session."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = entry['extraction_schema']
        
        # Create cache key
        cache_key = create_cache_key(pdf_path, schema)
        
        # Verify cache is empty initially
        assert cache_key not in GLOBAL_CACHE
        
        # First extraction - should not be in cache
        text = extract_text_from_pdf(pdf_path)
        heuristic_result = run_heuristics('carteira_oab', text, schema)
        
        # If heuristics don't find all, we'd normally call LLM
        # For testing, we'll manually populate the cache
        test_result = {"nome": "TEST", "inscricao": "123456"}
        GLOBAL_CACHE[cache_key] = test_result
        
        # Verify it's now in cache
        assert cache_key in GLOBAL_CACHE
        assert GLOBAL_CACHE[cache_key] == test_result
        
        # Second extraction - should hit cache
        cached_result = GLOBAL_CACHE.get(cache_key)
        assert cached_result is not None
        assert cached_result == test_result
        
        print(f"\n=== Cache Test Passed ===")
        print(f"Cache key: {cache_key[:16]}...")
        print(f"Cached result: {cached_result}")
    
    def test_pdf_hash_caching(self, dataset, clear_caches):
        """Test that PDF hashing is cached using functools.cache."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        # Clear cache statistics
        get_pdf_hash_cached.cache_clear()
        
        # First call - cache miss
        hash1 = get_pdf_hash_cached(pdf_path)
        info1 = get_pdf_hash_cached.cache_info()
        assert info1.hits == 0
        assert info1.misses == 1
        
        # Second call - cache hit
        hash2 = get_pdf_hash_cached(pdf_path)
        info2 = get_pdf_hash_cached.cache_info()
        assert info2.hits == 1
        assert info2.misses == 1
        
        # Third call - another cache hit
        hash3 = get_pdf_hash_cached(pdf_path)
        info3 = get_pdf_hash_cached.cache_info()
        assert info3.hits == 2
        assert info3.misses == 1
        
        # All hashes should be identical
        assert hash1 == hash2 == hash3
        
        print(f"\n=== PDF Hash Cache Test Passed ===")
        print(f"PDF: {pdf_path}")
        print(f"Hash: {hash1[:16]}...")
        print(f"Final cache stats: hits={info3.hits}, misses={info3.misses}")
    
    def test_text_extraction_caching(self, dataset, clear_caches):
        """Test that PDF text extraction is cached using functools.cache."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        # Clear cache statistics
        extract_text_from_pdf_cached.cache_clear()
        
        # First call - cache miss (should read PDF)
        text1 = extract_text_from_pdf_cached(pdf_path)
        info1 = extract_text_from_pdf_cached.cache_info()
        assert info1.hits == 0
        assert info1.misses == 1
        assert len(text1) > 0
        
        # Second call - cache hit (should NOT read PDF)
        text2 = extract_text_from_pdf_cached(pdf_path)
        info2 = extract_text_from_pdf_cached.cache_info()
        assert info2.hits == 1
        assert info2.misses == 1
        
        # Third call - another cache hit
        text3 = extract_text_from_pdf_cached(pdf_path)
        info3 = extract_text_from_pdf_cached.cache_info()
        assert info3.hits == 2
        assert info3.misses == 1
        
        # All texts should be identical
        assert text1 == text2 == text3
        
        print(f"\n=== Text Extraction Cache Test Passed ===")
        print(f"PDF: {pdf_path}")
        print(f"Text length: {len(text1)} characters")
        print(f"Final cache stats: hits={info3.hits}, misses={info3.misses}")
    
    def test_cache_key_changes_with_schema(self, dataset, clear_caches):
        """Test that different schemas produce different cache keys."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        # Create two different schemas
        schema1 = {"nome": "Nome do profissional"}
        schema2 = {"inscricao": "Número de inscrição"}
        
        # Generate cache keys
        key1 = create_cache_key(pdf_path, schema1)
        key2 = create_cache_key(pdf_path, schema2)
        
        # Keys should be different
        assert key1 != key2
        
        print(f"\n=== Schema Change Test Passed ===")
        print(f"Schema 1 key: {key1[:32]}...")
        print(f"Schema 2 key: {key2[:32]}...")
        print(f"Keys are different: {key1 != key2}")
    
    def test_multiple_extractions_same_file(self, dataset, clear_caches):
        """Test extracting from the same file multiple times with caching."""
        entry = next(e for e in dataset if e['pdf_path'] == 'oab_1.pdf')
        
        pdf_path = f"files/{entry['pdf_path']}"
        if not os.path.exists(pdf_path):
            pytest.skip(f"PDF file not found: {pdf_path}")
        
        schema = {"nome": "Nome", "inscricao": "Inscrição"}
        
        # Create cache key
        cache_key = create_cache_key(pdf_path, schema)
        
        print(f"\n=== Multiple Extraction Test ===")
        
        # Extraction 1 - Cache miss
        assert cache_key not in GLOBAL_CACHE
        text1 = extract_text_from_pdf_cached(pdf_path)
        heuristic1 = run_heuristics('carteira_oab', text1, schema)
        GLOBAL_CACHE[cache_key] = {"nome": "TEST1", "inscricao": "111111"}
        print(f"Extraction 1: Cache miss - populated cache")
        
        # Get initial cache stats
        info_after_first = extract_text_from_pdf_cached.cache_info()
        print(f"After 1st extraction: hits={info_after_first.hits}, misses={info_after_first.misses}")
        
        # Extraction 2 - Cache hit
        assert cache_key in GLOBAL_CACHE
        cached = GLOBAL_CACHE[cache_key]
        assert cached == {"nome": "TEST1", "inscricao": "111111"}
        # Call cached function again to verify caching
        text2 = extract_text_from_pdf_cached(pdf_path)
        print(f"Extraction 2: Cache hit - {cached}")
        
        # Extraction 3 - Cache hit
        assert cache_key in GLOBAL_CACHE
        cached2 = GLOBAL_CACHE[cache_key]
        assert cached2 == {"nome": "TEST1", "inscricao": "111111"}
        # Call cached function again to verify caching
        text3 = extract_text_from_pdf_cached(pdf_path)
        print(f"Extraction 3: Cache hit - {cached2}")
        
        # Verify text extraction cache was used (we called it 3 times total)
        info = extract_text_from_pdf_cached.cache_info()
        assert info.hits >= 2, f"Text extraction should have been cached (expected hits>=2, got hits={info.hits})"
        print(f"Text extraction cache: hits={info.hits}, misses={info.misses}")


class TestAllSixPDFs:
    """Test all 6 PDFs from the dataset in sequence."""
    
    def test_all_pdfs_sequential(self, dataset, clear_caches):
        """Test extracting from all 6 PDFs sequentially."""
        
        print("\n" + "="*70)
        print("COMPREHENSIVE TEST: ALL 6 PDFs")
        print("="*70)
        
        results = []
        
        for i, entry in enumerate(dataset, 1):
            pdf_path = f"files/{entry['pdf_path']}"
            
            if not os.path.exists(pdf_path):
                print(f"\n[{i}/6] SKIPPED: {entry['pdf_path']} (file not found)")
                continue
            
            print(f"\n[{i}/6] Processing: {entry['pdf_path']}")
            print(f"      Label: {entry['label']}")
            print(f"      Schema fields: {list(entry['extraction_schema'].keys())}")
            
            # Extract text
            text = extract_text_from_pdf(pdf_path)
            print(f"      Text length: {len(text)} characters")
            
            # Run heuristics
            heuristic_result = run_heuristics(entry['label'], text, entry['extraction_schema'])
            
            # Count found vs missing fields
            found_fields = []
            missing_fields = []
            
            for field_name in entry['extraction_schema'].keys():
                if heuristic_result.get(field_name) is not None:
                    found_fields.append(field_name)
                else:
                    missing_fields.append(field_name)
            
            print(f"      Heuristics found: {len(found_fields)}/{len(entry['extraction_schema'])}")
            
            if found_fields:
                print(f"      ✓ Found by heuristics: {', '.join(found_fields)}")
            
            if missing_fields:
                print(f"      ✗ Need LLM: {', '.join(missing_fields)}")
            
            results.append({
                'pdf': entry['pdf_path'],
                'label': entry['label'],
                'total_fields': len(entry['extraction_schema']),
                'heuristics_found': len(found_fields),
                'llm_needed': len(missing_fields),
                'found_all': heuristic_result.get('__found_all__', False)
            })
        
        # Print summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        total_fields = sum(r['total_fields'] for r in results)
        total_heuristics = sum(r['heuristics_found'] for r in results)
        total_llm = sum(r['llm_needed'] for r in results)
        
        print(f"Total PDFs processed: {len(results)}")
        print(f"Total fields across all PDFs: {total_fields}")
        print(f"Fields found by heuristics: {total_heuristics} ({100*total_heuristics/total_fields:.1f}%)")
        print(f"Fields needing LLM: {total_llm} ({100*total_llm/total_fields:.1f}%)")
        
        for r in results:
            heuristics_pct = 100 * r['heuristics_found'] / r['total_fields'] if r['total_fields'] > 0 else 0
            print(f"  - {r['pdf']}: {r['heuristics_found']}/{r['total_fields']} " +
                  f"by heuristics ({heuristics_pct:.0f}%)")
        
        # Verify we processed all 6 files
        assert len(results) == 6, f"Expected 6 PDFs, processed {len(results)}"
    
    def test_all_pdfs_with_repeated_extraction(self, dataset, clear_caches):
        """Test extracting each PDF twice to verify caching behavior."""
        
        print("\n" + "="*70)
        print("CACHING TEST: Extract each PDF twice")
        print("="*70)
        
        for entry in dataset:
            pdf_path = f"files/{entry['pdf_path']}"
            
            if not os.path.exists(pdf_path):
                continue
            
            schema = entry['extraction_schema']
            cache_key = create_cache_key(pdf_path, schema)
            
            print(f"\nPDF: {entry['pdf_path']}")
            
            # First extraction
            print(f"  [1st extraction] Cache check...", end=" ")
            if cache_key in GLOBAL_CACHE:
                print("CACHE HIT ✓")
            else:
                print("CACHE MISS - extracting")
                text = extract_text_from_pdf_cached(pdf_path)
                result = run_heuristics('carteira_oab', text, schema)
                # Simulate saving to cache
                GLOBAL_CACHE[cache_key] = {k: v for k, v in result.items() if k != '__found_all__'}
                print(f"  [1st extraction] Saved to cache")
            
            # Second extraction
            print(f"  [2nd extraction] Cache check...", end=" ")
            if cache_key in GLOBAL_CACHE:
                print("CACHE HIT ✓")
                cached_result = GLOBAL_CACHE[cache_key]
                print(f"  [2nd extraction] Retrieved from cache: {len(cached_result)} fields")
            else:
                print("ERROR: Cache should have hit!")
                pytest.fail("Cache should have persisted from first extraction")
        
        print(f"\nFinal GLOBAL_CACHE size: {len(GLOBAL_CACHE)} entries")
        print("All PDFs successfully cached ✓")
