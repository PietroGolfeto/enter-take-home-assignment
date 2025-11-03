"""
Unit tests for PDF text extraction functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from io import StringIO

from src.pdf_parser import extract_text_from_pdf


class TestExtractTextFromPdf:
    """Test suite for extract_text_from_pdf function."""
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_extract_text_success(self, mock_pymupdf_open):
        """
        Test that extract_text_from_pdf returns 'hello world' 
        when the PDF has one page with that text.
        """
        # Create a mock document
        mock_doc = Mock()
        mock_doc.page_count = 1
        
        # Create a mock page that returns 'hello world'
        mock_page = Mock()
        mock_page.get_text.return_value = 'hello world'
        
        # Configure the mock document to return the mock page
        mock_doc.load_page.return_value = mock_page
        
        # Configure pymupdf.open to return the mock document
        mock_pymupdf_open.return_value = mock_doc
        
        # Call the function
        result = extract_text_from_pdf('dummy.pdf')
        
        # Verify the result
        assert result == 'hello world'
        
        # Verify the function called the right methods
        mock_pymupdf_open.assert_called_once_with('dummy.pdf')
        mock_doc.load_page.assert_called_once_with(0)
        mock_page.get_text.assert_called_once_with('text')
        mock_doc.close.assert_called_once()
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_extract_text_zero_pages(self, mock_pymupdf_open, capsys):
        """
        Test that extract_text_from_pdf raises ValueError
        when the PDF has 0 pages.
        """
        # Create a mock document with 0 pages
        mock_doc = Mock()
        mock_doc.page_count = 0
        
        # Configure pymupdf.open to return the mock document
        mock_pymupdf_open.return_value = mock_doc
        
        # Call the function and expect a ValueError
        with pytest.raises(ValueError) as excinfo:
            extract_text_from_pdf('empty.pdf')
        
        # Verify the error message
        assert "has 0 pages" in str(excinfo.value)
        assert "empty.pdf" in str(excinfo.value)
        
        # Verify the document was still closed
        mock_doc.close.assert_called_once()
        
        # Verify load_page was never called (no pages to load)
        mock_doc.load_page.assert_not_called()
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_extract_text_file_not_found(self, mock_pymupdf_open, capsys):
        """
        Test that extract_text_from_pdf handles file open errors correctly.
        """
        # Configure pymupdf.open to raise an exception
        mock_pymupdf_open.side_effect = FileNotFoundError("File not found")
        
        # Call the function and expect an exception
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf('nonexistent.pdf')
        
        # Note: In the refactored version, library code doesn't print to stderr
        # Error handling is done through exceptions only
    
    @patch('src.pdf_parser.pymupdf.open')
    def test_document_closed_on_exception(self, mock_pymupdf_open):
        """
        Test that the document is closed even when an exception occurs.
        """
        # Create a mock document
        mock_doc = Mock()
        mock_doc.page_count = 1
        
        # Make load_page raise an exception
        mock_doc.load_page.side_effect = Exception("Page load error")
        
        # Configure pymupdf.open to return the mock document
        mock_pymupdf_open.return_value = mock_doc
        
        # Call the function and expect an exception
        with pytest.raises(Exception):
            extract_text_from_pdf('error.pdf')
        
        # Verify the document was still closed
        mock_doc.close.assert_called_once()
