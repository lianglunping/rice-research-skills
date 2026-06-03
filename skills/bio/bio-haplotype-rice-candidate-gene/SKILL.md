---
name: bio-haplotype-rice-candidate-gene
description: >
  This skill should be used when the user asks to run haplotype analysis on a
  rice candidate gene, set up haplotype pipeline for a new gene, needs
  单倍型分析, or wants to produce a delivery package with population genetics
  results from 3K RGP data. Covers the full pipeline: VCF QC → haplotype
  construction → population genetics (Fst/Pi/TajimaD) → visualization → QA →
  delivery zip.
---

# Rice Candidate Gene Haplotype Analysis

## Goal

Given standard inputs (Fst/Pi/TajimaD directories + GFF3 + VCF.gz), produce a fully QA-passed delivery package containing figures, data tables, and a Chinese methods description suitable for a thesis.

## Standard Inputs

```
{GENE_DIR}/
├── 01.Fst/          # {Group1}_{Group2}.windowed.weir.fst files
├── 02.Pi/           # {Group}.windowed.pi + {Group}.recode.vcf
├── 03.TajimaD/      # {Group}.Tajima.D files
├── {GENE_ID}.gff3   # MSU_osa1r7 annotation
└── {GENE_ID}.vcf.gz # 3K RGP VCF for the gene region (+ tabix index)
```

Plus shared metadata: `3K-info.csv` (columns: ID, K5, lat, lon, …)

## Pipeline Steps

### Step 0: New Gene Setup

1. Create the project runtime file scripts/formal_release_config.tsv from `references/config-template.tsv`.
2. Populate: gene coordinates from GFF3, chromosome (GFF = "ChrNN", VCF = "NN"), promoter (2 kb strand-aware upstream), analysis interval = gene ∪ promoter.
3. Run `bash scripts/run_formal_analysis_sitebad03.sh` from the gene directory.

For full pipeline step descriptions, see `references/pipeline-guide.md`.

### Step 1: Run the Pipeline

```bash
bash scripts/run_formal_analysis_sitebad03.sh
```

The driver runs steps 00–11 automatically (versions → metadata → VCF filter → haplotype QC → IBS tree → popgen → full analysis → QA). Logs land in `results/{RUN_ID}/logs/`.

### Step 2: Review QA Results

```bash
cat results/{RUN_ID}/summary/formal_release_qa.tsv
```

Confirm every check shows `PASS`, including the PDF text-layer chromosome-label guard. Fix any failures before proceeding; see `references/qa-checklist.md`.

### Step 3: Package Delivery

```bash
mkdir -p {GENE_DIR}/delivery
cd {GENE_DIR}/release/{RELEASE_ID}
zip -r ../../delivery/{GENE_ID}_分析结果.zip figures/*.pdf summary/*.xlsx manuscript/*.md
```

Confirm the zip contains no `.R`, `.sh`, `.log`, or `.png` files.

### Step 4: Archive Superseded Runs

After a corrected release is accepted, keep the active `results/{RUN_ID}`, `release/{RELEASE_ID}`, scripts, inputs, audit notes, and the main delivery zip. Move superseded/failed runs, obsolete delivery zips, and top-level run logs to `archive/{YYYYMMDD}_superseded_runs/` with a short README and SHA256 manifest. Delete only redundant duplicates and empty temporary folders; never delete raw inputs.

## Critical Quality Rules

Non-obvious rules that must be preserved across all genes:

| Rule | Description |
|------|-------------|
| **variant_count** | Report `post_site_qc_variant_count` (not pre-QC) in Figure_Legends and Results_Discussion. See DEC-005. |
| **per-site bad-rate** | Threshold = 3% `(missing + het) / total`. Rice is selfing; het calls are sequencing error. See DEC-001. |
| **major haplotype threshold** | Default n ≥ 30 (parameterizable). Encoded in `formal_release_config.tsv`. |
| **"混合群" not "芒稻"** | Call the Adm K5 group "混合群（Admixture）" in all Chinese text. |
| **Tajima's D order** | Positive D → 平衡选择或瓶颈效应 first; negative D → 方向性选择或扩张 second. |
| **run_id is dynamic** | `run_id <- basename(result_dir)` in formal_full_analysis.R; never hardcode a run ID. |
| **chromosome labels are dynamic** | Figure labels must be derived from `gene_chr_vcf` / `project_contract.tsv` (e.g. `Chromosome 7`), never copied as literal `Chromosome 11` or donor-gene text. |
| **PDF text-layer QA is mandatory** | QA must extract text from all release PDFs with `pdftotext` and fail on unexpected chromosome labels. Visual rendering alone is not sufficient. |

## Output Structure

```
release/{RELEASE_ID}/
├── figures/          # PDF + PNG figure pairs (17 figures for reference gene)
├── summary/          # XLSX data tables + QA report
├── manuscript/       # Figure_Legends.md, Results_Discussion.md, 方法描述.md
└── scripts/          # Snapshot of analysis scripts
```

## References

- `references/config-template.tsv` — blank config template for new genes
- `references/pipeline-guide.md` — full pipeline step descriptions and new-gene adaptation checklist
- `references/pipeline-decisions.md` — rationale for all major analytical choices (DEC-001 to DEC-007)
- `references/qa-checklist.md` — QA check descriptions and common failure fixes
- `references/method-template.md` — 方法描述.md template for new genes
