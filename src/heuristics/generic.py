"""
Generic Heuristics Module

Contains generic/adaptive "Prong 2" rules that work across different document types.
These rules are applied as fallback when label-specific rules don't find a field.
"""

import re
from typing import Dict, Any


def run_generic_rules(text: str, schema_dict: Dict[str, str], results: Dict[str, Any]) -> None:
    """
    Apply generic heuristics rules for fields not found by label-specific rules.
    
    These are adaptive rules that work across different document types:
    - CPF (Brazilian taxpayer ID)
    - Phone numbers
    - Dates
    
    Args:
        text: Extracted text from PDF
        schema_dict: Schema mapping field names to descriptions
        results: Current extraction results (modified in place)
        
    Returns:
        Updated results dictionary
    """
    for field_name, description in schema_dict.items():
        # Only apply generic rules if field wasn't found by label-specific rules
        if results[field_name] is None:
            
            # Generic Rule 1: CPF (Brazilian taxpayer ID) - Adaptive formats
            if 'CPF' in field_name.upper() or 'CPF' in description.upper() or 'XXX.XXX.XXX-X' in description:
                # Try formatted CPF first (XXX.XXX.XXX-XX)
                match = re.search(r'\b(\d{3}\.\d{3}\.\d{3}-\d{2})\b', text)
                if not match:
                    # Try unformatted CPF (11 continuous digits)
                    match = re.search(r'\b(\d{11})\b', text)
                if match:
                    results[field_name] = match.group(1).strip()
            
            # Generic Rule 2: Telefone (Phone) - Triggered by description or field name
            elif 'TELEFONE' in field_name.upper() or 'TELEFONE' in description.upper():
                if re.search(r'TELEFONE', text, re.IGNORECASE):
                    # Try multiple phone patterns
                    match = re.search(r'\(\d{2}\)\s*\d{4,5}-\d{4}', text)
                    if not match:
                        match = re.search(r'\b\d{2}\s+\d{4,5}-\d{4}\b', text)
                    if not match:
                        match = re.search(r'\b\d{10,11}\b', text)
                    if match:
                        results[field_name] = match.group(0).strip()
            
            # Generic Rule 3: Data (Date) - Only formatted dates with slashes
            elif 'DATA' in field_name.upper() or 'DD/MM/YYYY' in description.upper() or 'DATE' in description.upper():
                # Try DD/MM/YYYY (with slashes, 4-digit year)
                match = re.search(r'\b(\d{2}/\d{2}/\d{4})\b', text)
                if not match:
                    # Try DD/MM/YY (with slashes, 2-digit year)
                    match = re.search(r'\b(\d{2}/\d{2}/\d{2})\b', text)
                if match:
                    results[field_name] = match.group(1).strip()
