# Data Cleaning Results Summary

**Run Date:** 2025-05-25 12:43:09

## Files Processed
- Input file 1: `all_specs_and_syn.csv`
- Input file 2: `Gap_list_all_updated.csv`
- Output file 1: `all_specs_and_syn_cleaned.csv`
- Output file 2: `Gap_list_all_updated_cleaned.csv`
- Removed records: `Gap_list_all_removed_20250525_124150.csv`
- Log file: `log_20250525_124150.tsv`

## Results
- **File 1:** 159004 unique species processed
- **File 2:** 159004 unique species processed
- **Removed records:** 4424 (incomplete taxonomy)
- **Total modifications:** 528859

## Modification Types
- **added_from_file2_missing_match:** 1017
- **class_order_fields_inserted:** 88
- **duplicate_entry:** 65
- **duplicate_merged:** 135
- **gender_variant_merged:** 634
- **gender_variants_merged_file2_authority:** 317
- **incomplete_taxonomy_removed:** 4275
- **malformed_line:** 4276
- **master_added_from_file2:** 10
- **master_synonyms_updated:** 157
- **matched_synonym_in_file1:** 6
- **missing_match_file1:** 1166
- **missing_match_file2:** 2
- **order_field_inserted:** 2650
- **removed_improper_capitalization:** 5
- **removed_invalid_species_format:** 137
- **removed_matched_synonym_in_file1:** 6
- **removed_missing_match_file2:** 2
- **removed_not_species_format:** 1
- **subgenus_processed:** 21244
- **synonym_removed:** 7643
- **taxonomy_mismatch_fixed:** 20
- **taxonomy_mismatch_synonym_added:** 20
- **trailing_data_stripped:** 158388
- **unicode_fixed:** 72
- **variant_missing_in_file1:** 8
- **whitespace_removed:** 326515

## Details
For detailed logs, see: `log_20250525_124150.tsv`
