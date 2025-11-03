#!/usr/bin/env python3
"""
Final Analysis Script

Executes extraction on all 6 PDF files from dataset.json and provides comprehensive
statistics on heuristics vs LLM coverage.
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from src.orchestration import extract_data_from_pdf
from src.cache_manager import GLOBAL_CACHE, get_pdf_hash_cached
from src.pdf_parser import extract_text_from_pdf_cached
from src.utils.logging_config import setup_logging


def load_dataset() -> List[Dict]:
    """Load the dataset.json file."""
    with open('dataset.json', 'r', encoding='utf-8') as f:
        return json.load(f)


def run_analysis():
    """Run extraction on all files and collect statistics."""
    # Setup logging (quiet mode)
    setup_logging(verbose=False)

    # Suppress INFO/DEBUG logs from imported modules by setting level to WARNING
    logging.getLogger().setLevel(logging.WARNING)    
    
    # Clear all caches to ensure fresh analysis
    GLOBAL_CACHE.clear()
    get_pdf_hash_cached.cache_clear()
    extract_text_from_pdf_cached.cache_clear()
    
    print("=" * 80)
    print("PDF DATA EXTRACTION - FINAL ANALYSIS")
    print("=" * 80)
    print()
    
    # Load dataset
    dataset = load_dataset()
    
    # Statistics accumulators
    total_files = len(dataset)
    total_fields = 0
    total_heuristics_fields = 0
    total_llm_fields = 0
    
    results = []
    
    # Process each file
    for idx, entry in enumerate(dataset, 1):
        label = entry['label']
        schema = entry['extraction_schema']
        pdf_path = f"files/{entry['pdf_path']}"
        
        print(f"[{idx}/{total_files}] Processing: {pdf_path}")
        print(f"    (Label: {label}, Fields: {len(schema)})")
        
        try:
            # Run extraction
            final_result, metadata = extract_data_from_pdf(
                label=label,
                schema_dict=schema,
                pdf_path=pdf_path
            )
            
            # Analyze results
            num_fields = len(schema)
            heuristics_fields = len(metadata.get('found_by_heuristics', []))
            llm_fields = len(metadata.get('found_by_llm', []))
            
            # Handle case where all found by heuristics
            if metadata.get('heuristics_used') and not metadata.get('llm_used'):
                heuristics_fields = num_fields
                llm_fields = 0
            
            # Count non-null fields in final result
            found_fields = sum(1 for v in final_result.values() if v is not None)
            missing_fields = num_fields - found_fields
            
            # Update totals
            total_fields += num_fields
            total_heuristics_fields += heuristics_fields
            total_llm_fields += llm_fields
            
            # Store result
            results.append({
                'file': entry['pdf_path'],
                'label': label,
                'total_fields': num_fields,
                'heuristics': heuristics_fields,
                'llm': llm_fields,
                'found': found_fields,
                'missing': missing_fields,
                'coverage': (found_fields / num_fields * 100) if num_fields > 0 else 0,
                'heuristics_coverage': (heuristics_fields / num_fields * 100) if num_fields > 0 else 0
            })
            
            print(f"    ✓ {'Heuristics:':<13} {heuristics_fields}/{num_fields} fields ({heuristics_fields/num_fields*100:.1f}%)")
            if llm_fields > 0:
                print(f"    ✓ {'LLM:':<13} {llm_fields}/{num_fields} fields ({llm_fields/num_fields*100:.1f}%)")
            print(f"    ✓ {'Total Found:':<13} {found_fields}/{num_fields} fields ({found_fields/num_fields*100:.1f}%)")
            if missing_fields > 0:
                print(f"    ✗ {'Missing:':<13} {missing_fields} field(s)")
            print()
            
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            print()
            results.append({
                'file': entry['pdf_path'],
                'label': label,
                'total_fields': len(schema),
                'heuristics': 0,
                'llm': 0,
                'found': 0,
                'missing': len(schema),
                'coverage': 0,
                'heuristics_coverage': 0,
                'error': str(e)
            })
    
    # Print summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()
    
    # Per-file breakdown
    print("PER-FILE BREAKDOWN:")
    print("-" * 80)
    print(f"{'File':<25} {'Label':<15} {'Fields':<8} {'Heuristics':<18} {'LLM':<8} {'Coverage (not counting missing)'}")
    print("-" * 80)

    for r in results:
        file_short = r['file'].replace('tela_sistema_', 'sistema_')
        heur_pct = r['heuristics_coverage']
        cov_pct = r['coverage']
        
        # Build the heuristic string first
        heur_string = f"{r['heuristics']}/{r['total_fields']} ({heur_pct:>5.1f}%)"
        
        # Apply the left-alignment to the heur_string variable
        print(f"{file_short:<25} {r['label']:<15} {r['total_fields']:<8} "
              f"{heur_string:<18} "  # <-- This is the fix
              f"{r['llm']:<8} {cov_pct:>5.1f}%")    
    
    print("-" * 80)
    print()
    
    # Overall statistics
    overall_coverage = (total_heuristics_fields + total_llm_fields) / total_fields * 100 if total_fields > 0 else 0
    heuristics_coverage = total_heuristics_fields / total_fields * 100 if total_fields > 0 else 0

    print("OVERALL STATISTICS:")
    print("-" * 80)
    
    # Use 29-char padding for alignment
    print(f"{'Total Files Processed:':<29} {total_files}")
    print(f"{'Total Fields in Schemas:':<29} {total_fields}")
    print()
    
    # Calculate percentages for alignment (using >5.1f for 100.0)
    heur_pct = heuristics_coverage
    llm_pct = (total_llm_fields/total_fields*100) if total_fields > 0 else 0
    total_pct = overall_coverage

    print(f"{'Fields Found by Heuristics:':<29} {total_heuristics_fields}/{total_fields} ({heur_pct:>5.1f}%)")
    print(f"{'Fields Requiring LLM:':<29} {total_llm_fields}/{total_fields} ({llm_pct:>5.1f}%)")
    print(f"{'Total Fields Extracted:':<29} {total_heuristics_fields + total_llm_fields}/{total_fields} ({total_pct:>5.1f}%)")
    print()
    
    # Cost savings analysis
    if total_llm_fields > 0:
        savings_pct = (total_heuristics_fields / (total_heuristics_fields + total_llm_fields)) * 100
        reduction_factor = total_fields / total_llm_fields if total_llm_fields > 0 else float('inf')
   
        print("COST SAVINGS ANALYSIS:")
        print("-" * 80)
        
        # Use 25-char padding for alignment
        print(f"{'Heuristics Efficiency:':<25} {savings_pct:.1f}% of fields extracted without LLM")
        print(f"{'LLM Usage Reduction:':<25} {reduction_factor:.1f}x fewer LLM calls vs. a pure LLM approach")
        print(f"{'API Calls Saved:':<25} ~{total_heuristics_fields} field extractions avoided")
        print()
    
    # Document type breakdown
    print("BREAKDOWN BY DOCUMENT TYPE:")
    print("-" * 80)
    
    # OAB statistics
    oab_results = [r for r in results if r['label'] == 'carteira_oab']
    if oab_results:
        oab_fields = sum(r['total_fields'] for r in oab_results)
        oab_heur = sum(r['heuristics'] for r in oab_results)
        oab_llm = sum(r['llm'] for r in oab_results)
        oab_cov = (oab_heur / oab_fields * 100) if oab_fields > 0 else 0
        print(f"OAB Documents (carteira_oab):")
        # Use 14-char padding for alignment
        print(f"  {'Files:':<14} {len(oab_results)}")
        print(f"  {'Total Fields:':<14} {oab_fields}")
        print(f"  {'Heuristics:':<14} {oab_heur}/{oab_fields} ({oab_cov:>5.1f}%)")
        print(f"  {'LLM:':<14} {oab_llm}/{oab_fields} ({oab_llm/oab_fields*100:>5.1f}%)")
        print()
    
    # Sistema statistics
    sistema_results = [r for r in results if r['label'] == 'tela_sistema']
    if sistema_results:
        sistema_fields = sum(r['total_fields'] for r in sistema_results)
        sistema_heur = sum(r['heuristics'] for r in sistema_results)
        sistema_llm = sum(r['llm'] for r in sistema_results)
        sistema_cov = (sistema_heur / sistema_fields * 100) if sistema_fields > 0 else 0
        print(f"Sistema Documents (tela_sistema):")
        # Use 14-char padding for alignment
        print(f"  {'Files:':<14} {len(sistema_results)}")
        print(f"  {'Total Fields:':<14} {sistema_fields}")
        print(f"  {'Heuristics:':<14} {sistema_heur}/{sistema_fields} ({sistema_cov:>5.1f}%)")
        print(f"  {'LLM:':<14} {sistema_llm}/{sistema_fields} ({sistema_llm/sistema_fields*100:>5.1f}%)")
        print()
    
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    return results


if __name__ == '__main__':
    try:
        run_analysis()
    except Exception as e:
        print(f"ERROR: Analysis failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
