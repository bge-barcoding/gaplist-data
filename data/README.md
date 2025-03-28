# File listing

## [Gap_list_all_updated.csv](Gap_list_all_updated.csv)

- Contains canonical species names and higher taxonomic levels compatible with BOLD.
- Encoding: `latin-1`.
- 166946 lines.
- 158360 species.
- Duplicates:
  - Hexaxonopsis romijni,
  - Asterina gibbosa,
  - Parathyasella frigida,
  - Krendowskia latissima,
  - Limnolegeria longiseta,
  - Sperchon hibernicus
## [BGE_gap_list_darwincorelike.csv](BGE_gap_list_darwincorelike.csv)

The contents of `Gap_list_all_updated.csv` representing the higher classification as an [adjaceny list](https://en.wikipedia.org/wiki/Adjacency_list)

## [all_specs_and_syn.csv](all_specs_and_syn.csv) 

For each canonical species name (first element), any synonyms (subsequent elements)

## [targetlist.csv](targetlist.csv)

a reformatted version of `Gap_list_all_updated.csv` matching the columns of the gap list web app,
generated with [../src/get_arise_from_gap_list.pl](../src/get_arise_from_gap_list.pl)

 ## [BGE_gap_list.xml](BGE_gap_list.xml)
 
 a file explaining column mappings
