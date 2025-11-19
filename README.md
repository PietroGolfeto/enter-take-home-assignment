# SmartDocExtractor: Hybrid PDF Data Extraction

A production-ready, cost-optimized PDF data extraction system that combines rule-based heuristics with LLM fallback to achieve **81.1% cost savings** while maintaining 100% extraction accuracy.

## Key Features

- **Hybrid Architecture**: Combines fast, free regex heuristics with powerful LLM fallback.
- **Cost Efficient**: **81.1%** of fields extracted using zero-cost heuristics.
- **100% Accuracy**: LLM safety net ensures no data is left behind.
- **Modular Design**: Built with SOLID principles for easy extensibility.
- **Zero Dependencies**: Core extraction logic relies on standard libraries where possible.

## Performance Metrics

The system was benchmarked against a diverse dataset of documents (ID cards, system screenshots):

```
OVERALL STATISTICS:
────────────────────────────────────────────────
Total Files Processed:        6
Total Fields in Schemas:      37

Fields Found by Heuristics:   30/37 (81.1%)
Fields Requiring LLM:         7/37 (18.9%)
Total Fields Extracted:       37/37 (100.0%)

COST SAVINGS ANALYSIS:
────────────────────────────────────────────────
Heuristics Efficiency:    81.1% of fields extracted without LLM
LLM Usage Reduction:      5.3x fewer LLM calls vs. pure LLM approach
```

## Architecture

The system uses a 3-level extraction strategy to optimize for both speed and cost:

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Entry Point                         │
│                     (extract.py)                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orchestration Layer                         │
│              (3-Level Extraction Strategy)                  │
└─┬───────────────────┬───────────────────┬───────────────────┘
  │                   │                   │
  ▼                   ▼                   ▼
┌─────────┐    ┌──────────────┐   ┌────────────────┐
│ Level 1 │    │   Level 2    │   │    Level 3     │
│ Cache   │───▶│ Heuristics   │──▶│  LLM Fallback  │
│ Check   │    │ (81.1% hit)  │   │  (18.9% used)  │
└─────────┘    └──────────────┘   └────────────────┘
```

1. **Level 1 - Cache Check** (Instant, Free): SHA-256 content-based caching.
2. **Level 2 - Heuristics** (Fast, Free): Specialized regex rules for known document types.
3. **Level 3 - LLM Fallback** (Accurate, Paid): GPT-5-mini for complex or unstructured data.

## Project Structure

```
smart-doc-extractor/
│
├── src/                                    # Core application code
│   ├── __init__.py
│   ├── config.py                          # Configuration
│   ├── pdf_parser.py                      # PDF text extraction
│   ├── cache_manager.py                   # Hashing & caching logic
│   ├── llm_client.py                      # OpenAI API client
│   ├── orchestration.py                   # Main workflow
│   │
│   ├── heuristics/                        # Rule-based extraction
│   │   ├── registry.py
│   │   ├── generic.py
│   │   └── ...
│   │
│   └── utils/                             # Shared utilities
│
├── tests/                                 # Comprehensive test suite (226 tests)
├── files/                                 # Demo PDF files
├── dataset.json                           # Demo dataset configuration
├── extract.py                             # CLI entry point
└── run_final_analysis.py                  # Statistics & analysis tool
```

## Design Decisions

### 1. Modular Architecture (SOLID)
Refactored from a monolithic script into 14 specialized modules. This ensures single responsibility, easier testing, and scalability.

### 2. Dual-Mode Heuristics
Implemented both label-specific rules (e.g., for specific ID cards) and generic fallback rules (e.g., finding dates or CPFs anywhere). This allows the system to be both highly optimized for known types and adaptable to unknown ones.

### 3. Robust Caching
Uses `SHA-256(PDF_content):SHA-256(schema_json)` as the cache key. This guarantees that any change to the file or the requested data schema invalidates the cache, preventing stale data issues.

## Getting Started

### Prerequisites

- Python 3.8+
- OpenAI API key (for LLM fallback)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PietroGolfeto/smart-doc-extractor.git
   cd smart-doc-extractor
   ```

2. **Install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up Environment:**
   Create a `.env` file:
   ```env
   OPENAI_API_KEY=your-api-key-here
   ```

### Usage

**Extract data from a single PDF:**

```bash
python extract.py "carteira_oab" \
  '{"nome": "Nome do profissional", "inscricao": "Número de inscrição"}' \
  "files/oab_1.pdf"
```

**Run the analysis suite:**

```bash
python run_final_analysis.py
```

## Testing

The project includes a comprehensive test suite with **226 tests** covering unit, integration, and end-to-end scenarios.

```bash
pytest tests/ -v
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Project based on Enter's AI Fellowship technical challenge: https://github.com/talismanai/ai-fellowship-data
