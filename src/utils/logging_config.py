"""
Utility Module: Logging Configuration

Centralized logging setup for the extraction system.
This module follows the Single Responsibility Principle (SRP) by only managing logging configuration.
"""
import logging
import sys


def setup_logging(verbose: bool = False):
    """
    Configure logging for the application.
    
    Args:
        verbose: If True, set logging level to DEBUG; otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger with simple format (matching original)
    logging.basicConfig(
        level=level,
        format='# %(message)s',  # Add # prefix to match original format
        stream=sys.stderr,
        force=True  # Force reconfiguration
    )
    
    # Silence noisy loggers
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("pymupdf").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name for the logger (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
