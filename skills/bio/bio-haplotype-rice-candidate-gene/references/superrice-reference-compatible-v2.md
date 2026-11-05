# 万份水稻 Reference-Compatible Formal v2

Use this mode when the customer expects the information structure of the established formal rice haplotype release rather than a short common-haplotype summary.

When the customer instead wants 1-2 manuscript-style main figures centered on XI/GJ differentiation, do not delete panels ad hoc from this 23-pair contract. First validate this source mode, then derive `superrice_publication_compact_v3` according to `superrice-publication-compact-v3.md`.

## Scope

The workflow covers:

1. Strand-aware 2 kb promoter plus gene body for phased SNP+InDel haplotypes.
2. A wider SNP-only interval for Pi, Tajima's D, Weir-Cockerham Fst, and Pi ratio.
3. Detailed gene-model and allele-matrix views.
4. A pie-node MST network and a separate true NJ tree.
5. Area-centroid maps when only `Original Area` metadata exists.
6. A 23-pair figure release, manual publication review, manifest, and customer zip.

## Required Contract

Record these fields before execution:

- gene/promoter/analysis coordinates and strand
- `site_bad_rate_threshold` plus sensitivity-table rationale
- `grouping_mode=reference_subgroup`
- `major_haplotype_min_chromosome_count`
- `display_haplotype_max` and `display_focus_site_max`
- broad all range and narrower filter range
- population-genetics window/step and missingness threshold
- MAF-filter decision and callable-mask availability
- metadata files and centroid-table version
- random seed, run ID, release ID, and delivery zip name

Never copy the validated example's threshold or coordinate ranges to a new gene. Recompute the sensitivity audit and define biologically appropriate wide/filter ranges.

## Genotype Conversion

The wide SNP tables may contain both single-base homozygous values and phased values such as `G|A`. InDel tables may use phased numeric allele indices.

Maintain three separately named VCF products:

| Role | Required content | Use |
|---|---|---|
| Formal haplotype VCF | Every approved post-QC SNP+InDel site and every source accession; numeric phased GT or `.|.` | Customer-facing source data and reproducible haplotype reconstruction |
| Population-genetics VCF | Canonical biallelic A/C/G/T SNP records only | vcftools Pi, Tajima's D, and Weir-Cockerham Fst |
| Tree SNP VCF | The predeclared SNP subset and sample cohort used for tree inference | Sample-tree construction only |

For the formal haplotype VCF:

1. Preserve source sample order, site order, CHROM/POS, REF, and complete ALT definitions.
2. Convert every nonmissing genotype to numeric phased allele indices; encode missing calls as `.|.`.
3. Retain multiallelic SNP or InDel records when they belong to the approved post-QC haplotype matrix.
4. Write a bgzip-compressed VCF, tabix index, and conversion-audit TSV under `table/SourceData/VCF/`.
5. Compare a deterministic normalized source-GT hash with the VCF-GT hash in addition to count and allele checks.

For population genetics:

1. Keep only canonical biallelic SNP rows with A/C/G/T REF and ALT.
2. Convert single bases to homozygous GT and phased base pairs to phased numeric GT.
3. Treat alleles outside REF/ALT as missing and count them in the conversion audit.
4. Require unique sample IDs, exact metadata coverage, bgzip, tabix, and VCF validation.
5. Write group lists for XI, GJ, and Or; exclude Undefined.

## Haplotype and Display Rules

- Construct complete phased chromosome-copy haplotypes from post-site-QC SNP+InDel.
- Report total samples, complete samples, skipped samples, and retention by XI/GJ/Or/Undefined.
- Define major haplotypes by chromosome-copy `n >= 30` unless the approved contract changes it.
- Include all major haplotypes, then frequency-ranked supporting haplotypes to top 80.
- Keep top-80 as a display definition only.

If any group has zero or markedly unequal retention, show that fact in tables/figures and limit group-composition language to the retained cohort.

## Population Genetics

Use SNP-only VCF and standard vcftools commands:

```bash
vcftools --gzvcf input.vcf.gz --keep XI.list --max-missing THRESHOLD \
  --window-pi WINDOW --window-pi-step STEP --out XI

vcftools --gzvcf input.vcf.gz --keep XI.list --max-missing THRESHOLD \
  --TajimaD WINDOW --out XI

cat XI.list GJ.list > XI_vs_GJ.list
vcftools --gzvcf input.vcf.gz --keep XI_vs_GJ.list --max-missing THRESHOLD \
  --weir-fst-pop XI.list --weir-fst-pop GJ.list \
  --fst-window-size WINDOW --fst-window-step STEP --out XI_vs_GJ
```

Do not MAF-filter Pi/Tajima's D unless the plan justifies the SFS change. If no callable-site mask is available, record the vcftools warning and state that nominal-window estimates are descriptive.

## Figure Contract

The validated reference-compatible set contains:

- `major_haplotype_counts`
- `haplotype_network`
- `FigD_branchColorOnly`
- `var_gene`, `var_gene_all`, `var_gene_cds`, `var_gene_promoter`
- `vat_tab`, `vat_tab_all`, `vat_tab_cds`, `vat_tab_promoter`
- `hap_map_all`, `hap_map_by_haplotype`, `hap_map_facet`
- gene-prefixed Pi, TajimaD, Fst, Pi-ratio, and all/filter views
- `local_popgen_profiles`

The default matrix should remain readable; complete all/CDS matrices may be zoomable supplemental PDFs. Long insertions may be labeled `INS` in figures while full sequences stay in tables.

## Acceptance Checks

All checks must pass:

- remote/local wide-extract SHA256 equality
- coordinate and post-QC variant-count consistency
- XI/GJ/Or/Undefined group and retained-cohort tables
- major threshold and top-80 display consistency
- detailed gene features and focus-site contract
- pairwise distance count, MST `N-1`, NJ Newick tip equality
- nonempty standard vcftools outputs and plausible weighted Fst range
- real all/filter span difference
- centroid mapping rate and coordinate disclaimer
- exactly 23 PDF/PNG pairs at the required resolution
- PDF text layer, chromosome guard, and donor-gene residue guard
- row-by-row manual visual review
- formal SNP+InDel VCF count/allele/order/phased-GT/hash validation plus bgzip/tabix/bcftools checks
- release manifest SHA256 and clean customer ZIP whose top level is exactly `figure/`, `manuscript/`, `table/`, and `README.md`
- internal all-PASS QA evidence retained outside the customer package

The formal SNP+InDel haplotype VCF cannot be replaced by the smaller canonical population-genetics VCF or the tree-input SNP VCF. Historical mode-specific instructions that excluded all VCF files or required QA workbooks inside the customer ZIP are superseded by DEC-027 and DEC-028.

## Validated Example

Use the generic scripts in `templates/scripts/reference_compatible_v2/` and verify the contract and QA surfaces against caller-supplied inputs.
