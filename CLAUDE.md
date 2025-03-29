# CLAUDE.md - Assistant Instructions

## Repository Overview
This is primarily a data repository containing gap list data in various formats (XML, CSV).

## Commands
- Data validation: `perl -c src/get_arise_from_gap_list.pl` (syntax check only)
- Visual Basic compile: `vbc src/load_data.vb` (if VB compiler is installed)

## Code Style Guidelines
- For Perl:
  - Use strict and warnings pragmas
  - Follow camelCase for variables
  - Document functions with comments
- For Visual Basic:
  - Follow Microsoft VB naming conventions (PascalCase for procedures)
  - Keep procedures focused on single tasks

## Data Organization
- Keep raw data in the data/ directory
- Document data formats in README.md files
- Maintain data integrity when processing
- Avoid duplicate records (see recent commits)

## Error Handling
- Validate input data before processing
- Log errors during data transformation