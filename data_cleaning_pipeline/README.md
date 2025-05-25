# Data Cleaning Pipeline Documentation

## Overview
This pipeline cleans two corresponding CSV files containing species data to ensure consistency and proper formatting between species/synonyms and taxonomic information.

## Input Files
1. **Species and Synonyms**: `all_specs_and_syn.csv`
   - Structure: `valid_name;synonym1;synonym2;...`
   - Each line starts with a valid species name followed by synonyms separated by ";"

2. **Species and Taxonomy**: `Gap_list_all_updated.csv`
   - Structure: `valid_name;Phylum;Class;Order;Family;[other_columns...]`
   - Each line starts with a valid species name followed by taxonomic hierarchy and metrics

## Output Files
- `all_specs_and_syn_cleaned.csv`
- `Gap_list_all_updated_cleaned.csv`
- `log_[timestamp].tsv` - Detailed log of all modifications

## Processing Approach

### Phase 1: Initial File Processing
1. **File Reading and Basic Cleanup**
   - Read files with UTF-8 encoding
   - Remove empty lines and lines with only whitespace
   - Log malformed lines for manual resolution

2. **Whitespace and Separator Cleanup**
   - Remove leading and trailing whitespaces from all fields
   - Remove double separators (";;" → ";")
   - Remove trailing semicolons

3. **Unicode Correction**
   - Convert Unicode escape sequences (\uXXXX) to proper UTF-8 characters
   - Convert HTML entities (&aring; etc.) to proper UTF-8 characters

### Phase 2: Species Name Standardization
1. **Case Standardization**
   - Convert all species names to proper format: "Genus species" or "Genus (Subgenus) species"
   - Maintain taxonomically correct capitalization

2. **Subgenus Processing**
   - **For valid names with subgenus format** `Genus (Subgenus) species`:
     - Change valid name to `Genus species`
     - Add `Genus (Subgenus) species` as synonym (unless identical to new valid name)
     - Add `Subgenus species` as synonym (unless identical to valid name)
   - **For synonyms with subgenus format** `Genus (Subgenus) species`:
     - Keep original synonym
     - Add `Subgenus species` as additional synonym (unless identical to valid name)

### Phase 3: Gender Ending Merge
1. **Gender Variant Detection**
   - Identify species names that differ only by gender endings
   - Common patterns: -us/-a/-um, -is/-e, -ensis/-ense, -icus/-ica/-icum, -atus/-ata/-atum, -osus/-osa/-osum
   - Group variants by genus and species stem (e.g., "Quercus alb-" groups "alba", "albus", "album")

2. **Taxonomy Validation**
   - Only merge variants that exist in both files
   - Require identical taxonomy (Phylum, Class, Order, Family) in File 2
   - Skip merging if taxonomy differs between variants

3. **Merge Process**
   - Select first variant alphabetically as master valid name
   - Add all other variants as synonyms to master entry
   - Merge all synonyms from variant entries
   - Remove duplicate entries from both files
   - Maintain consistency between File 1 and File 2

### Phase 4: Duplicate Handling
1. **File 1 (Species and Synonyms)**
   - Identify duplicate valid names (case-insensitive comparison)
   - Merge all synonyms from duplicates into single record
   - Remove duplicate synonyms within merged record

2. **File 2 (Species and Taxonomy)**
   - Identify duplicate valid names
   - Log conflicts as "duplicate_entry" for manual resolution
   - Keep first occurrence, log others

### Phase 5: Data Consistency
1. **Cross-file Validation**
   - Ensure every valid name in File 1 has exact match in File 2
   - Report missing matches as errors
   - Continue processing despite errors

2. **Synonym Cleanup**
   - Remove synonyms that exactly match the valid name
   - Remove duplicate synonyms

### Phase 6: Final Formatting
1. **File 1**: Maintain format `valid_name;synonym1;synonym2;...`
2. **File 2**: 
   - Trim to `valid_name;Phylum;Class;Order;Family` (remove all other columns)
   - Remove entries with incomplete taxonomy (family subdivisions without full taxonomic hierarchy)
   - Only include entries with all 4 taxonomy fields (Phylum, Class, Order, Family) populated

## Examples

### Subgenus Processing Examples

**Input File 1:**
```
Actinia (Entacmaea) forskålii;Actinia forsk\u00e5lii
```

**Output File 1:**
```
Actinia forskålii;Actinia (Entacmaea) forskålii;Entacmaea forskålii;Actinia forskålii
```
*(Note: "Actinia forskålii" duplicate removed)*

**Input with synonym subgenus:**
```
Banana apple;Banana (Pear) apple;Blueberry (Pear) apple
```

**Output:**
```
Banana apple;Banana (Pear) apple;Pear apple;Blueberry (Pear) apple;Blueberry apple
```

### Gender Ending Merge Examples

**Input File 1:**
```
Quercus alba;synonym1;synonym2
Quercus albus;synonym3;synonym4
```

**Input File 2:**
```
Quercus alba;Plantae;Magnoliopsida;Fagales;Fagaceae
Quercus albus;Plantae;Magnoliopsida;Fagales;Fagaceae
```

**Output File 1:**
```
Quercus alba;synonym1;synonym2;synonym3;synonym4;Quercus albus
```

**Output File 2:**
```
Quercus alba;Plantae;Magnoliopsida;Fagales;Fagaceae
```

**Example with taxonomy mismatch (no merge):**

**Input File 2:**
```
Genus alba;Phylum1;Class1;Order1;Family1
Genus albus;Phylum2;Class1;Order1;Family1
```
*(No merge occurs due to different Phylum)*

### Duplicate Merging Example

**Input File 1:**
```
Genus species;synonym1;synonym2
Genus species;synonym3;synonym1
```

**Output File 1:**
```
Genus species;synonym1;synonym2;synonym3
```

### File 2 Filtering Example

**Input File 2:**
```
Abyla trigona;Cnidaria;Hydrozoa;Siphonophorae;Abylidae;BOLD,FE;2;3;1;;gap;731420;;;;;;;;
Abylidae
Abylopsis tetragona;Cnidaria;Hydrozoa;Siphonophorae;Abylidae;FE,SyDip;;;;;gap;;;;;;;;;
```

**Output File 2:**
```
Abyla trigona;Cnidaria;Hydrozoa;Siphonophorae;Abylidae
Abylopsis tetragona;Cnidaria;Hydrozoa;Siphonophorae;Abylidae
```
*(Note: "Abylidae" line removed as incomplete taxonomy)*

### Previous File 2 Trimming Example

**Input File 2:**
```
Aagaardia protensa;Arthropoda;Insecta;Diptera;Chironomidae;BOLD,FE,SyDip;2;3;1;;gap;731420;;;;;;;;
```

**Output File 2:**
```
Aagaardia protensa;Arthropoda;Insecta;Diptera;Chironomidae
```

## Log Categories
- `whitespace_removed`: Leading/trailing whitespace cleaned
- `separator_cleaned`: Double separators or trailing semicolons removed
- `unicode_fixed`: Unicode escape sequences converted
- `subgenus_processed`: Subgenus format standardized
- `gender_variant_merged`: Species name merged due to gender ending difference
- `gender_variants_merged`: Summary of gender variant group merge
- `master_missing_in_files`: Gender variant master not found in both files
- `variant_missing_in_files`: Gender variant not found in both files
- `taxonomy_mismatch`: Gender variants have different taxonomy, merge skipped
- `duplicate_merged`: Duplicate entries combined
- `duplicate_entry`: Conflict in File 2 requiring manual resolution
- `synonym_removed`: Synonym identical to valid name removed
- `missing_match`: Valid name exists in one file but not the other
- `malformed_line`: Line doesn't follow expected format
- `empty_line_removed`: Empty or whitespace-only line removed
- `incomplete_taxonomy_removed`: Family subdivision without full taxonomy removed

## Quality Assurance
1. Every valid name appears exactly once in each output file
2. Valid names match exactly between both files (case-insensitive comparison)
3. All modifications are logged with file, line number, and change details
4. Unicode characters are properly encoded
5. No leading/trailing whitespace or malformed separators remain
