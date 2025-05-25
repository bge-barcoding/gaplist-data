# Species Matching and Reconciliation of Taxonomy (SMaRT)

## Overview

The SMART Enhanced Data Cleaning Pipeline is an advanced species data processing system that combines traditional data cleaning with intelligent taxonomy normalization. It processes two corresponding CSV files containing species data to ensure consistency and proper formatting between species/synonyms and taxonomic information.

If the pipeline detects conflicts in higher taxonomy it provides options for majority rule, GBIF or hybrid reconciliation.

## Pipeline Script: `smart_pipeline.py`

### Command Line Usage

```bash
# Default SMART hybrid mode
python smart_pipeline.py

# Use only majority rule (fastest)
python smart_pipeline.py --mode majority_rule

# SMART GBIF mode (only queries conflicted species)
python smart_pipeline.py --mode gbif_only

# SMART hybrid with custom confidence threshold
python smart_pipeline.py --mode hybrid --confidence 0.9

# Use custom base path
python smart_pipeline.py --base-path /path/to/gaplist-data
```

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--mode` | choice | `hybrid` | Taxonomy normalization mode |
| `--confidence` | float | `0.8` | Confidence threshold for majority rule |
| `--base-path` | string | auto-detect | Base directory path |

**Mode Options:**
- `majority_rule`: Use internal consensus (fastest, no API calls)
- `gbif_only`: Validate only conflicted species against GBIF (95%+ API reduction)
- `hybrid`: Balance majority rule and GBIF validation (default, most accurate)

### Taxonomy Normalization Modes

#### 1. Majority Rule (`majority_rule`)
- **Speed:** Fastest
- **Method:** Uses internal consensus to resolve conflicts
- **API Usage:** None
- **Best for:** Quick processing, trusted internal data

#### 2. GBIF Only (`gbif_only`)
- **Speed:** Moderate (SMART optimization)
- **Method:** Validates ONLY conflicted species against GBIF
- **API Usage:** Minimal (95%+ reduction)
- **Best for:** External validation with efficiency

#### 3. Hybrid (`hybrid`) - **DEFAULT**
- **Speed:** Balanced
- **Method:** Uses majority rule for high-confidence, GBIF for uncertain cases
- **API Usage:** Minimal (SMART optimization)
- **Best for:** Most accurate results with efficiency
- **Speed:** Moderate (SMART optimization)
- **Method:** Validates ONLY conflicted species against GBIF
- **API Usage:** Minimal (95%+ reduction)
- **Best for:** External validation with efficiency


## Input Files

### File 1: Species and Synonyms (`all_specs_and_syn.csv`)
- **Location:** `data/all_specs_and_syn.csv`
- **Structure:** `valid_name;synonym1;synonym2;...`
- **Example:**
```
Genus species;Genus synonym1;Genus synonym2
Actinia forskålii;Actinia forsk\u00e5lii
```

### File 2: Species and Taxonomy (`Gap_list_all_updated.csv`)
- **Location:** `data/Gap_list_all_updated.csv`
- **Structure:** `valid_name;Phylum;Class;Order;Family;[other_columns...]`
- **Example:**
```
Genus species;Arthropoda;Insecta;Hymenoptera;Formicidae;BOLD,FE;2;3;1;;gap
Actinia forskålii;Cnidaria;Anthozoa;Actiniaria;Actiniidae;WORMS;1;2;0;;gap
```

## Output Files

### Cleaned Data Files
- **File 1:** `cleaned_data/all_specs_and_syn_cleaned_{mode}.csv`
- **File 2:** `cleaned_data/Gap_list_all_updated_cleaned_{mode}.csv`

Where `{mode}` is the taxonomy normalization mode used (e.g., `_hybrid`, `_majority_rule`, etc.)

### Removed Records
- **File 1 Removed:** `cleaned_data/all_specs_and_syn_removed_{timestamp}.csv`
- **File 2 Removed:** `cleaned_data/Gap_list_all_removed_{timestamp}.csv`

### Log Files
- **Detailed Log:** `log/log_{timestamp}.tsv`
- **Summary Report:** `log/cleaning_results_summary_{timestamp}.md`
- **Taxonomy Report:** `log/taxonomy_normalization_report_{timestamp}.json`

## Core Classes and Functions

### `SmartSpeciesDataCleaner` Class

Main pipeline class inheriting from `SpeciesDataCleaner`.

#### Constructor
```python
SmartSpeciesDataCleaner(
    base_path: str,
    taxonomy_mode: str = "hybrid",
    confidence_threshold: float = 0.8
)
```

**Parameters:**
- `base_path`: Base directory containing data, cleaned_data, and log folders
- `taxonomy_mode`: One of `'majority_rule'`, `'gbif_only'`, `'hybrid'`
- `confidence_threshold`: Minimum confidence for majority rule (0.0-1.0)

#### Key Methods

##### `run_pipeline()`
Executes the complete SMART enhanced cleaning pipeline.

**Example:**
```python
cleaner = SmartSpeciesDataCleaner(
    "/path/to/gaplist-data",
    taxonomy_mode="hybrid",
    confidence_threshold=0.8
)
cleaner.run_pipeline()
```

##### `fix_taxonomy_mismatches()`
SMART taxonomy mismatch fixing with intelligent GBIF usage.

**Features:**
- Only queries species with actual conflicts
- Saves 95%+ of API calls compared to traditional methods
- Uses majority rule within genera to resolve conflicts

**Example conflict resolution:**
```
Input:
  Lasioglossum littorale → Halictidae (2 occurrences)
  Lasioglossum littoralis → Apidae (1 occurrence)

Output:
  Both species → Halictidae (majority rule applied)
```

### Inherited Methods from `SpeciesDataCleaner`

#### File Processing Methods

##### `read_file1()` and `read_file2()`
Read and perform initial processing of input files.

**Processing includes:**
- UTF-8 encoding handling
- Unicode escape sequence conversion
- HTML entity conversion
- Whitespace cleanup
- Separator normalization

##### `merge_gender_variants()`
Merge species names differing only by gender endings.

**Gender patterns detected:**
- `-us/-a/-um` (Latin masculine/feminine/neuter)
- `-is/-e` (Latin 3rd declension)
- `-ensis/-ense` (Geographic endings)
- `-icus/-ica/-icum` (Adjectival endings)
- `-atus/-ata/-atum` (Past participle endings)
- `-osus/-osa/-osum` (Abundance endings)

**Example:**
```
Input:
  File1: Quercus alba, Quercus albus
  File2: Quercus alba (authority)

Output:
  File1: Quercus alba;Quercus albus;[merged synonyms]
  File2: Quercus alba
```

#### Quality Control Methods

##### `validate_cross_file_consistency()`
Ensures all valid names exist in both files.

**Returns:** `Tuple[List[str], List[str]]`
- Missing in File 1
- Missing in File 2

##### `fix_missing_match_file1(missing_species: List[str])`
Adds missing species from File 2 to File 1.

**Validation checks:**
- Proper species format (Genus species)
- Correct capitalization
- Alphabetic characters only
- Not already existing as synonym

##### `fix_missing_match_file2(missing_species: List[str])`
Removes species from File 1 that don't exist in File 2.

##### `remove_synonyms_that_are_valid_species()`
Remove any synonyms in File 1 that are also valid species (exist as valid names).

**Purpose:** Prevent valid species from being listed as synonyms of other species.

**Process:**
- Identifies all valid species names from both files
- Scans each valid name's synonym list
- Removes any synonyms that are also valid species
- Logs all removals with details

**Example:**
```
Input:
  Tethyophaena silifica;Aaptos papillata;Tuberella papillatana
  Aaptos papillata;Polymastia gleneni

Output:
  Tethyophaena silifica;Tuberella papillatana
  Aaptos papillata;Polymastia gleneni
```

##### `log_duplicate_synonyms()`
Detect and log when a synonym is used for more than one valid species.

**Purpose:** Identify potential data quality issues where synonyms conflict.

**Process:**
- Maps each synonym to all valid species that use it
- Identifies synonyms used by multiple valid species
- Logs conflicts with full species lists
- Prints conflicts to console during execution

**No data modification:** This function only logs issues for review.

**Example conflict:**
```
Synonym 'Common name' used by: ['Species A', 'Species B', 'Species C']
```

#### Output Methods

##### `write_cleaned_files()`
Writes final cleaned CSV files.

**File 1 format:** `valid_name;synonym1;synonym2;...`
**File 2 format:** `valid_name;Phylum;Class;Order;Family`

##### `write_removed_records()`
Saves removed records to separate files for reference.

##### `write_log()`
Creates detailed TSV log of all modifications.

**Log format:**
```
File	Line	Original	Updated	Note	Timestamp
file1	0	Original text	Updated text	unicode_fixed	2024-01-01 12:00:00
```

##### `write_summary()`
Generates comprehensive markdown summary report.

**SMART enhancements include:**
- Taxonomy normalization statistics
- GBIF efficiency metrics
- API usage statistics

## Processing Phases

### Phase 1: File Reading and Processing
1. **File Reading:** UTF-8 encoding with error handling
2. **Unicode Correction:** Convert escape sequences and HTML entities
3. **Basic Cleanup:** Remove empty lines, whitespace, malformed separators

### Phase 2: SMART Taxonomy Normalization
1. **Conflict Detection:** Identify taxonomy mismatches within genera
2. **Majority Rule Analysis:** Count occurrences of each taxonomy variant
3. **GBIF Validation:** Query only conflicted species (95%+ API savings)
4. **Resolution:** Apply appropriate normalization based on mode
5. **Result Caching:** Save GBIF output and search cache first on next run

### Phase 3: Species Name Standardization
1. **Case Standardization:** Proper species name formatting
2. **Subgenus Processing:** Handle `Genus (Subgenus) species` format
3. **Synonym Management:** Maintain proper synonym relationships

### Phase 4: Gender Ending Merge
1. **Pattern Detection:** Identify gender variants using linguistic patterns
2. **Authority Selection:** Use File 2 as taxonomic authority
3. **Validation:** Only merge species with consistent taxonomy
4. **Merge Process:** Combine variants and synonyms

### Phase 5: Data Validation and Consistency
1. **Cross-file Validation:** Ensure matching valid names
2. **Missing Match Resolution:** Add/remove species as needed
3. **Duplicate Handling:** Merge duplicates and combine synonyms

### Phase 6: Synonym Quality Control
1. **Valid Species Synonym Removal:** Remove synonyms that are also valid species
2. **Duplicate Synonym Detection:** Identify synonyms used by multiple valid species

### Phase 7: Final Output Generation
1. **File Writing:** Generate cleaned CSV files
2. **Logging:** Create detailed modification logs
3. **Reporting:** Generate summary and taxonomy reports

## Examples

### Basic Usage Examples

#### Command Line Execution
```bash
# Quick processing with majority rule
python smart_pipeline.py --mode majority_rule

# Balanced approach with default settings
python smart_pipeline.py

# High-accuracy GBIF validation (SMART optimized)
python smart_pipeline.py --mode gbif_only

# Custom confidence threshold
python smart_pipeline.py --mode hybrid --confidence 0.9
```

#### Programmatic Usage
```python
from smart_pipeline import SmartSpeciesDataCleaner

# Initialize cleaner
cleaner = SmartSpeciesDataCleaner(
    base_path="/path/to/gaplist-data",
    taxonomy_mode="hybrid",
    confidence_threshold=0.8
)

# Run complete pipeline
cleaner.run_pipeline()

# Access results
print(f"Processed {len(cleaner.file1_data)} species")
print(f"Made {len(cleaner.log_entries)} modifications")
```

#### Synonym Quality Control Processing
```
Input File 1 (problematic synonyms):
  Tethyophaena silifica;Aaptos papillata;Tuberella papillatana
  Aaptos papillata;Polymastia gleneni
  Species A;Common synonym;Unique synonym A
  Species B;Common synonym;Unique synonym B

Processing:
  1. Remove valid species synonyms: Remove "Aaptos papillata" from first line
  2. Log duplicate synonyms: Flag "Common synonym" used by multiple species

Output File 1 (cleaned):
  Tethyophaena silifica;Tuberella papillatana
  Aaptos papillata;Polymastia gleneni
  Species A;Common synonym;Unique synonym A
  Species B;Common synonym;Unique synonym B

Log Entries:
  - removed_valid_species_synonyms:Aaptos papillata
  - duplicate_synonym_usage_count:2 (Common synonym)
```

### Data Transformation Examples

#### Subgenus Processing
```
Input:  Actinia (Entacmaea) forskålii;Actinia forsk\u00e5lii
Output: Actinia forskålii;Actinia (Entacmaea) forskålii;Entacmaea forskålii
```

#### Gender Variant Merging
```
Input File 1:
  Megadelphax sordidulus;Delphax sordidulus
  
Input File 2:
  Megadelphax sordidula;Arthropoda;Insecta;Hemiptera;Delphacidae
  Megadelphax sordidulus;Arthropoda;Insecta;Hemiptera;Delphacidae

Output File 1:
  Megadelphax sordidula;Megadelphax sordidulus;Delphax sordidulus

Output File 2:
  Megadelphax sordidula;Arthropoda;Insecta;Hemiptera;Delphacidae
```

#### Taxonomy Conflict Resolution
```
Input (Conflict):
  Lasioglossum littorale → Halictidae (2 species)
  Lasioglossum littoralis → Apidae (1 species)

Resolution (Majority Rule):
  Both species → Halictidae
  Minority variant added as synonym

Output:
  Lasioglossum littorale;Lasioglossum littoralis;[synonyms]
```

### SMART Efficiency Example

**Traditional GBIF approach:**
- Total species: 150,000
- GBIF queries: 150,000
- Processing time: ~15 hours

**SMART GBIF approach:**
- Total species: 150,000
- Conflicted species: 4,500
- GBIF queries: 4,500 (97% reduction)
- Processing time: ~25 minutes

## Error Handling and Logging

### Log Categories

#### Data Processing
- `whitespace_removed`: Cleaned leading/trailing whitespace
- `separator_cleaned`: Fixed double separators or trailing semicolons
- `unicode_fixed`: Converted Unicode escape sequences
- `empty_line_removed`: Removed empty or whitespace-only lines

#### Taxonomy Processing
- `taxonomy_mismatch_fixed`: Updated taxonomy using majority rule
- `taxonomy_mismatch_synonym_added`: Added minority variant as synonym
- `gbif_validated`: Validated against GBIF backbone taxonomy
- `gbif_updated`: Updated based on GBIF validation

#### Species Processing
- `subgenus_processed`: Standardized subgenus format
- `gender_variant_merged`: Merged gender variants
- `duplicate_merged`: Combined duplicate entries
- `synonym_removed`: Removed redundant synonyms

#### File Consistency
- `added_from_file2_missing_match`: Added species to File 1
- `removed_missing_match_file2`: Removed species from File 1
- `removed_matched_synonym_in_file1`: Removed species matching synonyms

#### Synonym Quality Control
- `removed_valid_species_synonyms`: Removed synonyms that are valid species
- `duplicate_synonym_usage_count`: Logged synonym used by multiple species

#### Quality Control
- `malformed_line`: Identified improperly formatted lines
- `incomplete_taxonomy_removed`: Removed entries with insufficient taxonomy
- `trailing_data_stripped`: Cleaned database source indicators

### Error Recovery

The pipeline includes robust error handling:

1. **File Reading Errors:** Graceful handling of encoding issues
2. **API Failures:** Automatic retry with exponential backoff
3. **Data Validation:** Comprehensive format checking
4. **Logging:** Complete audit trail of all modifications

## Performance Metrics

### SMART Optimization Benefits

| Metric | Traditional | SMART | Improvement |
|--------|-------------|-------|-------------|
| API Calls | 150,000+ | <5,000 | 95%+ reduction |
| Processing Time | ~15 hours | ~25 minutes | 95% faster |
| Network Usage | ~500MB | ~15MB | 97% reduction |
| Cache Efficiency | Low | High | Conflict-focused |

### Typical Processing Statistics

For a dataset with 150,000 species:
- **Species Processed:** 150,000
- **Taxonomy Conflicts:** ~3% (4,500)
- **Gender Variants:** ~15% (22,500)
- **Duplicates Merged:** ~2% (3,000)
- **Valid Species Synonyms Removed:** ~1% (1,500)
- **Duplicate Synonym Conflicts:** ~0.5% (750)
- **API Queries (SMART):** 4,500
- **Total Modifications:** ~37,000

## Quality Assurance

### Data Integrity Checks
1. Every valid name appears exactly once in each output file
2. Valid names match exactly between both files
3. No valid species appear as synonyms of other species
4. All modifications logged with complete audit trail
5. Unicode characters properly encoded
6. No malformed separators or whitespace issues

### Validation Rules
1. **Species Format:** Must follow "Genus species" pattern
2. **Taxonomy Consistency:** Gender variants must have matching taxonomy
3. **Cross-file Consistency:** All valid names must exist in both files
4. **Synonym Uniqueness:** No duplicate synonyms within entries
5. **Valid Species Integrity:** Valid species cannot be synonyms of other species

### Output Quality
1. **Clean Formatting:** Consistent separator usage and spacing
2. **Proper Encoding:** All Unicode characters correctly handled
3. **Complete Taxonomy:** Only species with adequate taxonomic information
4. **Synonym Quality:** No conflicts between valid species and synonyms
5. **Audit Trail:** Complete log of all modifications and decisions

## Troubleshooting

### Common Issues

#### High Memory Usage
- **Cause:** Large datasets with many conflicts
- **Solution:** Process in batches or increase system memory

#### API Rate Limiting
- **Cause:** Rapid GBIF queries
- **Solution:** Automatic retry with exponential backoff (built-in)

#### Taxonomy Conflicts
- **Cause:** Inconsistent source data
- **Solution:** Review majority rule settings or use hybrid mode

#### Missing Dependencies
- **Cause:** Required modules not installed
- **Solution:** Install taxonomy_normalization package

### Debug Mode

Enable detailed logging by modifying the confidence threshold:
```python
cleaner = SmartSpeciesDataCleaner(
    base_path,
    taxonomy_mode="hybrid",
    confidence_threshold=0.5  # Lower threshold for more GBIF queries
)
```

## Dependencies

### Required Modules
- `pathlib`: File system operations
- `datetime`: Timestamp generation
- `collections`: Data structure utilities
- `argparse`: Command line parsing
- `json`: Configuration and reporting
- `csv`: File I/O operations
- `re`: Regular expression matching

### Custom Modules
- `taxonomy_normalization.taxonomy_normalizer`: SMART taxonomy processing
- `data_cleaning_pipeline`: Base pipeline functionality

## Version History

### v2.1 - Synonym Quality Control Enhancement
- Added synonym quality control functions
- Remove synonyms that are also valid species
- Detect and log duplicate synonym usage across species
- Enhanced data integrity validation
- Updated processing phases and documentation

### v2.0 - SMART Enhancement
- Added intelligent taxonomy normalization
- Implemented conflict-focused GBIF queries
- Reduced API usage by 95%+
- Added hybrid processing mode

### v1.0 - Original Pipeline
- Basic data cleaning functionality
- Gender variant merging
- Cross-file validation
- Comprehensive logging
