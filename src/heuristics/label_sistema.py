"""
Sistema Heuristics Module

Contains label-specific rules for tela_sistema documents (system form/report documents).
These are the 11 anti-fragile multi-pattern rules for extracting fields from various
system layouts (Form vs. Table).
"""

import re
from typing import Dict, Any


def run_sistema_rules(
    text: str,
    schema_dict: Dict[str, str],
    results: Dict[str, Any]
) -> None:
    """
    Apply Sistema-specific heuristics rules.
    
    Triggered for any label containing 'sistema' (e.g., 'tela_sistema', 'form_sistema').
    Contains 11 multi-pattern rules designed to handle layout variations.
    
    Args:
        text: Extracted text from PDF
        schema_dict: Schema mapping field names to descriptions
        results: Current extraction results (modified in place)
        
    Returns:
        Updated results dictionary
    """
    for field_name, description in schema_dict.items():
        field_name_lower = field_name.lower()
        
        # Rule 11: cidade - City name before U.F. (state abbreviation)
        if 'cidade' in field_name_lower and results[field_name] is None:
            match = re.search(r'Cidade:\s+([A-Za-zÀ-úç\s]+?)\s+U\.F', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1).strip()
        
        # Rule 12: pesquisa_por - Search type (CLIENTE, parente, prestador, outro)
        elif 'pesquisa_por' in field_name_lower and results[field_name] is None:
            match = re.search(r'Pesquisar por:.*?Buscar\s+(CLIENTE|parente|prestador|outro)', text, re.IGNORECASE | re.DOTALL)
            if match:
                results[field_name] = match.group(1)
        
        # Rule 13: pesquisa_tipo - Search method (CPF, CNPJ, Nome, email)
        elif 'pesquisa_tipo' in field_name_lower and results[field_name] is None:
            match = re.search(r'Tipo:.*?Buscar\s+\w+\s+(CPF|CNPJ|Nome|email)', text, re.IGNORECASE | re.DOTALL)
            if match:
                results[field_name] = match.group(1)
        
        # Rule 14: produto - Product name (MULTI-PATTERN)
        elif 'produto' in field_name_lower and results[field_name] is None:
            # Try Pattern 1: Explicit "Produto" label (form layout)
            match = re.search(r'Produto\s+([A-Z]+(?:\s+[A-Z]+)*?)(?:\s+[A-Z][a-z]|\s*$|\s+\d)', text)
            if match:
                results[field_name] = match.group(1).strip()
            # Pattern 2: Table layout - look for UPPERCASE words
            elif not match:
                uppercase_words = re.findall(r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})*)\b', text)
                exclude = {'CONSIGNADO', 'VENCIDAS', 'SISTEMA', 'CLIENTE', 'BUSCAR', 'TODOS'}
                for word in uppercase_words:
                    if word not in exclude and len(word) >= 4:
                        results[field_name] = word
                        break
        
        # Rule 15: quantidade_parcelas - Number of installments (MULTI-PATTERN)
        elif 'quantidade' in field_name_lower and 'parcela' in field_name_lower and results[field_name] is None:
            # Try Pattern 1: Standard "Qtd. Parcelas" format
            match = re.search(r'Qtd\.?\s*Parcelas?\s+(\d+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1)
            # Pattern 2: Look for any number near "parcela" or "parcel"
            elif not match:
                match = re.search(r'(?:parcelas?|parcel\w*)[:\s]+(\d+)', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1)
        
        # Rule 16: selecao_de_parcelas - Installment selection (MULTI-PATTERN)
        elif ('selecao' in field_name_lower or 'seleção' in field_name_lower) and 'parcela' in field_name_lower and results[field_name] is None:
            # Try Pattern 1: Standard "Seleção de parcelas:" format
            match = re.search(r'Seleção de parcelas:\s+([A-Za-zÀ-úç]+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1)
            # Pattern 2: Find status keywords near "parcelas"
            elif not match:
                match = re.search(r'parcelas[:\s]+.*?(Vencidas|pago|pendente)', text, re.IGNORECASE | re.DOTALL)
                if match:
                    results[field_name] = match.group(1)
        
        # Rule 17: sistema - System name (uppercase)
        elif 'sistema' in field_name_lower and 'tipo' not in field_name_lower and results[field_name] is None:
            # Try pattern with VIr. Parc. first (more specific)
            match = re.search(r'Sistema\s+([A-Z]+)\s+VIr\.\s*Parc\.', text)
            if not match:
                # Fallback to simpler pattern
                match = re.search(r'Sistema\s+([A-Z]+)', text)
            if match:
                results[field_name] = match.group(1)
        
        # Rule 18: tipo_de_operacao - Operation type (MULTI-PATTERN)
        elif 'tipo' in field_name_lower and 'operacao' in field_name_lower and results[field_name] is None:
            # Try Pattern 1: Standard "Tipo Operação:" format
            match = re.search(r'Tipo\s+Operação:\s+([A-Za-zÀ-úç]+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1)
            # Pattern 2: Look for operation keywords
            elif not match:
                match = re.search(r'\b(Renegociação|Renegociacao|Empréstimo|Emprestimo|Refinanciamento|Consignação|Consignacao)\b', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1)
        
        # Rule 19: tipo_de_sistema - System type (MULTI-PATTERN)
        elif 'tipo' in field_name_lower and 'sistema' in field_name_lower and 'operacao' not in field_name_lower and results[field_name] is None:
            # Try Pattern 1: Standard "Tipo Sistema:" format
            match = re.search(r'Tipo\s+Sistema:\s+([A-Za-zÀ-úç]+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1)
            # Pattern 2: Look for system types near "Sistema"
            elif not match:
                match = re.search(r'Sistema[:\s]+.*?(Consignado|Consignacao|Crédito|Credito|Débito|Debito)', text, re.IGNORECASE | re.DOTALL)
                if match:
                    results[field_name] = match.group(1)
        
        # Rule 20: total_de_parcelas - Total value (MULTI-PATTERN)
        elif 'total' in field_name_lower and 'parcela' in field_name_lower and results[field_name] is None:
            # Try Pattern 1: Standard "Total:" format
            match = re.search(r'Total:\s+(\d+(?:\.\d+)?,\d+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1)
            # Pattern 2: "Total Geral" format
            elif not match:
                match = re.search(r'Total\s+Geral\s+(\d+(?:\.\d+)?,\d+)', text, re.IGNORECASE)
                if match:
                    results[field_name] = match.group(1)
        
        # Rule 21: valor_parcela - Installment value
        elif 'valor' in field_name_lower and 'parcela' in field_name_lower and results[field_name] is None:
            match = re.search(r'VIr\.?\s*Parc\.\s+(\d+(?:\.\d+)?,\d+)', text, re.IGNORECASE)
            if match:
                results[field_name] = match.group(1)
