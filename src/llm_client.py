"""
LLM Client Module

Handles all OpenAI API interactions and prompt building.
This module follows the Single Responsibility Principle (SRP) by only managing LLM operations.
"""

import json
import os
import sys
from typing import Dict, Any

from openai import OpenAI

from src.config import OPENAI_MODEL, OPENAI_RESPONSE_FORMAT
from src.utils.error_handler import LLMError


def build_extraction_prompt(pdf_text: str, schema_dict: Dict[str, str]) -> str:
    """
    Build a perfect prompt for the LLM to extract field values from PDF text.
    
    This function creates a carefully structured prompt that instructs the LLM
    to extract specific fields from the PDF text according to the schema.
    The prompt includes clear delimiters and instructions for JSON output.
    
    Args:
        pdf_text: The extracted text from the PDF document
        schema_dict: Dictionary mapping field names to their descriptions
        
    Returns:
        Formatted prompt string for the LLM
        
    Example:
        >>> schema = {"nome": "Nome do profissional", "cpf": "CPF number"}
        >>> text = "João Silva CPF: 123.456.789-00"
        >>> prompt = build_extraction_prompt(text, schema)
    """
    # Convert schema to JSON string preserving special characters (ç, ã, etc.)
    schema_string = json.dumps(schema_dict, ensure_ascii=False, indent=2)
    
    # Build the user prompt with clear delimiters
    user_prompt = f"""Extract the following fields from the PDF text below.

SCHEMA (field_name: description):
{schema_string}

PDF TEXT:
---
{pdf_text}
---

INSTRUCTIONS:
- Extract each field according to its description in the schema
- Return a JSON object with the field names as keys
- If a field cannot be found in the text, use null as the value
- Only include fields that are specified in the schema
- Preserve the exact field names from the schema

Return your response as a valid JSON object."""
    
    return user_prompt


def run_llm_extraction(text: str, schema_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract field values using OpenAI LLM as a fallback extraction method.
    
    This function uses GPT to extract structured data when heuristics-based
    extraction fails or is insufficient. It ensures the response matches the
    schema structure exactly.
    
    Args:
        text: The extracted text from the PDF document
        schema_dict: Dictionary mapping field names to their descriptions
        
    Returns:
        Dictionary containing:
        - Each field name from schema_dict mapped to its extracted value (or None)
        - Fields not in schema_dict are excluded
        - Missing fields are set to None
        
    Raises:
        ValueError: If OPENAI_API_KEY is not set
        Exception: If API call fails
        
    Example:
        >>> text = "John Doe lives in Boston"
        >>> schema = {"name": "Person's name", "city": "City name"}
        >>> run_llm_extraction(text, schema)
        {'name': 'John Doe', 'city': 'Boston'}
    """
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise LLMError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it using: export OPENAI_API_KEY='your-api-key-here'"
        )
    
    # Instantiate OpenAI client (reads OPENAI_API_KEY from environment)
    client = OpenAI()
    
    # Build the extraction prompt
    prompt = build_extraction_prompt(text, schema_dict)
    
    try:
        # System message instructing the LLM to return JSON
        system_message = (
            "You are a professional data extraction assistant. "
            "Your task is to extract structured information from documents and return it in JSON format. "
            "Always respond with valid JSON. "
            "Be precise and only extract information that is clearly present in the text."
        )
        
        # Call OpenAI API with JSON response format
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format=OPENAI_RESPONSE_FORMAT
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content
        
        # Parse the JSON response
        result_dict = json.loads(response_content)
        
        # Build final result ensuring it matches the schema structure exactly
        final_result = {}
        for key in schema_dict.keys():
            # Use .get() to safely retrieve values, defaulting to None for missing fields
            final_result[key] = result_dict.get(key, None)
        
        # Note: Extra fields from LLM response are automatically ignored
        # Only fields present in schema_dict are included in final_result
        
        return final_result
        
    except Exception as e:
        raise LLMError(f"LLM extraction failed: {e}")
