# Data Cleaning Results Summary

**Run Date:** 2025-05-25 19:07:46

## Files Processed
- Input file 1: `all_specs_and_syn.csv`
- Input file 2: `Gap_list_all_updated.csv`
- Output file 1: `all_specs_and_syn_cleaned_hybrid.csv`
- Output file 2: `Gap_list_all_updated_cleaned_hybrid.csv`
- Removed records: `Gap_list_all_removed_20250525_190602.csv`
- Log file: `log_20250525_190602.tsv`

## Results
- **File 1:** 159005 unique species processed
- **File 2:** 159005 unique species processed
- **Removed records:** 4423 (incomplete taxonomy)
- **Total modifications:** 534477

## Modification Types
- **added_from_file2_missing_match:** 1018
- **class_order_fields_inserted:** 88
- **duplicate_entry:** 65
- **duplicate_merged:** 135
- **gender_variant_merged:** 634
- **gender_variants_merged_file2_authority:** 317
- **hybrid_gbif_validated_confidence_100:** 2930
- **hybrid_gbif_validated_confidence_91:** 3
- **hybrid_gbif_validated_confidence_92:** 6
- **hybrid_gbif_validated_confidence_93:** 51
- **hybrid_gbif_validated_confidence_94:** 8
- **hybrid_gbif_validated_confidence_95:** 158
- **hybrid_gbif_validated_confidence_96:** 2096
- **hybrid_majority_rule_confidence_0.80:** 57
- **hybrid_majority_rule_confidence_0.81:** 6
- **hybrid_majority_rule_confidence_0.82:** 18
- **hybrid_majority_rule_confidence_0.83:** 48
- **hybrid_majority_rule_confidence_0.85:** 15
- **hybrid_majority_rule_confidence_0.86:** 61
- **hybrid_majority_rule_confidence_0.87:** 5
- **hybrid_majority_rule_confidence_0.88:** 32
- **hybrid_majority_rule_confidence_0.89:** 17
- **hybrid_majority_rule_confidence_0.90:** 30
- **hybrid_majority_rule_confidence_0.91:** 30
- **hybrid_majority_rule_confidence_0.92:** 18
- **hybrid_majority_rule_confidence_0.93:** 33
- **hybrid_majority_rule_confidence_0.94:** 10
- **hybrid_majority_rule_confidence_0.95:** 5
- **hybrid_majority_rule_confidence_0.96:** 10
- **hybrid_majority_rule_confidence_0.97:** 6
- **hybrid_majority_rule_confidence_0.98:** 4
- **hybrid_majority_rule_confidence_0.99:** 4
- **incomplete_taxonomy_removed:** 4275
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
For detailed logs, see: `log_20250525_190602.tsv`

## SMART Taxonomy Normalization
- **Mode:** hybrid
- **Confidence Threshold:** 0.8
- **SMART GBIF:** Only queries conflicted species

### Normalization Statistics
- **Gbif Queries Made:** 5,252
- **Gbif Queries Saved:** 154,218
- **Majority Rule Applied:** 409
- **Gbif Changes Applied:** 5,252
- **High Confidence Conflicts:** 225
- **Low Confidence Conflicts:** 565

### SMART GBIF Efficiency
- **Total Species:** 159,470
- **Queries Made:** 5,252
- **Queries Saved:** 154,218 (96.7%)

### GBIF API Statistics
- **Api Calls:** 0
- **Cache Hits:** 5252
- **Successful Matches:** 0
- **Failed Matches:** 0
- **Rate Limited:** 0
