---
name: staged-agent-run-protocol
description: >-
  Use this skill for complex staged research, bioinformatics, molecular breeding,
  heavy-ion mutagenesis, reproducible data analysis, long-running pipelines, or
  tasks that need phase separation, fixed output paths, TODO tracking, QC gates,
  provenance, checksums, frozen results, HTML navigation, or multi-session Agent
  handoff. Chinese trigger hints: 阶段化执行, staged run, 每个会话一个阶段,
  可复现流程, 长任务监控, 固定路径, 质控门禁, provenance, TODO 动态更新.
---

# Staged Agent Run Protocol

Version: `0.2.1-rc`

Use this skill to turn complex research work into an auditable staged run.

Core rule: local protocol Markdown, TSV, and YAML are the canonical run-control sources. HTML is rendered locally for human navigation and is not a source of truth.

Language rule: Human-facing Markdown and HTML must use Chinese by default. Code, variables, commands, file paths, filenames, table headers, IDs, software names, environment names, and literal status values remain English.

## When To Trigger

Apply the protocol when the task involves any of these:

- multiple inputs, outputs, scripts, stages, or sessions
- formal bioinformatics or molecular breeding results
- paper figures, tables, reports, or archived outputs
- long-running jobs, background execution, or monitoring
- remote/server execution with local review, rendering, reporting, or archiving
- code changes requiring tests and reproducible QA
- downstream reuse, review, audit, provenance, or handoff

Do not use the full protocol for simple Q&A, translation, light polishing, or one-off explanations with no file artifacts.

## Profiles

- `lite`: run directory, phase Markdown, TODO, command/input/output/QC records. HTML optional.
- `standard`: default. Full run directory, phase Markdown, `index.html`, stage provenance, QC report, manifests, commands/jobs/monitor logs.
- `strict`: paper-core or high-risk work. HTML for every phase/stage, final checksums, frozen outputs, `reproduce.sh`, environment snapshot, final audit.

## Phase Boundary

Default one formal session equals one protocol phase.

- Phase 0 Bootstrap: create run directory and initial metadata only.
- Phase 1 Analysis: understand context, risks, strategies. Do not execute formal workflow.
- Phase 2 Plan And Path Freeze: lock paths, stages, QC, commands, monitoring, final outputs. Do not implement full workflow.
- Phase 3 Execution And Finalization: execute only the approved plan, stage by stage, with QC gates and provenance.

For high-risk, long-running, paper-core, or large file-change tasks, keep Phase 1, Phase 2, and Phase 3 in separate sessions.

## Required Sources Of Truth

- `metadata/run.yaml`: static run metadata.
- `metadata/status.yaml`: current run summary.
- `02_plan/stage_registry.tsv`: stage status and gate authority.
- `todo.tsv`: current action items.
- `todo_history.tsv`: TODO state history.
- `logs/commands.tsv`: formal command audit log.
- `logs/jobs.tsv`: long job submissions.
- `logs/monitor.tsv`: monitoring audit log.
- `metadata/hosts.tsv`: registered remote/server hosts.
- `metadata/path_maps.tsv`: remote canonical output to local mirror mappings.
- `metadata/env_registry.tsv`: registered local and remote formal environments.
- `metadata/software_registry.tsv`: tool version, executable, and install-source registry.
- `metadata/reference_registry.tsv`: reference genome, annotation, index, and database registry.
- `metadata/storage_policy.tsv`: raw/work/scratch/results/mirror retention policy.
- `logs/remote_commands.tsv`: all formal remote command audit rows.
- `logs/remote_jobs.tsv`: remote job audit log.
- `logs/sync.tsv`: remote/local synchronization provenance.
- `logs/install.tsv`: install, update, and uninstall audit rows.
- `logs/disk_usage.tsv`: local and remote disk usage checks.
- `logs/cleanup_candidates.tsv`: cleanup candidates only; not deletion authorization.
- `monitoring/remote_monitor_plan.md`: remote monitoring and sync policy.
- `path_registry.tsv`: planned and allowed paths.
- `files_manifest.tsv`: observed/audited files.

`index.html` is rendered locally from these files and must not be hand-maintained as the only status record.

The protocol control files live in the local run directory by default. Remote servers may hold remote logs, manifests, checksums, remote scientific outputs, and genuine pipeline reports, but not the primary protocol control layer.

## Required Workflow

1. If no run exists, initialize it with `scripts/init_agent_run.py`.
2. At the start of every phase, read `README.md`, `metadata/status.yaml`, `todo.tsv`, and relevant phase outputs.
3. Use subagents when helpful, but save their outputs under the phase `subagents/` directory and keep main-session decisions authoritative.
4. Before Phase 3, confirm Phase 2 plan approval and ensure paths, stages, QC criteria, and monitoring plan are registered.
5. During Phase 3, record every formal command in `logs/commands.tsv`; background jobs also go to `logs/jobs.tsv`.
6. A required stage may only unblock the next required stage when `gate_status` is `QC_Passed` or `Waived_With_Decision`.
7. QC failure must create or update a `Blocked` or `Active` TODO and cite evidence.
8. Final outputs must be checksummed and frozen in `03_execution/final/frozen_outputs.tsv`.

## Language Policy

- Human-facing Markdown and HTML are Chinese-first by default.
- Keep code, variables, commands, file paths, filenames, TSV/YAML field names, database identifiers, sample IDs, tool names, environment names, and exact status values in English.
- Section titles in protocol Markdown should be Chinese unless they are literal protocol names, file names, status values, or command examples.
- `render_index.py` output should use Chinese labels for human navigation while preserving canonical file paths and table column names.
- Scientific figure/table text follows the project figure policy; this language rule covers protocol documents and review/report pages.

## Remote Execution Layer

Use the remote layer when heavy compute runs on a server/HPC machine while the local run directory is used for review, rendering, reporting, and archiving. Do not run real remote commands unless the user has explicitly approved the execution phase and the host, path map, stage, environment, software versions, storage policy, logs, and monitoring plan are registered.

Remote rules:

- The server-side result is the remote canonical output.
- The local synchronized copy is a local mirror. It is for viewing, rendering, reporting, handoff, and archive packaging; it is not the canonical source.
- Protocol navigation HTML (`index.html`, phase HTML, stage HTML, QC HTML) is local-only and must be rendered under the local run directory. It must not be generated on the server, registered as remote canonical output, or used as remote provenance.
- Server-generated HTML is allowed only when it is a genuine scientific/pipeline output, and then it must be registered as a final/report artifact, checksummed, and synced into `local_results/reports/`.
- Protocol Markdown (`README.md`, phase Markdown, `stage.md`, `qc_report.md`, `provenance.md`, decisions, assumptions, handoff notes) is local run-control evidence. It should not be registered as remote canonical output.
- Server-generated Markdown is allowed only when it is a genuine scientific/pipeline report or remote provenance artifact, and then it must be registered, checksummed, and mirrored to `local_results/reports/` or `local_results/provenance/`.
- Register each server in `metadata/hosts.tsv` with `scripts/register_host.py`.
- Register each remote/local mapping in `metadata/path_maps.tsv` with `scripts/register_path_map.py`.
- Register formal local/remote environments in `metadata/env_registry.tsv` with `scripts/register_env.py`.
- Register key tool versions in `metadata/software_registry.tsv` with `scripts/register_software.py`.
- Register reference genomes, annotations, indexes, and databases in `metadata/reference_registry.tsv` with `scripts/register_reference.py`.
- Record every formal remote command in `logs/remote_commands.tsv` with `scripts/log_remote_command.py`.
- Record remote jobs in `logs/remote_jobs.tsv` with `scripts/log_remote_job.py`. This records provenance only; it does not submit a job.
- Every synchronization from or to a server must append a row to `logs/sync.tsv` with `scripts/log_sync.py`.
- `remote_is_canonical` must be `true` and `local_role` must be `local_mirror` for remote output mappings.
- A local mirror used for final or frozen output must have checksum evidence (`checksum_status=matched`) or an explicit `checksum_mismatch_policy`.
- Sync provenance should cite checksum files when available through `remote_checksum_path`, `local_checksum_path`, and `provenance_path`.
- Use `scripts/check_remote_mirror.py` for local mirror checks. It does not connect to remote hosts.
- Do not overwrite remote canonical outputs from local mirrors unless a Phase 2 plan explicitly permits reverse sync and records the decision.

## Local-Remote Role Contract

- Local Codex controls the run, edits code, performs small validation, renders protocol navigation HTML/reports, stores provenance summaries, and keeps final local mirrors.
- Remote servers store raw canonical data, heavy compute outputs, work/scratch files, remote logs, remote environments, references, and remote canonical final outputs.
- Local mirrors should live under `local_results/` by default.
- Do not sync `raw/`, `work/`, `scratch/`, large BAM/CRAM/FASTQ, large temporary VCF, or large temporary matrices to local mirrors by default.
- Final local sync should be whitelist-based: reports, provenance, checksums, QA summaries, frozen manifests, figures, tables, selected final outputs, compressed selected logs, and remote manifest summaries.

From a bioinformatics audit perspective, keep these locally in the run directory:

- Run-control Markdown/YAML/TSV: `README.md`, `TODO.md`, phase docs, stage docs, decisions, assumptions, status, TODO, stage registry, path maps, env/software/reference/storage registries.
- Provenance summaries: command logs, remote command logs, job/monitor/sync/install/disk logs, checksum summaries, frozen output manifests, cleanup candidates.
- Human-review artifacts: local `index.html`, local phase/stage HTML, final report, QC summaries, selected reports.
- Final lightweight scientific outputs: figures (`pdf/png`), tables (`tsv/xlsx`), selected small final VCF/CSV/TSV, compressed selected logs, remote manifest summaries.
- Code and configuration snapshots needed to reproduce the run: scripts, configs, environment lock/export summaries, tool-version files.

Do not keep these locally by default:

- Raw FASTQ/BAM/CRAM, full reference genomes, large indexes, large intermediate VCF/BCF, temporary matrices, work chunks, scratch directories, scheduler working directories, or full remote logs.

## HTML Placement Policy

- `index.html` is always local: `{run_dir}/index.html`.
- Phase/stage navigation HTML, when generated, is local: `{run_dir}/00_brief/*.html`, `{run_dir}/01_analysis/*.html`, `{run_dir}/02_plan/*.html`, `{run_dir}/03_execution/stages/*/*.html`.
- Remote servers must not be the primary location for protocol navigation HTML. Server-side records should be Markdown, TSV, YAML, logs, checksums, manifests, and remote scientific outputs.
- Do not add protocol navigation HTML to `metadata/path_maps.tsv`; it is not a remote canonical output and does not need remote/local mapping.
- If a remote pipeline produces HTML as a real result, classify it as `report_artifact` or `final_report_artifact`, not `index_html` or navigation HTML, and mirror it to `local_results/reports/` with checksum evidence.

## Markdown Placement Policy

- Protocol Markdown is local: `{run_dir}/README.md`, `{run_dir}/00_brief/brief.md`, `{run_dir}/01_analysis/analysis.md`, `{run_dir}/02_plan/plan.md`, `{run_dir}/03_execution/execution.md`, `{run_dir}/03_execution/stages/*/{stage.md,qc_report.md,provenance.md}`, and `{run_dir}/docs/*.md`.
- Do not map protocol Markdown through `metadata/path_maps.tsv`; it is already part of the local control plane.
- Remote Markdown is allowed only as a scientific report artifact or remote provenance artifact, not as the primary phase/stage control document.
- Mirror remote report Markdown to `local_results/reports/`; mirror remote provenance Markdown to `local_results/provenance/`.
- A remote `.md` artifact used in final reporting must have checksum evidence or an explicit mismatch policy, the same as other final local mirrors.

## Host Selection: sxyH3/sxyH2

- Use `host_id=sxyH3` and `host_id=sxyH2`; keep `host_id` aligned with the ssh alias.
- If the user says `sxyH3`, use `sxyH3`. If the user says `sxyH2`, use `sxyH2`.
- If the user only says "server", default to `sxyH3` and record the assumption in `docs/assumptions.md`.
- If both hosts are used, Phase 2 must assign `host_id` by stage. A single stage must not silently span hosts.
- Host changes during Phase 3 require a decision record and updated path maps.

## Environment And Version Governance

- Formal outputs must not be generated by unregistered environments or tools.
- Prefer local `uv` for report/render/check scripts and all protocol Markdown/HTML rendering; record `uv`, Python path/version, lock file, and lock checksum when used for formal outputs.
- Remote formal commands should use a registered `env_id`, explicit environment path, executable path, and observed version evidence.
- Do not use `base`, `latest`, `current`, `test`, `new`, or other ambiguous `env_id` values.
- Install/update/remove actions must be planned in Phase 2 and recorded in `logs/install.tsv`; update `env_registry.tsv` and `software_registry.tsv` afterward.
- Formal command provenance should record `which` evidence, version command output, PATH-sensitive assumptions, and lock/export files.

## Storage And Cleanup Governance

- Register raw, work, scratch, results, logs, env, reference, and local mirror storage policy in `metadata/storage_policy.tsv` when remote compute is enabled.
- Remote raw/reference/final/frozen outputs are never deleted automatically.
- Work, scratch, deprecated envs, failed partial syncs, and duplicate mirrors may only become cleanup candidates.
- Cleanup planning writes `logs/cleanup_candidates.tsv` and `03_execution/final/cleanup_plan.md`; it does not authorize deletion.
- Any real delete, overwrite, env rebuild, or path migration requires explicit user approval and a logged command.

## Remote Phase 3 Stage Order

When remote compute is enabled, Phase 3 starts with `00_remote_preflight`, then normally proceeds:

1. `00_remote_preflight`
2. `01_register_remote_paths`
3. `02_prepare_remote_environment`
4. `03_upload_or_validate_raw_data`
5. `04_run_remote_pipeline`
6. `05_remote_qc`
7. `06_freeze_remote_outputs`
8. `07_sync_final_to_local`
9. `08_local_final_qc`
10. `09_cleanup_plan_only`

`00_remote_preflight` checks connectivity, host identity, user, working directory, disk/quota status, project roots, package managers, Python, and shell context. It must not run formal analysis.

## Long Jobs

For jobs expected to exceed 10 minutes:

- submit in the background, not a foreground interactive session
- register the job in `logs/jobs.tsv`
- monitor with staged backoff: 1 minute x3, then 10 minutes x3, then 30 minutes
- on anomaly, reset to 1 minute checks and write an anomaly TODO
- use the bundled `scripts/monitor_job.py` for local PID/log/output checks, or the existing `job-monitor-loop` skill for remote/wrapper/scheduler monitoring
- for remote jobs, record status checks and sync events in canonical TSV files; do not rely on terminal scrollback or an HTML page as the only evidence
- remote monitoring must include job status, log growth, expected outputs/checkpoints, disk usage, error keywords, and runtime limits

## Bundled Resources

- `references/protocol_v0.1.md`: full protocol specification.
- `templates/staged_agent_run_protocol/`: empty run templates and CSS.
- `scripts/init_agent_run.py`: create a run directory.
- `scripts/render_index.py`: render local `index.html` from canonical sources.
- `scripts/check_manifest.py`: check required protocol files and stage artifacts.
- `scripts/hash_outputs.py`: write checksums for files.
- `scripts/register_stage.py`: add/update `stage_registry.tsv`.
- `scripts/update_todo.py`: create/update TODO rows with history.
- `scripts/validate_gate.py`: validate stage gate evidence before continuation.
- `scripts/write_command_log.py`: append command audit rows.
- `scripts/freeze_outputs.py`: freeze final outputs with checksums.
- `scripts/monitor_job.py`: local long-job monitor with backoff state.
- `scripts/register_host.py`: add/update a remote host record.
- `scripts/register_path_map.py`: add/update a remote canonical to local mirror mapping.
- `scripts/register_env.py`: add/update a formal environment record.
- `scripts/register_software.py`: add/update a tool version record.
- `scripts/register_reference.py`: add/update a reference data record.
- `scripts/register_storage_policy.py`: add/update raw/work/scratch/results/mirror retention policy.
- `scripts/log_remote_command.py`: append remote command provenance without executing it.
- `scripts/log_remote_job.py`: append remote job provenance without submitting a job.
- `scripts/log_sync.py`: append remote/local sync provenance.
- `scripts/log_install.py`: append install/update/remove provenance.
- `scripts/log_disk_usage.py`: append disk usage evidence.
- `scripts/make_cleanup_plan.py`: register cleanup candidates without deleting files.
- `scripts/remote_preflight.py`: create remote preflight artifacts and command template without connecting.
- `scripts/check_remote_mirror.py`: validate local mirror records without remote connections.

## Minimal Commands

```bash
python3 "$HOME/.codex/skills/staged-agent-run-protocol/scripts/init_agent_run.py" \
  --task-name rice_mutation_screening \
  --root agent_runs \
  --profile standard

python3 "$HOME/.codex/skills/staged-agent-run-protocol/scripts/render_index.py" \
  --run-dir agent_runs/2026-05-12_rice_mutation_screening

python3 "$HOME/.codex/skills/staged-agent-run-protocol/scripts/check_manifest.py" \
  --run-dir agent_runs/2026-05-12_rice_mutation_screening
```

Remote layer examples:

```bash
python3 "$HOME/.codex/skills/staged-agent-run-protocol/scripts/register_host.py" \
  --run-dir agent_runs/2026-05-12_rice_mutation_screening \
  --host-id hpc1 \
  --hostname login.example.edu \
  --access-mode manual \
  --scheduler slurm

python3 "$HOME/.codex/skills/staged-agent-run-protocol/scripts/register_path_map.py" \
  --run-dir agent_runs/2026-05-12_rice_mutation_screening \
  --path-map-id map_stage1_outputs \
  --host-id hpc1 \
  --remote-path /remote/project/results/stage1 \
  --local-path mirrors/hpc1/stage1 \
  --checksum-mismatch-policy investigate_before_freeze

python3 "$HOME/.codex/skills/staged-agent-run-protocol/scripts/log_sync.py" \
  --run-dir agent_runs/2026-05-12_rice_mutation_screening \
  --host-id hpc1 \
  --path-map-id map_stage1_outputs \
  --checksum-status matched
```

## Related Skills

- Use `provenance-doc` for deeper sealed provenance practices.
- Use `job-monitor-loop` for remote, scheduler, tmux, or wrapper-managed long jobs.
- Use `handover` before `/clear` or session transfer when the current run state is not fully captured.
