# Pipeline Decisions Reference

Key analytical decisions from the reference implementation (LOC_Os11g37890 + LOC_Os10g36703).
These are non-obvious choices that must be preserved when adapting to new genes.

---

## DEC-001: 3K RGP per-site bad-rate ≤ 3% (site QC)

**Scope and decision**: For the validated 3K RGP workflow, after standard missing/MAF filter, remove sites where `(missing_n + het_n) / total_n > 0.03`.

**Why**: Rice (Oryza sativa) is a selfing crop. Heterozygous genotype calls in 3K RGP data are predominantly sequencing/alignment artifacts, not true biological heterozygosity. A 3% threshold is empirically validated for this dataset.

**Effect on reference gene**: LOC_Os11g37890 went from 104 → 34 variants (67% removal); retained samples 1359 → 2327 (+71%). The higher sample retention is the primary benefit.

**Code location**: `prepare_formal_inputs_siteqc.R` function `run_haplotype()` lines 258–280.

**Threshold**: 0.03. Do not relax to 0.05 without client discussion. This is not a 万份水稻 default; see DEC-013.

---

## DEC-005: Report post_site_qc_variant_count (not pre-QC)

**Decision**: In Figure_Legends.md and Results_Discussion.md, the variant count must come from `haplotype_key_metrics.tsv` field `post_site_qc_variant_count`, not `filtered_haplotype_interval_variant_count`.

**Why**: The manuscript describes "variants used for haplotype construction." That is the post-QC number. Pre-QC numbers only belong in the Methods section when describing the QC procedure itself.

**Concrete example**: LOC_Os11g37890 had 104 pre-QC and 34 post-QC. The figure legend must say "34 SNPs", not "104 SNPs".

**Code location**: `formal_full_analysis.R` — ensure `variant_count` reads `post_site_qc_variant_count`.

---

## DEC-007: Delivery package content strategy

**Decision**: Delivery zip contains:
- PDF figures in every mode; include matching PNG only when the project contract sets `delivery_include_png=TRUE`
- Project-contract XLSX summary tables; do not hardcode the count
- The all-PASS QA and figure visual-review XLSX when the client needs to audit publication readiness
- 方法描述.md, 图注.md, 结果与讨论.md

Always exclude R/Python/shell scripts, logs, raw genotype files, and TSV files. Classic thesis delivery excludes PNG by default; publication-compact delivery may include declared 600-dpi PNG pairs. Keep complete reproducibility artifacts in the project `results/` and `release/` directories rather than the customer zip.

**Why**: Client is writing a thesis, not running the pipeline. They need figures + methods description in Chinese academic register. Code is internal IP.

---

## DEC-002: Figure aesthetics

**H001 haplotype color**: `#0F7FBF` (blue). H001 was originally red, which clashed with K5 XI color.

**FigD clade labels**: `geom_cladelab(label="", fontsize=0, barsize=4.0)` — color bars only, no text labels.

**var_gene grid**: `panel.grid.major = element_blank()` — remove grid lines.

---

## DEC-003: Multi-gene standardization

When the same client has multiple genes under analysis, all genes must use the identical pipeline version, figure aesthetics, and site-QC selection policy. For a common dataset and comparable input quality, use the same predeclared threshold; if sensitivity audits require different thresholds, retain every audit, state the rationale in Methods, and do not conceal the difference.

---

## DEC-004: cv() function resolution

The `cv()` helper in `prepare_formal_inputs_siteqc.R` was used at line 557 but not always defined. Fix: replace `cv("gene_chr_gff")` with the direct contract access `contract$gene_chr_gff`. Both `cv()` (defined in `qa_formal_release.R`) and direct access are semantically equivalent.

---

## DEC-006: Dynamic run_id in formal_full_analysis.R

```r
run_id <- basename(result_dir)
release_id <- basename(release_dir)
```

These two lines must appear near the top of `formal_full_analysis.R`. REPRODUCIBILITY.md and README.md templates must reference these variables, not hardcode a run ID string.

---

## DEC-008: Dynamic figure chromosome labels and PDF text QA

**Decision**: All figure chromosome labels must be generated from the gene contract, not copied as literal strings from a donor gene.

Required pattern:

```r
chromosome_title <- paste("Chromosome", gene_chr_vcf)
chromosome_sentence <- paste("chromosome", gene_chr_vcf)
```

Use `chromosome_title` for population-genetic x-axis labels and `chromosome_sentence` for labels such as `Position on chromosome N (bp)`.

**Why**: A copied plotting template can produce numerically correct figures with visibly wrong chromosome labels. Rendering PDFs to PNG proves that files are non-empty, but it does not verify semantic figure text.

**QA requirement**: `qa_formal_release.R` must run `pdftotext` on all release PDFs and fail if any extracted text contains an unexpected rice chromosome label (`Chromosome N`, `chromosome N`, `ChrN`) where `N != gene_chr_vcf`.

**Do not** manually edit exported PDFs. Fix the plotting source and re-run the formal pipeline.

---

## DEC-009: Domestication-style common haplotype network threshold

**Decision**: For Zhang et al. 2023-style haplotype network analysis, define common haplotypes as haplotypes with frequency `> 0.005` among retained phased haplotype chromosomes.

**Why**: This preserves the paper's `>0.5%` common-haplotype concept while keeping it separate from the existing thesis-delivery major-haplotype threshold (`n >= 30`).

**Implementation**: `common_haplotype_frequency_min=0.005` in `formal_release_config.tsv`; `build_common_haplotype_network.R --frequency-min 0.005`.

**Reporting rule**: Always state whether counts are sample counts or phased haplotype-chromosome counts. A diploid sample contributes up to two haplotype chromosomes.

---

## DEC-010: 万份水稻 phasing mode

**Decision**: If 万份水稻 genotype fields contain phased separators (`|`), treat them as already phased and do not run Beagle by default.

**Why**: The current `superrice` genotype tables are wide genotype matrices with values such as `0|0`, `0|1`, `1|1`, and `.|.`. Re-phasing these data would add compute cost and another dependency without improving a pre-phased input.

**Fallback**: If required genotypes contain unphased heterozygotes (`0/1`) and `phasing_mode=auto`, stop and either run Beagle explicitly (`phasing_mode=beagle`) or mark those samples/sites as excluded. Do not silently convert unphased heterozygotes into phased haplotypes.

---

## DEC-011: Wild/cultivar group recoding for 万份水稻

**Decision**: Use `Species Information` in the local 万份水稻 metadata as the first-pass grouping field.

| Analysis group | Default regex |
|---|---|
| Wild | `^Or|Or-|rufipogon|nivara` |
| Cultivar | `^XI|^GJ|^cA|^cB` |
| Undefined | everything else, including `Os-undefined` |

**Why**: The local metadata contains both detailed rice subgroups (`XI1`, `GJ5`, `Or1`, `Or2`, `Or3`) and undefined labels. Collapsing to Wild/Cultivar/Undefined makes the network comparable to domestication analyses while preserving ambiguous samples instead of forcing a biological label.

---

## DEC-012: Haplotype network evidence boundary

**Decision**: Common-haplotype networks are descriptive outputs. They cannot alone prove domestication origin, introgression, or selective sweep.

**Required wording**: Use phrases such as "haplotype structure", "wild/cultivar composition", and "descriptive network pattern". Avoid causal language unless supported by independent selection statistics, sampling design, and functional or breeding evidence.

---

## DEC-013: 万份水稻 site-QC threshold sensitivity and retained-cohort boundary

**Decision**: Do not apply a fixed 3K site-bad-rate cutoff to 万份水稻 genotype tables. Evaluate a documented threshold grid before formal haplotype construction, then select the most stringent cutoff that yields nonzero, analyzable SNP+InDel sites under the predeclared project rule.

**Required outputs**: `site_bad_rate_threshold_sensitivity.tsv/xlsx` must report threshold, retained SNP count, retained InDel count, total retained variants, and complete-sample count. `sample_qc_status.tsv/xlsx` must support a by-`analysis_group` retention table with complete, skipped, total, and complete rate.

**Interpretation rule**: Complete-case haplotypes describe only samples retained after site and sample QC. If any metadata group has zero or strongly unequal retention, state this in Methods/Results and do not use group-frequency patterns as unbiased wild/cultivar/undefined comparisons, selection evidence, or population-history evidence.

**Why**: 万份水稻 wide genotype tables can have data-quality and missingness patterns that differ from 3K VCFs. Reusing a numeric cutoff without sensitivity and cohort-retention evidence can create either an empty analysis or a biased retained cohort.

---

## DEC-014: Publication visual review and one-class allele matrices

**Decision**: Publication acceptance requires more than PDF/PNG existence, high resolution, and successful rendering. Record a manual review for every figure and verify sparse or apparently blank panels against their source tables.

**One-class matrix rule**: If all displayed major-haplotype cells are `REF/0` (or another single allele class), annotate the figure or its delivered legend with the exact number of cells, haplotypes, and variant sites. Keep it as a supplementary/supporting figure unless it directly answers the manuscript question.

**Why**: A matrix can be biologically valid yet look like a plotting failure. The explanation must travel with the delivery, not remain only in an internal QA note.

---

## DEC-015: Separate grouping modes for 万份水稻

**Decision**: Record `grouping_mode` and do not silently reuse one recoding for every biological question.

- `domestication_binary`: Wild/Cultivar/Undefined, used for a domestication-style composition summary.
- `reference_subgroup`: `XI* -> XI`, `GJ* -> GJ`, `Or* -> Or`, all other labels -> Undefined, used for the reference-compatible formal release.

Do not force `cA`, `cB`, `Os-undefined`, or missing labels into XI/GJ/Or without an explicit, separately justified mapping.

---

## DEC-016: Phased chromosome-copy haplotypes and display threshold separation

**Decision**: When complete accession-level homozygous genotypes are absent or severely depleted but phased alleles are available, construct haplotypes from chromosome copies. Report sample count and haplotype-chromosome count separately.

Major haplotypes remain defined by the predeclared threshold, normally chromosome-copy `n >= 30`. In reference-compatible figures, include every major haplotype and then add frequency-ranked non-major haplotypes to top 80. Top 80 is a display rule, not a second biological threshold.

---

## DEC-017: Standard population-genetic estimators

**Decision**: Convert 万份水稻 SNP genotypes to a validated canonical biallelic VCF and use established tools:

- Pi: `vcftools --window-pi`
- Tajima's D: `vcftools --TajimaD`
- Fst: `vcftools --weir-fst-pop`, reporting `WEIGHTED_FST`

For pairwise Fst, create an explicit combined keep list for the two populations before applying `--max-missing`. Never present a hand-written weighted average as Weir-Cockerham Fst.

---

## DEC-018: SFS filtering, callable masks, and real all/filter ranges

**Decision**: Pi/Tajima's D should not receive a MAF filter unless the analysis plan provides a specific reason, because MAF filtering truncates the site-frequency spectrum. Record the missingness threshold and callable-mask availability.

If no callable-site mask exists, state that vcftools uses the nominal window length and keep Pi/Tajima's D interpretation descriptive. Predeclare a broad `all` range and a narrower `filter` range; QA must confirm that their x spans and included-window counts differ.

---

## DEC-019: MST network and NJ tree are different outputs

**Decision**: A minimum spanning haplotype network cannot be relabeled as `FigD` or an NJ tree. Build the NJ tree from a symmetric unique-haplotype distance matrix with `ape::nj`, retain the branch-length Newick, and verify the tip set.

When extreme branches make a distance-scaled circular plot unreadable, a topology-only circular cladogram is allowed only if the figure says `branch lengths not to scale` and the complete Newick/distance table remains in the release.

---

## DEC-020: Reference-style gene model and allele matrices

**Decision**: Parse a primary transcript into promoter, 5' UTR, CDS, 3' UTR, ordinary intron, and splice-boundary classes. Keep all post-QC sites in complete supplemental views. The default view may hide ordinary intron sites and cap informative functional sites by a recorded display limit.

Allele matrices must use A/C/G/T plus DEL/INS or a clearly defined other category. Long insertion strings may be abbreviated in the figure, but full alleles must remain in TSV/XLSX tables.

---

## DEC-021: Original Area centroid maps and publication acceptance

**Decision**: If accession latitude/longitude is absent, a map may use a versioned `Original Area -> centroid` table. Record mapping method, confidence, mapped chromosome count, and mapped rate. Figure subtitles must say that the points are area centroids and not accession sampling coordinates.

A zero-retained group must appear explicitly as an empty facet or documented not-applicable panel. Publication acceptance requires manual review of every figure at export scale, with `figure`, `review_focus`, `visual_status`, and `action_taken` fields.

---

## DEC-022: Publication-compact primary haplotype rule

**Decision**: In `superrice_publication_compact_v3`, define the primary set by the joint rule `carrier accession n >= 30 AND max(XI chromosome frequency, GJ chromosome frequency) > 0.005`.

The frequency operator is strict: exactly 0.5% does not pass. Write a threshold-audit row for every haplotype and retain synthetic equality, just-above-threshold, and below-count cases in QA.

**Why**: The accession count avoids displaying poorly supported patterns, while the subgroup frequency screen keeps XI/GJ-relevant haplotypes that may be diluted in the whole cohort. Neither condition alone is sufficient for this mode.

---

## DEC-023: XI/GJ carrier inference uses accessions

**Decision**: Use unique accession carrier/non-carrier status for XI/GJ inference. Apply two-sided Fisher exact tests, BH correction across the primary set, and Newcombe hybrid-score 95% intervals for XI-minus-GJ carrier-rate differences.

Phased chromosome-copy frequencies remain descriptive and may be used in the primary screen, but the two copies from one accession are not independent inferential observations.

---

## DEC-024: Dual output and compact figure hierarchy

**Decision**: Deliver both a thresholded primary set and an unfiltered all-haplotype set. Use the primary set for two composite main figures and retain all haplotypes in TSV/XLSX plus a rank-abundance supplementary figure.

Each main figure gets its own directory containing the composite PDF/PNG, a `panels/` directory, a figure-specific Source Data workbook, and a legend. This preserves manuscript-ready concision without discarding panel-level reuse.

---

## DEC-025: Pure-vector publication graphics

**Decision**: Publication-compact PDFs must retain text layers and contain no embedded raster objects. Continuous colour bars must use vector rectangles rather than the default raster display. Export matching PNG at 600 dpi.

All figure text is English; the configured font is Arial or Times New Roman; gene labels are italic. Programmatic font/text/raster checks supplement, but do not replace, full-size manual review of every exported pair.

---

## DEC-026: XI/GJ evidence boundary under low regional Fst

**Decision**: It is valid to report specific haplotype carrier-frequency shifts together with low local regional Fst when both are supported by their source tables.

Do not translate that coexistence into claims of strong regional differentiation, selection, domestication origin, introgression, functional causality, or breeding value. Keep conclusions restricted to the retained complete-case cohort and disclose unequal retention and missing callable masks.

---

## DEC-027: Deliver a formal post-QC SNP+InDel haplotype VCF

**Decision**: A 万份水稻 customer release includes a formal haplotype VCF built from every approved post-QC SNP+InDel site and every source accession. Store the bgzip VCF, tabix `.tbi`, and conversion-audit TSV under `table/SourceData/VCF/`.

This VCF is distinct from both the canonical biallelic SNP-only VCF used for population genetics and the SNP subset used for the sample tree. Neither smaller analysis VCF may be renamed or delivered as the formal haplotype source VCF.

**Validation**: Reconcile sample count, site count, SNP/InDel count, multiallelic count, CHROM/POS, REF/ALT, site order, sample order, numeric phased GT, and missing GT. Compute a deterministic normalized GT hash on the source matrix and converted VCF and require equality. Require successful bgzip parsing, tabix indexing, bcftools reading, and region query.

**Why**: The figures and haplotype tables are derived from SNP+InDel genotypes. Delivering only a tree or population-genetics SNP subset would not reproduce the formal haplotypes and could conceal excluded InDels or multiallelic alleles.

---

## DEC-028: Four-entry customer release and internal QA separation

**Decision**: The customer release and ZIP top level contain exactly `figure/`, `manuscript/`, `table/`, and `README.md`. The formal VCF files live below `table/SourceData/VCF/`.

Scripts, logs, internal QA tables/workbooks, manifests, contact sheets, environment exports, and temporary tests remain in the internal `results/` or project script/config trees. They are required for acceptance and reproducibility but are not customer-facing release contents.

**QA**: Run all scientific and rendering QA before packaging, then run a verify-only package audit. Require all internal checks to pass, `unzip -t` success, exact top-level whitelist, and absence of internal artifacts. The ZIP does not need to contain its own QA workbook.

**Precedence**: This decision supersedes earlier mode-specific delivery text that excluded every VCF or required an all-PASS QA workbook inside the customer ZIP. It does not relax scientific QA; it changes only the customer-facing package boundary.

---

## Chinese language conventions

| Avoid | Use |
|-------|-----|
| 芒稻 | 混合群（Admixture） |
| 正值 before 负值 in Tajima's D | 正值 → 平衡选择/瓶颈效应；负值 → 方向性选择/扩张 |
| 籼稻/粳稻 alone | 籼稻（Xian/Indica）/ 粳稻（Geng/Japonica） |

---

## Promoter definition (strand-aware)

For a **negative-strand gene** (strand = "-"):
- Biological upstream = higher genomic coordinate
- promoter_start = gene_end + 1
- promoter_end = gene_end + promoter_length
- analysis interval = [gene_start, gene_end + promoter_length]

For a **positive-strand gene** (strand = "+"):
- promoter_start = gene_start - promoter_length
- promoter_end = gene_start - 1
- analysis interval = [gene_start - promoter_length, gene_end]
