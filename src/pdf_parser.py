"""
PDF Parser Module

Handles all PDF text extraction logic using PyMuPDF.
This module follows the Single Responsibility Principle (SRP) by only handling PDF parsing.
"""

import functools
import sys
import pymupdf
from src.utils.error_handler import PDFParseError


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from the first page of a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from the first page
        
    Raises:
        FileNotFoundError: If the PDF file cannot be found
        ValueError: If the PDF has 0 pages
        Exception: For other PDF processing errors
    """
    doc = None
    try:
        # Attempt to open the PDF file
        try:
            doc = pymupdf.open(pdf_path)
        except FileNotFoundError:
            # Let FileNotFoundError pass through for compatibility
            raise
        except Exception as e:
            raise PDFParseError(f"Failed to open PDF file '{pdf_path}': {e}")
        
        # Check if the PDF has any pages
        if doc.page_count == 0:
            raise ValueError(f"PDF file '{pdf_path}' has 0 pages")
        
        # Load the first page and extract text
        page = doc.load_page(0)
        text = page.get_text('text')
        
        return text
        
    finally:
        # Ensure the document is always closed
        if doc is not None:
            doc.close()


@functools.cache
def extract_text_from_pdf_cached(pdf_path: str) -> str:
    """
    Extract text from the first page of a PDF file with caching enabled.
    
    This function uses functools.cache to cache results based on the pdf_path.
    Subsequent calls with the same pdf_path will return the cached result
    without re-reading the PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text from the first page
        
    Raises:
        FileNotFoundError: If the PDF file cannot be found
        ValueError: If the PDF has 0 pages
        Exception: For other PDF processing errors
    """
    return extract_text_from_pdf(pdf_path)
