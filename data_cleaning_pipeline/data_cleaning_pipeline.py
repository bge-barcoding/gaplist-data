#!/usr/bin/env python3
"""
Data Cleaning Pipeline for Species CSV Files
============================================

This script processes two CSV files containing species data:
1. Species and synonyms file
2. Species and taxonomy file

Applies standardization, deduplication, and validation rules.
See data_cleaning_pipeline_documentation.md for detailed specifications.
"""

import csv
import re
import html
import unicodedata
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import logging

class SpeciesDataCleaner:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.log_entries = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Directories
        self.data_dir = self.base_path / "data"
        self.cleaned_dir = self.base_path / "cleaned_data"
        self.log_dir = self.base_path / "log"
        
        # Files
        self.file1_path = self.data_dir / "all_specs_and_syn.csv"
        self.file2_path = self.data_dir / "Gap_list_all_updated.csv"
        self.file1_output = self.cleaned_dir / "all_specs_and_syn_cleaned.csv"
        self.file2_output = self.cleaned_dir / "Gap_list_all_updated_cleaned.csv"
        self.removed_output = self.cleaned_dir / f"Gap_list_all_removed_{self.timestamp}.csv"
        self.log_path = self.log_dir / f"log_{self.timestamp}.tsv"
        self.summary_path = self.log_dir / f"cleaning_results_summary_{self.timestamp}.md"
        
        # Data storage
        self.file1_data = {}  # valid_name -> [synonyms]
        self.file2_data = {}  # valid_name -> [phylum, class, order, family]
        self.removed_records = []  # Store removed records for separate file
        
        # Gender ending patterns for merging
        self.gender_patterns = [
            # Common Latin gender endings - each entry is (pattern, all_endings_in_group)
            (r'(.+)us$', ['us', 'a', 'um']),      # -us, -a, -um
            (r'(.+)a$', ['us', 'a', 'um']),       # -us, -a, -um (from -a)
            (r'(.+)um$', ['us', 'a', 'um']),      # -us, -a, -um (from -um)
            (r'(.+)is$', ['is', 'e']),            # -is, -e
            (r'(.+)e$', ['is', 'e']),             # -is, -e (from -e)
            (r'(.+)ensis$', ['ensis', 'ense']),   # -ensis, -ense
            (r'(.+)ense$', ['ensis', 'ense']),    # -ensis, -ense (from -ense)
            (r'(.+)icus$', ['icus', 'ica', 'icum']), # -icus, -ica, -icum
            (r'(.+)ica$', ['icus', 'ica', 'icum']),  # -icus, -ica, -icum (from -ica)
            (r'(.+)icum$', ['icus', 'ica', 'icum']), # -icus, -ica, -icum (from -icum)
            (r'(.+)atus$', ['atus', 'ata', 'atum']), # -atus, -ata, -atum
            (r'(.+)ata$', ['atus', 'ata', 'atum']),  # -atus, -ata, -atum (from -ata)
            (r'(.+)atum$', ['atus', 'ata', 'atum']), # -atus, -ata, -atum (from -atum)
            (r'(.+)osus$', ['osus', 'osa', 'osum']), # -osus, -osa, -osum
            (r'(.+)osa$', ['osus', 'osa', 'osum']),  # -osus, -osa, -osum (from -osa)
            (r'(.+)osum$', ['osus', 'osa', 'osum']), # -osus, -osa, -osum (from -osum)
        ]
        
    def log_change(self, file_name: str, line_num: int, original: str, updated: str, note: str):
        """Add entry to modification log"""
        self.log_entries.append({
            'file': file_name,
            'line_number': line_num,
            'original_text': original.replace('\t', '\\t').replace('\n', '\\n'),
            'updated_text': updated.replace('\t', '\\t').replace('\n', '\\n'),
            'modification_notes': note
        })    
    def fix_unicode(self, text: str) -> str:
        """Fix Unicode escape sequences and HTML entities"""
        if not text:
            return text
            
        # Fix Unicode escape sequences (\uXXXX)
        def replace_unicode_escapes(match):
            code = match.group(1)
            try:
                return chr(int(code, 16))
            except ValueError:
                return match.group(0)  # Return original if invalid
        
        text = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode_escapes, text)
        
        # Fix HTML entities
        text = html.unescape(text)
        
        # Normalize Unicode (NFC form)
        text = unicodedata.normalize('NFC', text)
        
        return text
    
    def clean_basic_formatting(self, text: str) -> str:
        """Clean whitespace and separators"""
        if not text:
            return text
            
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Fix double separators
        text = re.sub(r';+', ';', text)
        
        # Remove trailing semicolon
        text = text.rstrip(';')
        
        return text
    
    def extract_subgenus_info(self, name: str) -> Tuple[str, str, str]:
        """
        Extract genus, subgenus, species from format 'Genus (Subgenus) species'
        Returns: (genus, subgenus, species)
        """
        pattern = r'^([A-Z][a-z]+)\s*\(([A-Z][a-z]+)\)\s+([a-z]+)$'
        match = re.match(pattern, name.strip())
        
        if match:
            return match.group(1), match.group(2), match.group(3)
        return "", "", ""    
    def process_subgenus_name(self, name: str) -> Tuple[str, List[str]]:
        """
        Process a name with potential subgenus format
        Returns: (standardized_valid_name, additional_synonyms)
        """
        genus, subgenus, species = self.extract_subgenus_info(name)
        
        if genus and subgenus and species:
            # Has subgenus format
            standard_name = f"{genus} {species}"
            additional_synonyms = []
            
            # Add original format as synonym if different from standard
            if name.strip() != standard_name:
                additional_synonyms.append(name.strip())
            
            # Add subgenus + species as synonym if different from standard
            subgenus_name = f"{subgenus} {species}"
            if subgenus_name != standard_name:
                additional_synonyms.append(subgenus_name)
            
            return standard_name, additional_synonyms
        
        return name.strip(), []
    
    def get_species_stem_and_variants(self, species_name: str) -> Tuple[str, List[str]]:
        """
        Extract stem and generate gender variants for a species name.
        Returns: (stem, [list of possible gender variants])
        """
        if not species_name or ' ' not in species_name.strip():
            return species_name, []
        
        genus, species = species_name.strip().split(' ', 1)
        variants = []
        
        for pattern, endings in self.gender_patterns:
            match = re.match(pattern, species, re.IGNORECASE)
            if match:
                stem = match.group(1)
                # Generate all variants in this ending group
                for ending in endings:
                    variant = stem + ending
                    full_variant = f"{genus} {variant}"
                    if full_variant.lower() != species_name.lower():
                        variants.append(full_variant)
                return f"{genus} {stem}", variants
        
        return species_name, []
    
    def find_gender_variant_groups(self) -> Dict[str, List[str]]:
        """
        Find groups of species names that are gender variants of each other.
        Returns: dict mapping stem -> [list of actual species names]
        """
        stem_groups = defaultdict(list)
        all_names = set()
        
        # Collect all valid names from both files
        for name_lower in self.file1_data:
            actual_name = self.file1_data[name_lower][0]
            all_names.add(actual_name)
        
        for name_lower in self.file2_data:
            actual_name = self.file2_data[name_lower][0]
            all_names.add(actual_name)
        
        # Group by stems
        for name in all_names:
            stem, variants = self.get_species_stem_and_variants(name)
            if variants:  # Only group names that have potential variants
                stem_groups[stem.lower()].append(name)
        
        # Filter to only groups with multiple members
        result = {}
        for stem, names in stem_groups.items():
            if len(names) > 1:
                result[stem] = names
        
        return result
    
    def fix_taxonomy_mismatches(self):
        """
        Fix taxonomy mismatches between different genders of the same species.
        Uses majority rule within each genus to determine correct taxonomy,
        then ensures minority variants are added as synonyms in file 1.
        """
        print("Fixing taxonomy mismatches...")
        
        # Group all species by genus
        genus_groups = defaultdict(list)
        for name_lower, (actual_name, taxonomy) in self.file2_data.items():
            name_parts = actual_name.strip().split()
            if len(name_parts) >= 2:
                genus = name_parts[0]
                genus_groups[genus.lower()].append((actual_name, name_lower, taxonomy))
        
        # Find gender variant groups within each genus
        mismatches_fixed = 0
        for genus_lower, species_list in genus_groups.items():
            genus_variants = self.find_genus_gender_variants(species_list)
            
            for stem, variants in genus_variants.items():
                if len(variants) < 2:
                    continue
                
                # Check for taxonomy mismatches
                taxonomies = [(variant[0], variant[2]) for variant in variants]  # (name, taxonomy)
                unique_taxonomies = {}
                
                for name, taxonomy in taxonomies:
                    tax_key = tuple(taxonomy[:4])  # First 4 fields: phylum, class, order, family
                    if tax_key not in unique_taxonomies:
                        unique_taxonomies[tax_key] = []
                    unique_taxonomies[tax_key].append(name)
                
                # If only one unique taxonomy, no mismatch
                if len(unique_taxonomies) <= 1:
                    continue
                
                print(f"Found taxonomy mismatch in genus {genus_lower} for stem '{stem}':")
                
                # Apply majority rule
                majority_taxonomy = None
                majority_count = 0
                majority_names = []
                
                for tax_key, names in unique_taxonomies.items():
                    print(f"  Taxonomy {';'.join(tax_key)}: {names}")
                    if len(names) > majority_count:
                        majority_count = len(names)
                        majority_taxonomy = tax_key
                        majority_names = names
                
                # If tie, use alphabetically first taxonomy
                if majority_count == 1 and len(unique_taxonomies) > 1:
                    sorted_taxonomies = sorted(unique_taxonomies.keys())
                    majority_taxonomy = sorted_taxonomies[0]
                    majority_names = unique_taxonomies[majority_taxonomy]
                
                print(f"  Selected majority taxonomy: {';'.join(majority_taxonomy)} (used by {majority_names})")
                
                # Update minority variants to use majority taxonomy
                minority_variants = []
                for tax_key, names in unique_taxonomies.items():
                    if tax_key != majority_taxonomy:
                        minority_variants.extend(names)
                
                for minority_name in minority_variants:
                    minority_lower = minority_name.lower()
                    if minority_lower in self.file2_data:
                        old_taxonomy = self.file2_data[minority_lower][1]
                        
                        # Update taxonomy in file2
                        self.file2_data[minority_lower] = (minority_name, list(majority_taxonomy))
                        
                        # Ensure minority variant is in file1 as synonym of majority variant
                        # Find a majority variant to use as master
                        master_name = majority_names[0]  # Use first majority name as master
                        master_lower = master_name.lower()
                        
                        if master_lower in self.file1_data:
                            # Add minority name as synonym if not already present
                            master_synonyms = self.file1_data[master_lower][1]
                            if minority_name not in master_synonyms and minority_lower != master_lower:
                                master_synonyms.append(minority_name)
                                self.log_change('file1', 0, 
                                              f"{master_name};{len(master_synonyms)-1}_synonyms",
                                              f"{master_name};{len(master_synonyms)}_synonyms", 
                                              'taxonomy_mismatch_synonym_added')
                        else:
                            # Create master entry in file1 with minority as synonym
                            self.file1_data[master_lower] = (master_name, [minority_name])
                            self.log_change('file1', 0, '', 
                                          f"{master_name};{minority_name}", 
                                          'taxonomy_mismatch_master_created')
                        
                        self.log_change('file2', 0, 
                                      f"{minority_name};{';'.join(old_taxonomy)}", 
                                      f"{minority_name};{';'.join(majority_taxonomy)}", 
                                      'taxonomy_mismatch_fixed')
                        mismatches_fixed += 1
                        
                        print(f"  Fixed: {minority_name} taxonomy updated and added as synonym to {master_name}")
        
        if mismatches_fixed > 0:
            print(f"Fixed {mismatches_fixed} taxonomy mismatches using majority rule")
        else:
            print("No taxonomy mismatches found to fix")
    
    def find_genus_gender_variants(self, species_list):
        """
        Find gender variants within a single genus.
        Returns: dict mapping stem -> [(name, name_lower, taxonomy), ...]
        """
        stem_groups = defaultdict(list)
        
        for actual_name, name_lower, taxonomy in species_list:
            stem, variants = self.get_species_stem_and_variants(actual_name)
            if variants:  # Only group names that have potential variants
                stem_key = stem.lower()
                stem_groups[stem_key].append((actual_name, name_lower, taxonomy))
        
        # Filter to only groups with multiple members
        result = {}
        for stem, variants in stem_groups.items():
            if len(variants) > 1:
                result[stem] = variants
        
        return result

    def merge_gender_variants(self):
        """
        Merge species names that differ only by gender endings.
        Uses File 2 as taxonomic authority - if gender variants exist,
        the version present in File 2 becomes the master valid name.
        """
        print("Merging gender variants...")
        
        variant_groups = self.find_gender_variant_groups()
        if not variant_groups:
            print("No gender variants found to merge.")
            return
        
        print(f"Found {len(variant_groups)} groups of gender variants to merge.")
        
        for stem, variant_names in variant_groups.items():
            print(f"Processing gender variants of '{stem}': {variant_names}")
            
            # Find which variants exist in File 2 (taxonomic authority)
            file2_variants = []
            file1_only_variants = []
            
            for variant in variant_names:
                variant_lower = variant.lower()
                if variant_lower in self.file2_data:
                    file2_variants.append(variant)
                elif variant_lower in self.file1_data:
                    file1_only_variants.append(variant)
            
            if not file2_variants:
                # No variants exist in File 2, skip merging
                self.log_change('gender_merge', 0, ';'.join(variant_names), 
                              '', 'no_variants_in_file2')
                continue
            
            # Select master from File 2 variants (first alphabetically if multiple)
            file2_variants.sort()
            master_name = file2_variants[0]
            master_lower = master_name.lower()
            
            print(f"Selected master from File 2: '{master_name}'")
            
            # Collect all other variants that need to be merged
            merge_variants = file2_variants[1:] + file1_only_variants
            
            if not merge_variants:
                # Only one variant exists, nothing to merge
                continue
            
            print(f"Merging variants: {merge_variants} -> master: '{master_name}'")
            
            # Validate taxonomy consistency for File 2 variants
            master_taxonomy = self.file2_data[master_lower][1]
            valid_merge_variants = []
            
            for merge_variant in merge_variants:
                merge_lower = merge_variant.lower()
                
                # Check if variant exists in File 2 and has matching taxonomy
                if merge_lower in self.file2_data:
                    merge_taxonomy = self.file2_data[merge_lower][1]
                    
                    # Check if taxonomy matches (first 4 fields: phylum, class, order, family)
                    if master_taxonomy[:4] != merge_taxonomy[:4]:
                        self.log_change('gender_merge', 0, 
                                      f"{master_name}:{';'.join(master_taxonomy)} vs {merge_variant}:{';'.join(merge_taxonomy)}", 
                                      '', 'taxonomy_mismatch')
                        continue
                
                # Check if variant exists in File 1
                if merge_lower not in self.file1_data:
                    self.log_change('gender_merge', 0, merge_variant, '', 
                                  'variant_missing_in_file1')
                    continue
                
                valid_merge_variants.append(merge_variant)
            
            if not valid_merge_variants:
                continue
            
            # Perform the merge in File 1
            # Start with master's synonyms (if master exists in File 1)
            if master_lower in self.file1_data:
                master_synonyms = list(self.file1_data[master_lower][1])  # Copy existing synonyms
                original_master_synonyms = len(master_synonyms)
            else:
                # Master doesn't exist in File 1, create new entry
                master_synonyms = []
                original_master_synonyms = 0
                self.log_change('file1', 0, '', master_name, 
                              'master_added_from_file2')
            
            # Merge all valid variants
            for merge_variant in valid_merge_variants:
                merge_lower = merge_variant.lower()
                
                if merge_lower in self.file1_data:
                    merge_synonyms = self.file1_data[merge_lower][1]
                    
                    # Add all synonyms from merge candidate
                    master_synonyms.extend(merge_synonyms)
                    
                    # Add the merge candidate name itself as a synonym
                    master_synonyms.append(merge_variant)
                    
                    # Remove merge candidate from file1_data
                    del self.file1_data[merge_lower]
                    
                    self.log_change('file1', 0, 
                                  f"{merge_variant};{';'.join(merge_synonyms)}", 
                                  f"merged_into:{master_name}", 
                                  'gender_variant_merged')
            
            # Remove duplicate synonyms
            unique_synonyms = []
            seen = set()
            for syn in master_synonyms:
                if syn.lower() not in seen and syn.lower() != master_lower:
                    unique_synonyms.append(syn)
                    seen.add(syn.lower())
            
            # Update/create master entry in file1
            self.file1_data[master_lower] = (master_name, unique_synonyms)
            
            if original_master_synonyms > 0:
                self.log_change('file1', 0, f"{master_name};{original_master_synonyms}_synonyms", 
                              f"{master_name};{len(unique_synonyms)}_synonyms", 
                              'master_synonyms_updated')
            
            # Handle File 2: Remove merge candidates that exist in File 2
            file2_merge_count = 0
            for merge_variant in valid_merge_variants:
                merge_lower = merge_variant.lower()
                
                if merge_lower in self.file2_data:
                    merge_taxonomy = self.file2_data[merge_lower][1]  # Get before deleting
                    
                    del self.file2_data[merge_lower]
                    
                    self.log_change('file2', 0, 
                                  f"{merge_variant};{';'.join(merge_taxonomy)}", 
                                  f"merged_into:{master_name}", 
                                  'gender_variant_merged')
                    file2_merge_count += 1
            
            self.log_change('gender_merge', 0, 
                          ';'.join(variant_names), 
                          f"master:{master_name};file1_merged:{len(valid_merge_variants)};file2_merged:{file2_merge_count}", 
                          'gender_variants_merged_file2_authority')
    
    def detect_encoding(self, file_path):
        """Detect file encoding"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # Read entire file to test encoding
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                return encoding
            except UnicodeDecodeError:
                continue
        return 'utf-8'  # fallback
    
    def read_file1(self):
        """Read and process file 1 (species and synonyms)"""
        print("Processing file 1: species and synonyms...")
        encoding = self.detect_encoding(self.file1_path)
        print(f"Detected encoding for file 1: {encoding}")
        
        with open(self.file1_path, 'r', encoding=encoding) as f:
            for line_num, line in enumerate(f, 1):
                original_line = line.rstrip('\n\r')
                
                # Skip empty lines
                if not original_line.strip():
                    self.log_change('file1', line_num, original_line, '', 'empty_line_removed')
                    continue
                
                # Basic cleanup
                line = self.clean_basic_formatting(original_line)
                if line != original_line.rstrip('\n\r'):
                    self.log_change('file1', line_num, original_line, line, 'whitespace_removed')
                
                # Fix Unicode
                unicode_fixed = self.fix_unicode(line)
                if unicode_fixed != line:
                    self.log_change('file1', line_num, line, unicode_fixed, 'unicode_fixed')
                    line = unicode_fixed
                
                # Parse line
                parts = line.split(';') if line else ['']
                if not parts[0].strip():
                    self.log_change('file1', line_num, original_line, '', 'malformed_line')
                    continue
                
                valid_name = parts[0].strip()
                synonyms = [s.strip() for s in parts[1:] if s.strip()]
                
                # Process subgenus in valid name
                original_valid = valid_name
                valid_name, additional_synonyms = self.process_subgenus_name(valid_name)
                if valid_name != original_valid:
                    self.log_change('file1', line_num, original_valid, valid_name, 'subgenus_processed')
                    synonyms.extend(additional_synonyms)
                
                # Process subgenus in synonyms
                processed_synonyms = []
                for syn in synonyms:
                    syn_standard, syn_additional = self.process_subgenus_name(syn)
                    processed_synonyms.append(syn_standard)
                    if syn_additional:
                        processed_synonyms.extend(syn_additional)
                        if syn != syn_standard or syn_additional:
                            self.log_change('file1', line_num, syn, 
                                          f"{syn_standard};{';'.join(syn_additional)}", 
                                          'subgenus_processed')
                
                synonyms = processed_synonyms                
                # Remove synonyms that match valid name (case insensitive)
                original_syn_count = len(synonyms)
                synonyms = [s for s in synonyms if s.lower() != valid_name.lower()]
                if len(synonyms) != original_syn_count:
                    self.log_change('file1', line_num, f"synonyms: {original_syn_count}", 
                                  f"synonyms: {len(synonyms)}", 'synonym_removed')
                
                # Remove duplicate synonyms
                unique_synonyms = []
                seen = set()
                for syn in synonyms:
                    if syn.lower() not in seen:
                        unique_synonyms.append(syn)
                        seen.add(syn.lower())
                
                # Store or merge with existing
                valid_name_lower = valid_name.lower()
                if valid_name_lower in self.file1_data:
                    # Merge synonyms with existing
                    existing_synonyms = self.file1_data[valid_name_lower][1]
                    all_synonyms = existing_synonyms + unique_synonyms
                    # Remove duplicates again
                    final_synonyms = []
                    seen = set()
                    for syn in all_synonyms:
                        if syn.lower() not in seen:
                            final_synonyms.append(syn)
                            seen.add(syn.lower())
                    
                    self.file1_data[valid_name_lower] = (valid_name, final_synonyms)
                    self.log_change('file1', line_num, f"duplicate: {valid_name}", 
                                  f"merged: {len(final_synonyms)} synonyms", 'duplicate_merged')
                else:
                    self.file1_data[valid_name_lower] = (valid_name, unique_synonyms)    
    def read_file2(self):
        """Read and process file 2 (species and taxonomy)"""
        print("Processing file 2: species and taxonomy...")
        encoding = self.detect_encoding(self.file2_path)
        print(f"Detected encoding for file 2: {encoding}")
        
        with open(self.file2_path, 'r', encoding=encoding) as f:
            for line_num, line in enumerate(f, 1):
                original_line = line.rstrip('\n\r')
                
                # Skip empty lines
                if not original_line.strip():
                    self.log_change('file2', line_num, original_line, '', 'empty_line_removed')
                    continue
                
                # Basic cleanup
                line = self.clean_basic_formatting(original_line)
                if line != original_line.rstrip('\n\r'):
                    self.log_change('file2', line_num, original_line, line, 'whitespace_removed')
                
                # Fix Unicode
                unicode_fixed = self.fix_unicode(line)
                if unicode_fixed != line:
                    self.log_change('file2', line_num, line, unicode_fixed, 'unicode_fixed')
                    line = unicode_fixed
                
                # Parse line
                parts = line.split(';') if line else ['']
                if not parts[0].strip():
                    self.log_change('file2', line_num, original_line, '', 'malformed_line')
                    continue
                
                valid_name = parts[0].strip()
                
                # Process subgenus in valid name
                original_valid = valid_name
                valid_name, _ = self.process_subgenus_name(valid_name)
                if valid_name != original_valid:
                    self.log_change('file2', line_num, original_valid, valid_name, 'subgenus_processed')
                
                # First pass: Check if this is a family-only line (like "Chironomidae;;;;;;;;;;;;;;;;;;;")
                if len(parts) > 1 and all(not part.strip() for part in parts[1:]):
                    # This is a family-only line with empty taxonomy fields
                    # Skip processing but don't add to removed records as these are handled correctly
                    self.log_change('file2', line_num, original_line, '', 'family_only_line_skipped')
                    continue
                
                # Clean taxonomy: Strip everything after family (ending in "idae")
                cleaned_parts = [valid_name]  # Start with species name
                original_parts = parts[1:] if len(parts) > 1 else []
                
                # Process up to 4 taxonomy fields: phylum, class, order, family
                taxonomy_fields = []
                family_found = False
                
                for i, part in enumerate(original_parts[:4]):  # Only look at first 4 taxonomy fields
                    field = part.strip()
                    taxonomy_fields.append(field)
                    
                    # Check if this field is a family (ends with "idae")
                    if field and field.endswith('idae'):
                        family_found = True
                        break
                
                # If we found a family but don't have 4 complete taxonomy fields, 
                # we need to ensure proper positioning
                if family_found and len(taxonomy_fields) < 4:
                    # If taxonomy is incomplete, we need to insert empty fields to maintain proper order
                    # Standard order is: phylum, class, order, family
                    if len(taxonomy_fields) == 3:  # phylum, class, family (missing order)
                        # Insert empty order field
                        taxonomy_fields = [taxonomy_fields[0], taxonomy_fields[1], '', taxonomy_fields[2]]
                        self.log_change('file2', line_num, 
                                      f"taxonomy: {';'.join(original_parts[:3])}", 
                                      f"taxonomy: {';'.join(taxonomy_fields)}", 
                                      'order_field_inserted')
                    elif len(taxonomy_fields) == 2:  # phylum, family (missing class and order)
                        # Insert empty class and order fields
                        taxonomy_fields = [taxonomy_fields[0], '', '', taxonomy_fields[1]]
                        self.log_change('file2', line_num, 
                                      f"taxonomy: {';'.join(original_parts[:2])}", 
                                      f"taxonomy: {';'.join(taxonomy_fields)}", 
                                      'class_order_fields_inserted')
                    elif len(taxonomy_fields) == 1:  # family only (missing phylum, class, order)
                        # Insert empty phylum, class, and order fields
                        taxonomy_fields = ['', '', '', taxonomy_fields[0]]
                        self.log_change('file2', line_num, 
                                      f"taxonomy: {original_parts[0]}", 
                                      f"taxonomy: {';'.join(taxonomy_fields)}", 
                                      'phylum_class_order_fields_inserted')
                
                # Pad to exactly 4 fields (phylum, class, order, family)
                while len(taxonomy_fields) < 4:
                    taxonomy_fields.append('')
                
                # Only keep first 4 taxonomy fields (strip trailing data)
                taxonomy = taxonomy_fields[:4]
                
                # Log if we stripped trailing data
                if len(original_parts) > 4 or (len(original_parts) == 4 and any(original_parts[i] != taxonomy[i] for i in range(len(original_parts)))):
                    original_taxonomy_str = ';'.join(original_parts) if original_parts else ''
                    cleaned_taxonomy_str = ';'.join(taxonomy)
                    self.log_change('file2', line_num, 
                                  f"taxonomy: {original_taxonomy_str}", 
                                  f"taxonomy: {cleaned_taxonomy_str}", 
                                  'trailing_data_stripped')
                
                # Skip entries with NO higher taxonomy at all (completely empty beyond name)
                # Only remove if ALL taxonomy fields are empty
                has_any_taxonomy = any(t.strip() for t in taxonomy)
                if not has_any_taxonomy:
                    # Store the removed record
                    self.removed_records.append(original_line)
                    self.log_change('file2', line_num, original_line, '', 'incomplete_taxonomy_removed')
                    continue
                
                # Handle duplicates
                valid_name_lower = valid_name.lower()
                if valid_name_lower in self.file2_data:
                    # Log conflict for manual resolution
                    existing_taxonomy = self.file2_data[valid_name_lower][1]
                    self.log_change('file2', line_num, 
                                  f"{valid_name};{';'.join(existing_taxonomy)}", 
                                  f"{valid_name};{';'.join(taxonomy)}", 
                                  'duplicate_entry')
                else:
                    self.file2_data[valid_name_lower] = (valid_name, taxonomy)    
    def validate_cross_file_consistency(self):
        """Validate that valid names match between files"""
        print("Validating cross-file consistency...")
        
        file1_names = set(self.file1_data.keys())
        file2_names = set(self.file2_data.keys())
        
        # Names in file1 but not file2
        missing_in_file2 = file1_names - file2_names
        for name_lower in missing_in_file2:
            actual_name = self.file1_data[name_lower][0]
            self.log_change('validation', 0, actual_name, '', 'missing_match_file2')
        
        # Names in file2 but not file1
        missing_in_file1 = file2_names - file1_names
        for name_lower in missing_in_file1:
            actual_name = self.file2_data[name_lower][0]
            self.log_change('validation', 0, actual_name, '', 'missing_match_file1')
        
        print(f"Found {len(missing_in_file2)} names missing in file2")
        print(f"Found {len(missing_in_file1)} names missing in file1")
        
        return missing_in_file1, missing_in_file2
    
    def fix_missing_match_file2(self, missing_in_file2: Set[str]):
        """
        Fix missing_match_file2 issue by removing species from file1 that don't exist in file2.
        Saves removed species to a separate file for reference.
        """
        if not missing_in_file2:
            print("No missing matches in file2 to fix.")
            return
        
        print(f"Fixing missing_match_file2 issue: Removing {len(missing_in_file2)} species from file1...")
        
        # Create output file path for removed species
        removed_file_path = self.cleaned_dir / f"all_specs_and_syn_removed_{self.timestamp}.csv"
        
        # Collect removed records
        removed_records = []
        removed_count = 0
        
        for name_lower in missing_in_file2:
            if name_lower in self.file1_data:
                actual_name, synonyms = self.file1_data[name_lower]
                
                # Format the record as it would appear in the original file
                if synonyms:
                    record = f"{actual_name};{';'.join(synonyms)}"
                else:
                    record = actual_name
                
                removed_records.append(record)
                
                # Remove from file1_data
                del self.file1_data[name_lower]
                
                self.log_change('fix_missing_file2', 0, record, '', 
                              'removed_missing_match_file2')
                removed_count += 1
        
        # Write removed records to file
        if removed_records:
            print(f"Writing {len(removed_records)} removed species to: {removed_file_path}")
            
            with open(removed_file_path, 'w', encoding='utf-8', newline='') as f:
                for record in removed_records:
                    f.write(f"{record}\n")
            
            print(f"Removed species saved to: {removed_file_path}")
        
        print(f"Removed {removed_count} species from file1 that were missing in file2")
    
    def check_if_synonym_in_file1(self, name_to_check: str) -> Tuple[bool, str]:
        """
        Check if a name exists as a synonym in any file1 record.
        Returns: (found, valid_name_it_is_synonym_of)
        """
        name_lower = name_to_check.lower()
        
        for valid_name_lower, (valid_name, synonyms) in self.file1_data.items():
            # Check if it exists as a synonym in this record
            for synonym in synonyms:
                if synonym.lower() == name_lower:
                    return True, valid_name
        
        return False, ""
    
    def fix_missing_match_file1(self, missing_in_file1: Set[str]):
        """
        Fix missing_match_file1 issue by adding valid species from file2 to file1.
        Only adds species names (not higher taxonomy), and only if they represent valid species.
        Also checks if the name already exists as a synonym in file1 - if so, removes it from file2.
        Family-only entries should already be filtered out during file2 processing.
        """
        if not missing_in_file1:
            print("No missing matches in file1 to fix.")
            return
        
        print(f"Fixing missing_match_file1 issue: Processing {len(missing_in_file1)} species...")
        
        added_count = 0
        skipped_count = 0
        synonym_match_count = 0
        
        # Track names to remove from file2 (those that match synonyms in file1)
        names_to_remove_from_file2 = []
        
        for name_lower in missing_in_file1:
            actual_name, taxonomy = self.file2_data[name_lower]
            
            # First check if this name already exists as a synonym in file1
            is_synonym, synonym_of_valid_name = self.check_if_synonym_in_file1(actual_name)
            if is_synonym:
                # This name from file2 already exists as a synonym in file1
                # Mark it for removal from file2
                names_to_remove_from_file2.append((name_lower, actual_name, taxonomy, synonym_of_valid_name))
                
                self.log_change('fix_missing_file1', 0, 
                              f"{actual_name};{';'.join(taxonomy)}", 
                              f"synonym_of:{synonym_of_valid_name}", 
                              'matched_synonym_in_file1')
                synonym_match_count += 1
                continue
            
            # Validate this is a proper species name (should have genus and species)
            name_parts = actual_name.strip().split()
            if len(name_parts) < 2:
                # This might be a higher taxonomy entry, remove it from file2
                record_line = f"{actual_name};{';'.join(taxonomy)}"
                self.removed_records.append(record_line)
                
                # Remove from file2_data
                if name_lower in self.file2_data:
                    del self.file2_data[name_lower]
                
                self.log_change('fix_missing_file1', 0, record_line, '', 
                              'removed_not_species_format')
                skipped_count += 1
                continue
            
            # Check if first part is capitalized (genus) and second is lowercase (species)
            if not (name_parts[0][0].isupper() and name_parts[1][0].islower()):
                # This might be a higher taxonomy entry, remove it from file2
                record_line = f"{actual_name};{';'.join(taxonomy)}"
                self.removed_records.append(record_line)
                
                # Remove from file2_data
                if name_lower in self.file2_data:
                    del self.file2_data[name_lower]
                
                self.log_change('fix_missing_file1', 0, record_line, '', 
                              'removed_improper_capitalization')
                skipped_count += 1
                continue
            
            # Additional check: ensure the first part looks like a genus name
            # (only letters, starts with capital)
            if not name_parts[0].isalpha():
                # Invalid genus format, remove it from file2
                record_line = f"{actual_name};{';'.join(taxonomy)}"
                self.removed_records.append(record_line)
                
                # Remove from file2_data
                if name_lower in self.file2_data:
                    del self.file2_data[name_lower]
                
                self.log_change('fix_missing_file1', 0, record_line, '', 
                              'removed_invalid_genus_format')
                skipped_count += 1
                continue
            
            # Additional check: ensure the second part looks like a species name
            # (only letters, starts with lowercase)
            if not name_parts[1].isalpha():
                # Invalid species format, remove it from file2
                record_line = f"{actual_name};{';'.join(taxonomy)}"
                self.removed_records.append(record_line)
                
                # Remove from file2_data
                if name_lower in self.file2_data:
                    del self.file2_data[name_lower]
                
                self.log_change('fix_missing_file1', 0, record_line, '', 
                              'removed_invalid_species_format')
                skipped_count += 1
                continue
            
            # Add to file1 with no synonyms (empty synonym list)
            self.file1_data[name_lower] = (actual_name, [])
            
            self.log_change('fix_missing_file1', 0, '', actual_name, 
                          'added_from_file2_missing_match')
            added_count += 1
        
        # Remove names from file2 that matched synonyms in file1
        if names_to_remove_from_file2:
            print(f"Removing {len(names_to_remove_from_file2)} names from file2 that match synonyms in file1...")
            
            for name_lower, actual_name, taxonomy, synonym_of in names_to_remove_from_file2:
                # Add to removed records for separate file
                record_line = f"{actual_name};{';'.join(taxonomy)}"
                self.removed_records.append(record_line)
                
                # Remove from file2_data
                if name_lower in self.file2_data:
                    del self.file2_data[name_lower]
                
                self.log_change('fix_missing_file1', 0, record_line, 
                              f"removed_matched_synonym:{synonym_of}", 
                              'removed_matched_synonym_in_file1')
        
        print(f"Added {added_count} valid species to file1")
        print(f"Removed {synonym_match_count} species from file2 (matched synonyms in file1)")
        if skipped_count > 0:
            print(f"Removed {skipped_count} entries from file2 (invalid species format)")
    
    
    def remove_synonyms_that_are_valid_species(self):
        """
        Remove any synonyms in file1 that are also valid species (exist as valid names).
        This prevents valid species from being listed as synonyms of other species.
        """
        print("Removing synonyms that are valid species...")
        
        # Create a set of all valid species names (lowercase) from both files
        valid_species = set()
        valid_species.update(self.file1_data.keys())
        valid_species.update(self.file2_data.keys())
        
        synonyms_removed = 0
        records_modified = 0
        
        # Check each valid name's synonyms
        for valid_name_lower, (valid_name, synonyms) in self.file1_data.items():
            original_synonym_count = len(synonyms)
            
            # Filter out synonyms that are valid species
            filtered_synonyms = []
            removed_synonyms = []
            
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                
                # If this synonym is also a valid species, remove it
                if synonym_lower in valid_species:
                    removed_synonyms.append(synonym)
                    synonyms_removed += 1
                else:
                    filtered_synonyms.append(synonym)
            
            # Update the record if any synonyms were removed
            if removed_synonyms:
                self.file1_data[valid_name_lower] = (valid_name, filtered_synonyms)
                records_modified += 1
                
                # Log the change
                removed_list = ';'.join(removed_synonyms)
                self.log_change('file1', 0, 
                              f"{valid_name};{original_synonym_count}_synonyms", 
                              f"{valid_name};{len(filtered_synonyms)}_synonyms", 
                              f'removed_valid_species_synonyms:{removed_list}')
        
        print(f"Removed {synonyms_removed} synonyms that were valid species from {records_modified} records")
    
    def log_duplicate_synonyms(self):
        """
        Log when a synonym is used for more than one valid species.
        This helps identify potential data quality issues.
        """
        print("Checking for duplicate synonyms across different valid species...")
        
        # Build a map: synonym_lower -> [(valid_name, valid_name_lower), ...]
        synonym_usage = defaultdict(list)
        
        for valid_name_lower, (valid_name, synonyms) in self.file1_data.items():
            for synonym in synonyms:
                synonym_lower = synonym.lower()
                synonym_usage[synonym_lower].append((valid_name, valid_name_lower))
        
        # Find synonyms used by multiple valid species
        duplicate_synonyms_found = 0
        total_conflicts = 0
        
        for synonym_lower, valid_species_list in synonym_usage.items():
            if len(valid_species_list) > 1:
                duplicate_synonyms_found += 1
                
                # Get the actual synonym name (use first occurrence for display)
                actual_synonym = ""
                for valid_name_lower, (valid_name, synonyms) in self.file1_data.items():
                    for syn in synonyms:
                        if syn.lower() == synonym_lower:
                            actual_synonym = syn
                            break
                    if actual_synonym:
                        break
                
                # Create list of valid species using this synonym
                species_list = [valid_name for valid_name, _ in valid_species_list]
                species_str = ';'.join(species_list)
                
                # Log this duplicate usage
                self.log_change('duplicate_synonym_check', 0, 
                              f"synonym:{actual_synonym}", 
                              f"used_by:{species_str}", 
                              f'duplicate_synonym_usage_count:{len(valid_species_list)}')
                
                total_conflicts += len(valid_species_list)
                
                print(f"  Synonym '{actual_synonym}' is used by {len(valid_species_list)} valid species: {species_list}")
        
        if duplicate_synonyms_found > 0:
            print(f"Found {duplicate_synonyms_found} synonyms used by multiple valid species (total {total_conflicts} conflicts)")
        else:
            print("No duplicate synonym usage found")

    def write_cleaned_files(self):
        """Write cleaned data to output files"""
        print("Writing cleaned files...")
        
        # Write file 1
        with open(self.file1_output, 'w', encoding='utf-8', newline='') as f:
            for name_lower in sorted(self.file1_data.keys()):
                valid_name, synonyms = self.file1_data[name_lower]
                if synonyms:
                    f.write(f"{valid_name};{';'.join(synonyms)}\n")
                else:
                    f.write(f"{valid_name}\n")
        
        # Write file 2
        with open(self.file2_output, 'w', encoding='utf-8', newline='') as f:
            for name_lower in sorted(self.file2_data.keys()):
                valid_name, taxonomy = self.file2_data[name_lower]
                f.write(f"{valid_name};{';'.join(taxonomy)}\n")
    
    def write_removed_records(self):
        """Write removed records to separate file"""
        if not self.removed_records:
            print("No records were removed due to incomplete taxonomy.")
            return
        
        print(f"Writing {len(self.removed_records)} removed records to: {self.removed_output}")
        
        with open(self.removed_output, 'w', encoding='utf-8', newline='') as f:
            for record in self.removed_records:
                f.write(f"{record}\n")
        
        print(f"Removed records saved to: {self.removed_output}")
            
    def write_log(self):
        """Write modification log to TSV file"""
        print("Writing log file...")
        
        with open(self.log_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, delimiter='\t', 
                                  fieldnames=['file', 'line_number', 'original_text', 
                                            'updated_text', 'modification_notes'])
            writer.writeheader()
            writer.writerows(self.log_entries)
        
        print(f"Log written to: {self.log_path}")
        print(f"Total modifications logged: {len(self.log_entries)}")
    
    def write_summary(self):
        """Write summary of cleaning results to markdown file"""
        print("Writing summary file...")
        
        with open(self.summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# Data Cleaning Results Summary\n\n")
            f.write(f"**Run Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"## Files Processed\n")
            f.write(f"- Input file 1: `{self.file1_path.name}`\n")
            f.write(f"- Input file 2: `{self.file2_path.name}`\n")
            f.write(f"- Output file 1: `{self.file1_output.name}`\n")
            f.write(f"- Output file 2: `{self.file2_output.name}`\n")
            f.write(f"- Removed records: `{self.removed_output.name}`\n")
            f.write(f"- Log file: `{self.log_path.name}`\n\n")
            
            f.write(f"## Results\n")
            f.write(f"- **File 1:** {len(self.file1_data)} unique species processed\n")
            f.write(f"- **File 2:** {len(self.file2_data)} unique species processed\n")
            f.write(f"- **Removed records:** {len(self.removed_records)} (incomplete taxonomy)\n")
            f.write(f"- **Total modifications:** {len(self.log_entries)}\n\n")
            
            # Count modification types
            mod_counts = {}
            for entry in self.log_entries:
                note = entry['modification_notes']
                mod_counts[note] = mod_counts.get(note, 0) + 1
            
            if mod_counts:
                f.write(f"## Modification Types\n")
                for mod_type, count in sorted(mod_counts.items()):
                    f.write(f"- **{mod_type}:** {count}\n")
                f.write(f"\n")
            
            f.write(f"## Details\n")
            f.write(f"For detailed logs, see: `{self.log_path.name}`\n")
        
        print(f"Summary written to: {self.summary_path}")
    
    def run_pipeline(self):
        """Execute the complete cleaning pipeline"""
        print("Starting data cleaning pipeline...")
        print(f"Input files:")
        print(f"  File 1: {self.file1_path}")
        print(f"  File 2: {self.file2_path}")
        print(f"Output files:")
        print(f"  File 1: {self.file1_output}")
        print(f"  File 2: {self.file2_output}")
        print(f"  Removed: {self.removed_output}")
        print(f"  Log: {self.log_path}")
        print()
        
        # Phase 1: Read and process files
        self.read_file1()
        self.read_file2()
        
        # Phase 2: Fix taxonomy mismatches using majority rule
        self.fix_taxonomy_mismatches()
        
        # Phase 3: Merge gender variants
        self.merge_gender_variants()
        
        # Phase 4: Validate consistency and fix missing matches
        missing_in_file1, missing_in_file2 = self.validate_cross_file_consistency()
        
        # Phase 5: Fix missing match issues
        self.fix_missing_match_file1(missing_in_file1)
        self.fix_missing_match_file2(missing_in_file2)
        
        # Phase 6: Remove synonyms that are valid species
        print("\nPhase 6: Removing synonyms that are valid species...")
        self.remove_synonyms_that_are_valid_species()
        
        # Phase 7: Check for duplicate synonyms
        print("\nPhase 7: Checking for duplicate synonym usage...")
        self.log_duplicate_synonyms()
        
        # Phase 8: Write outputs
        print("\nPhase 8: Writing outputs...")
        self.write_cleaned_files()
        self.write_removed_records()
        self.write_log()
        self.write_summary()
        
        print("\nPipeline completed successfully!")
        print(f"File 1: {len(self.file1_data)} unique species processed")
        print(f"File 2: {len(self.file2_data)} unique species processed")
        print(f"Total modifications: {len(self.log_entries)}")


def main():
    """Main entry point"""
    # Use relative path - assumes script is run from gaplist-data directory or its subdirectories
    base_path = Path(__file__).parent.parent  # Go up from data_cleaning_pipeline to gaplist-data
    
    cleaner = SpeciesDataCleaner(str(base_path))
    cleaner.run_pipeline()


if __name__ == "__main__":
    main()
