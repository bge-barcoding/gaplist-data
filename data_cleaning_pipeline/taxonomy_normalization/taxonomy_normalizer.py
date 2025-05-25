#!/usr/bin/env python3
"""
Taxonomy Normalization System - SMART Enhanced Version
=====================================================

This module provides comprehensive taxonomy normalization with three modes:
1. Majority Rule: Use internal data consensus
2. GBIF Validation: Use external GBIF backbone taxonomy (SMART - only conflicted species)
3. Hybrid: Combine both approaches intelligently

ENHANCEMENT: GBIF mode now only queries species with actual taxonomy conflicts,
dramatically reducing API calls from 150K+ to typically <10K.
"""

import time
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
from pathlib import Path
import json

from .gbif_validator import GBIFTaxonomyValidator


class TaxonomyMode(Enum):
    """Taxonomy normalization modes."""
    MAJORITY_RULE = "majority_rule"
    GBIF_ONLY = "gbif_only"
    HYBRID = "hybrid"


class TaxonomyConflict:
    """Represents a taxonomy conflict that needs resolution."""
    
    def __init__(self, species_name: str, taxonomy_field: str):
        self.species_name = species_name
        self.taxonomy_field = taxonomy_field  # 'phylum', 'class', 'order', or 'family'
        self.variants = Counter()  # Count of each taxonomy value
        self.affected_species = defaultdict(list)  # Which species have each value
        
    def add_variant(self, taxonomy_value: str, species_with_this_value: str):
        """Add a taxonomy variant and the species that has it."""
        if taxonomy_value.strip():  # Only add non-empty values
            self.variants[taxonomy_value] += 1
            self.affected_species[taxonomy_value].append(species_with_this_value)
    
    @property
    def total_count(self) -> int:
        """Total number of species with this conflict."""
        return sum(self.variants.values())
    
    @property
    def majority_value(self) -> str:
        """The taxonomy value with the most votes."""
        if not self.variants:
            return ""
        return self.variants.most_common(1)[0][0]
    
    @property
    def majority_count(self) -> int:
        """Number of species supporting the majority value."""
        if not self.variants:
            return 0
        return self.variants.most_common(1)[0][1]
    
    @property
    def confidence(self) -> float:
        """Confidence level of majority rule (0-1)."""
        if self.total_count == 0:
            return 0.0
        return self.majority_count / self.total_count
    
    @property
    def is_conflicted(self) -> bool:
        """True if there are multiple taxonomy values."""
        return len(self.variants) > 1
    
    def get_minority_species(self) -> List[str]:
        """Get list of species that don't follow the majority rule."""
        majority = self.majority_value
        minority_species = []
        
        for taxonomy_value, species_list in self.affected_species.items():
            if taxonomy_value != majority:
                minority_species.extend(species_list)
        
        return minority_species


class TaxonomyNormalizer:
    """
    SMART Comprehensive taxonomy normalization system.
    
    Supports three modes:
    - Majority Rule: Use consensus from internal data
    - GBIF Only: Validate ONLY conflicted species against GBIF backbone (SMART)
    - Hybrid: Use majority rule for high-confidence cases, GBIF for uncertain ones (SMART)
    
    ENHANCEMENT: GBIF validation now only queries species involved in actual conflicts.
    """
    
    def __init__(self, mode: TaxonomyMode = TaxonomyMode.HYBRID, 
                 gbif_cache_file: Optional[str] = None,
                 confidence_threshold: float = 0.8):
        """Initialize taxonomy normalizer."""
        self.mode = mode
        self.confidence_threshold = confidence_threshold
        self.log_entries = []
        
        # Initialize GBIF validator if needed
        if mode in [TaxonomyMode.GBIF_ONLY, TaxonomyMode.HYBRID]:
            cache_file = gbif_cache_file or "taxonomy_normalization/gbif_cache.json"
            self.gbif_validator = GBIFTaxonomyValidator(
                rate_limit_delay=0.2,
                cache_file=cache_file
            )
        else:
            self.gbif_validator = None
        
        # Analysis results
        self.conflicts = {}  # genus -> {field -> TaxonomyConflict}
        self.resolution_stats = defaultdict(int)
    
    def analyze_taxonomy_conflicts(self, file2_data: Dict[str, Tuple[str, List[str]]]) -> Dict[str, Dict[str, TaxonomyConflict]]:
        """Analyze taxonomy conflicts across all genera."""
        print("Analyzing taxonomy conflicts...")
        
        # Group species by genus
        genus_groups = defaultdict(list)
        for name_lower, (actual_name, taxonomy) in file2_data.items():
            name_parts = actual_name.strip().split()
            if len(name_parts) >= 2:
                genus = name_parts[0]
                genus_groups[genus.lower()].append((actual_name, taxonomy))
        
        # Analyze conflicts within each genus
        conflicts = {}
        taxonomy_fields = ['phylum', 'class', 'order', 'family']
        
        for genus_lower, species_list in genus_groups.items():
            genus_conflicts = {}
            
            # Check each taxonomy field for conflicts
            for field_idx, field_name in enumerate(taxonomy_fields):
                conflict = TaxonomyConflict(genus_lower, field_name)
                
                # Collect all values for this field
                for species_name, taxonomy in species_list:
                    if field_idx < len(taxonomy) and taxonomy[field_idx].strip():
                        conflict.add_variant(taxonomy[field_idx].strip(), species_name)
                
                # Only store if there's actually a conflict
                if conflict.is_conflicted:
                    genus_conflicts[field_name] = conflict
            
            if genus_conflicts:
                conflicts[genus_lower] = genus_conflicts
        
        self.conflicts = conflicts
        
        # Print summary
        total_conflicts = sum(len(genus_conflicts) for genus_conflicts in conflicts.values())
        print(f"Found {total_conflicts} taxonomy conflicts across {len(conflicts)} genera")
        
        return conflicts
    
    def get_conflicted_species_set(self, file2_data: Dict) -> Set[str]:
        """Get the set of all species involved in taxonomy conflicts."""
        conflicts = self.analyze_taxonomy_conflicts(file2_data)
        
        conflicted_species = set()
        for genus, genus_conflicts in conflicts.items():
            for field_name, conflict in genus_conflicts.items():
                for species_list in conflict.affected_species.values():
                    conflicted_species.update(species_list)
        
        return conflicted_species
    
    def normalize_taxonomy(self, file1_data: Dict, file2_data: Dict) -> Tuple[Dict, Dict]:
        """Normalize taxonomy using the selected mode."""
        print(f"Starting SMART taxonomy normalization in {self.mode.value} mode...")
        
        if self.mode == TaxonomyMode.MAJORITY_RULE:
            return self._normalize_majority_rule_only(file1_data, file2_data)
        elif self.mode == TaxonomyMode.GBIF_ONLY:
            return self._normalize_gbif_only_smart(file1_data, file2_data)
        else:  # HYBRID
            return self._normalize_hybrid_smart(file1_data, file2_data)
    
    def _normalize_majority_rule_only(self, file1_data: Dict, file2_data: Dict) -> Tuple[Dict, Dict]:
        """Apply majority rule normalization only."""
        print("Applying majority rule normalization...")
        
        conflicts = self.analyze_taxonomy_conflicts(file2_data)
        changes_made = 0
        
        for genus, genus_conflicts in conflicts.items():
            for field_name, conflict in genus_conflicts.items():
                # Always apply majority rule
                majority_value = conflict.majority_value
                minority_species = conflict.get_minority_species()
                
                print(f"  {genus} {field_name}: {conflict.majority_count}/{conflict.total_count} -> {majority_value}")
                
                # Update minority species to use majority taxonomy
                for species_name in minority_species:
                    species_lower = species_name.lower()
                    if species_lower in file2_data:
                        actual_name, taxonomy = file2_data[species_lower]
                        old_taxonomy = taxonomy.copy()
                        
                        # Update the specific field
                        field_idx = ['phylum', 'class', 'order', 'family'].index(field_name)
                        if field_idx < len(taxonomy):
                            taxonomy[field_idx] = majority_value
                            file2_data[species_lower] = (actual_name, taxonomy)
                            changes_made += 1
                            
                            self._log_change('majority_rule', species_name, 
                                           f"{field_name}:{old_taxonomy[field_idx]}", 
                                           f"{field_name}:{majority_value}",
                                           f'majority_rule_applied_confidence_{conflict.confidence:.2f}')
                
                self.resolution_stats['majority_rule_applied'] += len(minority_species)
        
        print(f"Majority rule normalization complete: {changes_made} changes made")
        return file1_data, file2_data
    
    def _normalize_gbif_only_smart(self, file1_data: Dict, file2_data: Dict) -> Tuple[Dict, Dict]:
        """Apply GBIF validation ONLY to species with taxonomy conflicts. SMART VERSION."""
        print("Applying SMART GBIF-only normalization (conflicted species only)...")
        
        if not self.gbif_validator:
            raise RuntimeError("GBIF validator not initialized")
        
        # Step 1: Get only conflicted species
        conflicted_species = self.get_conflicted_species_set(file2_data)
        conflicted_species_list = list(conflicted_species)
        
        total_species = len(file2_data)
        conflicted_count = len(conflicted_species_list)
        saved_queries = total_species - conflicted_count
        
        print(f"SMART GBIF: Found {conflicted_count} species with taxonomy conflicts")
        print(f"Total species in dataset: {total_species:,}")
        print(f"Species that need GBIF validation: {conflicted_count:,}")
        print(f"API calls saved by smart filtering: {saved_queries:,} ({(saved_queries/total_species)*100:.1f}%)")
        
        if not conflicted_species_list:
            print("No conflicted species found - no GBIF validation needed!")
            return file1_data, file2_data
        
        # Build enhanced hints for better GBIF matching
        kingdom_hints = {}
        family_hints = {}
        for species_name in conflicted_species_list:
            species_lower = species_name.lower()
            if species_lower in file2_data:
                actual_name, taxonomy = file2_data[species_lower]
                
                # Add kingdom hint from phylum
                if len(taxonomy) > 0 and taxonomy[0].strip():
                    phylum = taxonomy[0].strip()
                    if phylum in ['Arthropoda', 'Mollusca', 'Cnidaria', 'Chordata', 'Porifera']:
                        kingdom_hints[actual_name.lower()] = 'Animalia'
                    elif phylum in ['Tracheophyta', 'Bryophyta', 'Marchantiophyta']:
                        kingdom_hints[actual_name.lower()] = 'Plantae'
                    elif phylum in ['Ascomycota', 'Basidiomycota', 'Chytridiomycota']:
                        kingdom_hints[actual_name.lower()] = 'Fungi'
                
                # Add family hint if available
                if len(taxonomy) > 3 and taxonomy[3].strip():
                    family_hints[actual_name.lower()] = taxonomy[3].strip()
        
        print(f"Validating {conflicted_count} conflicted species with GBIF...")
        print(f"Using {len(kingdom_hints)} kingdom hints and {len(family_hints)} family hints")
        
        # Batch validate only conflicted species
        def progress_callback(current, total, successful):
            if current % 10 == 0:
                print(f"  Progress: {current}/{total} species, {successful} successful matches")
        
        gbif_results = self.gbif_validator.batch_validate(
            conflicted_species_list, 
            kingdom_hints=kingdom_hints,
            family_hints=family_hints,
            progress_callback=progress_callback
        )
        
        # Apply GBIF results to conflicted species
        changes_made = 0
        for species_name, gbif_data in gbif_results.items():
            species_lower = species_name.lower()
            if species_lower in file2_data:
                actual_name, current_taxonomy = file2_data[species_lower]
                
                # Build new taxonomy from GBIF
                new_taxonomy = [
                    gbif_data.get('phylum', ''),
                    gbif_data.get('class', ''),
                    gbif_data.get('order', ''),
                    gbif_data.get('family', '')
                ]
                
                # Only update if GBIF has meaningful data and it differs from current
                if any(new_val and new_val.strip() for new_val in new_taxonomy):
                    # Check if GBIF data is actually different/better
                    should_update = False
                    for i, (new_val, current_val) in enumerate(zip(new_taxonomy, current_taxonomy)):
                        if new_val and new_val.strip() and new_val != current_val:
                            should_update = True
                            break
                    
                    if should_update:
                        file2_data[species_lower] = (actual_name, new_taxonomy)
                        changes_made += 1
                        
                        self._log_change('gbif_smart_validation', species_name,
                                       f"taxonomy:{';'.join(current_taxonomy)}",
                                       f"taxonomy:{';'.join(new_taxonomy)}",
                                       f'gbif_validated_confidence_{gbif_data.get("confidence", 0)}')
        
        self.resolution_stats['gbif_queries_made'] = len(conflicted_species_list)
        self.resolution_stats['gbif_queries_saved'] = saved_queries
        self.resolution_stats['gbif_successful_matches'] = len(gbif_results)
        self.resolution_stats['gbif_changes_applied'] = changes_made
        
        print(f"SMART GBIF normalization complete:")
        print(f"   Queries made: {len(conflicted_species_list):,}")
        print(f"   Queries saved: {saved_queries:,}")
        print(f"   Successful matches: {len(gbif_results)}")
        print(f"   Changes applied: {changes_made}")
        
        if self.gbif_validator:
            self.gbif_validator.print_stats()
        
        return file1_data, file2_data
    
    def _normalize_hybrid_smart(self, file1_data: Dict, file2_data: Dict) -> Tuple[Dict, Dict]:
        """Apply hybrid normalization strategy with smart GBIF usage."""
        print("Applying SMART hybrid normalization strategy...")
        
        # Step 1: Analyze conflicts
        conflicts = self.analyze_taxonomy_conflicts(file2_data)
        
        # Step 2: Separate high-confidence vs low-confidence conflicts
        high_confidence_conflicts = []
        low_confidence_conflicts = []
        
        for genus, genus_conflicts in conflicts.items():
            for field_name, conflict in genus_conflicts.items():
                if conflict.confidence >= self.confidence_threshold:
                    high_confidence_conflicts.append((genus, field_name, conflict))
                else:
                    low_confidence_conflicts.append((genus, field_name, conflict))
        
        print(f"  High confidence conflicts (majority rule): {len(high_confidence_conflicts)}")
        print(f"  Low confidence conflicts (GBIF validation): {len(low_confidence_conflicts)}")
        
        # Step 3: Apply majority rule to high-confidence conflicts
        majority_changes = 0
        for genus, field_name, conflict in high_confidence_conflicts:
            majority_value = conflict.majority_value
            minority_species = conflict.get_minority_species()
            
            print(f"    {genus} {field_name}: {conflict.confidence:.1%} confidence -> {majority_value}")
            
            for species_name in minority_species:
                species_lower = species_name.lower()
                if species_lower in file2_data:
                    actual_name, taxonomy = file2_data[species_lower]
                    old_taxonomy = taxonomy.copy()
                    
                    field_idx = ['phylum', 'class', 'order', 'family'].index(field_name)
                    if field_idx < len(taxonomy):
                        taxonomy[field_idx] = majority_value
                        file2_data[species_lower] = (actual_name, taxonomy)
                        majority_changes += 1
                        
                        self._log_change('hybrid_majority', species_name,
                                       f"{field_name}:{old_taxonomy[field_idx]}",
                                       f"{field_name}:{majority_value}",
                                       f'hybrid_majority_rule_confidence_{conflict.confidence:.2f}')
        
        # Step 4: Use GBIF ONLY for low-confidence conflicts (SMART)
        gbif_changes = 0
        if low_confidence_conflicts and self.gbif_validator:
            # Collect ONLY species involved in low-confidence conflicts
            uncertain_species = set()
            for genus, field_name, conflict in low_confidence_conflicts:
                for species_list in conflict.affected_species.values():
                    uncertain_species.update(species_list)
            
            uncertain_species_list = list(uncertain_species)
            total_species = len(file2_data)
            
            print(f"  Validating {len(uncertain_species_list)} uncertain species with GBIF...")
            print(f"  Smart filtering: Only {len(uncertain_species_list)} of {total_species:,} species need GBIF validation")
            
            # Build hints for better GBIF matching
            kingdom_hints = {}
            family_hints = {}
            for species_name in uncertain_species_list:
                species_lower = species_name.lower()
                if species_lower in file2_data:
                    _, taxonomy = file2_data[species_lower]
                    
                    # Add kingdom hint from phylum
                    if len(taxonomy) > 0 and taxonomy[0].strip():
                        phylum = taxonomy[0].strip()
                        if phylum in ['Arthropoda', 'Mollusca', 'Cnidaria', 'Chordata']:
                            kingdom_hints[species_name.lower()] = 'Animalia'
                        elif phylum in ['Tracheophyta', 'Bryophyta']:
                            kingdom_hints[species_name.lower()] = 'Plantae'
                    
                    # Add family hint if available
                    if len(taxonomy) > 3 and taxonomy[3].strip():
                        family_hints[species_name.lower()] = taxonomy[3].strip()
            
            def progress_callback(current, total, successful):
                if current % 10 == 0:
                    print(f"    GBIF progress: {current}/{total} species, {successful} matches")
            
            gbif_results = self.gbif_validator.batch_validate(
                uncertain_species_list,
                kingdom_hints=kingdom_hints,
                family_hints=family_hints,
                progress_callback=progress_callback
            )
            
            # Apply GBIF results where confidence is high
            for species_name, gbif_data in gbif_results.items():
                if gbif_data.get('confidence', 0) >= 80:  # High GBIF confidence
                    species_lower = species_name.lower()
                    if species_lower in file2_data:
                        actual_name, current_taxonomy = file2_data[species_lower]
                        
                        # Build new taxonomy from GBIF
                        new_taxonomy = [
                            gbif_data.get('phylum', ''),
                            gbif_data.get('class', ''),
                            gbif_data.get('order', ''),
                            gbif_data.get('family', '')
                        ]
                        
                        # Apply GBIF taxonomy if it's meaningful
                        if any(new_val and new_val.strip() for new_val in new_taxonomy):
                            file2_data[species_lower] = (actual_name, new_taxonomy)
                            gbif_changes += 1
                            
                            self._log_change('hybrid_gbif', species_name,
                                           f"taxonomy:{';'.join(current_taxonomy)}",
                                           f"taxonomy:{';'.join(new_taxonomy)}",
                                           f'hybrid_gbif_validated_confidence_{gbif_data.get("confidence", 0)}')
            
            self.resolution_stats['gbif_queries_made'] = len(uncertain_species_list)
            self.resolution_stats['gbif_queries_saved'] = total_species - len(uncertain_species_list)
        
        # Update statistics
        self.resolution_stats['majority_rule_applied'] = majority_changes
        self.resolution_stats['gbif_changes_applied'] = gbif_changes
        self.resolution_stats['high_confidence_conflicts'] = len(high_confidence_conflicts)
        self.resolution_stats['low_confidence_conflicts'] = len(low_confidence_conflicts)
        
        print(f"SMART Hybrid normalization complete:")
        print(f"   Majority rule changes: {majority_changes}")
        print(f"   GBIF validation changes: {gbif_changes}")
        if self.gbif_validator:
            queries_saved = self.resolution_stats.get('gbif_queries_saved', 0)
            print(f"   GBIF queries saved by smart filtering: {queries_saved:,}")
        
        if self.gbif_validator:
            self.gbif_validator.print_stats()
        
        return file1_data, file2_data
    
    def _log_change(self, source: str, species: str, original: str, updated: str, note: str):
        """Log a taxonomy normalization change."""
        self.log_entries.append({
            'source': source,
            'species': species,
            'original': original,
            'updated': updated,
            'note': note
        })
    
    def get_normalization_report(self) -> Dict:
        """Generate a comprehensive normalization report."""
        report = {
            'mode': self.mode.value,
            'statistics': self.resolution_stats.copy(),
            'conflicts_analyzed': len(self.conflicts),
            'changes_logged': len(self.log_entries),
            'smart_gbif_enabled': True
        }
        
        if self.gbif_validator:
            report['gbif_stats'] = self.gbif_validator.get_stats()
        
        # Add conflict breakdown
        if self.conflicts:
            conflict_breakdown = {}
            for genus, genus_conflicts in self.conflicts.items():
                conflict_breakdown[genus] = {
                    field: {
                        'total_species': conflict.total_count,
                        'majority_value': conflict.majority_value,
                        'confidence': conflict.confidence,
                        'variants': dict(conflict.variants)
                    }
                    for field, conflict in genus_conflicts.items()
                }
            report['conflict_breakdown'] = conflict_breakdown
        
        return report
    
    def save_normalization_report(self, file_path: str):
        """Save normalization report to JSON file."""
        report = self.get_normalization_report()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Normalization report saved to: {file_path}")
    
    def print_summary(self):
        """Print a summary of normalization results."""
        print(f"\nTaxonomy Normalization Summary ({self.mode.value.upper()}):")
        print("=" * 60)
        
        for stat_name, count in self.resolution_stats.items():
            formatted_name = stat_name.replace('_', ' ').title()
            if 'saved' in stat_name.lower() or 'queries' in stat_name.lower():
                print(f"  {formatted_name}: {count:,}")
            else:
                print(f"  {formatted_name}: {count}")
        
        if self.conflicts:
            print(f"\nConflicts by Genus (Top 10):")
            for genus, genus_conflicts in list(self.conflicts.items())[:10]:
                print(f"  {genus}: {len(genus_conflicts)} fields")
                for field, conflict in genus_conflicts.items():
                    print(f"    {field}: {conflict.confidence:.1%} confidence, {conflict.total_count} species")
            
            if len(self.conflicts) > 10:
                print(f"  ... and {len(self.conflicts) - 10} more genera")
        
        # Show GBIF efficiency gains
        queries_made = self.resolution_stats.get('gbif_queries_made', 0)
        queries_saved = self.resolution_stats.get('gbif_queries_saved', 0)
        if queries_made > 0 or queries_saved > 0:
            total_possible = queries_made + queries_saved
            efficiency = (queries_saved / total_possible * 100) if total_possible > 0 else 0
            print(f"\nSMART GBIF Efficiency:")
            print(f"  Total species: {total_possible:,}")
            print(f"  Queries made: {queries_made:,}")
            print(f"  Queries saved: {queries_saved:,} ({efficiency:.1f}%)")
