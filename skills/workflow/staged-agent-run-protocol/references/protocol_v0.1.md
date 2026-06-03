# Staged Agent Run Protocol v0.1

Source: `/path/to/staged_agent_run_protocol_v0.1_revised.md`.

Use the downloaded revision as the full policy authority. This bundled copy records the operational minimum implemented by the skill:

- complex tasks first create `agent_runs/{YYYY-MM-DD}_{task-name}/`
- canonical sources are Markdown, TSV, and YAML
- HTML is rendered from canonical sources
- default profile is `standard`
- formal phases are Phase 1 Analysis, Phase 2 Plan And Path Freeze, and Phase 3 Execution And Finalization
- Phase 0 Bootstrap only initializes the run
- TODO is dynamic and recorded in both `todo.tsv` and `todo_history.tsv`
- `stage_registry.tsv` controls stage status and QC gates
- long jobs are registered in `logs/jobs.tsv` and monitored in `logs/monitor.tsv`
- final outputs are frozen with checksums

Local implementation supplements added after review:

- `update_todo.py` enforces TODO history updates.
- `validate_gate.py` checks stage gate evidence before continuation.
- `check_manifest.py` validates required headers, non-empty Markdown artifacts, dependencies, and gate/QC consistency.
- `freeze_outputs.py` checks path registration and stage gate status before freezing.
- `monitor_job.py` distinguishes normal, abnormal, and declared completed local jobs.

For full details, read the source file above or the design file:

`/path/to/staged_agent_run_protocol_design_for_review.md`
