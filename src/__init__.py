"""
PDF Data Extraction Package

This package provides modular components for extracting structured data from PDF files
using a hybrid approach combining heuristics-based extraction and LLM fallback.
"""

__version__ = "2.0.0"
__author__ = "Enter AI Take-Home Assignment"

# Package-level imports for convenience
from .orchestration import extract_data_from_pdf
from .heuristics.registry import run_heuristics

__all__ = [
    "extract_data_from_pdf",
    "run_heuristics",
]
