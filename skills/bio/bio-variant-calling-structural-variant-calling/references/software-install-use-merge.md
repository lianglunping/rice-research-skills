# Software installation, caller operation, and multi-caller merging

This reference provides executable patterns for paired-end short-read germline WGS. It does not authorize environment changes and does not define universal biological thresholds.

## Contents

1. [Safety and provenance contract](#safety-and-provenance-contract)
2. [Audited package interfaces](#audited-package-interfaces)
3. [Install isolated environments](#install-isolated-environments)
4. [Verify installations](#verify-installations)
5. [Run core callers](#run-core-callers)
6. [Prepare callsets for integration](#prepare-callsets-for-integration)
7. [Choose an integration engine](#choose-an-integration-engine)
8. [Merge with SVDB](#merge-with-svdb)
9. [Merge with SURVIVOR](#merge-with-survivor)
10. [Use Truvari correctly](#use-truvari-correctly)
11. [Validate ensemble outputs](#validate-ensemble-outputs)
12. [Failure modes](#failure-modes)
13. [Primary sources](#primary-sources)

## Safety and provenance contract

Before any installation or execution, record:

- target OS, architecture, scheduler/container runtime, and filesystem policy;
- requested caller set and why each caller is needed;
- installation prefix or container cache location;
- exact reference, BAM/CRAM, and output paths;
- permission to create or modify environments;
- available CPU, RAM, temporary storage, and wall time;
- whether the goal is paper reproduction or a current production run.

Do not install into `base`, change global `.condarc`, upgrade an existing environment, pull unpinned `latest` containers, or compile source unless explicitly requested. Prefer a new prefix and run a solver dry-run first. Preserve all existing environments and biological outputs.

Record `random_seed: not_applicable` for deterministic installation/calling/merging. Record an explicit seed for simulations, bootstrap uncertainty, or development/holdout splitting.

## Audited package interfaces

The versions below were visible in official Bioconda documentation on 2026-08-13. Re-query before a new production run and pin the resolved build, not merely the package name.

| Package | Audited available version | Important constraint |
|---|---:|---|
| Manta | 1.6.0 | Bioconda build depends on Python 2.7; isolate it from modern Python tools |
| Dysgu | 1.9.0 | Current Bioconda build uses Python 3.10 |
| Delly | 2.5.1 | Current short-read subcommand is `delly sr`; detect legacy `call` from installed help |
| SVDB | 2.12.0 | Modern merge interface has separate interval, BND, and insertion matching controls |
| SURVIVOR | 1.0.7 | Position-oriented merger; parameters materially define the result |
| Truvari | 5.4.0 | Current production interface differs from the paper's pinned 4.2.2 |
| samtools | 1.24 | Alignment preflight and indexing; current Bioconda build supports `osx-arm64` |
| bcftools | 1.24 | Use for VCF/BCF inspection, sorting, indexing, and sample operations, not event harmonization by itself |

For paper reproduction, pin the article's versions and released workflow. For production, use a separately validated current stack. Never compare metrics across a major Truvari or merger change without reporting the change.

Manta's current official repository and its Bioconda recipe display different license labels. Record the license bundled with the exact artifact used and review institutional/commercial constraints rather than assuming one label applies to every build.

## Install isolated environments

Use command-local channel settings so the user's global Conda configuration is not changed. Define an explicit environment root:

```bash
SV_ENV_ROOT=/abs/path/to/sv_envs
```

Inspect the package manager and target platform:

```bash
uname -s
uname -m
mamba --version
mamba search --channel conda-forge --channel bioconda manta
mamba search --channel conda-forge --channel bioconda dysgu
mamba search --channel conda-forge --channel bioconda delly
```

Run dry-runs before creation:

```bash
mamba create --dry-run --prefix "${SV_ENV_ROOT}/manta-1.6.0" \
  --channel conda-forge --channel bioconda --strict-channel-priority \
  manta=1.6.0

mamba create --dry-run --prefix "${SV_ENV_ROOT}/dysgu-1.9.0" \
  --channel conda-forge --channel bioconda --strict-channel-priority \
  dysgu=1.9.0

mamba create --dry-run --prefix "${SV_ENV_ROOT}/delly-2.5.1" \
  --channel conda-forge --channel bioconda --strict-channel-priority \
  delly=2.5.1

mamba create --dry-run --prefix "${SV_ENV_ROOT}/sv-integration" \
  --channel conda-forge --channel bioconda --strict-channel-priority \
  samtools=1.24 bcftools=1.24 truvari=5.4.0 svdb=2.12.0 survivor=1.0.7
```

Only after the dry-run is reviewed and installation is authorized, repeat the accepted commands without `--dry-run`. If the integration environment does not solve, split Truvari, SVDB, and SURVIVOR into separate prefixes instead of relaxing pins or channel priority silently.

Manta availability is platform-sensitive. If no native build exists for the target host, use an authorized Linux HPC node or a version-tagged Biocontainer. Pin a digest after pulling; never use an unqualified `latest` tag.

After installation, export both human-readable and exact locks:

```bash
conda env export --prefix "${SV_ENV_ROOT}/dysgu-1.9.0" --no-builds > /abs/path/to/locks/dysgu.environment.yaml
conda list --explicit --prefix "${SV_ENV_ROOT}/dysgu-1.9.0" > /abs/path/to/locks/dysgu.explicit.txt
```

Repeat for every environment. Store the original solver command and stdout/stderr beside the locks.

## Verify installations

An installed package is not accepted until its intended entry point responds and a smoke test passes.

```bash
conda run --prefix "${SV_ENV_ROOT}/manta-1.6.0" configManta.py --help
conda run --prefix "${SV_ENV_ROOT}/dysgu-1.9.0" dysgu --version
conda run --prefix "${SV_ENV_ROOT}/dysgu-1.9.0" dysgu test
conda run --prefix "${SV_ENV_ROOT}/delly-2.5.1" delly --version
conda run --prefix "${SV_ENV_ROOT}/delly-2.5.1" delly sr --help
conda run --prefix "${SV_ENV_ROOT}/sv-integration" bcftools --version
conda run --prefix "${SV_ENV_ROOT}/sv-integration" samtools --version
conda run --prefix "${SV_ENV_ROOT}/sv-integration" truvari --version
conda run --prefix "${SV_ENV_ROOT}/sv-integration" svdb --merge --help
conda run --prefix "${SV_ENV_ROOT}/sv-integration" SURVIVOR merge
```

Some programs return nonzero after printing usage. Save both the exit code and help text; confirm that required subcommands/flags are present rather than accepting only a nominal version string.

## Run core callers

Define run-scoped variables with absolute paths:

```bash
SV_RUN_ROOT=/abs/path/to/run_id
SV_REFERENCE=/abs/path/to/reference.fa
SV_ALIGNMENT=/abs/path/to/sample.bam
SV_SAMPLE_ID=sample_id
SV_THREADS=16
```

After confirming that `SV_RUN_ROOT` is a new run path, create caller-specific directories:

```bash
mkdir -p \
  "${SV_RUN_ROOT}/00_meta" \
  "${SV_RUN_ROOT}/01_callers/manta/${SV_SAMPLE_ID}/raw" \
  "${SV_RUN_ROOT}/01_callers/dysgu/${SV_SAMPLE_ID}/raw/work" \
  "${SV_RUN_ROOT}/01_callers/delly/${SV_SAMPLE_ID}/raw" \
  "${SV_RUN_ROOT}/02_normalized/manta" \
  "${SV_RUN_ROOT}/02_normalized/dysgu" \
  "${SV_RUN_ROOT}/02_normalized/delly" \
  "${SV_RUN_ROOT}/03_ensemble" \
  "${SV_RUN_ROOT}/04_benchmark/holdout"
```

Before every caller:

```bash
samtools quickcheck -v "${SV_ALIGNMENT}"
samtools view -H "${SV_ALIGNMENT}"
bcftools --version
```

Verify the FASTA index, alignment index, coordinate sort order, read-group sample name, contig names/lengths, duplicate-processing provenance, and CRAM reference access. Do not proceed merely because `quickcheck` is silent.

### Manta germline WGS

```bash
conda run --prefix "${SV_ENV_ROOT}/manta-1.6.0" \
  configManta.py \
  --bam "${SV_ALIGNMENT}" \
  --referenceFasta "${SV_REFERENCE}" \
  --runDir "${SV_RUN_ROOT}/01_callers/manta/${SV_SAMPLE_ID}/raw/run"

conda run --prefix "${SV_ENV_ROOT}/manta-1.6.0" \
  "${SV_RUN_ROOT}/01_callers/manta/${SV_SAMPLE_ID}/raw/run/runWorkflow.py" \
  -m local -j "${SV_THREADS}"
```

Preserve at least `diploidSV.vcf.gz`, `candidateSV.vcf.gz`, indexes, workflow state, and logs. Do not substitute `candidateSV` for the scored germline result without declaring the objective.

### Dysgu paired-end WGS

```bash
conda run --prefix "${SV_ENV_ROOT}/dysgu-1.9.0" \
  dysgu run \
  -p "${SV_THREADS}" \
  "${SV_REFERENCE}" \
  "${SV_RUN_ROOT}/01_callers/dysgu/${SV_SAMPLE_ID}/raw/work" \
  "${SV_ALIGNMENT}" \
  > "${SV_RUN_ROOT}/01_callers/dysgu/${SV_SAMPLE_ID}/raw/${SV_SAMPLE_ID}.vcf"
```

Keep the selected model and every non-default argument. Dysgu's default germline model incorporates diploid assumptions; reassess it for pooled, polyploid, aneuploid, or mosaic material.

### Delly paired-end WGS

```bash
conda run --prefix "${SV_ENV_ROOT}/delly-2.5.1" \
  delly sr \
  -g "${SV_REFERENCE}" \
  -o "${SV_RUN_ROOT}/01_callers/delly/${SV_SAMPLE_ID}/raw/${SV_SAMPLE_ID}.bcf" \
  "${SV_ALIGNMENT}"
```

Use `bio-delly-sv-calling` for exclusion regions, cohort site merge/re-genotyping, germline filtering, somatic designs, and legacy `delly call` detection. Do not label a mutant-parent comparison as tumor-control.

For GRIDSS2, SvABA, CNVpytor, or another optional caller, read its current official help and create a separate pinned environment. Do not invent a command by analogy with another caller.

## Prepare callsets for integration

Keep raw and caller-filtered layers separate. For every chosen input:

1. Confirm one intended biological sample and the same coordinate reference.
2. Preserve caller FILTER, FORMAT, BND mate/orientation, `CIPOS`/`CIEND`, inserted sequence, and original record ID.
3. Normalize contig aliases and sample names using a recorded map; never mix assemblies.
4. Sort, BGZF-compress, and index without silently reclassifying events.
5. Record caller name, version, environment lock, alignment mode, and raw checksum in `ensemble_manifest.tsv`.

Create one normalized integration input per caller. These commands only sort and convert the containers; caller-specific representation harmonization and sample/contig renaming must be declared separately when needed:

```bash
conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  bcftools sort \
  -Oz \
  -o "${SV_RUN_ROOT}/02_normalized/dysgu/${SV_SAMPLE_ID}.vcf.gz" \
  "${SV_RUN_ROOT}/01_callers/dysgu/${SV_SAMPLE_ID}/raw/${SV_SAMPLE_ID}.vcf"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  bcftools index --tbi "${SV_RUN_ROOT}/02_normalized/dysgu/${SV_SAMPLE_ID}.vcf.gz"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  bcftools sort \
  -Oz \
  -o "${SV_RUN_ROOT}/02_normalized/manta/${SV_SAMPLE_ID}.vcf.gz" \
  "${SV_RUN_ROOT}/01_callers/manta/${SV_SAMPLE_ID}/raw/run/results/variants/diploidSV.vcf.gz"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  bcftools index --tbi "${SV_RUN_ROOT}/02_normalized/manta/${SV_SAMPLE_ID}.vcf.gz"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  bcftools sort \
  -Oz \
  -o "${SV_RUN_ROOT}/02_normalized/delly/${SV_SAMPLE_ID}.vcf.gz" \
  "${SV_RUN_ROOT}/01_callers/delly/${SV_SAMPLE_ID}/raw/${SV_SAMPLE_ID}.bcf"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  bcftools index --tbi "${SV_RUN_ROOT}/02_normalized/delly/${SV_SAMPLE_ID}.vcf.gz"
```

Run the bundled ensemble-manifest validator before merging. Sorting is not event harmonization, and `bcftools norm` is not automatically safe for all symbolic/BND representations.

## Choose an integration engine

| Need | Preferred route | Boundary |
|---|---|---|
| Tagged cross-caller merge with separate interval/BND/INS controls | SVDB | Explicitly calibrate representative priority and matching parameters |
| Position-oriented compatibility or parameter sensitivity analysis | SURVIVOR | Union first; do not treat its support count as independent biological truth |
| Truth-set benchmarking and representation-aware redundancy collapse | Truvari | Not a drop-in cross-caller support counter |
| Combine different samples at already harmonized sites | `bcftools merge` | Does not determine whether caller records represent one event |
| Append records/regions | `bcftools concat` | Does not collapse equivalent events |

Use one engine and one versioned `matching_policy.yaml` for all ensemble views in a comparison. Changing the merger or parameters changes the result.

## Merge with SVDB

Current SVDB accepts unique caller tags and explicit representative priority. Build a union without `--pass_only` and without `--no_var` unless the project explicitly intends those semantics:

```bash
: "${SV_INTERVAL_OVERLAP:?set a calibrated reciprocal-overlap value from matching_policy.yaml}"
: "${SV_BND_DISTANCE:?set a calibrated BND distance in bp from matching_policy.yaml}"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  svdb --merge \
  --vcf \
    "${SV_RUN_ROOT}/02_normalized/manta/${SV_SAMPLE_ID}.vcf.gz:manta" \
    "${SV_RUN_ROOT}/02_normalized/dysgu/${SV_SAMPLE_ID}.vcf.gz:dysgu" \
    "${SV_RUN_ROOT}/02_normalized/delly/${SV_SAMPLE_ID}.vcf.gz:delly" \
  --priority manta,dysgu,delly \
  --no_intra \
  --overlap "${SV_INTERVAL_OVERLAP}" \
  --bnd_distance "${SV_BND_DISTANCE}" \
  --data_profile cohort \
  | bgzip -c > "${SV_RUN_ROOT}/03_ensemble/union.svdb.vcf.gz"

tabix -p vcf "${SV_RUN_ROOT}/03_ensemble/union.svdb.vcf.gz"
```

`--priority` selects the representative and therefore must be justified. `--no_intra` prevents the merge step from collapsing records within one caller; retain it when caller-internal duplicates must remain auditable. Choose the insertion data profile from sequence availability and the installed help rather than the label alone.

As audited on 2026-08-13, current SVDB merge defaults include reciprocal overlap 0.95 and BND distance 2000 bp, whereas the paper used 0.6 and 1000 bp with an older workflow. Do not rely on either set as a universal default. Pass explicit, calibrated values and save the rendered command.

Inspect the output header to identify SVDB's caller-membership fields. Convert them into `membership.tsv`, calculate tool and algorithm-family support separately, and derive `supported` and `rescued_singletons` from the same `union.svdb.vcf.gz`. Do not assume another merger's `SUPP` field exists in SVDB.

## Merge with SURVIVOR

Create a deterministic input list in declared priority order, one absolute VCF path per line. Render every positional argument from `matching_policy.yaml`:

```bash
: "${SV_MAX_DISTANCE:?set a calibrated distance in bp from matching_policy.yaml}"
: "${SV_REQUIRE_TYPE:?set 0 or 1 from matching_policy.yaml}"
: "${SV_REQUIRE_STRAND:?set 0 or 1 from matching_policy.yaml}"
: "${SV_ESTIMATE_DISTANCE:?set 0 or 1 from matching_policy.yaml}"
: "${SV_MIN_SIZE:?set the declared minimum SV size in bp from matching_policy.yaml}"

conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  SURVIVOR merge \
  /abs/path/to/vcf_list.txt \
  "${SV_MAX_DISTANCE}" \
  1 \
  "${SV_REQUIRE_TYPE}" \
  "${SV_REQUIRE_STRAND}" \
  "${SV_ESTIMATE_DISTANCE}" \
  "${SV_MIN_SIZE}" \
  "${SV_RUN_ROOT}/03_ensemble/union.survivor.vcf"
```

Use minimum caller support `1` for the union. Compress/index that union, then derive a supported view from the same records after verifying the installed output header and `SUPP`/`SUPP_VEC` semantics. Do not rerun clustering with minimum support `2`, because a second clustering run can make union and supported views non-comparable.

SURVIVOR's single maximum distance applies broadly across representations. Use it only when that approximation is acceptable or as a parameter-sensitivity branch. Preserve singletons and compute algorithm-family support outside SURVIVOR.

## Use Truvari correctly

Use Truvari primarily to benchmark fixed candidate callsets against a fixed truth set:

```bash
conda run --prefix "${SV_ENV_ROOT}/sv-integration" \
  truvari bench \
  -b /abs/path/to/truth.vcf.gz \
  -c "${SV_RUN_ROOT}/03_ensemble/union.svdb.vcf.gz" \
  -f "${SV_REFERENCE}" \
  -o "${SV_RUN_ROOT}/04_benchmark/holdout/union_svdb"
```

Truvari `collapse` can consolidate redundant variants in a suitably prepared merged VCF, but it does not by itself create trustworthy caller-family support semantics. The official quick-start example uses `bcftools merge -m none` across samples before `collapse`; do not add `--force-samples` to same-sample caller VCFs merely to imitate that example. Confirm sample identity, representation, and membership requirements first.

Pin Truvari 4.2.2 to reproduce the 2026 paper. For current Truvari, inspect `bench --help` and `collapse --help`, rerun a development benchmark, and keep type-aware and insertion-sequence-aware analyses when those are biological claims.

## Validate ensemble outputs

Acceptance requires all of the following:

- raw, filtered, normalized, and merged files are distinct and checksum-recorded;
- every VCF/BCF parses and indexes;
- every event maps back to original caller IDs and coordinates;
- union events partition into supported and singleton views under one matching policy;
- tool support and algorithm-family support are both available;
- BND mates/orientations and insertion sequences are not silently discarded;
- counts are reported by caller, SVTYPE, size bin, FILTER, support count, and region class;
- parameter-sweep decisions use development truth and are evaluated on untouched holdout data;
- commands, versions, environment locks, resources, timestamps, and exit codes are retained.

Run:

```bash
python3 scripts/validate_ensemble_manifest.py \
  --manifest "${SV_RUN_ROOT}/00_meta/ensemble_manifest.tsv" \
  --output-prefix "${SV_RUN_ROOT}/00_meta/ensemble_preflight"

bcftools view -h "${SV_RUN_ROOT}/03_ensemble/union.svdb.vcf.gz"
bcftools index --stats "${SV_RUN_ROOT}/03_ensemble/union.svdb.vcf.gz"
bcftools stats "${SV_RUN_ROOT}/03_ensemble/union.svdb.vcf.gz"
```

Write QC tables as TSV and XLSX. Preserve merger logs and negative benchmark results.

## Failure modes

| Failure | Required response |
|---|---|
| Solver cannot satisfy a monolithic environment | Split per caller/harmonizer; do not unpin silently |
| Package absent for OS/architecture | Use an authorized pinned container/HPC environment or stop |
| Installed help differs from this reference | Follow installed help, record the difference, and revalidate |
| Manta Python 2 contaminates modern tool environment | Recreate isolated prefixes; do not repair `base` in place |
| Input sample/reference differs across callers | Stop before merging |
| Caller tags collide | Assign unique tags and rebuild the manifest |
| BND/INS representation cannot be harmonized | Keep a separate representation-specific lane |
| Supported view was reclustered separately | Regenerate it from the union membership table |
| Merger parameters were chosen on final truth | Label exploratory or retune on development and reevaluate holdout |
| Installation or merge would overwrite existing output | Stop and create a new run/environment prefix |

## Primary sources

- Bioconda usage and channel policy: <https://bioconda.github.io/index.html#usage>
- samtools Bioconda recipe: <https://bioconda.github.io/recipes/samtools/README.html>
- bcftools Bioconda recipe: <https://bioconda.github.io/recipes/bcftools/README.html>
- Manta official repository: <https://github.com/Illumina/manta>
- Manta Bioconda recipe: <https://bioconda.github.io/recipes/manta/README.html>
- Dysgu official repository: <https://github.com/kcleal/dysgu>
- Dysgu Bioconda recipe: <https://bioconda.github.io/recipes/dysgu/README.html>
- Delly official repository: <https://github.com/dellytools/delly>
- Delly Bioconda recipe: <https://bioconda.github.io/recipes/delly/README.html>
- SVDB official repository: <https://github.com/J35P312/SVDB>
- SVDB Bioconda recipe: <https://bioconda.github.io/recipes/svdb/README.html>
- SURVIVOR official repository: <https://github.com/fritzsedlazeck/SURVIVOR>
- SURVIVOR Bioconda recipe: <https://bioconda.github.io/recipes/survivor/README.html>
- Truvari official repository: <https://github.com/ACEnglish/truvari>
- Truvari Bioconda recipe: <https://bioconda.github.io/recipes/truari/README.html>
- bcftools official repository: <https://github.com/samtools/bcftools>
- bcftools Bioconda recipe: <https://bioconda.github.io/recipes/bcftools/README.html>
