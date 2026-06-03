---
name: snakemake-variant-pipeline
description: This skill should be used when the user asks to scaffold a modular Snakemake workflow for resequencing projects, including FASTQ QC, BAM generation, GATK-first SNP/indel calling, or Manta/Delly SV calling, or explicitly wants a bcftools-based branch.
---

# Modular Snakemake Workflow Library

## Goal

Generate modular, reusable Snakemake workflows for resequencing analyses. The workflow may stop at:
- cleaned FASTQ
- BAM plus BAM QC
- GATK SNP/INDEL results
- SV results

Do not assume the user wants the full pipeline. First identify the final deliverable and stop at the smallest module set that satisfies it.

## Default Backend Policy

- Default SNP/INDEL backend: GATK
- Default workflow style: Snakemake project scaffold (`main.smk`, `rules/*.smk`, `config.yaml`, `samples.tsv`)
- `bcftools` is optional and should be used only when the user explicitly asks for `bcftools`, `mpileup`, `bcftools call`, or a lightweight alternate branch

## Role Boundaries

**This skill DOES:**
- scaffold modular Snakemake workflows
- choose the minimal module set that reaches the requested deliverable
- keep paths and resources in `config.yaml`
- include per-rule `log:`, `benchmark:`, and `threads:`
- support mapping-QC gating after alignment

**This skill does NOT:**
- install tools or create conda envs unless the user explicitly asks
- force a full variant workflow when the user only needs QC or BAM
- auto-drop low-mapping samples by default; the default behavior is to mark them

## Delivery Modes

| Goal | Typical modules |
|------|-----------------|
| QC-only | `qc.smk` |
| BAM-only | `qc.smk`, `align.smk`, optional `markdup.smk`, `bamstat.smk`, `alignment_qc.smk` |
| GATK default | `qc.smk`, `align.smk`, `markdup.smk`, `alignment_qc.smk`, `gatk_gvcf.smk`, `gatk_joint.smk`, `gatk_filter.smk` |
| SV-only | `alignment_qc.smk`, `sv_calling.smk`, `sv_merge.smk` |
| bcftools explicit-only | `alignment_qc.smk`, `bcftools_call.smk` |

## Default Workflow

1. Confirm the final deliverable:
- QC report or clean FASTQ
- BAM
- GATK VCF
- SV result
- bcftools branch explicitly requested

2. Confirm the input start point:
- raw FASTQ
- cleaned FASTQ
- existing BAM via `bam_dir` and `bam_suffix`
- existing gVCF

3. Gather project constraints:
- species and reference path
- FASTQ naming convention or sample sheet
- output base directory
- server cores and RAM
- conda init path and env names

4. Generate the minimal project:

```text
project/
├── main.smk
├── config.yaml
├── samples.tsv
├── scripts/
│   └── evaluate_mapping_qc.py
└── rules/
    ├── common.smk
    ├── qc.smk
    ├── align.smk
    ├── markdup.smk
    ├── bamstat.smk
    ├── alignment_qc.smk
    ├── gatk_gvcf.smk
    ├── gatk_joint.smk
    ├── gatk_filter.smk
    ├── bcftools_call.smk
    ├── sv_calling.smk
    └── sv_merge.smk
```

If `alignment_qc.smk` is included, also copy `scripts/evaluate_mapping_qc.py` into the generated project `scripts/` directory.

5. Validate:
- dry-run with `snakemake -s main.smk -n --printshellcmds`
- keep the module set aligned with the requested deliverable
- if mapping gating is enabled, default to `mark`, not `drop`

## Mapping QC Gate

When the user wants BAM or any downstream analysis, support a mapping-QC gate after alignment.

Default policy:
- metric: Picard/GATK `PCT_PF_READS_ALIGNED`
- action: `mark`
- `drop` is allowed only when the user explicitly asks or the project already defines a cutoff

Use `references/mapping-qc-gating.md` when:
- the user asks for a mapping-rate threshold
- the user wants low-mapping samples excluded
- the workflow needs checkpoint-based sample filtering

## Additional Resources

Load only what is needed:
- `references/snakefile-template.md` - module templates, config schema, and `main.smk` combinations
- `references/mapping-qc-gating.md` - mapping-rate thresholds, mark vs drop policy, checkpoint pattern
- `references/gpu-joint-calling.md` - GATK cohort joint calling acceleration options
- `examples/config-rice-131.yaml` - rice resequencing example with GATK default and mapping-QC config
- `scripts/evaluate_mapping_qc.py` - deterministic parser for Picard/samtools mapping metrics and sample gating
