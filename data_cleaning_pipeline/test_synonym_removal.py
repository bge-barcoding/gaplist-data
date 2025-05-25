#!/usr/bin/env python3
"""
Test script to demonstrate the new synonym removal functionality.
This script creates sample data to test the two new functions:
1. remove_synonyms_that_are_valid_species()
2. log_duplicate_synonyms()
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from data_cleaning_pipeline import SpeciesDataCleaner

class TestSynonymRemoval:
    def __init__(self):
        # Create a mock cleaner without actually running the full pipeline
        self.cleaner = SpeciesDataCleaner("/tmp")  # Dummy path
        
        # Set up test data that matches your example
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test data that demonstrates the functionality"""
        
        # Test data for synonym removal:
        # - Tethyophaena silifica has synonyms including Aaptos papillata
        # - Aaptos papillata is also a valid species on its own
        # - Expected: Aaptos papillata should be removed as synonym of Tethyophaena silifica
        
        self.cleaner.file1_data = {
            # Case 1: Synonym that is also a valid species (should be removed)
            'tethyophaena silifica': ('Tethyophaena silifica', ['Aaptos papillata', 'Tuberella papillatana']),
            'aaptos papillata': ('Aaptos papillata', ['Polymastia gleneni']),
            
            # Case 2: Duplicate synonym usage (should be logged)
            'species a': ('Species A', ['Common synonym', 'Unique synonym A']),
            'species b': ('Species B', ['Common synonym', 'Unique synonym B']),
            
            # Case 3: Normal case (no issues)
            'normal species': ('Normal species', ['Normal synonym']),
        }
        
        self.cleaner.file2_data = {
            'tethyophaena silifica': ('Tethyophaena silifica', ['Phylum1', 'Class1', 'Order1', 'Family1']),
            'aaptos papillata': ('Aaptos papillata', ['Phylum2', 'Class2', 'Order2', 'Family2']),
            'species a': ('Species A', ['Phylum3', 'Class3', 'Order3', 'Family3']),
            'species b': ('Species B', ['Phylum4', 'Class4', 'Order4', 'Family4']),
            'normal species': ('Normal species', ['Phylum5', 'Class5', 'Order5', 'Family5']),
        }
        
        # Initialize log entries
        self.cleaner.log_entries = []
    
    def print_before_state(self):
        """Print the state before running the functions"""
        print("=== BEFORE PROCESSING ===")
        print("\nFile 1 data:")
        for valid_name_lower, (valid_name, synonyms) in self.cleaner.file1_data.items():
            if synonyms:
                print(f"  {valid_name};{';'.join(synonyms)}")
            else:
                print(f"  {valid_name}")
        
        print("\nFile 2 data:")
        for valid_name_lower, (valid_name, taxonomy) in self.cleaner.file2_data.items():
            print(f"  {valid_name};{';'.join(taxonomy)}")
    
    def print_after_state(self):
        """Print the state after running the functions"""
        print("\n=== AFTER PROCESSING ===")
        print("\nFile 1 data:")
        for valid_name_lower, (valid_name, synonyms) in self.cleaner.file1_data.items():
            if synonyms:
                print(f"  {valid_name};{';'.join(synonyms)}")
            else:
                print(f"  {valid_name}")
        
        print("\nFile 2 data (unchanged):")
        for valid_name_lower, (valid_name, taxonomy) in self.cleaner.file2_data.items():
            print(f"  {valid_name};{';'.join(taxonomy)}")
    
    def print_log_entries(self):
        """Print the log entries created by the functions"""
        print("\n=== LOG ENTRIES ===")
        for entry in self.cleaner.log_entries:
            print(f"  {entry['file']}: {entry['modification_notes']}")
            print(f"    Original: {entry['original_text']}")
            print(f"    Updated:  {entry['updated_text']}")
            print()
    
    def run_test(self):
        """Run the test and display results"""
        print("Testing Synonym Removal Functionality")
        print("=" * 50)
        
        self.print_before_state()
        
        print("\n" + "=" * 50)
        print("RUNNING FUNCTIONS...")
        print("=" * 50)
        
        # Run the new functions
        print("\n1. Removing synonyms that are valid species...")
        self.cleaner.remove_synonyms_that_are_valid_species()
        
        print("\n2. Checking for duplicate synonyms...")
        self.cleaner.log_duplicate_synonyms()
        
        self.print_after_state()
        self.print_log_entries()
        
        # Verify expected results
        print("=" * 50)
        print("VERIFICATION")
        print("=" * 50)
        
        # Check if Aaptos papillata was removed from Tethyophaena silifica's synonyms
        tethyo_synonyms = self.cleaner.file1_data['tethyophaena silifica'][1]
        if 'Aaptos papillata' in tethyo_synonyms:
            print("FAILED: Aaptos papillata was NOT removed from Tethyophaena silifica")
        else:
            print("SUCCESS: Aaptos papillata was removed from Tethyophaena silifica")
            print(f"   Remaining synonyms: {tethyo_synonyms}")
        
        # Check if duplicate synonym usage was logged
        duplicate_logs = [entry for entry in self.cleaner.log_entries 
                         if 'duplicate_synonym_usage' in entry['modification_notes']]
        if duplicate_logs:
            print(f"SUCCESS: Found {len(duplicate_logs)} duplicate synonym usage log entries")
        else:
            print("FAILED: No duplicate synonym usage was logged")
        
        print("\nExpected output format:")
        print("Tethyophaena silifica;Tuberella papillatana")
        print("Aaptos papillata;Polymastia gleneni")

def main():
    test = TestSynonymRemoval()
    test.run_test()

if __name__ == "__main__":
    main()
