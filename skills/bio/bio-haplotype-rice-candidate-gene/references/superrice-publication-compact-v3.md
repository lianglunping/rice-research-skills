# Superrice Publication-Compact v3

## Contents

1. Scope
2. Required source contract
3. Primary and unfiltered haplotype sets
4. XI/GJ inference
5. Figure and table contract
6. Publication QA
7. Delivery and evidence boundary
8. Adaptation procedure

## Scope

Use `formal_mode=superrice_publication_compact_v3` when the client wants a concise, publication-oriented result focused on XI/GJ differentiation, with two composite main figures, separately reusable panels, supplementary figures, and both filtered and unfiltered haplotype tables.

This mode is a presentation and inference derivative of a validated 万份水稻 source run. It must not silently redo extraction, phasing, site QC, sample QC, or group recoding. Keep the source result read-only and record its absolute path plus SHA256 provenance.

Do not use this mode before the source run has passed the site-QC sensitivity, retained-cohort, canonical VCF, population-genetic, and reference-CDS checks described in `superrice-reference-compatible-v2.md`.

## Required Source Contract

The source result must provide:

- all phased chromosome-copy haplotype counts, patterns, and sample assignments;
- a detailed sample manifest with `sample_id`, subgroup, XI/GJ/Or/Undefined group, and Original Area;
- post-QC SNP+InDel variant table and the full interval genotype representation;
- canonical biallelic SNP VCF plus XI and GJ sample lists;
- sample-retention table by detailed group;
- vcftools Pi, Tajima's D, and pairwise weighted-Fst outputs;
- detailed primary-transcript annotation and reference FASTA/CDS FASTA.

The compact run must verify that the assembled primary-transcript CDS exactly matches the configured reference CDS. Do not infer coding consequences from a mismatched transcript.

## Primary And Unfiltered Haplotype Sets

Produce two explicit result versions:

1. `primary`: the concise figure set and primary summary table.
2. `all`: all phased chromosome-copy haplotypes with no haplotype-frequency filter, retained in TSV/XLSX and the rank-abundance supplement.

Default primary rule:

```text
carrier_accession_count >= 30
AND
max(XI_chromosome_frequency, GJ_chromosome_frequency) > 0.005
```

The frequency comparison is strictly `> 0.5%`; equality to 0.5% does not pass. Record every haplotype in `primary_haplotype_threshold_audit.tsv/xlsx`, including both input values, operator, thresholds, and selection result.

Keep units separate:

- use unique accessions for the `n >= 30` support threshold and statistical inference;
- use phased chromosome copies for XI/GJ descriptive frequencies and the `>0.5%` screen;
- report both accession count and chromosome-copy count in the tables.

The 0.5%/30 rule is the default for this compact mode, not a universal biological boundary. Any change must be predeclared in config and rerun through the threshold audit.

## XI/GJ Inference

For each primary haplotype, define accession carrier status as presence on either chromosome copy. Build a 2 x 2 carrier/non-carrier table for XI and GJ retained complete-case accessions.

Required statistics:

- two-sided Fisher exact test;
- Benjamini-Hochberg adjustment across the primary haplotype set;
- XI-minus-GJ carrier-rate difference;
- Newcombe hybrid-score 95% confidence interval from Wilson intervals.

Recompute these values independently in QA from source assignments. Do not use chromosome copies as independent observations in Fisher tests or confidence intervals.

For site-level differentiation, use canonical biallelic SNPs and `vcftools --weir-fst-pop` with explicit XI/GJ keep lists and the configured missingness threshold. Do not add a MAF filter to the site-frequency-spectrum analyses unless separately justified.

## Figure And Table Contract

### Main Figure 1: Haplotype Architecture And XI/GJ Distribution

- **a:** primary-transcript model, sites varying among primary haplotypes, A/C/G/T/DEL/INS/REF matrix, detailed-subgroup chromosome-copy counts, and unique carrier accessions;
- **b:** XI-GJ accession carrier-rate differences with Newcombe 95% CIs and BH-adjusted q values;
- **c:** detailed XI/GJ subgroup chromosome-copy frequencies.

### Main Figure 2: Relationships And Local Differentiation

- **a:** primary-haplotype minimum spanning tree; node area reflects chromosome-copy count, sectors show group composition, and edge labels are full-pattern Hamming distances;
- **b:** site-level XI-GJ allele-frequency contrast and Weir-Cockerham Fst aligned to promoter/gene structure;
- **c:** local XI/GJ Pi, Tajima's D, and weighted Fst.

### Supplementary Figures

- **S1:** rank-abundance plot of every unfiltered haplotype, with every primary haplotype labelled;
- **S2:** true neighbor-joining tree from the full-pattern distance matrix, with branch lengths shown to scale and Newick delivered;
- **S3:** Original Area centroid distribution, explicitly stating that points are not accession sampling coordinates.

Store each composite figure in its own directory, with reusable panels in `panels/`:

```text
figure/
├── Fig1_HaplotypeArchitecture_XI_GJ/
│   ├── Fig1_HaplotypeArchitecture_XI_GJ.pdf
│   ├── Fig1_HaplotypeArchitecture_XI_GJ.png
│   ├── Fig1_SourceData.xlsx
│   └── panels/
├── Fig2_HaplotypeRelationships_XI_GJ/
│   ├── Fig2_HaplotypeRelationships_XI_GJ.pdf
│   ├── Fig2_HaplotypeRelationships_XI_GJ.png
│   ├── Fig2_SourceData.xlsx
│   └── panels/
└── Supplementary/
```

Required workbooks:

- `Table1_HaplotypeSummary.xlsx`: publication table, primary set, top 20 counts, all unfiltered haplotypes, subgroup counts/frequencies, denominators, carrier assignments, and threshold audit;
- `Table2_XI_GJ_Differentiation.xlsx`: carrier tests and site-level differentiation;
- `Table3_VariantMatrix.xlsx`: site information, primary variable matrix, primary all-site matrix, and all-haplotype all-site matrix;
- `TableS1_PopulationGenetics.xlsx`: Pi, Tajima's D, Fst, and source summaries;
- one Source Data workbook for each main figure and one for supplementary figures.

## Publication QA

All 11 PDF/PNG pairs must pass programmatic checks and row-by-row manual review.

Programmatic checks must include:

- source SHA256 unchanged and exact reference-CDS match;
- expected accession, chromosome-copy, haplotype, variant, and matrix dimensions;
- two chromosome copies per retained accession;
- strict threshold recomputation, including synthetic equality and just-above-threshold cases;
- independent Fisher, BH, and Newcombe recomputation;
- MST edge count `N-1` and NJ tip-set equality;
- 600-dpi PNG pixel dimensions;
- non-empty PDF text layers and dynamic chromosome/gene labels;
- only configured Arial or Times New Roman family, with an italic font for gene labels;
- English-only figure text;
- no embedded raster objects in PDFs, including rasterized colour bars;
- internal all-PASS QA, ZIP integrity, the four-entry top-level whitelist, and forbidden internal-file exclusion.

Generate contact sheets for review, but inspect full-size panels whenever labels are dense. The review input must be written after inspection and must contain `relative_stem`, `review_focus`, `visual_status`, and `action_taken`. Never auto-populate `PASS` from file existence.

## Delivery And Evidence Boundary

Use English figure text, italic gene labels, Arial or Times New Roman, white background, and no panel grid. Export vector PDF and 600-dpi PNG. The customer ZIP may include both formats when `delivery_include_png=TRUE`. Follow DEC-027/028: include the formal post-QC SNP+InDel VCF, `.tbi`, and conversion audit under `table/SourceData/VCF/`; exclude scripts, logs, internal QA, environment files, temporary tests, and raw genotype matrices.

Allowed conclusion: specific haplotype carrier-frequency shifts can coexist with low regional Fst in the retained complete-case cohort.

Do not claim strong regional differentiation, selection, domestication origin, introgression, functional causality, or breeding value from these figures alone. State unequal group retention and missing callable masks where applicable.

## Adaptation Procedure

1. Copy `templates/config-superrice-publication-compact-v3.tsv` to the project `config/publication_compact_v3.tsv`.
2. Fill every `REPLACE_*` field from validated source TSVs; never estimate expected counts.
3. Copy `templates/scripts/publication_compact_v3/` into the project scripts directory.
4. Set `CONFIG`, `PY_PREFIX`, `NGS_PREFIX`, and optional `REVIEW_INPUT` explicitly.
5. Run through plotting/contact-sheet generation, inspect all figures, and create the manual review TSV.
6. Run the full driver. It must execute release, QA, final release, and verify-only QA in that order.
7. Accept the result only when final internal QA has no FAIL rows and verify-only QA confirms the customer ZIP's four-entry whitelist and internal-artifact exclusions.

Entry point:

```bash
CONFIG=/absolute/project/config/publication_compact_v3.tsv \
PY_PREFIX=<ABSOLUTE_PROJECT_PYTHON_PREFIX> \
NGS_PREFIX=<ABSOLUTE_PROJECT_NGS_PREFIX> \
bash scripts/publication_compact_v3/run_publication_compact_v3.sh
```
