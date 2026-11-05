# Task Types

Use the closest matching sections and combine them when a task spans execution
environments.

## Local Background Process

Check:

- process and captured exit state;
- stdout/stderr advancement and new error evidence;
- output size, modification time, and expected checkpoints;
- disk space and other relevant resource limits;
- wrapper or pid-file state when present.

Record the submission command, process identifier, environment, logs, and
expected outputs.

## Remote Job

Use an available, supported transport appropriate to the environment: a
persistent remote session, SSH, scheduler interface, or project-provided
monitor command.

- Prefer a persistent connection when available and reliable.
- Batch short read-only checks to reduce connection churn.
- Raw SSH is acceptable when it is the available authorized transport; avoid
  high-frequency repeated connections.
- Do not assume a host alias, credential method, or named tool.
- Record the actual host, working directory, environment, status command, and
  transport used.

Check the remote process or scheduler state, logs, outputs, disk/quota, and
stage-specific checkpoints.

## Wrapper or Tmux Harness

Require when available:

- RUN_ID, RUN_DIR, and current attempt;
- MONITOR_CMD and machine-readable state;
- terminal state, live payload/session, lock, heartbeat, and log paths;
- scheduler/process identifier for each attempt.

Decision rules:

- SUCCESS: execution reached a success terminal state; continue through
  completion gates.
- FAILED plus no live payload plus released lock:
  - OBSERVE_ONLY: preserve evidence and report;
  - REPAIR_PREAUTHORIZED: apply the bounded same-run recovery contract;
  - otherwise: DECISION_REQUIRED.
- RUNNING with the session gone or heartbeat stale: anomalous.
- Held lock with no live payload: anomalous; do not clean it without explicit
  authority and owner-exclusion evidence.

Do not rely on free-text grep, last_attempt, or session presence alone. Do not
perform unauthorized, evidence-free, or repeated blind resubmission.

## Workflow Engines

For Snakemake, Nextflow, WDL/Cromwell, or similar engines, inspect:

- engine and scheduler state;
- main and per-rule/per-process logs;
- work-directory and checkpoint progression;
- failed rule/process and its exact command;
- lock files as evidence;
- shard-level progress and partial-output consistency.

Do not unlock, cancel, or resubmit in OBSERVE_ONLY. Under
REPAIR_PREAUTHORIZED, preserve the failed attempt and resume only when the root
cause and bounded repair are supported by evidence.

## Scheduler Jobs

For SLURM, SGE, PBS, LSF, or similar schedulers, collect:

- job and array-task IDs, state, exit code, runtime, memory, and node;
- scheduler stdout/stderr;
- timeout, OOM, preemption, dependency, cancellation, and array-task failures;
- new job ID linked to the same logical RUN_ID when recovery creates one.

Do not cancel or resubmit in OBSERVE_ONLY. In REPAIR_PREAUTHORIZED, create a new
scheduler attempt only after preserving the failed job evidence and confirming
that scientific inputs and parameters remain unchanged.

## Downloads and Transfers

Check:

- source and destination identities;
- expected size, checksum, manifest, and partial-file policy;
- network errors, authentication state, disk space, and retry count;
- whether resumption preserves or replaces a partial file.

Do not treat byte growth as completion. Verify checksum or source-defined
integrity whenever available.

## Generic Bioinformatics Outputs

Use stage-specific signals:

- FASTQ/BAM/CRAM: file size, format validation, read-count logs, index creation,
  sample identity, and shard completion.
- VCF/BCF/gVCF: contig shards, indexes, header/reference consistency,
  sample/contig completeness, and variant-count sanity checks.
- Annotation tables: chunk or partition completion, schema, row/key counts,
  missingness, and input-output joins.
- Reports: expected TSV/XLSX/PDF/PNG artifacts, source-data linkage, render logs,
  and cross-format consistency.

File existence or growth proves only that output is being produced. Final
acceptance requires applicable format, index, record-count, sample/chromosome,
and project-specific semantic QA.

## Rice Mutagenesis and Breeding Pipelines

Use project-provided paths and contracts; do not hard-code them. Possible
progress and acceptance signals include:

- workflow progress by rule, sample, chromosome, or shard;
- alignment, duplicate, index, and mapping-QC artifacts;
- per-chromosome calling, joint genotyping, normalization, filtering, and
  annotation evidence;
- parent/control subtraction and generation/sample identity checks;
- candidate tables, KASP/Sanger evidence, phenotype links, and release reports;
- machine-readable tables, human-facing workbooks, figures, manifests, and
  immutable input evidence.

Detection of a variant is not proof that it was induced, inherited, causal, or
valuable for breeding. Monitoring must not elevate execution progress into a
scientific conclusion.
