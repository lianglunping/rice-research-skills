# Pipeline Guide — Full Step Descriptions and New-Gene Adaptation

## Pipeline Step Details

| Step | Script / Command | What happens |
|------|-----------------|-------------|
| 00 | bash | Record micromamba, R, bcftools, plink, vcftools versions to `logs/00_versions.log` |
| 01 | prepare_formal_inputs_siteqc.R metadata | Read 3K-info.csv; exclude K5=na samples; write `included_samples.txt` and `project_contract.tsv` |
| 02 | vcftools | Filter VCF: `--max-missing 0.95 --maf 0.05`; bgzip + tabix index |
| 02b | extract_superrice_region.py | For `dataset_mode=superrice`, extract target interval from 万份水稻 wide genotype tables and write sample manifest / group counts |
| 03 | haplotype QC | For 3K, apply the validated per-site bad-rate QC (≤ 3%). For 万份水稻, run a configured threshold sensitivity audit before selecting the project-specific cutoff; write site-QC, sample-QC, and threshold-sensitivity tables before building haplotypes. |
| 03b | build_common_haplotype_network.R | Build phased common-haplotype tables and network using frequency > 0.5% by default |
| 03c | build_publication_tables_v3.py | For compact XI/GJ mode, build the strict joint-threshold audit, accession carrier tests, unfiltered/primary matrices, MST/NJ inputs, Source Data, and publication workbooks |
| 04 | plink + bcftools | Filter SNPs with `--mac 1`; compute IBS distance matrix; used for NJ tree |
| 05 | prepare_formal_inputs_siteqc.R summarize | Summarize Fst/Pi/TajimaD windowed statistics from 01.Fst / 02.Pi / 03.TajimaD |
| 10 | formal_full_analysis.R | Generate all figures (PDF + PNG); write Figure_Legends.md, Results_Discussion.md, 方法描述.md |
| 10b | plot_publication_compact_v3.R | Generate two compact main composites, six reusable panels, and three supplementary figures |
| 11 | qa_formal_release.R | Run the formal QA suite, including PDF text-layer chromosome-label checks; write `formal_release_qa.tsv`; exit non-zero if any FAIL |
| 11b | qa_common_haplotype_network.R | For common-haplotype runs, verify node/edge/count/figure consistency |
| 11c | qa_publication_compact_v3.py | Recompute thresholds/statistics and verify matrix, tree, vector-PDF, typography, manual-review, release-manifest, and zip contracts |

## Adapting to a New Gene

Execute these steps in order when onboarding a new gene:

1. Copy the full `scripts/` directory from the reference gene (LOC_Os11g37890).
2. Edit `formal_release_config.tsv`: update `gene_id`, `gene_chr_gff`, `gene_chr_vcf`, all coordinate fields (`gene_start`, `gene_end`, `gene_strand`, `promoter_start`, `promoter_end`, `analysis_start`, `analysis_end`), `input_vcf`, `input_gff`, `run_date`.
3. If using 万份水稻, set `dataset_mode=superrice`, confirm `superrice_remote_snp_dir`, `superrice_remote_indel_dir`, and `superrice_metadata_xlsx`, then extract the interval with `extract_superrice_region.py`. Run site-QC threshold sensitivity before formal haplotype construction and record, for every candidate cutoff, raw/retained variant counts, complete-sample count, and complete-sample retention by `analysis_group`.
4. Confirm plotting scripts derive all chromosome labels from `project_contract.tsv` / `gene_chr_vcf`; no literal labels such as `Chromosome 11`, `chromosome 11`, or donor coordinates may remain.
5. Confirm `qa_formal_release.R` reads the expected gene contract from config/result tables and includes a generic unexpected-chromosome guard plus `pdf_text_chromosome_guard`.
6. Run the dataset-matched formal driver. `run_formal_analysis_siteqc.sh` is the 3K reference driver; 万份水稻 requires a formal superrice driver that writes the threshold and sample-retention evidence in the project run directory.
7. When `domestication_network_enabled=true`, run `build_common_haplotype_network.R` and `qa_common_haplotype_network.R` before packaging.
8. Confirm every QA check PASS, especially `old_project_residue_guard`, `pdf_text_chromosome_guard`, `pdf_render_visual_check`, threshold selection, retention by group, manual visual review, and common-haplotype network count consistency. If a metadata group has zero or strongly unequal complete-sample retention, restrict interpretation to the retained cohort and do not present group-frequency differences as unbiased population comparisons.
9. When `formal_mode=superrice_publication_compact_v3`, derive the compact run only from a validated source result, fill every expected-count field from source TSVs, and follow `references/superrice-publication-compact-v3.md`.

## Trait-First Dual-Dataset Selection

For projects with both 3K and 万份水稻 VCF sources plus a client phenotype table, run a sample-overlap audit before extracting the gene VCF:

1. Normalize the phenotype table to `sample_id` plus trait value.
2. Read 3K sample grouping from the local-authoritative workbook `/path/to/metadata/population_groups.xlsx`.
3. Read 万份水稻 sample metadata from the local-authoritative directory `/path/to/metadata/`.
4. On `REPLACE_HOST`, activate `conda activate ngs` and use `fd` and `rg` to locate VCFs and audit sample IDs.
5. Compare phenotype overlap for `/path/to/reference-data/3K/3K/SNP` and `/path/to/reference-data/superrice`.
6. Select the dataset with the larger matched phenotype sample count (`dataset_selection_rule=max_trait_overlap`); if tied, stop for a human decision.
7. Write TSV and XLSX audit outputs before formal haplotype analysis.

## Common-Haplotype Network Module

Use this module when the analysis needs a domestication-style haplotype network rather than only the standard `n >= 30` major-haplotype network.

Default command shape:

```bash
python templates/scripts/extract_superrice_region.py \
  --chrom Chr1 --start 100000 --end 120000 \
  --genotype /path/to/reference-data/superrice/1.rare_SNP/Chr1.rareSNP.genotype.gz \
  --metadata-xlsx /path/to/metadata/metadata_primary.xlsx \
  --metadata-xlsx /path/to/metadata/metadata_secondary.xlsx \
  --out-dir results/{RUN_ID}/superrice \
  --prefix {GENE_ID}

Rscript templates/scripts/build_common_haplotype_network.R \
  --genotype results/{RUN_ID}/superrice/{GENE_ID}.superrice_region_genotype.tsv.gz \
  --sample-manifest results/{RUN_ID}/superrice/{GENE_ID}.superrice_sample_manifest.tsv \
  --out-dir results/{RUN_ID}/common_haplotype_network \
  --prefix {GENE_ID} \
  --frequency-min 0.005 \
  --plot TRUE

Rscript templates/scripts/qa_common_haplotype_network.R \
  --out-dir results/{RUN_ID}/common_haplotype_network \
  --prefix {GENE_ID} \
  --frequency-min 0.005
```

Do not interpret this network alone as proof of domestication, introgression, or selection. It is a descriptive visualization unless paired with explicit wild/cultivar sampling design, selection statistics, and biological validation.

## Publication-Compact XI/GJ Module

Use this module after the validated superrice source run when the customer prefers 1-2 manuscript main figures and a concise XI/GJ narrative.

1. Copy `templates/config-superrice-publication-compact-v3.tsv` to `config/publication_compact_v3.tsv`.
2. Populate source paths, coordinates, expected counts, retention denominators, figure settings, and release IDs from traceable source tables.
3. Copy `templates/scripts/publication_compact_v3/` into the project.
4. Run the driver once through contact-sheet generation, inspect all full-size figures, and write the manual review TSV without auto-filled PASS rows.
5. Run the complete driver; it must finish release, QA, final release, and verify-only QA.

The primary set uses `accession carriers >= 30` plus strict `max(XI,GJ chromosome frequency) > 0.5%`. The all-haplotype workbook remains unfiltered. Fisher/BH/Newcombe statistics use accession carrier status, not chromosome copies.

The expected output is two main composites, six independent main panels, and three supplementary figures. Every PDF must have an English text layer, configured Arial/Times New Roman fonts, italic gene labels, and no embedded raster objects. Use `guide_colourbar(display="rectangles")` for continuous legends.

Do not collapse a specific haplotype-frequency shift into a claim of strong regional differentiation when regional Fst is low. Preserve both results and state the evidence boundary.

## Promoter Definition (Strand-Aware)

The promoter is always defined as 2 kb **biological upstream** of the transcription start site.

**Negative strand gene (strand = "−"):**
- Biological upstream = higher genomic coordinate
- `promoter_start = gene_end + 1`
- `promoter_end = gene_end + 2000`
- `analysis_start = gene_start`, `analysis_end = gene_end + 2000`

**Positive strand gene (strand = "+"):**
- `promoter_start = gene_start − 2000`
- `promoter_end = gene_start − 1`
- `analysis_start = gene_start − 2000`, `analysis_end = gene_end`

## Environment Variables

Override default tool paths if needed:

```bash
MICROMAMBA_BIN=/opt/homebrew/bin/micromamba \
R_PREFIX=<ABSOLUTE_PROJECT_R_PREFIX> \
NGS_PREFIX=<ABSOLUTE_PROJECT_NGS_PREFIX> \
META_CSV=/path/to/3K-info.csv \
bash scripts/run_formal_analysis_siteqc.sh
```

On `REPLACE_HOST`, the default software environment for VCF and sequencing utilities is conda environment `ngs`:

```bash
conda activate ngs
```

## Delivery Contents Checklist

Confirm before packaging:
- [ ] All QA checks PASS
- [ ] PDF text-layer audit reports only the configured chromosome label or no chromosome label
- [ ] `figures/` contains PDF + PNG pairs
- [ ] Every advertised summary table has an XLSX counterpart
- [ ] Every figure has a recorded manual visual review; sparse one-class matrices carry an explicit count-based explanation
- [ ] Complete/skipped sample counts are reported overall and by metadata group
- [ ] `manuscript/` contains 方法描述.md, 图注.md, 结果与讨论.md
- [ ] Zip excludes `.R`, `.sh`, `.py`, `.log`, and `.tsv`; PNG presence exactly follows `delivery_include_png`
- [ ] Internal QA is all-PASS; customer ZIP passes `unzip -t`, has the four-entry top-level whitelist, and contains no internal QA workbook
- [ ] `mkdir -p delivery/` exists before running zip command

## Post-Run Cleanup and Archival

After a corrected release supersedes earlier attempts:

1. Keep raw inputs, the active `results/{RUN_ID}`, the active `release/{RELEASE_ID}`, `scripts/`, `decisions/`, `audit/`, and the main delivery zip.
2. Move failed or superseded run directories to `archive/{YYYYMMDD}_superseded_runs/results/` and `archive/{YYYYMMDD}_superseded_runs/release/`.
3. Move obsolete delivery packages and top-level run logs into the same archive tree.
4. Write an archive README explaining why each run was superseded.
5. Write a SHA256 manifest for archived files.
6. Delete only redundant duplicate packages, `.DS_Store`, and empty `scratch/` / `temp_tests/` folders.

Do not delete raw VCF/GFF3, population-genetic input directories, or the accepted release unless the user explicitly asks for that exact operation.
