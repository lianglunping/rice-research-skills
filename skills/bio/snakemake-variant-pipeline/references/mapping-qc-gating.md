# Mapping QC Gating

## Goal

Use mapping rate as an explicit workflow gate after alignment, without pretending one fixed cutoff is valid for every project.

## Recommended Default

- metric: Picard/GATK `PCT_PF_READS_ALIGNED`
- action: `mark`
- `warn_below`: start with a configurable engineering default such as `0.85`
- `drop_below`: unset unless the project has a validated cutoff

This means the pipeline records low-mapping samples, but still keeps them in downstream rules unless the user explicitly enables dropping.
The workflow templates define `checkpoint filter_samples` inside `alignment_qc.smk` and route downstream cohort rules through `selected_samples(wc)`, so `action: drop` is executable rather than advisory as long as the workflow includes `alignment_qc.smk`.

## Why the Threshold Must Be Configurable

The upstream tools define the metric, not a universal cutoff:

- GATK/Picard documents `PCT_PF_READS_ALIGNED` as part of alignment summary metrics
- `samtools flagstat` documents `mapped` and `mapped %`
- MultiQC can surface these values in the general summary table
- Snakemake checkpoints support result-dependent sample filtering

The human WGS thresholds published by Illumina are useful as context, but should not be copied directly into rice or mutagenesis workflows without project-specific validation.

## Metric Priority

1. `picard_pct_pf_reads_aligned`
   - default
   - stable with a GATK-first workflow
   - easier to keep consistent with downstream Picard/GATK QC

2. `flagstat_mapped_pct`
   - optional secondary metric
   - helpful for MultiQC and quick inspection

When both are available, keep both files, but let the gating decision use the configured primary metric.

## Action Modes

### `mark`

- default mode
- every sample continues downstream
- low-mapping samples are highlighted in `mapping_qc.summary.tsv`
- use this when low mapping is a warning, not a hard failure

### `drop`

- only enable when the project already defines a cutoff
- generate `passing_samples.tsv` and `excluded_samples.tsv`
- downstream cohort rules and `rule all` blocks must call `selected_samples(wc)`
- always preserve the exclusion reason and mapping rate

## Suggested Starting Policy

For exploratory or heterogeneous projects:

```yaml
mapping_qc:
  enabled: true
  metric: picard_pct_pf_reads_aligned
  action: mark
  warn_below: 0.85
  drop_below: null
  use_flagstat: true
```

For a project with an agreed exclusion rule:

```yaml
mapping_qc:
  enabled: true
  metric: picard_pct_pf_reads_aligned
  action: drop
  warn_below: 0.85
  drop_below: 0.75
  use_flagstat: true
```

## Official References

- GATK: AlignmentSummaryMetrics
  https://gatk.broadinstitute.org/hc/en-us/articles/27007980736155-AlignmentSummaryMetrics
- GATK: CollectAlignmentSummaryMetrics (Picard)
  https://gatk.broadinstitute.org/hc/en-us/articles/360045799412-CollectAlignmentSummaryMetrics-Picard
- samtools flagstat
  https://www.htslib.org/doc/samtools-flagstat.html
- MultiQC customisation
  https://docs.seqera.io/multiqc/reports/customisation/
- MultiQC samtools module
  https://docs.seqera.io/multiqc/modules/samtools/
- MultiQC picard module
  https://docs.seqera.io/multiqc/modules/picard
- Snakemake checkpoints
  https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html
- Illumina minimal checklist for human WGS context
  https://help.connected.illumina.com/dragen/product-guides/dragen-v4.5/qc-metrics-reporting/minimal_checklist
