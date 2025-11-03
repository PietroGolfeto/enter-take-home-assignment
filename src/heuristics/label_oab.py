"""
Heuristics Module: OAB-Specific Rules

Contains 8 optimized heuristics rules for Brazilian lawyer ID cards (Carteira da OAB).
This module follows the Single Responsibility Principle by only handling OAB document extraction.
"""

import re
from typing import Dict, Any


def run_oab_rules(text: str, schema_dict: Dict[str, str], results: Dict[str, Any]) -> None:
    """
    Apply OAB-specific heuristics rules to extract field values.
    
    This function modifies the results dictionary in-place.
    Contains 8 specialized rules for Brazilian lawyer ID cards.
    
    Args:
        text: The extracted text from the PDF document
        schema_dict: Dictionary mapping field names to their descriptions
        results: Dictionary to store extracted values (modified in-place)
    """
    # OAB-SPECIFIC RULE BANK (8 rules for OAB ID card fields)
    # Triggered for any label containing 'oab'
    
    for field_name, description in schema_dict.items():
        # Only apply if field not already found
        if results[field_name] is not None:
            continue
        
        # OAB Rule 1: Nome (Name) - Uppercase names
        if 'nome' in field_name.lower():
            match = re.search(r'\b([A-ZÀ-Ú]+(?:[\s\'][A-ZÀ-Ú]+)*)\b', text)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 2: Inscricao (Registration) - 6 digits
        elif ('inscricao' in field_name.lower() or 'inscriçao' in field_name.lower() or 
              'inscriçâo' in field_name.lower() or 'oab' in field_name.lower()):
            match = re.search(r'\b(\d{6})\b', text)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 3: Seccional (State section) - 2-letter state code
        elif 'seccional' in field_name.lower():
            # Try pattern 1: After "CONSELHO SECCIONAL"
            match = re.search(r'CONSELHO SECCIONAL[\s\-]+([A-Z]{2})\b', text, re.IGNORECASE)
            if not match:
                # Try pattern 2: Standalone state code
                if re.search(r'Seccional', text, re.IGNORECASE):
                    match = re.search(r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', text)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 4: Subsecao (Subsection) - Full state name after "CONSELHO SECCIONAL"
        elif 'subsec' in field_name.lower() or 'subseç' in field_name.lower():
            # Pattern 1: With dash
            match = re.search(r'CONSELHO\s+SECCIONAL\s*[-–]\s*([A-ZÀ-Ú\s]+?)(?=\n)', text, re.IGNORECASE)
            if not match:
                # Pattern 2: Without dash
                match = re.search(r'CONSELHO\s+SECCIONAL\s+([A-ZÀ-Ú\s]+?)(?=\n)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 5: Categoria (Category) - Professional status keywords
        elif 'categoria' in field_name.lower():
            match = re.search(r'\b(ADVOGADO|ADVOGADA|SUPLEMENTAR|ESTAGIARIO|ESTAGIARIA)\b', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 6: Endereco (Address) - Multi-line address after "ENDEREÇO Profissional"
        elif 'endereco' in field_name.lower() or 'endereço' in field_name.lower():
            match = re.search(r'ENDERE[CÇ]O\s+Profissional\s*\n([A-ZÀ-Ú0-9][^\n]+)\n([A-ZÀ-Ú][^\n]+)\n(\d+)', text, re.IGNORECASE)
            if match:
                address_parts = [match.group(1), match.group(2), match.group(3)]
                results[field_name] = '\n'.join(address_parts).strip()
        
        # OAB Rule 7: Telefone (Phone) - Brazilian phone formats or None if keyword exists
        elif 'telefone' in field_name.lower():
            if re.search(r'TELEFONE', text, re.IGNORECASE):
                # Try multiple phone patterns
                match = re.search(r'\(\d{2}\)\s*\d{4,5}-\d{4}', text)
                if not match:
                    match = re.search(r'\b\d{2}\s+\d{4,5}-\d{4}\b', text)
                if not match:
                    match = re.search(r'\b\d{10,11}\b', text)
                if match:
                    results[field_name] = match.group(0).strip()
        
        # OAB Rule 8: Situacao (Status) - Status after "SITUAÇÃO"
        elif 'situacao' in field_name.lower() or 'situação' in field_name.lower():
            match = re.search(r'SITUA[CÇ](?:A[OÃ]|Ã[OÃ])\s+([A-ZÀ-Ú]+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()

import re
from typing import Dict, Any


def apply_oab_rules(
    text: str,
    schema_dict: Dict[str, str],
    results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply OAB-specific heuristics rules.
    
    Triggered for any label containing 'oab' (e.g., 'carteira_oab', 'documento_oab').
    Contains 8 specialized rules for Brazilian lawyer ID card fields.
    
    Args:
        text: Extracted text from PDF
        schema_dict: Schema mapping field names to descriptions
        results: Current extraction results (modified in place)
        
    Returns:
        Updated results dictionary
    """
    for field_name, description in schema_dict.items():
        
        # OAB Rule 1: Nome (Name) - Uppercase names
        if 'nome' in field_name.lower():
            match = re.search(r'\b([A-ZÀ-Ú]+(?:[\s\'][A-ZÀ-Ú]+)*)\b', text)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 2: Inscricao (Registration) - 6 digits
        elif ('inscricao' in field_name.lower() or 'inscriçao' in field_name.lower() or 
              'inscriçâo' in field_name.lower() or 'oab' in field_name.lower()):
            match = re.search(r'\b(\d{6})\b', text)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 3: Seccional (State section) - 2-letter state code
        elif 'seccional' in field_name.lower():
            # Try pattern 1: After "CONSELHO SECCIONAL"
            match = re.search(r'CONSELHO SECCIONAL[\s\-]+([A-Z]{2})\b', text, re.IGNORECASE)
            if not match:
                # Try pattern 2: Standalone state code
                if re.search(r'Seccional', text, re.IGNORECASE):
                    match = re.search(r'\b(AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO)\b', text)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 4: Subsecao (Subsection) - Full state name after "CONSELHO SECCIONAL"
        elif 'subsec' in field_name.lower() or 'subseç' in field_name.lower():
            # Pattern 1: With dash
            match = re.search(r'CONSELHO\s+SECCIONAL\s*[-–]\s*([A-ZÀ-Ú\s]+?)(?=\n)', text, re.IGNORECASE)
            if not match:
                # Pattern 2: Without dash
                match = re.search(r'CONSELHO\s+SECCIONAL\s+([A-ZÀ-Ú\s]+?)(?=\n)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 5: Categoria (Category) - Professional status keywords
        elif 'categoria' in field_name.lower():
            match = re.search(r'\b(ADVOGADO|ADVOGADA|SUPLEMENTAR|ESTAGIARIO|ESTAGIARIA)\b', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()
        
        # OAB Rule 6: Endereco (Address) - Multi-line address after "ENDEREÇO Profissional"
        elif 'endereco' in field_name.lower() or 'endereço' in field_name.lower():
            match = re.search(r'ENDERE[CÇ]O\s+Profissional\s*\n([A-ZÀ-Ú0-9][^\n]+)\n([A-ZÀ-Ú][^\n]+)\n(\d+)', text, re.IGNORECASE)
            if match:
                address_parts = [match.group(1), match.group(2), match.group(3)]
                results[field_name] = '\n'.join(address_parts).strip()
        
        # OAB Rule 7: Telefone (Phone) - Brazilian phone formats or None if keyword exists
        elif 'telefone' in field_name.lower():
            if re.search(r'TELEFONE', text, re.IGNORECASE):
                # Try multiple phone patterns
                match = re.search(r'\(\d{2}\)\s*\d{4,5}-\d{4}', text)
                if not match:
                    match = re.search(r'\b\d{2}\s+\d{4,5}-\d{4}\b', text)
                if not match:
                    match = re.search(r'\b\d{10,11}\b', text)
                if match:
                    results[field_name] = match.group(0).strip()
                # else: stays None (keyword exists but no number found)
        
        # OAB Rule 8: Situacao (Status) - Status after "SITUAÇÃO"
        elif 'situacao' in field_name.lower() or 'situação' in field_name.lower():
            match = re.search(r'SITUA[CÇ](?:A[OÃ]|Ã[OÃ])\s+([A-ZÀ-Ú]+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()
    
    return results
