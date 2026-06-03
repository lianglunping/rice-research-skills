# Pipeline Guide — Full Step Descriptions and New-Gene Adaptation

## Pipeline Step Details

| Step | Script / Command | What happens |
|------|-----------------|-------------|
| 00 | bash | Record micromamba, R, bcftools, plink, vcftools versions to `logs/00_versions.log` |
| 01 | prepare_formal_inputs_sitebad03.R metadata | Read 3K-info.csv; exclude K5=na samples; write `included_samples.txt` and `project_contract.tsv` |
| 02 | vcftools | Filter VCF: `--max-missing 0.95 --maf 0.05`; bgzip + tabix index |
| 03 | prepare_formal_inputs_sitebad03.R haplotype | Per-site bad-rate QC (≤ 3%); write `sitebad03_positions.tsv`; build haplotype table with geneHapR |
| 04 | plink + bcftools | Filter SNPs with `--mac 1`; compute IBS distance matrix; used for NJ tree |
| 05 | prepare_formal_inputs_sitebad03.R summarize | Summarize Fst/Pi/TajimaD windowed statistics from 01.Fst / 02.Pi / 03.TajimaD |
| 10 | formal_full_analysis.R | Generate all figures (PDF + PNG); write Figure_Legends.md, Results_Discussion.md, 方法描述.md |
| 11 | qa_formal_release.R | Run the formal QA suite, including PDF text-layer chromosome-label checks; write `formal_release_qa.tsv`; exit non-zero if any FAIL |

## Adapting to a New Gene

Execute these steps in order when onboarding a new gene:

1. Copy the full `scripts/` directory from the reference gene (LOC_Os11g37890).
2. Edit `formal_release_config.tsv`: update `gene_id`, `gene_chr_gff`, `gene_chr_vcf`, all coordinate fields (`gene_start`, `gene_end`, `gene_strand`, `promoter_start`, `promoter_end`, `analysis_start`, `analysis_end`), `input_vcf`, `input_gff`, `run_date`.
3. Confirm plotting scripts derive all chromosome labels from `project_contract.tsv` / `gene_chr_vcf`; no literal labels such as `Chromosome 11`, `chromosome 11`, or donor coordinates may remain.
4. Confirm `qa_formal_release.R` reads the expected gene contract from config/result tables and includes a generic unexpected-chromosome guard plus `pdf_text_chromosome_guard`.
5. Run `bash scripts/run_formal_analysis_sitebad03.sh`.
6. Confirm every QA check PASS, especially `old_project_residue_guard`, `pdf_text_chromosome_guard`, and `pdf_render_visual_check`.

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
R_PREFIX=/path/to/micromamba/envs/py3 \
NGS_PREFIX=/path/to/micromamba/envs/ngs \
META_CSV=/path/to/3K-info.csv \
bash scripts/run_formal_analysis_sitebad03.sh
```

## Delivery Contents Checklist

Confirm before packaging:
- [ ] All QA checks PASS
- [ ] PDF text-layer audit reports only the configured chromosome label or no chromosome label
- [ ] `figures/` contains PDF + PNG pairs
- [ ] `summary/` contains 9 XLSX tables
- [ ] `manuscript/` contains 方法描述.md, 图注.md, 结果与讨论.md
- [ ] Zip excludes `.R`, `.sh`, `.log`, `.png`, `.tsv` files
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
