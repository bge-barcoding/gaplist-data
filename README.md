# Gap List Data Repository

<img src="doc/IBOL_LOGO_TRANSPARENT.png" style="width: 200px; display: inline-block; margin-right: 20px;" alt="IBOL Europe Logo"> <img src="doc/Logo BGE.png" style="width: 200px; display: inline-block;" alt="BGE Logo">

This repository contains species data files and an advanced data cleaning pipeline for processing taxonomic information and synonyms.

## Overview

The repository provides a comprehensive system for cleaning and normalizing species data across two primary datasets:
- **Species and Synonyms**: Valid species names with their synonyms
- **Species and Taxonomy**: Species with taxonomic classifications

## Data Files

### Input Data (`/data/`)
- [`all_specs_and_syn.csv`](data/all_specs_and_syn.csv) - Species and their synonyms
- [`Gap_list_all_updated.csv`](data/Gap_list_all_updated.csv) - Species with taxonomic hierarchy
- [`targetlist.csv`](data/targetlist.csv) - Additional target species list

### Processed Data (`/cleaned_data/`)
- Cleaned and normalized versions of input files
- Removed records for audit trail
- Generated with mode-specific suffixes (e.g., `_hybrid`, `_majority_rule`)

## Data Cleaning Pipeline

### SMART Enhanced Pipeline (`/data_cleaning_pipeline/`)

The **SMART Enhanced Data Cleaning Pipeline** provides intelligent taxonomy normalization with 95%+ reduction in API calls.

#### Main Script
- [`smart_pipeline.py`](data_cleaning_pipeline/smart_pipeline.py) - Enhanced pipeline with SMART taxonomy normalization

#### Key Features
- **Three Processing Modes**: Majority rule, GBIF validation, and hybrid approach
- **Intelligent GBIF Usage**: Only queries species with actual taxonomy conflicts
- **Comprehensive Cleaning**: Unicode handling, gender variant merging, duplicate resolution
- **Complete Audit Trail**: Detailed logging of all modifications

#### Quick Start
```bash
# Default hybrid mode (recommended)
python data_cleaning_pipeline/smart_pipeline.py

# Fast processing with majority rule
python data_cleaning_pipeline/smart_pipeline.py --mode majority_rule

# External validation (SMART optimized)
python data_cleaning_pipeline/smart_pipeline.py --mode gbif_only
```

#### Documentation
- [Complete Pipeline Documentation](data_cleaning_pipeline/README.md)
- Processing phases, examples, and troubleshooting

### Core Pipeline Components
- [`data_cleaning_pipeline.py`](data_cleaning_pipeline/data_cleaning_pipeline.py) - Base cleaning functionality
- [`taxonomy_normalization/`](data_cleaning_pipeline/taxonomy_normalization/) - SMART taxonomy processing modules

## Processing Results (`/log/`)
- Detailed modification logs (TSV format)
- Summary reports (Markdown format)
- Taxonomy normalization reports (JSON format)

## Usage

### Command Line
```bash
# Process with default settings
python data_cleaning_pipeline/smart_pipeline.py

# Custom confidence threshold
python data_cleaning_pipeline/smart_pipeline.py --mode hybrid --confidence 0.9
```

### Programmatic
```python
from data_cleaning_pipeline.smart_pipeline import SmartSpeciesDataCleaner

cleaner = SmartSpeciesDataCleaner(".", taxonomy_mode="hybrid")
cleaner.run_pipeline()
```

## Output Files

The pipeline generates:
- **Cleaned CSV files** with normalized taxonomy and merged synonyms
- **Removed records** for audit and review
- **Comprehensive logs** with all modifications tracked
- **Summary reports** with processing statistics and SMART efficiency metrics

## Support

- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/bge-barcoding/gaplist-data/issues)
- **Documentation**: See the [Pipeline Documentation](data_cleaning_pipeline/README.md)
- **BGE Consortium**: Visit [biodiversitygenomics.eu](https://biodiversitygenomics.eu) for project updates

---

## Acknowledgments

This work is supported by the Biodiversity Genomics Europe (BGE) consortium and contributes to the International Barcode of Life (IBOL) initiative. Biodiversity Genomics Europe (Grant no.101059492) is funded by Horizon Europe under the Biodiversity, Circular Economy and Environment call (REA.B.3); co-funded by the Swiss State Secretariat for Education, Research and Innovation (SERI) under contract numbers 22.00173 and 24.00054; and by the UK Research and Innovation (UKRI) under the Department for Business, Energy and Industrial Strategy’s Horizon Europe Guarantee Scheme.
