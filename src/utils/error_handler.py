"""
Utility Module: Error Handler

Custom exception classes for structured error handling.
This module follows the Single Responsibility Principle (SRP) by only defining exceptions.
"""


class ExtractionError(Exception):
    """Base exception for all extraction-related errors."""
    pass


class PDFExtractionError(ExtractionError):
    """Raised when PDF extraction fails."""
    pass


class PDFParseError(ExtractionError):
    """Raised when PDF parsing fails."""
    pass


class CacheError(ExtractionError):
    """Raised when cache operations fail."""
    pass


class LLMError(ExtractionError):
    """Raised when LLM API calls fail."""
    pass


class SchemaError(ExtractionError):
    """Raised when schema validation fails."""
    pass


class SchemaValidationError(ExtractionError):
    """Raised when schema validation fails."""
    pass
