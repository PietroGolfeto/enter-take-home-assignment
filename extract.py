#!/usr/bin/env python3
"""
PDF Data Extraction CLI

Lightweight CLI entry point for the PDF data extraction system.
This module follows the Single Responsibility Principle by only handling CLI parsing
and delegating extraction logic to the src package.
"""

import argparse
import json
import sys
import logging

from src.orchestration import extract_data_from_pdf
from src.utils.logging_config import setup_logging
from src.utils.error_handler import (
    PDFExtractionError,
    PDFParseError,
    SchemaError,
    LLMError,
    CacheError
)


def main():
    """
    Main entry point for the extraction script.
    
    This function orchestrates the three-level extraction strategy:
    Level 1: Check global cache for previously extracted results
    Level 2: Use heuristics-based extraction (fast, rule-based)
    Level 3: Fall back to LLM extraction if heuristics fail
    
    The extracted data is cached for future use and printed as JSON.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Extract structured data from PDF files based on a JSON schema.'
    )
    
    # Add three mandatory positional arguments
    parser.add_argument(
        'label',
        type=str,
        help='Label or identifier for the extraction task'
    )
    
    parser.add_argument(
        'extraction_schema',
        type=str,
        help='JSON string defining the extraction schema'
    )
    
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to the PDF file to extract data from'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print a detailed debug report to stderr.'
    )
    
    # Step 1: Parse command-line arguments
    args = parser.parse_args()
    
    # Step 2: Set up logging (uses --verbose)
    setup_logging(args.verbose)
    
    try:
        # Step 3: Validate Schema
        try:
            schema_dict = json.loads(args.extraction_schema)
        except json.JSONDecodeError as e:
            raise SchemaError(f"Invalid JSON in extraction_schema: {e}")
        
        # Step 4: Run the Main Extraction Process
        # This is now A SINGLE function call
        final_result, metadata = extract_data_from_pdf(
            label=args.label,
            schema_dict=schema_dict,
            pdf_path=args.pdf_path
        )
        
        # Step 5: Print the SUCCESS output (to stdout)
        print(json.dumps(final_result, indent=2, ensure_ascii=False))
        sys.exit(0)
        
    except (PDFExtractionError, PDFParseError, SchemaError, LLMError, CacheError, FileNotFoundError) as e:
        # Step 6: Catch any expected errors
        logging.error(f"Extraction failed: {e}")
        sys.exit(1)
    except Exception as e:
        # Step 7: Catch any other unexpected errors
        logging.error(f"An unexpected error occurred: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()
