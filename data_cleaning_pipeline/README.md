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
- `all_specs_and_syn_removed_[timestamp].csv` - Species removed from file1 (missing_match_file2 fix)
- `Gap_list_all_removed_[timestamp].csv` - Records removed from file2 (incomplete taxonomy)
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

### Phase 2: Taxonomy Mismatch Resolution
1. **Genus-Level Analysis**
   - Group all species by genus for comprehensive taxonomy analysis
   - Identify gender variants within each genus using stem detection
   - Compare taxonomy classifications across gender variants

2. **Conflict Detection**
   - Detect cases where gender variants have different higher taxonomy
   - Focus on first 4 taxonomy fields: Phylum, Class, Order, Family
   - Example: Lasioglossum littorale (Halictidae) vs Lasioglossum littoralis (Apidae)

3. **Majority Rule Application**
   - Count occurrences of each unique taxonomy within the genus
   - Select most common taxonomy as the correct classification
   - Use alphabetically first taxonomy as tie-breaker when counts are equal

4. **Data Correction**
   - Update minority variants in File 2 to use majority taxonomy
   - Add minority variants as synonyms in File 1 under majority variant
   - Ensure proper synonym relationships for later gender merging

### Phase 3: Species Name Standardization
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

### Phase 4: Gender Ending Merge
1. **Gender Variant Detection**
   - Identify species names that differ only by gender endings
   - Common patterns: -us/-a/-um, -is/-e, -ensis/-ense, -icus/-ica/-icum, -atus/-ata/-atum, -osus/-osa/-osum
   - Group variants by genus and species stem (e.g., "Quercus alb-" groups "alba", "albus", "album")

2. **File 2 Authority Selection**
   - **File 2 is the taxonomic authority**: Gender variants present in File 2 determine the correct valid name
   - If multiple variants exist in File 2, select first alphabetically as master
   - If only one variant exists in File 2, that becomes the master regardless of File 1 contents
   - Variants that exist only in File 1 (not in File 2) are merged into the File 2 master

3. **Taxonomy Validation**
   - Only merge File 2 variants that have identical taxonomy (Phylum, Class, Order, Family)
   - Skip merging variants with taxonomy mismatches
   - File 1-only variants are always merged (no taxonomy validation needed)

4. **Merge Process**
   - Update or create master entry in File 1 using the File 2 authority name
   - Add all variant names as synonyms to the master entry
   - Merge all synonyms from all variant entries
   - Remove merged variant entries from both files
   - Preserve all synonym information during the merge

### Phase 5: Duplicate Handling
1. **File 1 (Species and Synonyms)**
   - Identify duplicate valid names (case-insensitive comparison)
   - Merge all synonyms from duplicates into single record
   - Remove duplicate synonyms within merged record

2. **File 2 (Species and Taxonomy)**
   - Identify duplicate valid names
   - Log conflicts as "duplicate_entry" for manual resolution
   - Keep first occurrence, log others

### Phase 6: Data Consistency
1. **Cross-file Validation**
   - Ensure every valid name in File 1 has exact match in File 2
   - Report missing matches as errors
   - Continue processing despite errors

2. **Missing Match Resolution**
   - Fix "missing_match_file1" issue by adding valid species from File 2 to File 1
   - **Synonym Check**: Before adding, checks if the name already exists as a synonym in File 1
   - If name exists as synonym in File 1, removes it from File 2 instead of adding to File 1
   - **Species Format Validation**: Validates species format before adding to File 1
   - Invalid entries (improper format, capitalization, or non-alphabetic characters) are removed from File 2
   - All removed entries are saved to `Gap_list_all_removed_[timestamp].csv` for reference
   - Only adds proper species names (genus + species format with proper capitalization)
   - Adds species with empty synonym lists to maintain file format consistency
   - Fix "missing_match_file2" issue by removing species from File 1 that don't exist in File 2
   - Removed species are saved to `all_specs_and_syn_removed_[timestamp].csv` for reference

3. **Synonym Cleanup**
   - Remove synonyms that exactly match the valid name
   - Remove duplicate synonyms

### Phase 7: Final Formatting
1. **File 1**: Maintain format `valid_name;synonym1;synonym2;...`
2. **File 2**: 
   - Trim to `valid_name;Phylum;Class;Order;Family` (remove all other columns)
   - **Strip trailing data after family names**: Remove everything after family names (typically ending in "idae"), including database source indicators like "BOLD", "FE", "SyDip", "ITIS", etc.
   - **Handle incomplete taxonomic hierarchies**: For taxa missing intermediate ranks (commonly Order), insert empty fields to maintain proper positioning (e.g., `species;phylum;class;family` becomes `species;phylum;class;;family`)
   - Remove entries with incomplete taxonomy (family subdivisions without full taxonomic hierarchy)
   - Only include entries with some taxonomic information (at least one of the 4 taxonomy fields populated)

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

**Example 1: File 2 Authority Selection**

**Input File 1:**
```
Megadelphax sordidulus;Delphax sordidulus;Delphacodes sahlbergi
```

**Input File 2:**
```
Megadelphax sordidula;Arthropoda;Insecta;Hemiptera;Delphacidae
Megadelphax sordidulus;Arthropoda;Insecta;Hemiptera;Delphacidae
```

**Output File 1:**
```
Megadelphax sordidula;Megadelphax sordidulus;Delphax sordidulus;Delphacodes sahlbergi
```

**Output File 2:**
```
Megadelphax sordidula;Arthropoda;Insecta;Hemiptera;Delphacidae
```

**Example 2: File 1 Has Both Variants, File 2 Has One**

**Input File 1:**
```
Quercus alba;synonym1;synonym2
Quercus albus;synonym3;synonym4
```

**Input File 2:**
```
Quercus alba;Plantae;Magnoliopsida;Fagales;Fagaceae
```

**Output File 1:**
```
Quercus alba;Quercus albus;synonym1;synonym2;synonym3;synonym4
```

**Output File 2:**
```
Quercus alba;Plantae;Magnoliopsida;Fagales;Fagaceae
```

**Example 3: Multiple File 2 Variants (Alphabetical Selection)**

**Input File 1:**
```
Genus species1;syn1
Genus species2;syn2
Genus species3;syn3
```

**Input File 2:**
```
Genus species2;Phylum;Class;Order;Family
Genus species3;Phylum;Class;Order;Family
```

**Output File 1:**
```
Genus species2;Genus species1;Genus species3;syn1;syn2;syn3
```

**Output File 2:**
```
Genus species2;Phylum;Class;Order;Family
```

**Example 4: Taxonomy Mismatch Resolution**

**Input File 2:**
```
Lasioglossum littorale;Arthropoda;Insecta;Hymenoptera;Halictidae
Lasioglossum littoralis;Arthropoda;Insecta;Hymenoptera;Apidae
Lasioglossum littorum;Arthropoda;Insecta;Hymenoptera;Halictidae
```

**Input File 1:**
```
Lasioglossum littorale;synonym1
Lasioglossum littoralis;synonym2
```

**After Taxonomy Mismatch Fix:**

**File 2 (Majority Rule Applied - Halictidae wins 2 vs 1):**
```
Lasioglossum littorale;Arthropoda;Insecta;Hymenoptera;Halictidae
Lasioglossum littoralis;Arthropoda;Insecta;Hymenoptera;Halictidae  ← Updated
Lasioglossum littorum;Arthropoda;Insecta;Hymenoptera;Halictidae
```

**File 1 (Minority variant added as synonym):**
```
Lasioglossum littorale;synonym1;Lasioglossum littoralis  ← Minority added
Lasioglossum littoralis;synonym2
```

**After Gender Merge (Now succeeds with consistent taxonomy):**
```
Lasioglossum littorale;Lasioglossum littoralis;synonym1;synonym2
```

**Final File 2:**
```
Lasioglossum littorale;Arthropoda;Insecta;Hymenoptera;Halictidae
```

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
Lyonsia norwegica;Mollusca;Bivalvia;Lyonsiidae;BOLD,WORMS
```

**Output File 2:**
```
Abyla trigona;Cnidaria;Hydrozoa;Siphonophorae;Abylidae
Abylopsis tetragona;Cnidaria;Hydrozoa;Siphonophorae;Abylidae
Lyonsia norwegica;Mollusca;Bivalvia;;Lyonsiidae
```
*(Note: "Abylidae" line removed as incomplete taxonomy; trailing data stripped; order field inserted for incomplete hierarchy)*

### Previous File 2 Trimming Example

**Input File 2:**
```
Aagaardia protensa;Arthropoda;Insecta;Diptera;Chironomidae;BOLD,FE,SyDip;2;3;1;;gap;731420;;;;;;;;
```

**Output File 2:**
```
Aagaardia protensa;Arthropoda;Insecta;Diptera;Chironomidae
```

### Missing Match Fix Example

**Input File 1:**
```
Genus species1;synonym1;synonym2
Genus species2;synonym3;Genus species4
```

**Input File 2:**
```
Genus species1;Phylum;Class;Order;Family
Genus species2;Phylum;Class;Order;Family
Genus species3;Phylum;Class;Order;Family
Genus species4;Phylum;Class;Order;Family
InvalidEntry;Phylum;Class;Order;Family
Abylidae
```

**After missing_match_file1 fix - Output File 1:**
```
Genus species1;synonym1;synonym2
Genus species2;synonym3;Genus species4
Genus species3
```

**Output File 2:**
```
Genus species1;Phylum;Class;Order;Family
Genus species2;Phylum;Class;Order;Family
Genus species3;Phylum;Class;Order;Family
```

**Removed File 2 (`Gap_list_all_removed_[timestamp].csv`):**
```
Genus species4;Phylum;Class;Order;Family
InvalidEntry;Phylum;Class;Order;Family
```

**Explanation:**
- `Genus species3` was added to File 1 (not present as valid name or synonym)
- `Genus species4` was removed from File 2 because it already exists as a synonym under `Genus species2` in File 1
- `InvalidEntry` was removed from File 2 because it doesn't follow proper species naming format (single word)
- `Abylidae` family-only entry was already filtered out during file2 processing

## Log Categories
- `whitespace_removed`: Leading/trailing whitespace cleaned
- `separator_cleaned`: Double separators or trailing semicolons removed
- `unicode_fixed`: Unicode escape sequences converted
- `subgenus_processed`: Subgenus format standardized
- `gender_variant_merged`: Species name merged due to gender ending difference
- `gender_variants_merged_file2_authority`: Summary of gender variant group merge using File 2 authority
- `master_missing_in_files`: Gender variant master not found in both files (legacy)
- `no_variants_in_file2`: Gender variant group skipped because no variants exist in File 2
- `variant_missing_in_file1`: Gender variant exists in File 2 but not in File 1
- `master_added_from_file2`: Master variant added to File 1 from File 2 during gender merge
- `master_synonyms_updated`: Master entry's synonyms updated during gender merge
- `taxonomy_mismatch`: Gender variants have different taxonomy, merge skipped (deprecated - now fixed before merge)
- `taxonomy_mismatch_fixed`: Taxonomy updated using majority rule within genus
- `taxonomy_mismatch_synonym_added`: Minority taxonomy variant added as synonym to majority variant
- `taxonomy_mismatch_master_created`: New master entry created in file1 with minority variant as synonym
- `duplicate_merged`: Duplicate entries combined
- `duplicate_entry`: Conflict in File 2 requiring manual resolution
- `synonym_removed`: Synonym identical to valid name removed
- `missing_match`: Valid name exists in one file but not the other
- `malformed_line`: Line doesn't follow expected format
- `empty_line_removed`: Empty or whitespace-only line removed
- `incomplete_taxonomy_removed`: Family subdivision without full taxonomy removed
- `family_only_line_skipped`: Line with only family name and empty taxonomy fields skipped
- `trailing_data_stripped`: Data after family name (e.g., BOLD, FE, SyDip, ITIS) removed
- `order_field_inserted`: Empty order field inserted for incomplete taxonomy hierarchy (phylum, class, family → phylum, class, , family)
- `class_order_fields_inserted`: Empty class and order fields inserted (phylum, family → phylum, , , family)
- `phylum_class_order_fields_inserted`: Empty phylum, class, and order fields inserted (family → , , , family)
- `added_from_file2_missing_match`: Valid species added to file1 to fix missing_match_file1 issue
- `matched_synonym_in_file1`: Species from file2 found as synonym in file1, marked for removal from file2
- `removed_matched_synonym_in_file1`: Species removed from file2 because it matched a synonym in file1
- `removed_not_species_format`: Entry removed from file2 during missing_match_file1 fix due to improper species format (less than 2 parts)
- `removed_improper_capitalization`: Entry removed from file2 during missing_match_file1 fix due to improper capitalization
- `removed_invalid_genus_format`: Entry removed from file2 during missing_match_file1 fix due to invalid genus format (non-alphabetic)
- `removed_invalid_species_format`: Entry removed from file2 during missing_match_file1 fix due to invalid species format (non-alphabetic)
- `removed_missing_match_file2`: Species removed from file1 because it doesn't exist in file2

## Quality Assurance
1. Every valid name appears exactly once in each output file
2. Valid names match exactly between both files (case-insensitive comparison)
3. All modifications are logged with file, line number, and change details
4. Unicode characters are properly encoded
5. No leading/trailing whitespace or malformed separators remain
