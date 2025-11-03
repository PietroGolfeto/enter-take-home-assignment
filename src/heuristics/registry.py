"""
Heuristics Registry Module

Lightweight coordinator that routes heuristics extraction to appropriate label-specific modules.
This module follows the Open/Closed Principle by allowing new document types to be added
without modifying existing code.
"""

from typing import Dict, Any

from . import label_oab, label_sistema, generic


def run_heuristics(label: str, text: str, schema_dict: Dict[str, str]) -> Dict[str, Any]:
    """
    Extract field values from text based on the provided schema using heuristics.
    
    This function uses a dual-mode strategy:
    - Prong 1: Optimized label-specific rules for known document types
    - Prong 2: Generic adaptive rules as fallback
    
    Args:
        label: The document label/type (e.g., 'carteira_oab', 'tela_sistema')
        text: The extracted text from the PDF document
        schema_dict: Dictionary mapping field names to their descriptions
    
    Returns:
        Dictionary containing:
        - Each field name mapped to its extracted value (or None if not found)
        - '__found_all__': Boolean indicating if all fields were successfully extracted
    """
    # STEP 1: Initialize all fields to None
    results: Dict[str, Any] = {field_name: None for field_name in schema_dict.keys()}
    
    # STEP 2: PRONG 1 - Label-Specific Optimized Rules
    if 'oab' in label.lower():
        label_oab.run_oab_rules(text, schema_dict, results)
    elif 'sistema' in label.lower():
        label_sistema.run_sistema_rules(text, schema_dict, results)
    
    # STEP 3: PRONG 2 - Generic Adaptive Rules
    generic.run_generic_rules(text, schema_dict, results)
    
    # STEP 4: Calculate metadata and return
    found_all = all(results.get(field_name) is not None for field_name in schema_dict)
    results['__found_all__'] = found_all
    
    return results
