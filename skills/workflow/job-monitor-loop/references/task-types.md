# Task Types

Use the closest matching section. Combine sections when a task spans local and remote execution.

## Local Background Shell

Check:
- pid state with `ps`.
- stdout/stderr log tail and whether the log advanced.
- output file size and modification time.
- disk space for the output filesystem.
- shell exit status if captured by the wrapper.

Useful evidence:
- submission command,
- pid file if present,
- `nohup.out`, explicit log file, or terminal session output,
- expected output paths.

## SSH Remote Job

Mandatory access path for `sxyH3`, `sxyH2`, and `sxycloud1.top` hosts:
- Use persistent `ssh-session` MCP tools, such as `mcp__ssh_session__execute_command`, `mcp__ssh_session__execute_command_async`, and `mcp__ssh_session__get_command_status`.
- Do not run repeated raw `ssh host cmd` checks during a monitoring loop.
- Batch multiple short checks into one remote command when possible.
- Use raw `ssh`, `scp`, or `rsync` only for documented exceptions such as file transfer or PTY-specific work.

Check on the remote host:
- remote pid, scheduler job id, or process tree.
- remote log tail.
- remote output timestamps and sizes.
- remote disk/quota status when output stalls.

Record:
- host alias,
- remote working directory,
- remote conda/module environment,
- exact command used for status checks.

## Tmux + Wrapper.sh Harness

Use this section for jobs submitted by `submit-monitor` or an equivalent remote `tmux + wrapper.sh` state-machine harness.

Required identifiers:
- `RUN_ID`
- `RUN_DIR`
- `HOST`
- `MONITOR_CMD`, usually `bash <RUN_DIR>/monitor.sh <RUN_DIR>`

Authoritative evidence:
- `monitor.sh` output in `KEY=VALUE` format.
- `state/terminal_state` or equivalent `STATE_terminal_state`.
- `state/attempt` for the current attempt index.
- `active.lock` or emitted `LOCK` state.
- `TMUX` state as supporting evidence.
- heartbeat age as a liveness signal.

Do not rely on:
- free-text grep as the primary state signal,
- `last_attempt` alone,
- `tmux ls` alone,
- auto-resubmit after failure.

Decision table:
- `STATE_terminal_state=SUCCESS` -> completed; close monitoring after output checks.
- `STATE_terminal_state=FAILED` and `TMUX=gone` and `LOCK=released` -> structural failure; gather stderr/log tails and ask the user before any resubmit.
- `STATE_terminal_state=RUNNING` and `TMUX=alive` and fresh heartbeat -> normal, even if output is temporarily stagnant.
- `STATE_terminal_state=RUNNING` and `TMUX=gone` -> suspicious or externally killed; gather forensics and ask the user.
- `LOCK=held` and `TMUX=gone` -> stale lock; report and ask before cleanup.

## Workflow Engines

For Snakemake, Nextflow, WDL/Cromwell, or similar engines, check:
- engine process or scheduler job state.
- engine main log plus per-rule/per-process logs.
- work directory growth and checkpoint files.
- failed rule/process names and exact shell command if available.
- lock files only as evidence; do not delete them without approval.

Normal progress may be shard-specific. A large workflow can be healthy even when one output file is unchanged if other shards are advancing.

## HPC Scheduler Jobs

For SLURM, SGE, PBS, LSF, or similar:
- query scheduler state with the cluster-appropriate command.
- collect job id, state, exit code, runtime, memory, and node if available.
- inspect scheduler stdout/stderr logs.
- check for timeout, OOM, preemption, dependency failure, cancelled jobs, and array-task failures.

Do not resubmit, cancel, or modify scheduler jobs without explicit approval.

## Generic Bioinformatics Outputs

Use domain-specific progress signals:
- FASTQ/BAM/CRAM: file size growth, index creation, read-count logs, temporary shard outputs.
- VCF/BCF/gVCF: contig shards, tabix indexes, completed chromosome outputs, variant-count summaries.
- Annotation tables: TSV chunk outputs, SQLite/Parquet partitions, index/checkpoint files.
- Reports: expected PDF/PNG/XLSX/TSV outputs and render logs.

Large compressed outputs may update in bursts. Treat no growth as anomalous only when logs and intermediate files also stop advancing beyond the expected stage duration.

## Rice Mutagenesis Pipelines

Use these as optional progress signals when monitoring rice heavy-ion mutagenesis, variant calling, annotation, or breeding-analysis pipelines. Do not hard-code project paths unless the current task provides them.

Typical signals:
- Snakemake or workflow logs advancing by rule, sample, chromosome, or shard.
- FASTQ to BAM stages: fastp reports, mapped BAM/CRAM growth, duplicate-marked BAMs, `.bai` or `.crai` indexes.
- Variant calling stages: per-chromosome VCF/gVCF/BCF shards, tabix indexes, joint-genotyping logs, variant-count summaries.
- Annotation stages: SnpEff or VEP logs, annotated VCF plus `.tbi`, TSV/XLSX summaries, per-sample or per-chromosome tables.
- Reporting stages: reproducible TSV plus XLSX outputs, PDF/PNG figure exports, and render logs.
