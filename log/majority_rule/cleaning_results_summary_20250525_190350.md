# Data Cleaning Results Summary

**Run Date:** 2025-05-25 19:05:08

## Files Processed
- Input file 1: `all_specs_and_syn.csv`
- Input file 2: `Gap_list_all_updated.csv`
- Output file 1: `all_specs_and_syn_cleaned_majority_rule.csv`
- Output file 2: `Gap_list_all_updated_cleaned_majority_rule.csv`
- Removed records: `Gap_list_all_removed_20250525_190350.csv`
- Log file: `log_20250525_190350.tsv`

## Results
- **File 1:** 159005 unique species processed
- **File 2:** 159005 unique species processed
- **Removed records:** 4423 (incomplete taxonomy)
- **Total modifications:** 531339

## Modification Types
- **added_from_file2_missing_match:** 1018
- **class_order_fields_inserted:** 88
- **duplicate_entry:** 65
- **duplicate_merged:** 135
- **gender_variant_merged:** 634
- **gender_variants_merged_file2_authority:** 317
- **incomplete_taxonomy_removed:** 4275
- **majority_rule_applied_confidence_0.50:** 329
- **majority_rule_applied_confidence_0.51:** 22
- **majority_rule_applied_confidence_0.52:** 34
- **majority_rule_applied_confidence_0.53:** 41
- **majority_rule_applied_confidence_0.54:** 104
- **majority_rule_applied_confidence_0.55:** 245
- **majority_rule_applied_confidence_0.56:** 122
- **majority_rule_applied_confidence_0.57:** 207
- **majority_rule_applied_confidence_0.58:** 49
- **majority_rule_applied_confidence_0.59:** 28
- **majority_rule_applied_confidence_0.60:** 149
- **majority_rule_applied_confidence_0.61:** 24
- **majority_rule_applied_confidence_0.62:** 84
- **majority_rule_applied_confidence_0.63:** 26
- **majority_rule_applied_confidence_0.64:** 53
- **majority_rule_applied_confidence_0.65:** 6
- **majority_rule_applied_confidence_0.66:** 40
- **majority_rule_applied_confidence_0.67:** 170
- **majority_rule_applied_confidence_0.69:** 23
- **majority_rule_applied_confidence_0.70:** 36
- **majority_rule_applied_confidence_0.71:** 45
- **majority_rule_applied_confidence_0.72:** 26
- **majority_rule_applied_confidence_0.73:** 27
- **majority_rule_applied_confidence_0.74:** 14
- **majority_rule_applied_confidence_0.75:** 121
- **majority_rule_applied_confidence_0.76:** 14
- **majority_rule_applied_confidence_0.77:** 10
- **majority_rule_applied_confidence_0.78:** 40
- **majority_rule_applied_confidence_0.79:** 25
- **majority_rule_applied_confidence_0.80:** 57
- **majority_rule_applied_confidence_0.81:** 6
- **majority_rule_applied_confidence_0.82:** 18
- **majority_rule_applied_confidence_0.83:** 48
- **majority_rule_applied_confidence_0.85:** 15
- **majority_rule_applied_confidence_0.86:** 61
- **majority_rule_applied_confidence_0.87:** 5
- **majority_rule_applied_confidence_0.88:** 32
- **majority_rule_applied_confidence_0.89:** 17
- **majority_rule_applied_confidence_0.90:** 30
- **majority_rule_applied_confidence_0.91:** 30
- **majority_rule_applied_confidence_0.92:** 18
- **majority_rule_applied_confidence_0.93:** 33
- **majority_rule_applied_confidence_0.94:** 10
- **majority_rule_applied_confidence_0.95:** 5
- **majority_rule_applied_confidence_0.96:** 10
- **majority_rule_applied_confidence_0.97:** 6
- **majority_rule_applied_confidence_0.98:** 4
- **majority_rule_applied_confidence_0.99:** 4
- **malformed_line:** 4276
- **master_added_from_file2:** 10
- **master_synonyms_updated:** 155
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
- **trailing_data_stripped:** 158388
- **unicode_fixed:** 72
- **variant_missing_in_file1:** 8
- **whitespace_removed:** 326515

## Details
For detailed logs, see: `log_20250525_190350.tsv`

## SMART Taxonomy Normalization
- **Mode:** majority_rule
- **Confidence Threshold:** 0.8
- **SMART GBIF:** Only queries conflicted species

### Normalization Statistics
- **Majority Rule Applied:** 2,523
