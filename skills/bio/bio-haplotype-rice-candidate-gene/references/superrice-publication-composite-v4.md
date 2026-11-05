# Superrice Publication-Composite v4

## Contents

1. Scope and source contract
2. Primary and unfiltered haplotypes
3. XI/GJ inference
4. Figure and table contract
5. Publication QA
6. Delivery and evidence boundary
7. Adaptation procedure

## Scope And Source Contract

Use `formal_mode=superrice_publication_composite_v4` when the client wants the established reference-style figures retained in substance, duplicate views removed, and the result reorganized into one or two manuscript main figures plus reusable panels and supplements.

Treat this mode as a presentation and inference derivative of a validated 万份水稻 reference-compatible run. Keep the source result read-only. Do not redo extraction, phasing, site QC, sample QC, grouping, or population-genetic windows unless the source contract fails. Record absolute source paths and SHA256 provenance.

Require source tables for all phased chromosome-copy haplotypes and assignments, detailed XI/GJ/Or/Undefined metadata, post-QC SNP+InDel sites, canonical biallelic SNP VCF, sample retention, vcftools Pi/Tajima's D/weighted Fst, top-80 network inputs, detailed gene features, Original Area centroids, and reference FASTA/CDS. Verify the assembled primary-transcript CDS exactly matches the configured reference CDS before reporting coding consequences.

## Primary And Unfiltered Haplotype Sets

Deliver both:

1. `primary`: used in concise main-figure matrix and map panels.
2. `all`: every phased chromosome-copy haplotype without a haplotype-frequency filter, retained in TSV/XLSX and the complete matrix.

Default primary rule:

```text
carrier_accession_count >= 30
AND
max(XI_chromosome_frequency, GJ_chromosome_frequency) > 0.005
```

Use strict `>`: exactly 0.5% does not pass. Audit every haplotype, and include equality, just-above-threshold, and below-count synthetic cases in tests. Keep units separate: accession carriers for `n >= 30` and inference; phased chromosome copies for subgroup frequencies and the `>0.5%` screen. This is a display rule, not a universal biological cutoff.

## XI/GJ Inference

For each primary haplotype, define accession carrier status as presence on either chromosome copy. Require:

- two-sided Fisher exact test;
- Benjamini-Hochberg correction across the primary set;
- XI-minus-GJ carrier-rate difference;
- Newcombe hybrid-score 95% CI from Wilson intervals.

Recompute all values in QA from source assignments. Never treat the two phased copies from one accession as independent inferential units. Use canonical biallelic SNPs and `vcftools --weir-fst-pop` for site Fst, with explicit XI/GJ lists and no unplanned MAF filter.

## Figure And Table Contract

Retain the reference-compatible visual grammar. Do not replace the established panels with a new compact visual system.

### Figure 1: Haplotype Architecture

- **a:** top-20 phased chromosome-copy counts, highlighting the primary set;
- **b:** original top-80 pie-node MST, with primary haplotypes labelled and outlined;
- **c:** detailed primary-transcript model and informative functional variants;
- **d:** primary-haplotype allele matrix across differentiating sites;
- **e:** primary-haplotype Original Area centroid maps.

### Figure 2: Population Genetics

- **a,b:** broad and local Pi;
- **c,d:** broad and local Tajima's D;
- **e,f:** broad and local vcftools weighted Fst.

### Supplementary Figures

- **S1:** true top-80 NJ topology; branch lengths not to scale in the circular display, with branch-length Newick delivered;
- **S2-S4:** all-site, CDS-only, and promoter-only gene/variant views;
- **S5-S7:** all-site, CDS-only, and promoter-only top-80 allele matrices;
- **S8:** area-level top-haplotype composition map;
- **S9:** XI/GJ/Or/Undefined centroid maps;
- **S10:** local Pi ratios.

Do not deliver duplicate `local_popgen_profiles` or legacy `all_filter` composites. The fixed default inventory is 2 composite main figures, 11 independent main panels, and 10 supplementary figures: 23 PDF/PNG pairs.

Store each main figure with its panels, legend, and Source Data:

```text
figure/
├── Fig1_HaplotypeArchitecture/
│   ├── Fig1_HaplotypeArchitecture.pdf
│   ├── Fig1_HaplotypeArchitecture.png
│   ├── Fig1_SourceData.xlsx
│   ├── Fig1_Legend.md
│   └── panels/
├── Fig2_PopulationGenetics/
│   ├── Fig2_PopulationGenetics.pdf
│   ├── Fig2_PopulationGenetics.png
│   ├── Fig2_SourceData.xlsx
│   ├── Fig2_Legend.md
│   └── panels/
└── Supplementary/
    └── Supplementary_SourceData.xlsx
```

Required workbooks are `Table1_HaplotypeSummary.xlsx`, `Table2_XI_GJ_Differentiation.xlsx`, `Table3_VariantMatrix.xlsx`, `TableS1_PopulationGenetics.xlsx`, and the three figure Source Data workbooks. Table 1 must include the top-20 accession carrier counts and chromosome-copy counts plus the unfiltered all-haplotype table.

## Publication QA

Require all 23 pairs to pass both programmatic and manual review:

- exact counts for complete accessions, phased copies, all/primary/display haplotypes, post-QC variants, and primary variable sites;
- strict threshold, Fisher, BH, and Newcombe recomputation;
- primary MST `N-1`, top-80 network 80 nodes/79 edges and connectedness, and NJ 80-tip equality;
- exact figure manifest and rejection of duplicate legacy views;
- 600-dpi PNG dimensions and metadata;
- single-page vector PDFs with text layers and no embedded raster objects;
- embedded Arial or Times New Roman only, allowing Symbol for mathematical glyphs, with italic gene labels;
- English-only figure text and dynamic chromosome/gene guards;
- exact workbook sheets and matrix dimensions;
- release SHA256, exact ZIP figure count, four-entry top-level whitelist, and forbidden internal-file exclusion; retain the final QA workbook internally.

Generate contact sheets after the final render. Inspect dense matrices and both composites at full export size. Write `relative_stem`, `review_focus`, `visual_status`, and `action_taken` only after inspection; never infer PASS from file existence or successful rendering.

## Delivery And Evidence Boundary

Use white backgrounds, English figure text, Arial or Times New Roman, italic gene labels, vector PDF, and 600-dpi PNG. Follow DEC-027/028: include the formal post-QC SNP+InDel VCF, `.tbi`, and conversion audit under `table/SourceData/VCF/`; exclude scripts, logs, internal QA, environment files, temporary tests, compressed raw genotype matrices, and raw data from the customer ZIP. Keep reproducibility artifacts in the internal `results/` tree and project script/config directories.

Allowed conclusion: specific haplotype carrier-frequency shifts may coexist with low regional Fst in the retained complete-case cohort.

Do not claim strong regional differentiation, selection, domestication origin, introgression, functional causality, breeding value, or population history from these outputs alone. Disclose unequal retention and unavailable callable masks.

## Adaptation Procedure

1. Copy `templates/config-superrice-publication-composite-v4.tsv` to project `config/publication_composite_v4.tsv`.
2. Fill every `REPLACE_*` value from source TSV/XLSX; do not estimate counts.
3. Copy `templates/scripts/publication_composite_v4/` into the project.
4. Set `CONFIG`, `PY_PREFIX`, `NGS_PREFIX`, and optional `REVIEW_INPUT`/`TEST_DIR`.
5. Run through plotting and contact-sheet generation; inspect every final figure and write the manual review TSV.
6. Run the complete driver. It must execute release, QA, final release, and verify-only QA in that order.
7. Accept only an all-PASS internal final QA and a verify-only package audit confirming the four-entry whitelist and absence of internal artifacts.

```bash
CONFIG=/absolute/project/config/publication_composite_v4.tsv \
PY_PREFIX=<ABSOLUTE_PROJECT_PYTHON_PREFIX> \
NGS_PREFIX=<ABSOLUTE_PROJECT_NGS_PREFIX> \
bash scripts/publication_composite_v4/run_publication_composite_v4.sh
```
