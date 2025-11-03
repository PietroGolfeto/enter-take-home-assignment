"""
Orchestration Module

The brain of the 3-level extraction process.
This module coordinates the entire extraction workflow:
  Level 1: Cache lookup
  Level 2: Heuristics-based extraction
  Level 3: LLM fallback for missing fields

This module follows the Single Responsibility Principle (SRP) by only managing orchestration.
"""

import sys
import logging
from typing import Dict, Any, Tuple, List

from src.cache_manager import create_cache_key, get_cached_result, set_cached_result
from src.pdf_parser import extract_text_from_pdf_cached
from src.heuristics.registry import run_heuristics
from src.llm_client import run_llm_extraction


logger = logging.getLogger(__name__)


def extract_data_from_pdf(
    label: str,
    schema_dict: Dict[str, str],
    pdf_path: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Extract structured data from a PDF using a three-level strategy.
    
    This is the main orchestration function that coordinates:
    - Level 1: Cache lookup
    - Level 2: Heuristics-based extraction
    - Level 3: LLM fallback for missing fields
    
    Args:
        label: Document type label (e.g., 'carteira_oab', 'tela_sistema')
        schema_dict: Dictionary mapping field names to their descriptions
        pdf_path: Path to the PDF file
        
    Returns:
        Tuple of (final_result, metadata) where:
        - final_result: Dictionary with extracted field values
        - metadata: Dictionary with extraction statistics and information
        
    Raises:
        FileNotFoundError: If PDF file is not found
        ValueError: If schema is invalid or API key missing
        Exception: For other extraction errors
    """
    # Step 1: Create cache key
    cache_key = create_cache_key(pdf_path, schema_dict)
    
    # Step 2: Level 1 - Check cache
    cached_result = get_cached_result(cache_key)
    if cached_result is not None:
        logging.info(f"Cache hit! Returning cached result for {label}")
        metadata = {
            "cache_hit": True,
            "heuristics_used": False,
            "llm_used": False,
            "label": label
        }
        return cached_result, metadata
    
    # Step 3: Extract text from PDF (cached)
    text = extract_text_from_pdf_cached(pdf_path)
    
    # Step 4: Level 2 - Heuristics extraction
    logging.info(f"Attempting heuristics-based extraction for {label}...")
    heuristic_results = run_heuristics(label, text, schema_dict)
    
    # Analyze heuristics results
    found_fields, missing_fields = _analyze_results(schema_dict, heuristic_results)
    
    # Step 5: Check if all fields were found
    if heuristic_results.get('__found_all__') is True:
        logging.info(f"Heuristics successful! All {len(found_fields)} fields found.")
        logging.info(f"  ✓ Heuristics: {', '.join(found_fields)}")
        
        # Clean result (remove metadata)
        final_result = {k: v for k, v in heuristic_results.items() if k != '__found_all__'}
        
        metadata = {
            "cache_hit": False,
            "heuristics_used": True,
            "llm_used": False,
            "found_by_heuristics": found_fields,
            "label": label
        }
    else:
        # Step 6: Level 3 - Hybrid approach (heuristics + LLM)
        if found_fields:
            logging.info(f"Heuristics found {len(found_fields)}/{len(schema_dict)} fields:")
            logging.info(f"  ✓ Heuristics: {', '.join(found_fields)}")
            logging.info(f"  ✗ Need LLM: {', '.join(missing_fields)}")
        else:
            logging.info(f"Heuristics found 0/{len(schema_dict)} fields. All need LLM.")
        
        logging.info(f"Calling LLM to extract {len(missing_fields)} missing field(s)...")
        
        try:
            # Create schema only for missing fields
            missing_fields_schema = {
                field_name: description 
                for field_name, description in schema_dict.items() 
                if heuristic_results.get(field_name) is None
            }
            
            # Extract only missing fields with LLM
            llm_results = run_llm_extraction(text, missing_fields_schema)
            logging.info(f"LLM extraction completed for {len(missing_fields)} field(s).")
            
            # Merge heuristics + LLM results
            final_result = {k: v for k, v in heuristic_results.items() if k != '__found_all__'}
            final_result.update(llm_results)
            
            metadata = {
                "cache_hit": False,
                "heuristics_used": True,
                "llm_used": True,
                "found_by_heuristics": found_fields,
                "found_by_llm": list(llm_results.keys()),
                "label": label
            }
            
        except Exception as e:
            logging.error(f"Error during LLM extraction: {e}")
            # Use heuristic results as fallback
            final_result = {k: v for k, v in heuristic_results.items() if k != '__found_all__'}
            logging.info("Using partial heuristics results as fallback.")
            
            metadata = {
                "cache_hit": False,
                "heuristics_used": True,
                "llm_used": False,
                "llm_error": str(e),
                "found_by_heuristics": found_fields,
                "label": label
            }
    
    # Step 7: Cache the result
    set_cached_result(cache_key, final_result)
    
    return final_result, metadata


def _analyze_results(
    schema_dict: Dict[str, str],
    results: Dict[str, Any]
) -> Tuple[List[str], List[str]]:
    """
    Analyze extraction results to determine which fields were found.
    
    Args:
        schema_dict: Original schema dictionary
        results: Extraction results from heuristics
        
    Returns:
        Tuple of (found_fields, missing_fields) lists
    """
    found_fields = []
    missing_fields = []
    
    for field_name in schema_dict.keys():
        if results.get(field_name) is not None:
            found_fields.append(field_name)
        else:
            missing_fields.append(field_name)
    
    return found_fields, missing_fields
