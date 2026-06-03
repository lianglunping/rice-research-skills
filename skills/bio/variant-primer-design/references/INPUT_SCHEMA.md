# Input Schema

## Minimal Required Fields

The workflow accepts these logical fields:

- `name`
- `chrom`
- `pos`
- `ref`
- `alt`

The workflow also accepts historical aliases:

- `name`: `name`, `Name`, `marker`, `locus`, `名称`
- `chrom`: `chrom`, `CHROM`, `chr`, `染色体`
- `pos`: `pos`, `POS`, `position`, `位置`
- `ref`: `ref`, `REF`
- `alt`: `alt`, `ALT`
- `full_seq`: `full_seq`, `full_sequence`, `sequence`, `全长`
- `upstream_seq`: `upstream_seq`, `Upstream_1kb`
- `downstream_seq`: `downstream_seq`, `Downstream_1kb`
- `left_flank_len`: `left_flank_len`

## Two Supported Input Modes

### Mode A: Coordinate-Based Input

Use when the table has variant coordinates and alleles but no `full_seq`.

Required:

- `name`
- `chrom`
- `pos`
- `ref`
- `alt`
- `reference_fasta` passed on the command line

The workflow will fetch flanking sequence from the reference FASTA and construct `full_seq`.

### Mode B: Prebuilt `full_seq`

Use when the table already includes `full_seq`.

Required:

- `name`
- `chrom`
- `pos`
- `ref`
- `alt`
- `full_seq`
- either `reference_fasta` or `blast_db_prefix` for BLAST specificity screening

Recommended:

- `left_flank_len` or `upstream_seq`

If `left_flank_len` and `upstream_seq` are missing, the workflow falls back to `--assume-left-flank` and defaults to `1000`.

## Additional Columns

Additional columns are preserved in the final output unless they conflict with reserved output field names.

## Notes

- Positions are interpreted as 1-based genomic coordinates.
- `ref` must match the reference genome when a FASTA is provided.
- The workflow is designed for SNP and InDel validation tables and does not infer unsupported assay types.
