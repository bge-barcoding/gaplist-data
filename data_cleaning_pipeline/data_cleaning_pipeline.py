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
        
        # Files
        self.file1_path = self.base_path / "all_specs_and_syn.csv"
        self.file2_path = self.base_path / "Gap_list_all_updated.csv"
        self.file1_output = self.base_path / "all_specs_and_syn_cleaned.csv"
        self.file2_output = self.base_path / "Gap_list_all_updated_cleaned.csv"
        self.log_path = self.base_path / f"log_{self.timestamp}.tsv"
        
        # Data storage
        self.file1_data = {}  # valid_name -> [synonyms]
        self.file2_data = {}  # valid_name -> [phylum, class, order, family]
        
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
                
                # Extract taxonomy (next 4 fields after valid name)
                taxonomy = []
                for i in range(1, min(5, len(parts))):
                    taxonomy.append(parts[i].strip() if i < len(parts) else '')
                
                # Pad to 4 fields if needed
                while len(taxonomy) < 4:
                    taxonomy.append('')
                
                # Skip entries without complete taxonomy (family subdivisions)
                # Check if we have at least Phylum, Class, Order, Family (all non-empty)
                clean_taxonomy = [t for t in taxonomy if t]
                if len(clean_taxonomy) < 4:
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
                # Only write entries with complete taxonomy (all 4 fields non-empty)
                clean_taxonomy = [t for t in taxonomy if t]
                if len(clean_taxonomy) == 4:
                    f.write(f"{valid_name};{';'.join(clean_taxonomy)}\n")    
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
    
    def run_pipeline(self):
        """Execute the complete cleaning pipeline"""
        print("Starting data cleaning pipeline...")
        print(f"Input files:")
        print(f"  File 1: {self.file1_path}")
        print(f"  File 2: {self.file2_path}")
        print(f"Output files:")
        print(f"  File 1: {self.file1_output}")
        print(f"  File 2: {self.file2_output}")
        print(f"  Log: {self.log_path}")
        print()
        
        # Phase 1: Read and process files
        self.read_file1()
        self.read_file2()
        
        # Phase 2: Validate consistency
        self.validate_cross_file_consistency()
        
        # Phase 3: Write outputs
        self.write_cleaned_files()
        self.write_log()
        
        print("\nPipeline completed successfully!")
        print(f"File 1: {len(self.file1_data)} unique species processed")
        print(f"File 2: {len(self.file2_data)} unique species processed")
        print(f"Total modifications: {len(self.log_entries)}")


def main():
    """Main entry point"""
    base_path = r"C:\GitHub\gaplist-data\data"
    
    cleaner = SpeciesDataCleaner(base_path)
    cleaner.run_pipeline()


if __name__ == "__main__":
    main()
