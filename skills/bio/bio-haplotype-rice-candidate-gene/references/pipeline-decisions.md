# Pipeline Decisions Reference

Key analytical decisions from the reference implementation (LOC_Os11g37890 + LOC_Os10g36703).
These are non-obvious choices that must be preserved when adapting to new genes.

---

## DEC-001: Per-site bad-rate ≤ 3% (site QC)

**Decision**: After standard missing/MAF filter, remove sites where `(missing_n + het_n) / total_n > 0.03`.

**Why**: Rice (Oryza sativa) is a selfing crop. Heterozygous genotype calls in 3K RGP data are predominantly sequencing/alignment artifacts, not true biological heterozygosity. A 3% threshold is empirically validated for this dataset.

**Effect on reference gene**: LOC_Os11g37890 went from 104 → 34 variants (67% removal); retained samples 1359 → 2327 (+71%). The higher sample retention is the primary benefit.

**Code location**: `prepare_formal_inputs_sitebad03.R` function `run_haplotype()` lines 258–280.

**Threshold**: 0.03. Do not relax to 0.05 without client discussion.

---

## DEC-005: Report post_site_qc_variant_count (not pre-QC)

**Decision**: In Figure_Legends.md and Results_Discussion.md, the variant count must come from `haplotype_key_metrics.tsv` field `post_site_qc_variant_count`, not `filtered_haplotype_interval_variant_count`.

**Why**: The manuscript describes "variants used for haplotype construction." That is the post-QC number. Pre-QC numbers only belong in the Methods section when describing the QC procedure itself.

**Concrete example**: LOC_Os11g37890 had 104 pre-QC and 34 post-QC. The figure legend must say "34 SNPs", not "104 SNPs".

**Code location**: `formal_full_analysis.R` — ensure `variant_count` reads `post_site_qc_variant_count`.

---

## DEC-007: Delivery package content strategy

**Decision**: Delivery zip contains:
- PDF figures only (not PNG — PDF is the archival format)
- 9 key XLSX data tables
- 方法描述.md, 图注.md, 结果与讨论.md

Excluded: R scripts, shell scripts, logs, PNG files, internal audit files, metadata TSVs.

**Why**: Client is writing a thesis, not running the pipeline. They need figures + methods description in Chinese academic register. Code is internal IP.

---

## DEC-002: Figure aesthetics

**H001 haplotype color**: `#0F7FBF` (blue). H001 was originally red, which clashed with K5 XI color.

**FigD clade labels**: `geom_cladelab(label="", fontsize=0, barsize=4.0)` — color bars only, no text labels.

**var_gene grid**: `panel.grid.major = element_blank()` — remove grid lines.

---

## DEC-003: Two-gene standardization

When the same client has multiple genes under analysis, all genes must use the identical pipeline version (same sitebad03 threshold, same figure aesthetics). Mixed-version results in the same paper are not acceptable.

---

## DEC-004: cv() function resolution

The `cv()` helper in `prepare_formal_inputs_sitebad03.R` was used at line 557 but not always defined. Fix: replace `cv("gene_chr_gff")` with the direct contract access `contract$gene_chr_gff`. Both `cv()` (defined in `qa_formal_release.R`) and direct access are semantically equivalent.

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
