#!/usr/bin/env python3
"""
GBIF Taxonomy Validator
======================

This module provides functionality to validate taxonomic classifications
against the GBIF (Global Biodiversity Information Facility) backbone taxonomy.
"""

import requests
import time
import json
from typing import Dict, Optional, List, Tuple
from pathlib import Path
import logging


class GBIFTaxonomyValidator:
    """
    Validates species names and taxonomy against GBIF backbone taxonomy.
    
    Features:
    - Fuzzy matching for species names
    - Caching to avoid duplicate API calls
    - Rate limiting to be respectful to GBIF servers
    - Confidence scoring for match quality
    - Batch processing capabilities
    """
    
    def __init__(self, rate_limit_delay: float = 0.2, cache_file: Optional[str] = None):
        """
        Initialize GBIF validator.
        
        Args:
            rate_limit_delay: Seconds to wait between API calls
            cache_file: Path to cache file for storing results
        """
        self.base_url = "https://api.gbif.org/v1/species"
        self.rate_limit_delay = rate_limit_delay
        self.cache = {}
        self.cache_file = Path(cache_file) if cache_file else None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Species-Data-Cleaning-Pipeline/1.0 (https://github.com/your-repo)'
        })
        
        # Load existing cache if available
        self._load_cache()
        
        # Statistics
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'successful_matches': 0,
            'failed_matches': 0,
            'rate_limited': 0
        }
    
    def _load_cache(self):
        """Load cached results from file."""
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"Loaded {len(self.cache)} cached GBIF results from {self.cache_file}")
            except Exception as e:
                print(f"Warning: Could not load cache file {self.cache_file}: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save cached results to file."""
        if self.cache_file:
            try:
                self.cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.cache, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: Could not save cache file {self.cache_file}: {e}")
    
    def match_species(self, species_name: str, kingdom: Optional[str] = None, 
                     phylum: Optional[str] = None, family: Optional[str] = None,
                     verbose: bool = False) -> Optional[Dict]:
        """
        Query GBIF for a species and return standardized taxonomy.
        
        Args:
            species_name: Scientific name to match
            kingdom: Optional kingdom to improve matching
            phylum: Optional phylum to improve matching  
            family: Optional family to improve matching
            verbose: Include additional match details
            
        Returns:
            Dictionary with standardized taxonomy or None if no match
        """
        # Build cache key
        cache_key = self._build_cache_key(species_name, kingdom, phylum, family, verbose)
        
        # Check cache first
        if cache_key in self.cache:
            self.stats['cache_hits'] += 1
            return self.cache[cache_key]
        
        # Build query parameters
        params = {'name': species_name.strip()}
        if kingdom:
            params['kingdom'] = kingdom.strip()
        if phylum:
            params['phylum'] = phylum.strip()
        if family:
            params['family'] = family.strip()
        if verbose:
            params['verbose'] = 'true'
        
        result = None
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.stats['api_calls'] += 1
                response = self.session.get(f"{self.base_url}/match", params=params, timeout=15)
                
                if response.status_code == 429:  # Rate limited
                    self.stats['rate_limited'] += 1
                    wait_time = (2 ** attempt) * 2  # Exponential backoff
                    print(f"Rate limited by GBIF, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code == 200:
                    data = response.json()
                    result = self._parse_gbif_response(data, verbose)
                    if result:
                        self.stats['successful_matches'] += 1
                    else:
                        self.stats['failed_matches'] += 1
                    break
                    
                else:
                    print(f"GBIF API returned status {response.status_code} for {species_name}")
                    break
                    
            except requests.exceptions.Timeout:
                print(f"GBIF API timeout for {species_name} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue
                
            except Exception as e:
                print(f"GBIF query failed for {species_name}: {e}")
                break
        
        if result is None:
            self.stats['failed_matches'] += 1
        
        # Cache the result (even if None)
        self.cache[cache_key] = result
        
        # Rate limiting delay
        time.sleep(self.rate_limit_delay)
        
        return result
    
    def _build_cache_key(self, species_name: str, kingdom: Optional[str], 
                        phylum: Optional[str], family: Optional[str], verbose: bool) -> str:
        """Build a cache key from query parameters."""
        parts = [species_name.strip().lower()]
        if kingdom:
            parts.append(f"k:{kingdom.strip().lower()}")
        if phylum:
            parts.append(f"p:{phylum.strip().lower()}")
        if family:
            parts.append(f"f:{family.strip().lower()}")
        if verbose:
            parts.append("v:true")
        return "|".join(parts)
    
    def _parse_gbif_response(self, data: Dict, verbose: bool = False) -> Optional[Dict]:
        """
        Extract standardized taxonomy from GBIF response.
        
        Args:
            data: JSON response from GBIF API
            verbose: Include additional match details
            
        Returns:
            Parsed taxonomy data or None if no valid match
        """
        # Check if we got a valid match
        match_type = data.get('matchType', 'NONE')
        if match_type == 'NONE':
            return None
        
        # Extract taxonomy
        result = {
            'accepted_name': data.get('species') or data.get('scientificName', ''),
            'kingdom': data.get('kingdom', ''),
            'phylum': data.get('phylum', ''),
            'class': data.get('class', ''),  # Note: 'class' is a reserved word in Python
            'order': data.get('order', ''),
            'family': data.get('family', ''),
            'genus': data.get('genus', ''),
            'species': data.get('specificEpithet', ''),
            'confidence': data.get('confidence', 0),
            'match_type': match_type,
            'usage_key': data.get('usageKey'),
            'status': data.get('status', ''),
            'rank': data.get('rank', '')
        }
        
        # Add verbose information if requested
        if verbose:
            result.update({
                'synonym': data.get('synonym', False),
                'accepted_usage_key': data.get('acceptedUsageKey'),
                'note': data.get('note', ''),
                'issues': data.get('issues', [])
            })
        
        # Only return if we have meaningful taxonomy data
        if result['kingdom'] or result['family'] or result['genus']:
            return result
        
        return None
    
    def batch_validate(self, species_list: List[str], kingdom_hints: Optional[Dict[str, str]] = None,
                      family_hints: Optional[Dict[str, str]] = None, 
                      batch_size: int = 100, progress_callback=None) -> Dict[str, Dict]:
        """
        Validate multiple species in batches with progress tracking.
        
        Args:
            species_list: List of species names to validate
            kingdom_hints: Optional dict mapping species -> kingdom
            family_hints: Optional dict mapping species -> family
            batch_size: Number of species to process before saving cache
            progress_callback: Function to call with progress updates
            
        Returns:
            Dictionary mapping species names to validation results
        """
        results = {}
        kingdom_hints = kingdom_hints or {}
        family_hints = family_hints or {}
        
        total_species = len(species_list)
        
        for i, species_name in enumerate(species_list):
            # Get hints for this species
            kingdom = kingdom_hints.get(species_name.lower())
            family = family_hints.get(species_name.lower())
            
            # Validate species
            result = self.match_species(species_name, kingdom=kingdom, family=family)
            if result:
                results[species_name] = result
            
            # Progress reporting
            if progress_callback and (i + 1) % 10 == 0:
                progress_callback(i + 1, total_species, len(results))
            
            # Save cache periodically
            if (i + 1) % batch_size == 0:
                self._save_cache()
                print(f"Processed {i + 1}/{total_species} species, {len(results)} successful matches")
        
        # Final cache save
        self._save_cache()
        
        return results
    
    def get_stats(self) -> Dict:
        """Get validation statistics."""
        return self.stats.copy()
    
    def print_stats(self):
        """Print validation statistics."""
        print("\nGBIF Validation Statistics:")
        print(f"  API calls made: {self.stats['api_calls']}")
        print(f"  Cache hits: {self.stats['cache_hits']}")
        print(f"  Successful matches: {self.stats['successful_matches']}")
        print(f"  Failed matches: {self.stats['failed_matches']}")
        print(f"  Rate limited: {self.stats['rate_limited']}")
        
        total_queries = self.stats['api_calls'] + self.stats['cache_hits']
        if total_queries > 0:
            success_rate = (self.stats['successful_matches'] / total_queries) * 100
            cache_rate = (self.stats['cache_hits'] / total_queries) * 100
            print(f"  Success rate: {success_rate:.1f}%")
            print(f"  Cache hit rate: {cache_rate:.1f}%")
