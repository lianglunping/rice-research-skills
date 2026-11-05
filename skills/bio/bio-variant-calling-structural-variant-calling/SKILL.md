---
name: bio-variant-calling-structural-variant-calling
description: "Structural-variant calling and integration with caller-specific evidence, sample/reference contracts and breakpoint representation checks."
---

# Short-read germline SV calling

Build a version-pinned, objective-driven workflow. Never present one caller, one caller set, one merge distance, or a two-caller vote as universally optimal. Keep raw evidence and alternative ensemble views so sensitivity can be improved without silently discarding valid caller-specific events.

## Establish the analysis contract

Record these fields before generating commands or changing files:

- Objective: sensitivity-first discovery, balanced F-score, precision-first validation queue, cohort genotyping, graph-alignment comparison, or audit only.
- Biological design: species, ploidy, sample relationships, mutant/parent status, expected SV classes and sizes, and whether germline diploid assumptions are defensible.
- Inputs: exact reference FASTA and checksum, indexed coordinate-sorted BAM/CRAM files, sample manifest, callable/confident and exclusion regions, truth VCF if available, and graph construction/surjection provenance when applicable.
- Outputs: immutable per-caller callsets, normalized callsets, union and support-tagged ensemble views, rescued-singleton table, benchmark/QC tables, logs, environment lock, and a decision record.
- Boundaries: separate discovery from cohort genotyping, annotation, frequency prioritization, causal inference, primer design, and experimental validation.
- Acceptance: inputs pass preflight; coordinates and representations are compatible; every transformation is traceable; caller and merger parameters are recorded; performance is stratified; no biological result is fabricated; and production thresholds are evaluated on data not used to tune them.

Create a new run directory. Do not overwrite source alignments, truth sets, raw caller outputs, or previous results.

## Apply the paper-derived guardrails

Read [references/evidence-and-design.md](references/evidence-and-design.md) when selecting callers, ensembles, or graph alignment. The 2026 human benchmark supports these design rules, not a universal caller recipe:

1. Caller performance changes by SV class, size, chromosome/region, dataset, and representation.
2. A union can improve recall and sometimes F1; requiring support from two or more callers can reduce recall and F1. Treat `support_count` as evidence metadata, not truth.
3. Algorithmically related callers do not provide independent votes. In particular, LUMPY and Smoove must not be counted as two independent evidence families.
4. Ensemble results depend on normalization and clustering. A fixed 1000-bp window is not a biological constant.
5. Graph alignment can have a small mean effect but a large caller-specific effect or low true-positive callset overlap. Test it as an optional discovery branch rather than assuming benefit or irrelevance.
6. Human 30x rankings and a human HPRC graph do not transfer directly to rice.

## Select a caller portfolio

Choose by evidence diversity and the project objective. Confirm installed help, supported input type, license, and species/ploidy assumptions before execution.

| Role | Candidate callers | Use deliberately |
|---|---|---|
| Fast junction/local-assembly baseline | Manta | General paired-end WGS baseline; preserve all documented result layers |
| Complementary integrated caller | Dysgu | Candidate for sensitivity and resource-efficient discovery; inspect its diploid model for non-diploid material |
| Cohort discovery and re-genotyping | Delly | Use the dedicated `bio-delly-sv-calling` skill; do not substitute multi-BAM discovery for joint genotyping |
| Assembly-heavy breakpoint branch | SvABA or GRIDSS2 | Add when inversions, breakends, or complex junctions matter and compute/review capacity permits |
| Read-depth complement | CNVpytor or a project CNV workflow | Keep dosage evidence separate from balanced-junction evidence until harmonization |
| LUMPY ecosystem | LUMPY or Smoove | Choose one unless comparing wrappers; never count both as independent algorithms |

For a new rice WGS project, `Manta + Dysgu + Delly` is an example calibration panel, not a production default. Add or replace a caller after a pilot stratified by the target SV classes, difficult regions, compute budget, and locally validated events. Do not copy the paper's best human quartet or seven-tool union into rice without calibration.

Route ONT/PacBio discovery to `bio-long-read-sequencing-structural-variants`; use long-read or assembly calls as truth support, not as an unqualified perfect truth set.

## Install and operate the toolchain

Read [references/software-install-use-merge.md](references/software-install-use-merge.md) whenever the request includes software installation, caller commands, environment repair, or multi-caller merging.

- Treat installation, package upgrades, container pulls, and global channel changes as environment mutations. Execute them only when the user explicitly authorizes that change; otherwise return a dry-run, environment specification, lock strategy, and acceptance commands.
- Use isolated, version-pinned environments or digest-pinned containers. Do not force Manta and modern Python callers/harmonizers into one environment: current Bioconda Manta uses Python 2.7, whereas Dysgu and SVDB use modern Python.
- Query package availability for the target OS/architecture before solving. If a caller has no native build, use an authorized Linux container or HPC environment rather than silently emulating or compiling.
- Record the exact package build or container digest, license source, solver command, explicit lock file, installed help text, and smoke-test result.
- Run each caller through its own environment and write into a caller-specific output directory. Never let installation or a rerun replace prior biological outputs.

## Gate inputs and versions

Capture executable/container identifiers and help text in `00_meta/`:

```bash
samtools --version
bcftools --version
truvari --version
SV_CALLER_COMMAND=/abs/path/to/caller
"${SV_CALLER_COMMAND}" --version 2>&1 || true
"${SV_CALLER_COMMAND}" --help 2>&1
```

Also save the exact environment lock (`conda list --explicit`, Pixi lock, or container digest) and the software-installation acceptance report.

Verify reference/header contig names and lengths, BAM/CRAM indexes, coordinate sort order, read-group sample names, duplicate-processing provenance, coverage distribution, insert-size distribution, mapping quality, and assembly-matched callable/exclusion BED files.

Before harmonization, validate the ensemble manifest:

```bash
python3 scripts/validate_ensemble_manifest.py \
  --manifest /path/to/ensemble_manifest.tsv \
  --output-prefix /path/to/run/00_meta/ensemble_preflight
```

Stop on `ERROR`. Resolve warnings that change interpretation, especially a single algorithm family, missing indexes, incomplete per-sample caller panels, or graph-surjected and linear calls lacking one shared coordinate reference.

## Execute without losing provenance

Follow [references/workflow-contract.md](references/workflow-contract.md) for schemas and output layout. Read [references/software-install-use-merge.md](references/software-install-use-merge.md) before emitting caller or consolidation commands.

1. Run each caller independently against the same immutable coordinate reference and record complete commands, versions, resources, timestamps, and exit codes.
2. Preserve raw callsets. Create caller-specific filtered derivatives only from documented caller semantics; do not apply a universal `QUAL`, `PE`, or `SR` cutoff across callers.
3. Normalize contig names, sorting, sample names, SVTYPE conventions, BND pairing, and symbolic versus sequence-resolved insertion representation. Do not erase confidence intervals or inserted sequence.
4. Harmonize calls with an explicit, versioned matching policy. Distinguish interval SVs, insertions, and BNDs; stratify distance/overlap rules by class and breakpoint precision when supported.
5. Emit all three views:
   - `union`: one representative for every harmonized event seen by any selected caller; sensitivity lane.
   - `supported`: the same event table annotated with `support_count >= N`; prioritization lane, not a claim of truth.
   - `rescued_singletons`: single-caller events retained because caller quality, orthogonal evidence, segregation, target-gene impact, or graph/linear complement justifies review.
6. Keep caller membership, original IDs, original coordinates, matching rule, and transformation history for every representative event.

Use SVDB for explicitly tagged cross-caller merging when its representation model fits the project; use SURVIVOR for a documented position-based sensitivity analysis or compatibility requirement; use Truvari primarily for benchmarking and representation-aware collapse after confirming the input semantics. `bcftools merge` combines samples and `bcftools concat` concatenates records; neither alone is cross-caller event harmonization. Read installed help and record every parameter. Never copy `SURVIVOR merge ... 1000 2 ...` as a default. Build the union with minimum support one, then derive supported and singleton views from the same clustered event set so the views remain comparable. Tool support count and algorithm-family support count are distinct columns.

## Benchmark and tune without truth leakage

Use a fixed reference, truth VCF, confident-region BED, sample identity, and evaluation policy. Split available truth-supported events or samples into development and holdout partitions before choosing callers, merge thresholds, or filters. If the truth set is too small for a holdout, label the result exploratory and do not claim generalization.

Start from the installed Truvari interface and save the rendered command:

```bash
truvari bench \
  -b /path/to/truth.vcf.gz \
  -c /path/to/candidate.vcf.gz \
  -f /path/to/reference.fa \
  -o /path/to/benchmark/run_id
```

- Make SVTYPE-aware evaluation the primary analysis when class accuracy matters. If `--typeignore` is used, label the result as breakpoint/location matching.
- Evaluate inserted-sequence identity when sequence-resolved INS claims are made. If sequence similarity is disabled, state that insertion identity was not tested.
- Report precision, recall, F1 or the declared objective, genotype concordance where meaningful, and review burden. Stratify by SVTYPE, size bin, region class, chromosome, caller, ensemble view, and reference/alignment mode.
- Optimize on development data and report the untouched holdout result. Preserve negative or null results.
- Benchmark single callers and every retained ensemble view under the same matching policy; otherwise metric differences are not attributable to the caller set.

## Treat graph alignment as an opt-in experiment

Keep a linear-alignment baseline. Add a graph branch only if the graph represents the target germplasm and the downstream caller accepts the resulting alignment or a documented surjection.

For each caller compare linear versus graph-surjected inputs using the same reads, coordinate reference, callable regions, caller version, and evaluation policy. Report not only F1/precision/recall but also true-positive Jaccard overlap, graph-only and linear-only supported events, mapping/QC shifts, and resource cost. A small aggregate F1 change does not prove identical callsets.

For rice, record graph accessions/haplotypes, indica/japonica composition, construction software/version, graph hash, path names, surjection target, and coordinate-liftover policy. A human HPRC-derived result is external evidence, not a rice parameter.

## Adapt to rice and induced mutants

- Use one exact assembly and matching annotation/masks throughout a run; never silently mix IRGSP, MSU, MH63, ZS97, or custom assemblies.
- Pilot across the relevant subpopulation and repetitive-region strata. Reference divergence can change both mapping and apparent caller performance.
- Build a local validation panel from assembly/long-read-supported events, manually reviewed breakpoints, parental line calls, segregating progeny, and orthogonal assays. State ascertainment bias for each source.
- For induced mutants, retain rare or unique calls; use the parental line and unrelated background panel for prioritization, not unconditional frequency exclusion. A common allele may still be breeding-relevant, and a rare call is not automatically induced or causal.
- Require read-level review, parental/background comparison, segregation, and orthogonal validation before causal or breeding claims.
- Flag diploidy assumptions for polyploid, aneuploid, pooled, mixed, or mosaic samples.

## Report reproducibility

Return absolute input/output paths, checksums or immutable resource identifiers, manifest, software/container versions, complete commands, matching and filtering parameters, scheduler resources, timestamps, exit codes, and TSV/XLSX QC tables. Record `random_seed: not_applicable` for deterministic calling steps; record explicit seeds for simulation, resampling, or train/holdout splitting.

If execution is impossible, provide copyable templates, expected artifacts, validation commands, and unresolved assumptions. Do not invent counts, performance, or biological conclusions.

## Related skills

- `bio-delly-sv-calling`: Delly-specific single-sample, cohort, and somatic workflows.
- `snakemake-variant-pipeline`: workflow scaffolding after the SV design and ensemble contract are fixed.
- `bio-long-read-sequencing-structural-variants`: primary long-read discovery and truth-support generation.
- `bio-copy-number-copy-ratio-segmentation`: dosage-focused CNV analysis.
- `bio-vcf-manipulation`, `bio-variant-normalization`, and `bio-vcf-statistics`: representation and QC utilities.
- `bio-pangenome-pav-rice-breeding`: rice pangenome PAV interpretation beyond short-read calling.

## Scope notes

Before choosing inputs, comparison units or conclusion thresholds, read
[the scientific scope notes](references/scope-notes.md) for this task.
