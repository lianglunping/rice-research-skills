# Workflow

## Read Order

1. `USER_DEFAULT_PREFERENCES.md`
2. `INPUT_SCHEMA.md`
3. `ASSAY_MODES.md`
4. `TOOLCHAIN.md`
5. `REDESIGN_POLICY.md`
6. `OUTPUT_CONTRACT.md`

Before running the v1 workflow, first check whether the requested assay and the current script
behavior are compatible with the user default preferences. If they are not compatible, stop and
report a `preference_conflict` instead of silently using the baseline short-amplicon defaults.

## First-Use Setup

```bash
cd /path/to/codex/skills/variant-primer-design
bash scripts/bootstrap_env.sh
```

## Standard Run

Use this path when the input table only contains variant coordinates and alleles:

```bash
mamba run -n primer-design python scripts/run_primer_workflow.py \
  --input /path/to/variants.xlsx \
  --reference-fasta /path/to/reference.fa \
  --assay-mode indel_pcr \
  --output-dir /path/to/results/primer_design_20260407
```

Use the standard run only when the user default preferences are compatible with the requested assay
or the user has explicitly approved a relaxation.

## Input Already Has `full_seq`

Use this path when the input table already contains `full_seq` and BLAST should run against an existing reference genome or prebuilt BLAST database:

```bash
mamba run -n primer-design python scripts/run_primer_workflow.py \
  --input /path/to/variants_with_full_seq.tsv \
  --reference-fasta /path/to/reference.fa \
  --assay-mode snp_pcr \
  --assume-left-flank 1000 \
  --output-dir /path/to/results/primer_design_20260407
```

If the BLAST database already exists:

```bash
mamba run -n primer-design python scripts/run_primer_workflow.py \
  --input /path/to/variants_with_full_seq.tsv \
  --blast-db-prefix /path/to/blast_db/reference \
  --assay-mode indel_pcr \
  --assume-left-flank 1000 \
  --output-dir /path/to/results/primer_design_20260407
```

## Review Checklist

- `final_primers.tsv`: final selected primer pair per locus
- `primer_specificity.tsv`: hit counts and specificity status
- `primer_order.tsv`: flat order-ready primer table
- `design_report.txt`: summary, failure reasons, and run metadata
- `intermediate/`: round-specific design and BLAST artifacts

## Failure Handling

- `FAILED` with `no_forward_primer`, `no_reverse_primer`, or `no_primer_pair` means the design stage failed.
- `non_specific` means the design stage produced a pair, but BLAST hit counts were not unique.
- `preference_conflict` means the user default preferences are not compatible with the current v1 workflow or assay mode.
- If both strict and relaxed rounds fail, report the locus explicitly and keep the reason code.
