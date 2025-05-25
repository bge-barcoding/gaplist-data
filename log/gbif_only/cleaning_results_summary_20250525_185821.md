# Data Cleaning Results Summary

**Run Date:** 2025-05-25 19:00:26

## Files Processed
- Input file 1: `all_specs_and_syn.csv`
- Input file 2: `Gap_list_all_updated.csv`
- Output file 1: `all_specs_and_syn_cleaned_gbif_only.csv`
- Output file 2: `Gap_list_all_updated_cleaned_gbif_only.csv`
- Removed records: `Gap_list_all_removed_20250525_185821.csv`
- Log file: `log_20250525_185821.tsv`

## Results
- **File 1:** 159006 unique species processed
- **File 2:** 159006 unique species processed
- **Removed records:** 4423 (incomplete taxonomy)
- **Total modifications:** 533597

## Modification Types
- **added_from_file2_missing_match:** 1018
- **class_order_fields_inserted:** 88
- **duplicate_entry:** 65
- **duplicate_merged:** 135
- **gbif_validated_confidence_100:** 820
- **gbif_validated_confidence_91:** 6
- **gbif_validated_confidence_92:** 8
- **gbif_validated_confidence_93:** 77
- **gbif_validated_confidence_94:** 14
- **gbif_validated_confidence_95:** 286
- **gbif_validated_confidence_96:** 3573
- **gender_variant_merged:** 632
- **gender_variants_merged_file2_authority:** 316
- **incomplete_taxonomy_removed:** 4275
- **malformed_line:** 4276
- **master_added_from_file2:** 10
- **master_synonyms_updated:** 154
- **matched_synonym_in_file1:** 5
- **missing_match_file1:** 1166
- **missing_match_file2:** 2
- **order_field_inserted:** 2650
- **removed_improper_capitalization:** 5
- **removed_invalid_species_format:** 137
- **removed_matched_synonym_in_file1:** 5
- **removed_missing_match_file2:** 2
- **removed_not_species_format:** 1
- **subgenus_processed:** 21244
- **synonym_removed:** 7643
- **taxonomy_mismatch:** 1
- **trailing_data_stripped:** 158388
- **unicode_fixed:** 72
- **variant_missing_in_file1:** 8
- **whitespace_removed:** 326515

## Details
For detailed logs, see: `log_20250525_185821.tsv`

## SMART Taxonomy Normalization
- **Mode:** gbif_only
- **Confidence Threshold:** 0.8
- **SMART GBIF:** Only queries conflicted species

### Normalization Statistics
- **Gbif Queries Made:** 8,955
- **Gbif Queries Saved:** 150,515
- **Gbif Successful Matches:** 8,955
- **Gbif Changes Applied:** 4,784

### SMART GBIF Efficiency
- **Total Species:** 159,470
- **Queries Made:** 8,955
- **Queries Saved:** 150,515 (94.4%)

### GBIF API Statistics
- **Api Calls:** 0
- **Cache Hits:** 8955
- **Successful Matches:** 0
- **Failed Matches:** 0
- **Rate Limited:** 0
