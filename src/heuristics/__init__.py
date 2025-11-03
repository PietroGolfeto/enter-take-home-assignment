"""
Heuristics Package

This package contains all heuristics-based extraction rules organized by document type.
The registry module coordinates rule execution based on label matching.
"""

from .registry import run_heuristics

__all__ = ["run_heuristics"]
