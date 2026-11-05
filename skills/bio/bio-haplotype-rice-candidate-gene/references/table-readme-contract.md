# Table README Contract

Use this contract whenever a customer release contains `table/` or nested Source Data directories.

## Required layout

- Every directory at or below `table/` must contain `README.md`, including `table/` itself.
- Each README documents every immediate child file and subdirectory. It does not need to list itself.
- Documentation is generated from the delivered files, not copied from an older gene or inferred only from filenames.
- Chinese is the default explanation language; delivered filenames, sheet names, column names, figure text, and publication-table text remain English unless the project contract says otherwise.

## Required content

For every directory README:

1. State the directory purpose and analysis scope.
2. List every immediate child and give a concise purpose.
3. State shared reference build, coordinate system, counting unit, denominator, and missing-value rules where relevant.

For every real table (`.xlsx`, `.tsv`, or `.csv`):

1. State what one data row represents.
2. For `.xlsx`, document every sheet separately and record the actual header row.
3. Reproduce every delivered column name exactly.
4. For every column, define meaning, unit or denominator, allowed categorical values, and permitted missing values.
5. Distinguish accession counts, phased chromosome-copy counts, genotype-pattern counts, and variant/window counts.
6. State the frequency denominator. For per-site call-rate tables, disclose that the denominator can vary by site.
7. State the reference build and coordinate convention. Preserve software-native window coordinates rather than silently converting them.
8. Mark descriptive or derived fields as such; a README must not upgrade them to causal, selective, evolutionary, or breeding evidence.
9. Render the field dictionary as a four-column Markdown table with the exact headings `Column`, `Definition`, `Unit / denominator / allowed values`, and `Missing-value rule`, unless the project validator declares another schema before generation. The generator and validator must implement the same declared schema.

## Special formats

- VCF: document the 8 fixed VCF fields, `FORMAT`, `GT`, all sample columns as a class, allele-index mapping, phasing separator, missing GT, sample/site counts, `.tbi`, and conversion audit. Use the literal header name `#CHROM`, not a normalized `CHROM`. Derive sample/site counts independently from each delivered file; different analysis roles may have different valid sample counts after documented exclusions.
- Conversion audit: define `metric` and `value`, then explain each project-specific metric value.
- Newick: state tip unit, inference method, marker scope, whether branch lengths are meaningful, and that a regional tree is not a genome-wide phylogeny.
- SHA256 manifest: state the line format and whether listed paths are internal provenance paths or delivered files.
- Index/binary helper files: explain their role and explicitly state that they are not independent biological result tables.

## Build and QA procedure

1. Read actual workbook sheets and headers with a structured parser such as `openpyxl`.
2. Read TSV/CSV headers with `csv`; read VCF headers directly from the compressed file.
3. Bind each observed column to a curated field definition. Fail generation if any column lacks a definition.
4. Freeze the README schema shared by generator and validator before writing. Run a small representative fixture through both whenever either implementation changes; a generator-produced README that the validator rejects is a release-blocking interface defect.
5. Write an internal schema inventory containing relative path, sheet, header row, row count, column count, and ordered columns.
6. Write an internal README manifest with relative path, byte size, SHA256, and immediate-child count.
7. Run `templates/scripts/qa_table_readme_contract.py` or an equivalent project QA.
8. Require all checks to pass before ZIP creation, then compare ZIP members and SHA256 values against the release tree.

## Acceptance rules

- Recursive README coverage is complete.
- Every immediate child is named in its directory README.
- Every workbook, sheet, and actual column is represented by a non-empty data-dictionary row.
- Every TSV/CSV column is represented by a non-empty data-dictionary row.
- VCF documentation covers fixed fields, `FORMAT/GT`, sample columns, `.tbi`, and conversion audit.
- No `TODO`, `TBD`, placeholder, donor-gene residue, or guessed field definition remains.
- A documentation-only revision is released under a new version. All scientific payload files must remain byte-identical to the accepted source release except the explicitly revised README files.
