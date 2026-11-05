---
name: staged-agent-run-protocol
description: "Approved research-run execution and recovery with auditable state, provenance, QC gates and frozen outputs. Use for an authorized run, not for planning or ordinary questions."
---

# Staged Agent Run Protocol

Execute approved research plans through an auditable local control plane.
Canonical run-control records are Markdown, TSV, and YAML. Rendered HTML is for
navigation only and is never the sole source of truth.

Use Chinese for human-facing run documents by default. Preserve literal code,
commands, paths, filenames, field names, IDs, environment names, tool names, and
status values in English.

## Execution Boundary

- Apply this protocol to an approved research plan that needs auditable run
  control, including ordinary approved research execution and an explicitly
  invoked or verifiably active three-stage run. It does not itself constrain
  ordinary task reads, file generation, writes, or agent dispatch.
- Runtime-policy model roles apply only within an explicit or active three-stage run.
- Consume an approved plan; do not recreate, debate, or materially redesign it.
- Bootstrap a run directory only to establish control records, not to reopen
  scientific planning.
- Do not repeat approval when all entry conditions pass.
- Pause only for missing or contradictory approval evidence, execution-critical
  ambiguity, material drift from the approved scope, or new destructive or
  external-side-effect authority.
- Route scientific redesign to multi-agent-bioinformatics-planner and long-job
  supervision to job-monitor-loop.

Enter execution directly when:

    plan.status == approved
    approval_evidence is present
    current request asks to execute, continue, or resume
    observed inputs, outputs, and scope match the approved plan

## Approved Plan Contract

Read the plan completely. Require:

    status
    scope
    inputs
    outputs
    acceptance_criteria
    environment
    assumptions
    risks
    approval_evidence

Confirm through read-only checks that referenced paths, environments, and
acceptance criteria are resolvable. Do not ask again about facts already frozen
in the approved plan. If a material conflict is found, cite it and stop before
the affected stage.

## Profiles

- lite: run metadata, stage registry, TODO, command, input/output, and QC records.
- standard: lite plus provenance, manifests, job/monitor logs, checksums, and
  local navigation.
- strict: standard plus frozen outputs, environment snapshot, reproduction
  entry point, final audit, and release-grade evidence.

Choose the profile from the approved plan or risk. Do not inflate a small task
into a strict run without justification.

## Core Sources of Truth

Keep these records when applicable:

- metadata/run.yaml and metadata/status.yaml;
- 02_plan/stage_registry.tsv;
- todo.tsv and todo_history.tsv;
- path_registry.tsv and files_manifest.tsv;
- logs/commands.tsv, logs/jobs.tsv, and logs/monitor.tsv;
- metadata/hosts.tsv and metadata/path_maps.tsv;
- metadata/env_registry.tsv and metadata/software_registry.tsv;
- metadata/reference_registry.tsv and metadata/storage_policy.tsv;
- logs/remote_commands.tsv, logs/remote_jobs.tsv, logs/sync.tsv,
  logs/install.tsv, and logs/disk_usage.tsv;
- logs/cleanup_candidates.tsv;
- 03_execution/final/frozen_outputs.tsv.
- metadata/coordination.yaml;
- coordination/agent_assignments.tsv, coordination/integration_events.tsv,
  and coordination/audit_receipts.tsv;
- coordination/snapshots/ and coordination/revisions/.

Keep the local run directory as the canonical control layer. Do not hand-edit a
rendered HTML page as the only state record.

## Model and Coordination Contract

Within an explicit or active three-stage run, load
`<CODEX_HOME>/policies/three-stage-runtime-v1.json` as the machine-readable
complement to this contract. Its
`explicit_skill_natural_autonomy_or_active_run` activation means
every assignment requires evidence-supported model suitability, terminal assignments cannot reopen,
and current runtime policy permits at most one active writer. It is not a
global model permission rule.

Within an explicit or active three-stage run, new-run stage leads default to
`gpt-6-astra` for ANALYZE/REFINE and `gpt-6.1-sol` for EXECUTE, unless explicit
user model evidence overrides them. Keep the observed root identity distinct
from the actual stage lead. Delegate only with applicable human authority and
available tools; unavailable routes pause without silent fallback. Child model
IDs have no fixed allowlist: current runtime availability and a separate task
capability assessment establish suitability; neither grants stage or file rights.
Legacy records keep their prior compatibility semantics. Use the three-stage
composition contract for evidence schemas and `register_agent_assignment.py`
with `--runtime-evidence`, `--capability-evidence`, `--workflow-stage`,
`--delegation-authorized` and `--delegation-evidence` for dynamic child models.
The registry retains evidence paths and hashes in notes. Root-only canonical
integration, read-only planning, scope isolation and at most one active writer
remain mandatory.

When more than one agent participates, register every assignment before work
starts. Use only `READ_ONLY_REVIEWER`, `STAGING_WRITER`,
`CANONICAL_INTEGRATOR`, and `AUDITOR`. Root is the sole canonical integrator.
Reviewers and auditors are read-only. A staging writer may write only under
`coordination/staging/<assignment_id>/`, and active write scopes must be
disjoint.

Each assignment binds to the current `base_revision`. Agent returns must include
a staged manifest or `return_fingerprint`. Reject stale returns and record the
decision; do not let agents patch moving canonical files or retry indefinitely.
Integrate accepted returns sequentially with `record_integration.py`, advancing
the canonical revision after each accepted change.

All coordination TSV updates are locked read-modify-write transactions and
persistent state replacement is atomic. Locks prevent lost registry updates;
they do not replace role and scope validation.

## Revision Seal and Audit Receipt

Before final audit, require every assignment and local/remote job to be in a
terminal state. Take one manifest snapshot, then take a second observation over
the same canonical scope. Seal only when path, size, mtime-ns, and SHA256 are
identical and no work is active.

An audit receipt must bind all of:

```text
revision_id + manifest_sha256 + scope_fingerprint + audit_cutoff
```

Validate the sealed revision immediately before using the receipt. Any later
canonical change, manifest drift, or scope change invalidates the receipt. Mark
the reason and re-run only the minimal affected dependency, seal, and audit
chain. Do not interpret an mtime-only change as scientific drift until its
semantic equivalence rule has been evaluated.

## Execution Workflow

1. Read the approved plan, nearest project rules, current status, TODO, and any
   prior attempt evidence.
2. Discover the actual host, project root, environment, executable paths,
   versions, reference resources, storage policy, and output mappings.
3. Initialize or resume the run with the bundled scripts. Preserve an existing
   RUN_ID and attempt history during recovery.
4. Register stages, paths, environments, software, references, hosts, and
   remote/local mappings before the affected formal stage.
5. Execute only approved stages. Record every formal command; record background
   and remote jobs in their dedicated logs.
6. Apply stage QC. Unblock the next required stage only when gate_status is
   QC_Passed or Waived_With_Decision.
7. On failure, preserve logs and partial outputs, update TODO/status, and follow
   the approved recovery authority. Do not hide or overwrite a failed attempt.
8. Quiesce assignments/jobs, take two stable observations, and seal the current
   canonical revision.
9. Run audit against that sealed revision and issue a revision-bound receipt.
10. Freeze accepted outputs with checksums and write a final acceptance report.

## Host and Environment Selection

- Use the host specified by the plan, project configuration, registry, or user.
- Discover missing host facts with read-only checks when possible.
- Never default an unspecified server to a named host. If multiple choices
  would change outputs or cost, report the ambiguity before execution.
- Use the project environment and lock/config files named in the plan.
- Conda/mamba, uv, containers, modules, or project-specific environments are
  all valid when they are the approved or existing project mechanism.
- Do not create, rebuild, install, or upgrade an environment unless the approved
  scope includes it.
- Record the observed executable, version, environment identifier, and relevant
  lock or export evidence for formal outputs.

## Remote Execution

Enable the remote layer only when the approved plan uses it.

- Treat server-side scientific outputs as remote canonical outputs and local
  synchronized copies as mirrors.
- Keep protocol Markdown, YAML, TSV, and navigation HTML in the local control
  directory.
- Register each host and remote/local path mapping.
- Record remote commands, jobs, synchronization events, checksum status, and
  attempt identifiers.
- Whitelist final synchronization. Do not mirror raw FASTQ/BAM/CRAM, large
  references, work directories, or scratch data unless explicitly required.
- Do not reverse-sync over canonical remote outputs unless the approved plan
  expressly permits it.
- Select only the remote preflight, environment, pipeline, QC, freeze, sync, and
  local-QC stages that apply. Do not create irrelevant stages mechanically.

## Long Jobs

- Submit long-running work in the background and retain job IDs, logs, output
  paths, and expected checkpoints.
- Use job-monitor-loop for staged backoff, evidence classification, and bounded
  recovery.
- Record each attempt under the same logical RUN_ID when recovering an approved
  run; preserve failed-attempt evidence.
- Do not use terminal scrollback or process presence as the only completion
  evidence.

## Acceptance and Cleanup

Accept completion only when all applicable gates pass:

- expected terminal state;
- expected artifacts and schema/content checks;
- task-specific semantic QA;
- command, environment, parameter, and provenance records;
- checksums or manifest evidence;
- source-input immutability or explicitly documented authorized change.
- a current sealed revision and valid audit receipt when audit applies.

Cleanup planning does not authorize deletion. Register cleanup candidates, and
delete only task-owned temporary artifacts or targets explicitly authorized by
the user. Never delete raw inputs, references, final outputs, or failed-attempt
evidence automatically.

## Bundled Resources

- Use scripts/init_agent_run.py to initialize a run.
- Use scripts/register_stage.py, update_todo.py, and validate_gate.py for stage
  and gate control.
- Use scripts/write_command_log.py and the log_remote_* scripts for provenance.
- Use scripts/register_host.py, register_path_map.py, register_env.py,
  register_software.py, register_reference.py, and register_storage_policy.py
  for registries.
- Use scripts/hash_outputs.py, freeze_outputs.py, check_manifest.py, and
  check_remote_mirror.py for final evidence.
- Use scripts/register_agent_assignment.py before dispatch,
  scripts/record_integration.py for sequential canonical integration,
  scripts/snapshot_revision.py for snapshot/seal/verify, and
  scripts/audit_receipt.py for issue/validate/invalidate.
- Use scripts/monitor_job.py for local job checks and job-monitor-loop for
  remote, scheduler, wrapper, or automation-based supervision.
- Treat references/protocol_v0.1.md and
  references/staged_agent_run_protocol_v0.1_revised.md as legacy field/schema
  references only. This `SKILL.md` is the sole authority for triggering,
  approval, scope, profile, host/environment selection, path expansion, safety,
  and acceptance. Do not load those references to decide those matters. If a
  legacy field definition is needed, ignore any conflicting claim of external
  policy authority, mandatory replanning, repeated approval, or Phase 3 path
  self-authorization. A new output root, external path, formal output class, or
  other material drift still requires plan support or explicit user authority.
