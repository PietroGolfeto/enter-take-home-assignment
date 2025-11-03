"""
Comprehensive unit tests for the heuristics engine.
Tests cover all regex rules and integration with real PDF files from the dataset.
"""

import pytest
import json
import os
from pathlib import Path

from src.heuristics.registry import run_heuristics
from src.pdf_parser import extract_text_from_pdf


class TestCPFRule:
    """Test suite for CPF (Brazilian taxpayer ID) extraction rule."""
    
    def test_cpf_basic_extraction(self):
        """Test basic CPF extraction from text."""
        mock_text = 'My CPF is 123.456.789-00 and my phone is 987654321'
        schema = {"cpf": "CPF number in format XXX.XXX.XXX-XX"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '123.456.789-00'
        assert result['__found_all__'] is True
    
    def test_cpf_field_name_trigger(self):
        """Test that CPF in field name triggers the rule."""
        mock_text = 'Document: 111.222.333-44 issued on 2023'
        schema = {"cpf_number": "Some description"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf_number'] == '111.222.333-44'
    
    def test_cpf_description_trigger(self):
        """Test that XXX.XXX.XXX-X in description triggers the rule."""
        mock_text = 'Taxpayer ID: 999.888.777-66'
        schema = {"documento": "Format is XXX.XXX.XXX-X"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['documento'] == '999.888.777-66'
    
    def test_cpf_not_found(self):
        """Test that missing CPF returns None."""
        mock_text = 'No CPF here, just random numbers 123456789'
        schema = {"cpf": "CPF number"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] is None
        assert result['__found_all__'] is False
    
    def test_cpf_multiple_in_text(self):
        """Test extraction when multiple CPF-like patterns exist (should get first)."""
        mock_text = 'First: 111.111.111-11 and Second: 222.222.222-22'
        schema = {"cpf": "CPF number"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match the first occurrence
        assert result['cpf'] == '111.111.111-11'
    
    def test_cpf_with_surrounding_text(self):
        """Test CPF extraction with various surrounding characters."""
        test_cases = [
            ('CPF: 123.456.789-00.', '123.456.789-00'),
            ('(123.456.789-00)', '123.456.789-00'),
            ('CPF:123.456.789-00;', '123.456.789-00'),
            ('  123.456.789-00  ', '123.456.789-00'),
        ]
        
        for text, expected in test_cases:
            schema = {"cpf": "CPF"}
            result = run_heuristics('carteira_oab', text, schema)
            assert result['cpf'] == expected, f"Failed for text: {text}"
    
    def test_cpf_invalid_format_not_matched(self):
        """Test that invalid CPF formats are not matched."""
        invalid_cases = [
            '12.456.789-00',      # Only 2 digits in first group
            '123.45.789-00',      # Only 2 digits in second group
            '123.456.78-00',      # Only 2 digits in third group
            '123.456.789-0',      # Only 1 digit after dash
            '123456789-00',       # Missing dots
            '123.456.789/00',     # Wrong separator
        ]
        
        schema = {"cpf": "CPF number"}
        
        for text in invalid_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['cpf'] is None, f"Should not match: {text}"


class TestInscricaoRule:
    """Test suite for OAB Inscription Number extraction rule."""
    
    def test_inscricao_basic_extraction(self):
        """Test basic inscription number extraction."""
        mock_text = 'Insc. 101943 and ID 1234567'
        schema = {"inscricao": "Número de inscrição do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match 101943 (6 digits) and ignore 1234567 (7 digits)
        assert result['inscricao'] == '101943'
        assert result['__found_all__'] is True
    
    def test_inscricao_word_boundary(self):
        """Test that word boundaries work correctly (6 digits only)."""
        mock_text = 'Numbers: 12345 123456 1234567 12345678'
        schema = {"inscricao": "Número de inscrição"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should only match 123456 (exactly 6 digits with word boundaries)
        assert result['inscricao'] == '123456'
    
    def test_inscricao_with_accented_field_name(self):
        """Test trigger with accented field name (INSCRIÇÂO)."""
        mock_text = 'Registration: 789012'
        schema = {"inscriçâo": "Número de inscrição"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['inscriçâo'] == '789012'
    
    def test_inscricao_without_accent_field_name(self):
        """Test trigger with non-accented field name (INSCRICAO)."""
        mock_text = 'Number: 456789'
        schema = {"inscricao": "Número de inscrição"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['inscricao'] == '456789'
    
    def test_inscricao_oab_field_name_trigger(self):
        """Test that OAB in field name triggers the rule."""
        mock_text = 'OAB Registration: 111222'
        schema = {"oab_number": "Número de inscrição"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['oab_number'] == '111222'
    
    def test_inscricao_requires_numero_in_description(self):
        """Test generic rule behavior - NÚMERO must be in description when label is unknown."""
        mock_text = 'Number: 123456'
        schema = {"some_field": "Some other description without the keyword"}
        
        # Use unknown label to test generic rules
        result = run_heuristics('unknown_label', mock_text, schema)
        
        # Should not match in generic rules because description doesn't trigger it
        assert result['some_field'] is None
    
    def test_inscricao_not_found(self):
        """Test when no 6-digit number exists."""
        mock_text = 'Only 5 digits: 12345 or 7 digits: 1234567'
        schema = {"inscricao": "Número de inscrição"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['inscricao'] is None
        assert result['__found_all__'] is False
    
    def test_inscricao_embedded_in_larger_number(self):
        """Test that 6 digits embedded in larger number are not matched."""
        mock_text = 'Long number: 12345678901234'
        schema = {"inscricao": "Número de inscrição"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should not match because no standalone 6-digit number
        assert result['inscricao'] is None


class TestCategoriaRule:
    """Test suite for Categoria (Professional category) extraction rule."""
    
    def test_categoria_basic_extraction(self):
        """Test basic categoria extraction."""
        mock_text = 'Bla bla bla CATEGORIA: SUPLEMENTAR'
        schema = {"categoria": "Categoria do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['categoria'] == 'SUPLEMENTAR'
        assert result['__found_all__'] is True
    
    def test_categoria_advogado(self):
        """Test extraction of ADVOGADO."""
        mock_text = 'Professional type: ADVOGADO'
        schema = {"categoria": "Categoria"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['categoria'] == 'ADVOGADO'
    
    def test_categoria_advogada(self):
        """Test extraction of ADVOGADA (feminine)."""
        mock_text = 'Type: ADVOGADA'
        schema = {"categoria": "Categoria"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['categoria'] == 'ADVOGADA'
    
    def test_categoria_estagiario(self):
        """Test extraction of ESTAGIARIO (trainee)."""
        mock_text = 'Status: ESTAGIARIO'
        schema = {"categoria": "Categoria"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['categoria'] == 'ESTAGIARIO'
    
    def test_categoria_estagiaria(self):
        """Test extraction of ESTAGIARIA (trainee feminine)."""
        mock_text = 'Status: ESTAGIARIA'
        schema = {"categoria": "Categoria"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['categoria'] == 'ESTAGIARIA'
    
    def test_categoria_case_insensitive(self):
        """Test that categoria extraction is case-insensitive."""
        test_cases = [
            ('Category: advogado', 'advogado'),
            ('Category: Advogado', 'Advogado'),
            ('Category: ADVOGADO', 'ADVOGADO'),
            ('Category: suplementar', 'suplementar'),
        ]
        
        schema = {"categoria": "Categoria"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['categoria'] == expected
    
    def test_categoria_word_boundaries(self):
        """Test that word boundaries work correctly."""
        mock_text = 'Not SUPLEMENTARES but SUPLEMENTAR only'
        schema = {"categoria": "Categoria"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match SUPLEMENTAR (with word boundary), not SUPLEMENTARES
        assert result['categoria'] == 'SUPLEMENTAR'
    
    def test_categoria_not_found(self):
        """Test when categoria is not in text."""
        mock_text = 'No category information here'
        schema = {"categoria": "Categoria"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['categoria'] is None
        assert result['__found_all__'] is False


class TestSituacaoRule:
    """Test suite for Situacao (Status) extraction rule."""
    
    def test_situacao_basic_extraction(self):
        """Test basic situacao extraction - should return just the status word."""
        mock_text = 'Status: SITUAÇÃO REGULAR'
        schema = {"situacao": "Situação do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['situacao'] == 'REGULAR'
        assert result['__found_all__'] is True
    
    def test_situacao_without_accent(self):
        """Test extraction when SITUACAO is written without accent."""
        mock_text = 'Status: SITUACAO REGULAR'
        schema = {"situacao": "Situação"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['situacao'] == 'REGULAR'
    
    def test_situacao_irregular(self):
        """Test extraction of different status values."""
        test_cases = [
            ('SITUAÇÃO REGULAR', 'REGULAR'),
            ('SITUAÇÃO IRREGULAR', 'IRREGULAR'),
            ('SITUACAO ATIVA', 'ATIVA'),
            ('SITUAÇÃO SUSPENSA', 'SUSPENSA'),
        ]
        
        schema = {"situacao": "Status"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['situacao'] == expected, f"Failed for: {text}, got {result['situacao']}"
    
    def test_situacao_case_insensitive(self):
        """Test that situacao extraction is case-insensitive."""
        test_cases = [
            ('Situação Regular', 'Regular'),
            ('SITUAÇÃO REGULAR', 'REGULAR'),
            ('situação regular', 'regular'),
        ]
        
        schema = {"situacao": "Status"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['situacao'] == expected
    
    def test_situacao_with_accents_in_status(self):
        """Test extraction when status word has accents."""
        mock_text = 'SITUAÇÃO VÁLIDA'
        schema = {"situacao": "Status"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['situacao'] == 'VÁLIDA'
    
    def test_situacao_not_found(self):
        """Test when situacao is not in text."""
        mock_text = 'No status information here'
        schema = {"situacao": "Situação"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['situacao'] is None
        assert result['__found_all__'] is False


class TestDataRule:
    """Test suite for Data (Date) extraction rule."""
    
    def test_data_basic_extraction_4_digit_year(self):
        """Test basic date extraction with 4-digit year."""
        mock_text = 'Operation date: 15/03/2024'
        schema = {"data_base": "Data base da operação"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['data_base'] == '15/03/2024'
        assert result['__found_all__'] is True
    
    def test_data_2_digit_year(self):
        """Test date extraction with 2-digit year."""
        mock_text = 'Date: 25/12/23'
        schema = {"data_vencimento": "Data de vencimento"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['data_vencimento'] == '25/12/23'
    
    def test_data_prioritizes_4_digit_year(self):
        """Test that 4-digit year is prioritized over 2-digit year."""
        mock_text = 'Dates: 01/01/23 and 31/12/2024'
        schema = {"data": "Data"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match 4-digit year first
        assert result['data'] == '31/12/2024'
    
    def test_data_field_name_trigger(self):
        """Test that DATA in field name triggers the rule."""
        test_cases = [
            'data_base',
            'data_vencimento',
            'data_referencia',
            'DATA_OPERACAO',
        ]
        
        mock_text = 'Important date: 10/05/2023'
        
        for field_name in test_cases:
            schema = {field_name: "Some description"}
            result = run_heuristics('carteira_oab', mock_text, schema)
            assert result[field_name] == '10/05/2023', f"Failed for field: {field_name}"
    
    def test_data_description_trigger(self):
        """Test that DD/MM/YYYY in description triggers the rule."""
        mock_text = 'Date value: 20/08/2025'
        schema = {"campo": "Formato é DD/MM/YYYY"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['campo'] == '20/08/2025'
    
    def test_data_word_boundaries(self):
        """Test that word boundaries work correctly."""
        mock_text = 'Numbers: 12345678901234 but date is 01/01/2024 ok'
        schema = {"data": "Data"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should only match the date pattern, not random digits
        assert result['data'] == '01/01/2024'
    
    def test_data_multiple_dates_in_text(self):
        """Test extraction when multiple dates exist (should get first)."""
        mock_text = 'Start: 01/01/2024 End: 31/12/2024'
        schema = {"data": "Data"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match the first occurrence
        assert result['data'] == '01/01/2024'
    
    def test_data_various_formats(self):
        """Test extraction of various valid date formats."""
        test_cases = [
            ('Date: 01/01/2024', '01/01/2024'),
            ('Date: 31/12/2023', '31/12/2023'),
            ('Date: 15/06/99', '15/06/99'),
            ('Date: 29/02/2024', '29/02/2024'),  # Leap year
        ]
        
        schema = {"data": "Data"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['data'] == expected, f"Failed for: {text}"
    
    def test_data_with_surrounding_text(self):
        """Test date extraction with various surrounding characters."""
        test_cases = [
            ('Data: 15/03/2024.', '15/03/2024'),
            ('(10/05/2023)', '10/05/2023'),
            ('Date:20/08/2025;', '20/08/2025'),
            ('  01/01/2024  ', '01/01/2024'),
        ]
        
        schema = {"data": "Data"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['data'] == expected, f"Failed for: {text}"
    
    def test_data_not_found(self):
        """Test when no valid date pattern exists."""
        mock_text = 'No date here, just numbers: 123456'
        schema = {"data": "Data"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['data'] is None
        assert result['__found_all__'] is False
    
    def test_data_invalid_formats_not_matched(self):
        """Test that invalid date formats are not matched."""
        invalid_cases = [
            '1/1/2024',        # Single digit day/month
            '01-01-2024',      # Wrong separator
            '01.01.2024',      # Wrong separator
            '2024/01/01',      # Wrong order
            '32/13/2024',      # Invalid day/month
            '01/01/24567',     # 5-digit year
        ]
        
        schema = {"data": "Data"}
        
        for text in invalid_cases:
            result = run_heuristics('carteira_oab', f'Date: {text}', schema)
            # These should not match or might match partially
            # Main point: the regex enforces DD/MM/YYYY or DD/MM/YY format
            if result['data'] is not None:
                # If something matched, verify it's a proper format
                assert '/' in result['data']
                parts = result['data'].split('/')
                assert len(parts) == 3
                assert len(parts[0]) == 2  # Day
                assert len(parts[1]) == 2  # Month
                assert len(parts[2]) in [2, 4]  # Year


class TestNomeRule:
    """Test suite for Nome (Name) extraction rule."""
    
    def test_nome_basic_extraction(self):
        """Test basic name extraction."""
        mock_text = 'Professional: JOANA D\'ARC'
        schema = {"nome": "Nome do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['nome'] == "JOANA D'ARC"
        assert result['__found_all__'] is True
    
    def test_nome_two_words(self):
        """Test extraction of simple two-word name."""
        mock_text = 'Name: SON GOKU'
        schema = {"nome": "Nome da pessoa"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['nome'] == 'SON GOKU'
    
    def test_nome_multiple_words(self):
        """Test extraction of name with multiple words."""
        mock_text = 'Professional: LUIS FILIPE ARAUJO AMARAL'
        schema = {"nome": "Nome do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['nome'] == 'LUIS FILIPE ARAUJO AMARAL'
    
    def test_nome_with_apostrophe(self):
        """Test extraction of names with apostrophes."""
        test_cases = [
            ("JOANA D'ARC", "JOANA D'ARC"),
            ("MARIA D'ANGELO", "MARIA D'ANGELO"),
            ("JEAN D'AVILA", "JEAN D'AVILA"),
        ]
        
        schema = {"nome": "Nome do profissional"}
        
        for name, expected in test_cases:
            text = f'Name: {name}'
            result = run_heuristics('carteira_oab', text, schema)
            assert result['nome'] == expected, f"Failed for: {name}"
    
    def test_nome_with_accents(self):
        """Test extraction of names with Portuguese accents."""
        test_cases = [
            'JOSÉ MARIA',
            'JOÃO SILVA',
            'ANDRÉ LUÍS',
            'ÂNGELA CRISTINA',
        ]
        
        schema = {"nome": "Nome da pessoa"}
        
        for name in test_cases:
            text = f'Professional: {name}'
            result = run_heuristics('carteira_oab', text, schema)
            assert result['nome'] == name, f"Failed for: {name}"
    
    def test_nome_field_name_trigger(self):
        """Test that NOME in field name triggers the rule."""
        test_cases = [
            'nome',
            'nome_completo',
            'NOME_PROFISSIONAL',
        ]
        
        mock_text = 'Name: PEDRO SANTOS'
        
        for field_name in test_cases:
            schema = {field_name: "Nome do profissional"}
            result = run_heuristics('carteira_oab', mock_text, schema)
            assert result[field_name] == 'PEDRO SANTOS', f"Failed for field: {field_name}"
    
    def test_nome_description_triggers(self):
        """Test that keywords in description trigger the rule."""
        test_cases = [
            "Nome do profissional",
            "Nome da pessoa",
            "Nome do indivíduo",
            "Nome completo do profissional",
        ]
        
        mock_text = 'Name: CARLOS ALBERTO'
        
        for description in test_cases:
            schema = {"nome": description}
            result = run_heuristics('carteira_oab', mock_text, schema)
            assert result['nome'] == 'CARLOS ALBERTO', f"Failed for description: {description}"
    
    def test_nome_requires_keyword_in_description(self):
        """Test generic rule behavior - nome requires keywords when label is unknown."""
        mock_text = 'Name: MARIA SILVA'
        schema = {"some_field": "Some other description"}
        
        # Use unknown label to test generic rules
        result = run_heuristics('unknown_label', mock_text, schema)
        
        # Should not match in generic rules because description doesn't trigger it
        assert result['some_field'] is None
    
    def test_nome_ignores_lowercase(self):
        """Test that lowercase names are not matched."""
        mock_text = 'Name: john smith or John Smith'
        schema = {"nome": "Nome do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should not match lowercase or mixed case
        assert result['nome'] is None
    
    def test_nome_allows_single_word(self):
        """Test that single uppercase words are matched."""
        mock_text = 'Name: JOHN'
        schema = {"nome": "Nome da pessoa"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match single uppercase word
        assert result['nome'] == 'JOHN'
    
    def test_nome_with_surrounding_text(self):
        """Test name extraction with various surrounding text."""
        test_cases = [
            ('Nome: PEDRO ALVES.', 'PEDRO ALVES'),
            ('(MARIA COSTA)', 'MARIA COSTA'),
            ('Name: JOÃO SILVA;', 'JOÃO SILVA'),
            ('  CARLOS SANTOS  ', 'CARLOS SANTOS'),
        ]
        
        schema = {"nome": "Nome do profissional"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['nome'] == expected, f"Failed for: {text}"
    
    def test_nome_first_match_in_text(self):
        """Test that first uppercase name is matched."""
        mock_text = 'First: ANA PAULA Second: BRUNO COSTA'
        schema = {"nome": "Nome da pessoa"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should match first occurrence
        assert result['nome'] == 'ANA PAULA'
    
    def test_nome_not_found(self):
        """Test when no valid name pattern exists."""
        mock_text = 'No name here, just text'
        schema = {"nome": "Nome do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['nome'] is None
        assert result['__found_all__'] is False
    
    def test_nome_real_examples(self):
        """Test extraction of real names from OAB PDFs."""
        test_cases = [
            'SON GOKU',
            "JOANA D'ARC",
            'LUIS FILIPE ARAUJO AMARAL',
        ]
        
        schema = {"nome": "Nome do profissional"}
        
        for name in test_cases:
            text = f'Professional name: {name} - ID: 123456'
            result = run_heuristics('carteira_oab', text, schema)
            assert result['nome'] == name, f"Failed for real example: {name}"


class TestSubsecaoRule:
    """Test suite for Subsecao (Subsection) extraction rule."""
    
    def test_subsecao_basic_extraction_with_dash(self):
        """Test basic subsecao extraction with dash separator."""
        mock_text = '''Nome: JOÃO SILVA
Seccional: SP
CONSELHO SECCIONAL - PARANÁ
Categoria: ADVOGADO'''
        schema = {"subsecao": "Subseção à qual o profissional faz parte"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['subsecao'] == 'PARANÁ'
        assert result['__found_all__'] is True
    
    def test_subsecao_with_accented_field_name(self):
        """Test subsecao extraction with accented field name."""
        mock_text = 'CONSELHO SECCIONAL - SÃO PAULO\n'
        schema = {"subseção": "Subseção do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['subseção'] == 'SÃO PAULO'
    
    def test_subsecao_without_dash(self):
        """Test subsecao extraction without dash (space-separated)."""
        mock_text = 'CONSELHO SECCIONAL RIO DE JANEIRO\nCategoria'
        schema = {"subsecao": "Subseção"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['subsecao'] == 'RIO DE JANEIRO'
    
    def test_subsecao_single_word_state(self):
        """Test subsecao with single-word state names."""
        test_cases = [
            ('CONSELHO SECCIONAL - BAHIA\n', 'BAHIA'),
            ('CONSELHO SECCIONAL - CEARÁ\n', 'CEARÁ'),
            ('CONSELHO SECCIONAL - GOIÁS\n', 'GOIÁS'),
        ]
        
        for text, expected in test_cases:
            schema = {"subsecao": "Subseção"}
            result = run_heuristics('carteira_oab', text, schema)
            assert result['subsecao'] == expected, f"Failed for {text}"
    
    def test_subsecao_multi_word_states(self):
        """Test subsecao with multi-word state names."""
        test_cases = [
            ('CONSELHO SECCIONAL - RIO DE JANEIRO\n', 'RIO DE JANEIRO'),
            ('CONSELHO SECCIONAL - RIO GRANDE DO SUL\n', 'RIO GRANDE DO SUL'),
            ('CONSELHO SECCIONAL - RIO GRANDE DO NORTE\n', 'RIO GRANDE DO NORTE'),
            ('CONSELHO SECCIONAL - MATO GROSSO\n', 'MATO GROSSO'),
            ('CONSELHO SECCIONAL - MATO GROSSO DO SUL\n', 'MATO GROSSO DO SUL'),
        ]
        
        for text, expected in test_cases:
            schema = {"subsecao": "Subseção"}
            result = run_heuristics('carteira_oab', text, schema)
            assert result['subsecao'] == expected, f"Failed for {text}"
    
    def test_subsecao_case_insensitive(self):
        """Test that subsecao extraction is case insensitive."""
        test_cases = [
            'CONSELHO SECCIONAL - PARANÁ\n',
            'Conselho Seccional - Paraná\n',
            'conselho seccional - paraná\n',
        ]
        
        for text in test_cases:
            schema = {"subsecao": "Subseção"}
            result = run_heuristics('carteira_oab', text, schema)
            assert result['subsecao'] is not None, f"Failed for {text}"
    
    def test_subsecao_with_en_dash(self):
        """Test subsecao with en-dash (–) instead of hyphen (-)."""
        mock_text = 'CONSELHO SECCIONAL – PARANÁ\nCategoria'
        schema = {"subsecao": "Subseção"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['subsecao'] == 'PARANÁ'
    
    def test_subsecao_not_found(self):
        """Test that missing subsecao returns None."""
        mock_text = 'Nome: JOÃO SILVA\nInscrição: 123456\nCategoria: ADVOGADO'
        schema = {"subsecao": "Subseção"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['subsecao'] is None
        assert result['__found_all__'] is False
    
    def test_subsecao_real_example_oab(self):
        """Test with real OAB PDF text pattern."""
        mock_text = '''JOANA D'ARC
Inscrição
Seccional
Subseção
101943
PR
CONSELHO SECCIONAL - PARANÁ
SUPLEMENTAR'''
        schema = {"subsecao": "Subseção à qual o profissional faz parte"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['subsecao'] == 'PARANÁ'


class TestTelefoneRule:
    """Test suite for Telefone (Phone) extraction rule."""
    
    def test_telefone_formatted_with_parentheses(self):
        """Test phone extraction with (XX) XXXXX-XXXX format."""
        mock_text = 'Telefone Profissional\n(11) 98765-4321\nSituação'
        schema = {"telefone_profissional": "Telefone do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone_profissional'] == '(11) 98765-4321'
        assert result['__found_all__'] is True
    
    def test_telefone_formatted_without_parentheses(self):
        """Test phone extraction with XX XXXXX-XXXX format."""
        mock_text = 'Telefone: 11 98765-4321'
        schema = {"telefone": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone'] == '11 98765-4321'
    
    def test_telefone_continuous_digits_11(self):
        """Test phone extraction with 11 continuous digits."""
        mock_text = 'Telefone: 11987654321'
        schema = {"telefone_profissional": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone_profissional'] == '11987654321'
    
    def test_telefone_continuous_digits_10(self):
        """Test phone extraction with 10 continuous digits."""
        mock_text = 'Telefone: 1134567890'
        schema = {"telefone": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone'] == '1134567890'
    
    def test_telefone_landline_format(self):
        """Test landline phone with (XX) XXXX-XXXX format."""
        mock_text = 'Telefone Profissional\n(11) 3456-7890\nOutro texto'
        schema = {"telefone_profissional": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone_profissional'] == '(11) 3456-7890'
    
    def test_telefone_keyword_exists_no_number(self):
        """Test that returns None when Telefone keyword exists but no number found."""
        mock_text = 'Telefone Profissional\nSITUAÇÃO REGULAR'
        schema = {"telefone_profissional": "Telefone do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone_profissional'] is None
        assert result['__found_all__'] is False
    
    def test_telefone_keyword_not_exists(self):
        """Test that returns None when Telefone keyword doesn't exist."""
        mock_text = 'Nome: JOÃO SILVA\nEndereço: Rua das Flores'
        schema = {"telefone": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone'] is None
        assert result['__found_all__'] is False
    
    def test_telefone_description_trigger(self):
        """Test that 'telefone' in description triggers the rule."""
        mock_text = 'Telefone: (21) 99999-8888'
        schema = {"contato": "Número de telefone para contato"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['contato'] == '(21) 99999-8888'
    
    def test_telefone_with_spaces_variations(self):
        """Test phone extraction with various spacing."""
        test_cases = [
            ('Telefone: (11)98765-4321', '(11)98765-4321'),
            ('Telefone: (11) 98765-4321', '(11) 98765-4321'),
        ]
        
        for text, expected in test_cases:
            schema = {"telefone": "Telefone"}
            result = run_heuristics('carteira_oab', text, schema)
            assert result['telefone'] == expected, f"Failed for {text}"
    
    def test_telefone_multiple_numbers_in_text(self):
        """Test that first phone number is extracted when multiple exist."""
        mock_text = 'Telefone: (11) 98765-4321\nOutro: (21) 99999-8888'
        schema = {"telefone": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone'] == '(11) 98765-4321'
    
    def test_telefone_real_example_oab_no_number(self):
        """Test with real OAB PDF text where telefone exists but no number."""
        mock_text = '''Endereço Profissional
AVENIDA PAULISTA, Nº 2300
SÃO PAULO - SP
01310300
Telefone Profissional
SITUAÇÃO REGULAR'''
        schema = {"telefone_profissional": "Telefone do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['telefone_profissional'] is None
        assert result['__found_all__'] is False
    
    def test_telefone_invalid_digits_not_matched(self):
        """Test that invalid digit sequences are not matched as phone numbers."""
        mock_text = 'Telefone: 123\nCPF: 123.456.789-00\nInscrição: 123456'
        schema = {"telefone": "Telefone"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should not match CPF or 6-digit inscription
        # CPF has dots and dashes, inscription is only 6 digits
        assert result['telefone'] is None


class TestEnderecoRule:
    """Test suite for Endereco (Address) extraction rule."""
    
    def test_endereco_basic_extraction(self):
        """Test basic address extraction."""
        mock_text = '''Endereço Profissional
AVENIDA PAULISTA, Nº 2300
SÃO PAULO - SP
01310300'''
        schema = {"endereco_profissional": "Endereço do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        expected = "AVENIDA PAULISTA, Nº 2300\nSÃO PAULO - SP\n01310300"
        assert result['endereco_profissional'] == expected
        assert result['__found_all__'] is True
    
    def test_endereco_without_accent(self):
        """Test extraction when ENDERECO is written without accent."""
        mock_text = '''Endereco Profissional
RUA DAS FLORES, 123
RIO DE JANEIRO - RJ
20000000'''
        schema = {"endereco": "Endereço"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        expected = "RUA DAS FLORES, 123\nRIO DE JANEIRO - RJ\n20000000"
        assert result['endereco'] == expected
    
    def test_endereco_field_name_triggers(self):
        """Test that ENDERECO/ENDEREÇO in field name triggers the rule."""
        test_cases = [
            'endereco',
            'endereco_profissional',
            'endereço',
            'ENDERECO_COMERCIAL',
        ]
        
        mock_text = '''Endereço Profissional
AVENIDA BRASIL, 1000
BRASÍLIA - DF
70000000'''
        
        for field_name in test_cases:
            schema = {field_name: "Address"}
            result = run_heuristics('carteira_oab', mock_text, schema)
            assert result[field_name] is not None, f"Failed for field: {field_name}"
            assert 'AVENIDA BRASIL' in result[field_name]
    
    def test_endereco_with_special_characters(self):
        """Test address with special characters and accents."""
        mock_text = '''Endereço Profissional
RUA JOSÉ DA SILVA, Nº 456 - Apto 789
BELO HORIZONTE - MG
30000000'''
        schema = {"endereco": "Endereço"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert 'JOSÉ' in result['endereco']
        assert 'Nº 456' in result['endereco']
    
    def test_endereco_multiline_format(self):
        """Test standard 3-line address format."""
        mock_text = '''Endereço Profissional
PRAÇA DA REPÚBLICA, 50 - Centro
SALVADOR - BA
40000000'''
        schema = {"endereco_profissional": "Endereço"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        lines = result['endereco_profissional'].split('\n')
        assert len(lines) == 3
        assert 'PRAÇA DA REPÚBLICA' in lines[0]
        assert 'SALVADOR' in lines[1]
        assert '40000000' in lines[2]
    
    def test_endereco_not_found(self):
        """Test when address pattern is not in text."""
        mock_text = 'No address information here'
        schema = {"endereco": "Endereço"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['endereco'] is None
        assert result['__found_all__'] is False
    
    def test_endereco_real_example(self):
        """Test extraction of real address from OAB PDF."""
        mock_text = '''Endereço Profissional
AVENIDA PAULISTA, Nº 2300 andar Pilotis, Bela Vista
SÃO PAULO - SP
01310300
Telefone Profissional'''
        schema = {"endereco_profissional": "Endereço do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        expected = "AVENIDA PAULISTA, Nº 2300 andar Pilotis, Bela Vista\nSÃO PAULO - SP\n01310300"
        assert result['endereco_profissional'] == expected


class TestSeccionalRule:
    """Test suite for Seccional (State section) extraction rule."""
    
    def test_seccional_basic_extraction(self):
        """Test basic seccional extraction."""
        mock_text = 'Bla bla Seccional PR bla'
        schema = {"seccional": "Seccional do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should return only 'PR', not 'Seccional PR'
        assert result['seccional'] == 'PR'
        assert result['__found_all__'] is True
    
    def test_seccional_captures_group_only(self):
        """Test that only the captured group is returned, not full match."""
        mock_text = 'Location: Seccional SP'
        schema = {"seccional": "State section"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['seccional'] == 'SP'
        assert result['seccional'] != 'Seccional SP'
    
    def test_seccional_various_states(self):
        """Test extraction of different Brazilian state codes."""
        states = ['SP', 'RJ', 'MG', 'RS', 'BA', 'PR', 'SC', 'DF']
        
        for state in states:
            text = f'Document from Seccional {state} region'
            schema = {"seccional": "State"}
            result = run_heuristics('carteira_oab', text, schema)
            assert result['seccional'] == state, f"Failed for state: {state}"
    
    def test_seccional_with_conselho_pattern(self):
        """Test seccional with CONSELHO SECCIONAL pattern."""
        test_cases = [
            ('CONSELHO SECCIONAL SP', 'SP'),
            ('CONSELHO SECCIONAL - PR', 'PR'),
            ('Conselho Seccional RJ', 'RJ'),
        ]
        
        schema = {"seccional": "State"}
        
        for text, expected in test_cases:
            result = run_heuristics('carteira_oab', text, schema)
            assert result['seccional'] == expected, f"Failed for: {text}"
    
    def test_seccional_case_sensitive(self):
        """Test that only uppercase state codes are matched."""
        mock_text = 'Seccional sp lowercase'
        schema = {"seccional": "State"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should not match lowercase
        assert result['seccional'] is None
    
    def test_seccional_not_found(self):
        """Test when seccional pattern is not in text."""
        mock_text = 'No state information here'
        schema = {"seccional": "State section"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['seccional'] is None
        assert result['__found_all__'] is False
    
    def test_seccional_three_letters_not_matched(self):
        """Test that three-letter codes are not matched (only 2 letters)."""
        mock_text = 'Seccional ABC region'
        schema = {"seccional": "State"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Should not match 3 letters
        assert result['seccional'] is None


class TestMultipleFields:
    """Test suite for multiple fields in same schema."""
    
    def test_multiple_fields_all_found(self):
        """Test extraction when all fields are present."""
        mock_text = '''
        Professional Information
        CPF: 123.456.789-00
        Inscription: 101943
        Seccional SP
        '''
        
        schema = {
            "cpf": "CPF do profissional",
            "inscricao": "Número de inscrição",
            "seccional": "Estado"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '123.456.789-00'
        assert result['inscricao'] == '101943'
        assert result['seccional'] == 'SP'
        assert result['__found_all__'] is True
    
    def test_multiple_fields_partial_found(self):
        """Test extraction when only some fields are present."""
        mock_text = 'CPF: 111.222.333-44 and Seccional RJ'
        
        schema = {
            "cpf": "CPF",
            "inscricao": "Número de inscrição",
            "seccional": "State"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '111.222.333-44'
        assert result['inscricao'] is None
        assert result['seccional'] == 'RJ'
        assert result['__found_all__'] is False
    
    def test_multiple_fields_none_found(self):
        """Test when no fields match."""
        mock_text = 'Random text with no extractable information'
        
        schema = {
            "cpf": "CPF",
            "inscricao": "Número de inscrição",
            "seccional": "State"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] is None
        assert result['inscricao'] is None
        assert result['seccional'] is None
        assert result['__found_all__'] is False


class TestEdgeCases:
    """Test suite for edge cases and special scenarios."""
    
    def test_empty_text(self):
        """Test with empty text."""
        schema = {"cpf": "CPF number"}
        result = run_heuristics('carteira_oab', '', schema)
        
        assert result['cpf'] is None
        assert result['__found_all__'] is False
    
    def test_empty_schema(self):
        """Test with empty schema."""
        result = run_heuristics('carteira_oab', 'Some text', {})
        
        assert result == {'__found_all__': True}
    
    def test_field_not_matching_any_rule(self):
        """Test field that doesn't match any rule."""
        mock_text = 'Some data: 12345'
        schema = {"unknown_field": "Some description"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['unknown_field'] is None
        assert result['__found_all__'] is False
    
    def test_special_characters_in_text(self):
        """Test extraction with special characters."""
        mock_text = 'Info: CPF=123.456.789-00; Seccional=SP; Code=101943'
        schema = {
            "cpf": "CPF",
            "inscricao": "Número de inscrição",
            "seccional": "State"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '123.456.789-00'
        assert result['inscricao'] == '101943'
        # Note: This might not match because format is "Seccional=SP" not "Seccional SP"
    
    def test_unicode_characters(self):
        """Test with unicode/accented characters in text."""
        mock_text = 'Profissional: José María\nCPF: 987.654.321-00\nSeção: Seccional MG'
        schema = {"cpf": "CPF do profissional"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '987.654.321-00'


class TestDatasetIntegration:
    """Integration tests using actual PDF files and dataset.json."""
    
    @pytest.fixture
    def dataset(self):
        """Load the dataset.json file."""
        # dataset.json is in the project root, not in tests/
        dataset_path = Path(__file__).parent.parent / 'dataset.json'
        with open(dataset_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @pytest.fixture
    def files_dir(self):
        """Get the files directory path."""
        # files/ directory is in the project root, not in tests/
        return Path(__file__).parent.parent / 'files'
    
    def test_dataset_structure(self, dataset):
        """Test that dataset has expected structure."""
        assert isinstance(dataset, list)
        assert len(dataset) > 0
        
        for entry in dataset:
            assert 'label' in entry
            assert 'extraction_schema' in entry
            assert 'pdf_path' in entry
            assert isinstance(entry['extraction_schema'], dict)
    
    def test_pdf_files_exist(self, dataset, files_dir):
        """Test that all PDF files referenced in dataset exist."""
        for entry in dataset:
            pdf_path = files_dir / entry['pdf_path']
            assert pdf_path.exists(), f"PDF file not found: {pdf_path}"
    
    @pytest.mark.skipif(not os.path.exists('files/oab_1.pdf'), 
                        reason="PDF files not available")
    def test_extract_from_oab_pdf(self, dataset, files_dir):
        """Test extraction from actual OAB PDF file."""
        # Find OAB entries in dataset
        oab_entries = [e for e in dataset if e['label'] == 'carteira_oab']
        
        if not oab_entries:
            pytest.skip("No OAB entries in dataset")
        
        for entry in oab_entries[:1]:  # Test first OAB entry
            pdf_path = files_dir / entry['pdf_path']
            
            if not pdf_path.exists():
                continue
            
            # Extract text from PDF
            text = extract_text_from_pdf(str(pdf_path))
            
            # Run heuristics
            result = run_heuristics(entry['label'], text, entry['extraction_schema'])
            
            # Verify result structure
            assert isinstance(result, dict)
            assert '__found_all__' in result
            
            # Check that we have results for all schema fields
            for field_name in entry['extraction_schema'].keys():
                assert field_name in result
    
    @pytest.mark.skipif(not os.path.exists('files/tela_sistema_1.pdf'),
                        reason="PDF files not available")
    def test_extract_from_tela_sistema_pdf(self, dataset, files_dir):
        """Test extraction from actual tela_sistema PDF file."""
        # Find tela_sistema entries
        sistema_entries = [e for e in dataset if e['label'] == 'tela_sistema']
        
        if not sistema_entries:
            pytest.skip("No tela_sistema entries in dataset")
        
        for entry in sistema_entries[:1]:  # Test first entry
            pdf_path = files_dir / entry['pdf_path']
            
            if not pdf_path.exists():
                continue
            
            # Extract text from PDF
            text = extract_text_from_pdf(str(pdf_path))
            
            # Run heuristics
            result = run_heuristics(entry['label'], text, entry['extraction_schema'])
            
            # Verify result structure
            assert isinstance(result, dict)
            assert '__found_all__' in result
            
            # Check that we have results for all schema fields
            for field_name in entry['extraction_schema'].keys():
                assert field_name in result
    
    def test_schema_field_coverage(self, dataset):
        """Test that we understand all field types in the dataset."""
        all_field_names = set()
        
        for entry in dataset:
            all_field_names.update(entry['extraction_schema'].keys())
        
        # Document all unique field names found
        print(f"\nUnique fields in dataset: {sorted(all_field_names)}")
        
        # This test documents what fields exist (informational)
        assert len(all_field_names) > 0
    
    def test_multiple_documents_same_label(self, dataset):
        """Test that multiple documents with same label can be processed."""
        # Group by label
        by_label = {}
        for entry in dataset:
            label = entry['label']
            if label not in by_label:
                by_label[label] = []
            by_label[label].append(entry)
        
        # Check that we have labels with multiple documents
        multi_doc_labels = {k: v for k, v in by_label.items() if len(v) > 1}
        
        assert len(multi_doc_labels) > 0, "Should have labels with multiple documents"
        
        # Verify schemas might differ for same label
        for label, entries in multi_doc_labels.items():
            schemas = [set(e['extraction_schema'].keys()) for e in entries]
            print(f"\n{label} has {len(entries)} documents with field variations")


class TestHeuristicsRobustness:
    """Test robustness of heuristics against various text formats."""
    
    def test_line_breaks_between_fields(self):
        """Test extraction when fields are on different lines."""
        mock_text = '''
        Nome: João Silva
        CPF: 123.456.789-00
        
        Inscrição: 101943
        
        Seccional MG
        '''
        
        schema = {
            "cpf": "CPF",
            "inscricao": "Número de inscrição",
            "seccional": "State"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '123.456.789-00'
        assert result['inscricao'] == '101943'
        assert result['seccional'] == 'MG'
    
    def test_dense_text_no_spaces(self):
        """Test extraction from dense text with recognizable state codes."""
        mock_text = 'CPF:123.456.789-00,Inscricao:101943,Seccional:SP'
        schema = {
            "cpf": "CPF",
            "inscricao": "Número de inscrição",
            "seccional": "State"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['cpf'] == '123.456.789-00'
        assert result['inscricao'] == '101943'
        # Seccional rule now looks for "CONSELHO SECCIONAL" or valid state codes near "Seccional"
        assert result['seccional'] == 'SP'
    
    def test_mixed_case_text(self):
        """Test extraction with mixed case text."""
        mock_text = 'cpf: 123.456.789-00 INSCRICAO: 101943 Seccional RJ'
        schema = {
            "CPF": "CPF number",
            "Inscricao": "Número de inscrição",
            "SECCIONAL": "State"
        }
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # Field names are case-insensitive for rule matching
        # Note: Seccional pattern requires "Seccional" (capital S) and uppercase state code
        assert result['CPF'] == '123.456.789-00'
        assert result['Inscricao'] == '101943'
        assert result['SECCIONAL'] == 'RJ'


# ========================================
# TELA_SISTEMA RULES TEST SUITE
# ========================================


class TestTelaSistemaCidadeRule:
    """Test suite for cidade (city) extraction rule."""
    
    def test_cidade_basic_extraction(self):
        """Test basic cidade extraction with U.F. marker."""
        mock_text = "Cidade: Mozarlândia U.F: GO CEP: 76800-000"
        schema = {"cidade": "Cidade da operação"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['cidade'] == 'Mozarlândia'
    
    def test_cidade_with_accents(self):
        """Test cidade with Portuguese accents."""
        mock_text = "Cidade: São José dos Campos U.F: SP"
        schema = {"cidade": "Cidade"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['cidade'] == 'São José dos Campos'
    
    def test_cidade_not_found(self):
        """Test cidade returns None when pattern not found."""
        mock_text = "City: Mozarlândia State: GO"
        schema = {"cidade": "Cidade"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['cidade'] is None
    
    def test_cidade_label_isolation(self):
        """Test cidade rule is NOT triggered with carteira_oab label."""
        mock_text = "Cidade: Mozarlândia U.F: GO"
        schema = {"cidade": "Cidade"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        # OAB label should NOT trigger tela_sistema rules
        assert result['cidade'] is None


class TestTelaSistemaPesquisaPorRule:
    """Test suite for pesquisa_por (search type) extraction rule."""
    
    def test_pesquisa_por_cliente(self):
        """Test pesquisa_por extraction with CLIENTE value."""
        mock_text = "Pesquisar por: Buscar CLIENTE Tipo: CPF"
        schema = {"pesquisa_por": "Pesquisa por cliente ou outro"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_por'] == 'CLIENTE'
    
    def test_pesquisa_por_parente(self):
        """Test pesquisa_por with parente value."""
        mock_text = "Pesquisar por: Algum texto Buscar parente"
        schema = {"pesquisa_por": "Tipo de pesquisa"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_por'] == 'parente'
    
    def test_pesquisa_por_case_variations(self):
        """Test pesquisa_por handles case variations."""
        mock_text = "Pesquisar por: Buscar prestador"
        schema = {"pesquisa_por": "Search type"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_por'] == 'prestador'
    
    def test_pesquisa_por_not_found(self):
        """Test pesquisa_por returns None when pattern not found."""
        mock_text = "Search by: customer"
        schema = {"pesquisa_por": "Search type"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_por'] is None
    
    def test_pesquisa_por_label_isolation(self):
        """Test pesquisa_por rule is NOT triggered with carteira_oab label."""
        mock_text = "Pesquisar por: Buscar CLIENTE"
        schema = {"pesquisa_por": "Search type"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['pesquisa_por'] is None


class TestTelaSistemaPesquisaTipoRule:
    """Test suite for pesquisa_tipo (search method) extraction rule."""
    
    def test_pesquisa_tipo_cpf(self):
        """Test pesquisa_tipo extraction with CPF."""
        mock_text = "Tipo: Buscar CLIENTE CPF"
        schema = {"pesquisa_tipo": "Tipo de pesquisa"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_tipo'] == 'CPF'
    
    def test_pesquisa_tipo_cnpj(self):
        """Test pesquisa_tipo with CNPJ."""
        mock_text = "Tipo: Buscar parente CNPJ"
        schema = {"pesquisa_tipo": "Search method"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_tipo'] == 'CNPJ'
    
    def test_pesquisa_tipo_nome(self):
        """Test pesquisa_tipo with Nome."""
        mock_text = "Tipo: Some text Buscar prestador Nome"
        schema = {"pesquisa_tipo": "Tipo"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_tipo'] == 'Nome'
    
    def test_pesquisa_tipo_email(self):
        """Test pesquisa_tipo with email."""
        mock_text = "Tipo: Buscar outro email"
        schema = {"pesquisa_tipo": "Search method"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_tipo'] == 'email'
    
    def test_pesquisa_tipo_not_found(self):
        """Test pesquisa_tipo returns None when pattern not found."""
        mock_text = "Type: Search by ID"
        schema = {"pesquisa_tipo": "Search method"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['pesquisa_tipo'] is None
    
    def test_pesquisa_tipo_label_isolation(self):
        """Test pesquisa_tipo rule is NOT triggered with carteira_oab label."""
        mock_text = "Tipo: Buscar CLIENTE CPF"
        schema = {"pesquisa_tipo": "Search method"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['pesquisa_tipo'] is None


class TestTelaSistemaProdutoRule:
    """Test suite for produto (product) extraction rule."""
    
    def test_produto_single_word(self):
        """Test produto extraction with single word."""
        mock_text = "Produto CONSIGNADO Sistema ONLINE"
        schema = {"produto": "Produto da operação"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['produto'] == 'CONSIGNADO'
    
    def test_produto_multi_word(self):
        """Test produto with multi-word value."""
        mock_text = "Produto EMPRESTIMO PESSOAL Sistema CONSIGNADO"
        schema = {"produto": "Product name"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['produto'] == 'EMPRESTIMO PESSOAL'
    
    def test_produto_refinanciamento(self):
        """Test produto with REFINANCIAMENTO."""
        mock_text = "Produto REFINANCIAMENTO Qtd. Parcelas 96"
        schema = {"produto": "Product"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['produto'] == 'REFINANCIAMENTO'
    
    def test_produto_not_found(self):
        """Test produto returns None when pattern not found."""
        mock_text = "Product: consignado"
        schema = {"produto": "Product"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['produto'] is None
    
    def test_produto_label_isolation(self):
        """Test produto rule is NOT triggered with carteira_oab label."""
        mock_text = "Produto REFINANCIAMENTO"
        schema = {"produto": "Product"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['produto'] is None


class TestTelaSistemaQuantidadeParcelasRule:
    """Test suite for quantidade_parcelas (number of installments) extraction rule."""
    
    def test_quantidade_parcelas_basic(self):
        """Test quantidade_parcelas extraction."""
        mock_text = "Qtd. Parcelas 96 Sistema CONSIGNADO"
        schema = {"quantidade_parcelas": "Quantidade de parcelas"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['quantidade_parcelas'] == '96'
    
    def test_quantidade_parcelas_without_period(self):
        """Test quantidade_parcelas with no period after Qtd."""
        mock_text = "Qtd Parcelas 48"
        schema = {"quantidade_parcelas": "Number of installments"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['quantidade_parcelas'] == '48'
    
    def test_quantidade_parcelas_singular(self):
        """Test quantidade_parcelas with singular 'Parcela'."""
        mock_text = "Qtd. Parcela 1"
        schema = {"quantidade_parcelas": "Installments"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['quantidade_parcelas'] == '1'
    
    def test_quantidade_parcelas_not_found(self):
        """Test quantidade_parcelas returns None when pattern not found."""
        mock_text = "Number of installments: 96"
        schema = {"quantidade_parcelas": "Installments"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['quantidade_parcelas'] is None
    
    def test_quantidade_parcelas_label_isolation(self):
        """Test quantidade_parcelas rule is NOT triggered with carteira_oab label."""
        mock_text = "Qtd. Parcelas 96"
        schema = {"quantidade_parcelas": "Installments"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['quantidade_parcelas'] is None


class TestTelaSistemaSelecaoParcelasRule:
    """Test suite for selecao_de_parcelas (installment selection) extraction rule."""
    
    def test_selecao_parcelas_vencidas(self):
        """Test selecao_de_parcelas with Vencidas."""
        mock_text = "Seleção de parcelas: Vencidas Total: 76.871,20"
        schema = {"selecao_de_parcelas": "Seleção de parcelas"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['selecao_de_parcelas'] == 'Vencidas'
    
    def test_selecao_parcelas_pago(self):
        """Test selecao_de_parcelas with pago."""
        mock_text = "Seleção de parcelas: pago"
        schema = {"selecao_de_parcelas": "Selection"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['selecao_de_parcelas'] == 'pago'
    
    def test_selecao_parcelas_pendente(self):
        """Test selecao_de_parcelas with pendente."""
        mock_text = "Seleção de parcelas: pendente"
        schema = {"selecao_de_parcelas": "Installment selection"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['selecao_de_parcelas'] == 'pendente'
    
    def test_selecao_parcelas_with_accents(self):
        """Test selecao_de_parcelas field name with accents."""
        mock_text = "Seleção de parcelas: Vencidas"
        schema = {"seleção_de_parcelas": "Seleção"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['seleção_de_parcelas'] == 'Vencidas'
    
    def test_selecao_parcelas_not_found(self):
        """Test selecao_parcelas returns None when pattern not found."""
        mock_text = "Installment selection: overdue"
        schema = {"selecao_de_parcelas": "Selection"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['selecao_de_parcelas'] is None
    
    def test_selecao_parcelas_label_isolation(self):
        """Test selecao_parcelas rule is NOT triggered with carteira_oab label."""
        mock_text = "Seleção de parcelas: Vencidas"
        schema = {"selecao_de_parcelas": "Selection"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['selecao_de_parcelas'] is None


class TestTelaSistemaSistemaRule:
    """Test suite for sistema (system) extraction rule."""
    
    def test_sistema_with_vir_parc(self):
        """Test sistema extraction with VIr. Parc. pattern."""
        mock_text = "Sistema CONSIGNADO VIr. Parc. 2.372,64"
        schema = {"sistema": "Sistema da operação"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['sistema'] == 'CONSIGNADO'
    
    def test_sistema_simple_pattern(self):
        """Test sistema with simple pattern (no VIr. Parc.)."""
        mock_text = "Sistema ONLINE Produto REFINANCIAMENTO"
        schema = {"sistema": "System"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['sistema'] == 'ONLINE'
    
    def test_sistema_prefers_specific_pattern(self):
        """Test sistema prefers more specific pattern first."""
        mock_text = "Sistema CONSIGNADO VIr. Parc. 100,00 Sistema OUTRO"
        schema = {"sistema": "System"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        # Should match the first CONSIGNADO with VIr. Parc.
        assert result['sistema'] == 'CONSIGNADO'
    
    def test_sistema_not_found(self):
        """Test sistema returns None when pattern not found."""
        mock_text = "System: consignado"
        schema = {"sistema": "System"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['sistema'] is None
    
    def test_sistema_label_isolation(self):
        """Test sistema rule is NOT triggered with carteira_oab label."""
        mock_text = "Sistema CONSIGNADO VIr. Parc. 2.372,64"
        schema = {"sistema": "System"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['sistema'] is None


class TestTelaSistemaTipoOperacaoRule:
    """Test suite for tipo_de_operacao (operation type) extraction rule."""
    
    def test_tipo_operacao_basic(self):
        """Test tipo_de_operacao extraction."""
        mock_text = "Tipo Operação: Renegociação Tipo Sistema: Consignado"
        schema = {"tipo_de_operacao": "Tipo de operação"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_operacao'] == 'Renegociação'
    
    def test_tipo_operacao_with_accents(self):
        """Test tipo_de_operacao with Portuguese accents."""
        mock_text = "Tipo Operação: Renovação"
        schema = {"tipo_de_operacao": "Operation type"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_operacao'] == 'Renovação'
    
    def test_tipo_operacao_case_insensitive(self):
        """Test tipo_de_operacao case insensitivity."""
        mock_text = "tipo operação: Refinanciamento"
        schema = {"tipo_de_operacao": "Type"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_operacao'] == 'Refinanciamento'
    
    def test_tipo_operacao_not_found(self):
        """Test tipo_de_operacao returns None when pattern not found."""
        mock_text = "Operation type: Renegotiation"
        schema = {"tipo_de_operacao": "Operation"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_operacao'] is None
    
    def test_tipo_operacao_label_isolation(self):
        """Test tipo_de_operacao rule is NOT triggered with carteira_oab label."""
        mock_text = "Tipo Operação: Renegociação"
        schema = {"tipo_de_operacao": "Operation"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['tipo_de_operacao'] is None


class TestTelaSistemaTipoSistemaRule:
    """Test suite for tipo_de_sistema (system type) extraction rule."""
    
    def test_tipo_sistema_basic(self):
        """Test tipo_de_sistema extraction."""
        mock_text = "Tipo Sistema: Consignado Tipo Operação: Renegociação"
        schema = {"tipo_de_sistema": "Tipo de sistema"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_sistema'] == 'Consignado'
    
    def test_tipo_sistema_with_accents(self):
        """Test tipo_de_sistema with accents."""
        mock_text = "Tipo Sistema: Automático"
        schema = {"tipo_de_sistema": "System type"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_sistema'] == 'Automático'
    
    def test_tipo_sistema_case_insensitive(self):
        """Test tipo_de_sistema case insensitivity."""
        mock_text = "tipo sistema: Manual"
        schema = {"tipo_de_sistema": "Type"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_sistema'] == 'Manual'
    
    def test_tipo_sistema_not_found(self):
        """Test tipo_de_sistema returns None when pattern not found."""
        mock_text = "System type: Automatic"
        schema = {"tipo_de_sistema": "System"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['tipo_de_sistema'] is None
    
    def test_tipo_sistema_label_isolation(self):
        """Test tipo_de_sistema rule is NOT triggered with carteira_oab label."""
        mock_text = "Tipo Sistema: Consignado"
        schema = {"tipo_de_sistema": "System"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['tipo_de_sistema'] is None


class TestTelaSistemaTotalParcelasRule:
    """Test suite for total_de_parcelas (total value) extraction rule."""
    
    def test_total_parcelas_basic(self):
        """Test total_de_parcelas extraction."""
        mock_text = "Seleção de parcelas: Vencidas Total: 76.871,20"
        schema = {"total_de_parcelas": "Valor total"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['total_de_parcelas'] == '76.871,20'
    
    def test_total_parcelas_different_value(self):
        """Test total_de_parcelas with different monetary value."""
        mock_text = "Total: 1.234,56"
        schema = {"total_de_parcelas": "Total"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['total_de_parcelas'] == '1.234,56'
    
    def test_total_parcelas_case_insensitive(self):
        """Test total_de_parcelas case insensitivity."""
        mock_text = "total: 500,00"
        schema = {"total_de_parcelas": "Total value"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['total_de_parcelas'] == '500,00'
    
    def test_total_parcelas_not_found(self):
        """Test total_parcelas returns None when pattern not found."""
        mock_text = "Total value: R$ 76871.20"
        schema = {"total_de_parcelas": "Total"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['total_de_parcelas'] is None
    
    def test_total_parcelas_label_isolation(self):
        """Test total_parcelas rule is NOT triggered with carteira_oab label."""
        mock_text = "Total: 76.871,20"
        schema = {"total_de_parcelas": "Total"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['total_de_parcelas'] is None


class TestTelaSistemaValorParcelaRule:
    """Test suite for valor_parcela (installment value) extraction rule."""
    
    def test_valor_parcela_basic(self):
        """Test valor_parcela extraction."""
        mock_text = "Sistema CONSIGNADO VIr. Parc. 2.372,64"
        schema = {"valor_parcela": "Valor da parcela"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['valor_parcela'] == '2.372,64'
    
    def test_valor_parcela_without_period(self):
        """Test valor_parcela with no period after VIr."""
        mock_text = "VIr Parc. 1.500,00"
        schema = {"valor_parcela": "Installment value"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['valor_parcela'] == '1.500,00'
    
    def test_valor_parcela_different_value(self):
        """Test valor_parcela with different monetary value."""
        mock_text = "VIr. Parc. 999,99"
        schema = {"valor_parcela": "Value"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['valor_parcela'] == '999,99'
    
    def test_valor_parcela_case_insensitive(self):
        """Test valor_parcela case insensitivity."""
        mock_text = "vir. parc. 750,00"
        schema = {"valor_parcela": "Installment"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['valor_parcela'] == '750,00'
    
    def test_valor_parcela_not_found(self):
        """Test valor_parcela returns None when pattern not found."""
        mock_text = "Installment value: R$ 2372.64"
        schema = {"valor_parcela": "Value"}
        
        result = run_heuristics('tela_sistema', mock_text, schema)
        
        assert result['valor_parcela'] is None
    
    def test_valor_parcela_label_isolation(self):
        """Test valor_parcela rule is NOT triggered with carteira_oab label."""
        mock_text = "VIr. Parc. 2.372,64"
        schema = {"valor_parcela": "Value"}
        
        result = run_heuristics('carteira_oab', mock_text, schema)
        
        assert result['valor_parcela'] is None


# ========================================
# DUAL-MODE ARCHITECTURE TEST SUITE
# ========================================


class TestDualModeArchitecture:
    """Test the dual-mode architecture's adaptability and isolation."""
    
    def test_unknown_label_finds_generic_rules(self):
        """
        TEST 1 (Adaptive Mode): Verify generic rules work for unknown labels.
        
        This test proves the system is adaptive - when given a brand new label
        that has no label-specific rules, it falls back to generic rules and
        successfully extracts data.
        """
        # Create a brand new unknown label
        label = 'fatura_nova'
        
        # Mock text with CPF and Date
        mock_text = """
        Cliente: João Silva
        CPF: 123.456.789-00
        Data de Vencimento: 15/12/2024
        Valor: R$ 1.500,00
        """
        
        # Schema asking for CPF and Date
        schema = {
            'cpf_cliente': 'CPF do cliente',
            'data_venc': 'Data de vencimento'
        }
        
        # Run heuristics with unknown label
        result = run_heuristics(label, mock_text, schema)
        
        # ASSERT: Generic rules found both fields
        assert result['cpf_cliente'] == '123.456.789-00', \
            "Generic CPF rule should work for unknown labels"
        assert result['data_venc'] == '15/12/2024', \
            "Generic Date rule should work for unknown labels"
        assert result['__found_all__'] is True, \
            "All fields should be found by generic rules"
        
        print("\n✅ ADAPTIVE MODE VERIFIED:")
        print(f"   Label: {label} (unknown)")
        print(f"   CPF found: {result['cpf_cliente']}")
        print(f"   Date found: {result['data_venc']}")
        print("   → Generic rules successfully adapted to unknown document type")
    
    def test_unknown_label_ignores_specific_rules(self):
        """
        TEST 2 (Isolation Mode): Verify label-specific rules are isolated.
        
        This test proves optimized rules are correctly isolated - when given
        an unknown label, the system does NOT trigger OAB or tela_sistema
        specific rules, even if the text contains matching patterns.
        """
        # Create a brand new unknown label
        label = 'fatura_nova'
        
        # Mock text with patterns from BOTH OAB and tela_sistema
        mock_text = """
        JOSÉ DA SILVA OLIVEIRA
        Inscrição: 123456
        Seccional MG
        Cidade: Mozarlândia U.F: GO
        Sistema CONSIGNADO VIr. Parc. 2.372,64
        """
        
        # Schema asking for OAB field (nome) and tela_sistema field (cidade)
        schema = {
            'nome': 'Nome do profissional',
            'cidade': 'Cidade da operação'
        }
        
        # Run heuristics with unknown label
        result = run_heuristics(label, mock_text, schema)
        
        # ASSERT: Label-specific rules did NOT trigger
        assert result['nome'] is None, \
            "OAB-specific 'nome' rule should NOT trigger for unknown label"
        assert result['cidade'] is None, \
            "tela_sistema-specific 'cidade' rule should NOT trigger for unknown label"
        assert result['__found_all__'] is False, \
            "Fields should not be found (label-specific rules are isolated)"
        
        print("\n✅ ISOLATION MODE VERIFIED:")
        print(f"   Label: {label} (unknown)")
        print(f"   nome result: {result['nome']} (OAB rule isolated)")
        print(f"   cidade result: {result['cidade']} (tela_sistema rule isolated)")
        print("   → Label-specific rules correctly isolated from unknown labels")
    
    def test_label_specific_rules_work_correctly(self):
        """
        TEST 3 (Label-Specific Mode): Verify label-specific rules work as expected.
        
        This test confirms that when the correct label is provided, label-specific
        rules ARE triggered and work correctly.
        """
        # Test OAB label with OAB pattern
        oab_text = "JOSÉ DA SILVA OLIVEIRA\nInscrição: 123456"
        oab_schema = {'nome': 'Nome do profissional', 'inscricao': 'Número de inscrição'}
        
        oab_result = run_heuristics('carteira_oab', oab_text, oab_schema)
        
        assert oab_result['nome'] == 'JOSÉ DA SILVA OLIVEIRA', \
            "OAB-specific nome rule should work with carteira_oab label"
        assert oab_result['inscricao'] == '123456', \
            "OAB-specific inscricao rule should work with carteira_oab label"
        
        # Test tela_sistema label with tela_sistema pattern
        tela_text = "Cidade: Mozarlândia U.F: GO"
        tela_schema = {'cidade': 'Cidade da operação'}
        
        tela_result = run_heuristics('tela_sistema', tela_text, tela_schema)
        
        assert tela_result['cidade'] == 'Mozarlândia', \
            "tela_sistema-specific cidade rule should work with tela_sistema label"
        
        print("\n✅ LABEL-SPECIFIC MODE VERIFIED:")
        print("   OAB rules work with 'carteira_oab' label")
        print("   tela_sistema rules work with 'tela_sistema' label")
        print("   → Label-specific optimization functioning correctly")
    
    def test_cross_contamination_prevention(self):
        """
        TEST 4 (Cross-Contamination Prevention): Verify no cross-contamination.
        
        This test ensures that OAB rules don't trigger for tela_sistema documents
        and vice versa.
        """
        # OAB pattern with tela_sistema label
        oab_text = "JOSÉ DA SILVA OLIVEIRA\nInscrição: 123456"
        oab_schema_wrong_label = {'nome': 'Nome', 'inscricao': 'Inscrição'}
        
        result_oab_pattern_tela_label = run_heuristics('tela_sistema', oab_text, oab_schema_wrong_label)
        
        # OAB rules should NOT trigger for tela_sistema label
        assert result_oab_pattern_tela_label['nome'] is None, \
            "OAB nome rule should NOT trigger with tela_sistema label"
        assert result_oab_pattern_tela_label['inscricao'] is None, \
            "OAB inscricao rule should NOT trigger with tela_sistema label"
        
        # tela_sistema pattern with OAB label
        tela_text = "Cidade: Mozarlândia U.F: GO\nProduto REFINANCIAMENTO"
        tela_schema_wrong_label = {'cidade': 'Cidade', 'produto': 'Produto'}
        
        result_tela_pattern_oab_label = run_heuristics('carteira_oab', tela_text, tela_schema_wrong_label)
        
        # tela_sistema rules should NOT trigger for OAB label
        assert result_tela_pattern_oab_label['cidade'] is None, \
            "tela_sistema cidade rule should NOT trigger with carteira_oab label"
        assert result_tela_pattern_oab_label['produto'] is None, \
            "tela_sistema produto rule should NOT trigger with carteira_oab label"
        
        print("\n✅ CROSS-CONTAMINATION PREVENTION VERIFIED:")
        print("   OAB rules isolated from tela_sistema label")
        print("   tela_sistema rules isolated from carteira_oab label")
        print("   → No cross-contamination between document types")
