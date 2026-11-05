# Workflow contract for short-read germline SV ensembles

Use this contract after the biological objective and caller portfolio are fixed. It defines auditable interfaces; it does not prescribe universal filters.

## Input schemas

### Sample manifest

UTF-8 TSV with one row per biological sample:

```text
sample_id	alignment	role	population	parent_id	sex_or_ploidy_note
MUT001	/abs/path/MUT001.bam	mutant	japonica	WT001	diploid
WT001	/abs/path/WT001.bam	parent	japonica	NA	diploid
```

Required: `sample_id`, `alignment`. Optional fields must use the explicit missing value `NA`; do not infer pedigree or ploidy from filenames.

### Ensemble manifest

UTF-8 TSV with one row per caller callset:

```text
sample_id	caller	caller_version	callset	algorithm_family	alignment_mode	coordinate_reference
MUT001	manta	<installed_version>	/abs/path/MUT001.manta.vcf.gz	junction_local_assembly	linear	IRGSP-1.0|sha256:<digest>
MUT001	dysgu	<installed_version>	/abs/path/MUT001.dysgu.vcf.gz	integrated_junction_depth	linear	IRGSP-1.0|sha256:<digest>
MUT001	delly	<installed_version>	/abs/path/MUT001.delly.bcf	paired_split_genotyping	linear	IRGSP-1.0|sha256:<digest>
```

Required columns are exactly those shown. `alignment_mode` is `linear` or `graph_surjected`; native graph coordinates are outside this VCF ensemble contract. Relative callset paths resolve against the manifest directory but absolute paths are preferred.

`algorithm_family` is a declared design label, not an automatically verified biological fact. Record the rationale in the decision log. LUMPY and Smoove must share one family label.

## Suggested output layout

```text
run_id/
├── 00_meta/
│   ├── samples.tsv
│   ├── ensemble_manifest.tsv
│   ├── ensemble_preflight.{tsv,xlsx,json}
│   ├── reference.sha256
│   ├── software_versions.tsv
│   ├── commands.sh
│   └── decision_record.yaml
├── 01_callers/<caller>/<sample>/
│   ├── raw/
│   ├── filtered/
│   ├── logs/
│   └── benchmarks/
├── 02_normalized/<caller>/<sample>.vcf.gz
├── 03_ensemble/
│   ├── union.vcf.gz
│   ├── supported.vcf.gz
│   ├── rescued_singletons.tsv
│   ├── membership.tsv
│   └── matching_policy.yaml
├── 04_benchmark/<development|holdout>/<view>/
├── 05_qc/
│   ├── summary.tsv
│   ├── summary.xlsx
│   └── figures/
└── 06_annotation/
```

Never replace `raw/` or `02_normalized/` with a merged representative-only VCF.

## Decision record

At minimum record:

```yaml
objective: sensitivity_first
primary_metric: recall
secondary_metrics: [precision, f1, review_burden]
reference_id: IRGSP-1.0
reference_sha256: <digest>
callable_regions: /abs/path/confident.bed.gz
truth_set: /abs/path/truth.vcf.gz
truth_ascertainment: long_read_plus_manual_review
development_holdout_seed: 20260813
callers: [manta, dysgu, delly]
ensemble_views: [union, supported, rescued_singletons]
support_threshold: 2
support_semantics: prioritization_only
acceptance_criteria:
  primary_metric: "<predeclared threshold or not_estimable>"
  maximum_review_burden: "<predeclared event count or not_applicable>"
  minimum_holdout_events_by_svtype: "<predeclared mapping or not_estimable>"
decision_status: planned
random_seed_calling: not_applicable
```

Predeclare acceptance thresholds before inspecting the holdout. Use `decision_status: planned`, `accepted`, `rejected`, or `exploratory`; do not change a rejected result to accepted by redefining the objective after evaluation. If there is no truth set, use `truth_set: null`, state which conclusions become unavailable, set unavailable criteria to `not_estimable`, and do not optimize thresholds on visual preference.

## Representation and matching policy

Write a versioned `matching_policy.yaml` before merging. It must declare:

- coordinate reference and contig alias map;
- VCF normalization and sorting commands;
- treatment of multi-allelic records;
- supported SVTYPE vocabulary and caller-specific translations;
- interval-SV reciprocal overlap and breakpoint-distance rules;
- INS distance, length-ratio, and sequence-similarity rules;
- BND mate/orientation and distance rules;
- whether same-caller duplicates may collapse;
- representative-selection priority;
- preservation of `CIPOS`, `CIEND`, inserted sequence, original IDs, and caller filters;
- tool and version used for consolidation.

Do not use one distance for all types and sizes unless a project-specific benchmark justifies it. The paper's SVDB `--bnd_distance 1000` is a reproduced benchmark parameter, not a general BND rule.

## Ensemble event table

The `membership.tsv` primary key is a stable `ensemble_event_id`. Include:

```text
ensemble_event_id
coordinate_reference
chrom
pos
end
svtype
svlen
representative_alt
support_count_tools
support_count_families
callers
algorithm_families
alignment_modes
original_call_ids
matching_rule_id
representative_rule
sequence_resolved
status_union
status_supported
status_rescued_singleton
rescue_reason
```

Keep BND size blank. Use absolute size only for size-bin summaries; retain the signed original `SVLEN` where meaningful.

## Benchmark contract

Primary comparisons must hold constant:

- truth VCF and sample identity;
- confident/callable regions;
- coordinate reference;
- candidate preprocessing;
- Truvari version and all parameters;
- treatment of filtered calls, genotypes, SVTYPE, and insertion sequences.

Report at least:

- `TP-base`, `TP-call`, `FP`, `FN`, precision, recall, F1;
- genotype concordance if genotypes are a claim;
- event count and manual-review burden;
- SVTYPE, size-bin, chromosome, repeat/region, and alignment-mode strata;
- confidence intervals or uncertainty when truth events are sparse;
- development and untouched holdout results separately.

Never tune on a truth-labelled VCF and report the same events as independent validation. The paper's exhaustive union script used truth-labelled TP/FN and FP clustering for analysis; it is not a production merger.

## Graph branch contract

Graph-surjected callsets may enter an ensemble only when all rows share the same `coordinate_reference`. Also record:

- graph construction software and versions;
- source assemblies/accessions and checksums;
- graph/index hashes;
- aligner and surjection command;
- graph path and target linear assembly;
- unprojectable and multi-mapped read handling;
- linear-versus-graph mapping QC, all-call Jaccard, and truth-supported TP Jaccard when a valid truth set exists. Record the common matching policy, set definitions, and zero-denominator handling.

Do not merge native graph-coordinate calls into a linear VCF by positional proximity.

## Frequency and prioritization layers

Keep the raw population/background frequency as an annotation. Emit at least:

- `unfiltered`;
- `frequency_prioritized` under a declared rule;
- `parent_absent_or_low_support` for mutant studies;
- `validation_queue` with reason codes.

Never delete the unfiltered layer. A frequency threshold that changes recall must be benchmarked and reported.

## Failure scenarios

| Failure | Required action |
|---|---|
| Reference/header contigs differ | Stop; regenerate or select assembly-matched inputs |
| Callset file or index missing | Stop before harmonization |
| Same sample/caller/alignment mode repeated | Stop; resolve duplicate provenance |
| Different coordinate references in one sample ensemble | Stop; do not positional-merge |
| Only one algorithm family | Continue only as a single-family comparison; do not call it an independent ensemble |
| LUMPY and Smoove declared as different families | Stop; correct pseudo-independent support |
| Truth regions absent | Benchmark exploratory whole-space counts only; do not claim calibrated precision/recall |
| Truth used for both tuning and final reporting | Split data or label overfit exploratory result |
| Very few events in a stratum | Report counts/uncertainty; do not rank callers strongly |
| Graph and linear coordinates cannot be proven identical | Keep branches separate |
| Production metric worsens after adding a caller | Preserve the result and stop expansion at the objective-specific local optimum |

## Verification

Run:

```bash
python3 scripts/validate_ensemble_manifest.py \
  --manifest /abs/path/ensemble_manifest.tsv \
  --output-prefix /abs/path/run_id/00_meta/ensemble_preflight

bcftools index --stats /abs/path/normalized.vcf.gz
bcftools view -h /abs/path/normalized.vcf.gz
snakemake -s main.smk -n --printshellcmds
```

The last command applies only when a Snakemake implementation exists. Save stdout, stderr, exit code, and the exact environment/container identifiers.
