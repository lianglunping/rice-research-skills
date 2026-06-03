---
name: job-monitor-loop
description: This skill should be used when the user asks to monitor a long-running job, loop on task status, watch logs, check a background task, create Claude-like loop behavior, detect job anomalies, monitor tmux/wrapper.sh jobs with RUN_ID or RUN_DIR, use submit-monitor style supervision, or handle failures during bioinformatics pipelines and other long-running analyses.
---

# Job Monitor Loop

Use this skill to monitor long-running tasks with staged backoff, reproducible evidence, and bounded anomaly handling.

## Goal

Provide a Claude `/loop`-like workflow for Codex sessions and automations:
- submit or attach to a background task,
- check status, logs, and outputs on a staged schedule,
- detect early crashes or obvious anomalies,
- report evidence and next actions without destructive changes.

For remote tasks expected to exceed 5 minutes, prefer the `submit-monitor` architecture: `tmux + wrapper.sh` on the server, `ssh-session` MCP for transport, and Codex heartbeat/cron automation for supervised checks. Load `references/submit-monitor-architecture.md` when `RUN_ID`, `RUN_DIR`, `MONITOR_CMD`, `tmux`, or wrapper state files are involved.

## Boundaries

- Do not run long tasks in a foreground interactive session.
- Do not delete, overwrite, rename, restart, or resubmit critical jobs unless the user explicitly approved that action.
- Do not auto-resubmit failed jobs. Gather forensics and ask the user.
- For `sxyH3`, `sxyH2`, and `sxycloud1.top` hosts, use the persistent `ssh-session` MCP tools for remote checks. Do not poll with repeated raw `ssh` calls.
- For wrapper-managed jobs, treat wrapper state files as the source of truth; `tmux` state is supporting evidence only.
- Do not treat missing evidence as success. Mark unknowns and explain what evidence is missing.
- Do not high-frequency poll beyond the configured early stability window.
- Keep all commands, paths, parameters, versions, job ids, and output locations reproducible in the report.

## Default Workflow

1. Define the monitoring target.
   - Record task goal, command or scheduler job id, pid if available, host, working directory, conda environment, log paths, expected outputs, and completion criteria.
   - If the task was submitted via `submit-monitor` or an equivalent `tmux + wrapper.sh` harness, record `RUN_ID`, `RUN_DIR`, `HOST`, `MONITOR_CMD`, wrapper state paths, and `state/attempt`.
   - If key paths or ids are missing, ask for them or discover them from local context before monitoring.
   - If a remote task is expected to exceed 5 minutes and has not been submitted yet, prefer the `submit-monitor` architecture instead of a raw foreground remote command.

2. Establish a baseline.
   - Capture current job state, recent log tail, output file timestamps/sizes, disk status if relevant, and environment/version clues.
   - Choose the closest task type from `references/task-types.md`.
   - For wrapper-managed jobs, run `MONITOR_CMD` and parse `KEY=VALUE` lines; do not infer state from free-text log grep alone.

3. Apply the staged backoff policy.
   - Use `references/monitoring-policy.md` as the authority for intervals and normal/anomalous criteria.
   - Prefer Codex heartbeat automation for thread wakeups and cron automation for detached workspace monitoring when the user asks for automatic follow-up.

4. On each check, compare against the baseline.
   - State whether the job is running, completed, failed, or unknown.
   - Check whether logs advanced and whether new lines contain clear error signals.
   - Check whether expected outputs grew or checkpoints appeared.
   - Record the next interval according to the policy.

5. On anomaly, stop interval expansion.
   - Reset to the 1-minute stability window after any anomaly.
   - Produce an anomaly report using `references/report-template.md`.
   - Provide minimal repair options and a reproducible validation command, but do not perform destructive remediation without approval.

6. On expected completion, close out.
   - Report completion evidence, key outputs, exit code or scheduler state, log location, and the minimal reproducibility record.

## Automation Guidance

When the user asks to "keep watching", "check back later", "loop", "monitor automatically", or similar:
- Use heartbeat automation for follow-up in the current thread.
- Use cron automation for long-lived detached checks in a workspace.
- Put only the monitoring task in the automation prompt; schedules belong in the automation fields.
- Preserve the same normal/anomaly criteria from `references/monitoring-policy.md`.
- Load `references/codex-automation.md` before creating or updating an automation.

## References

Load only what is needed. For long files, load the matching subsection rather than the entire reference.
- `references/monitoring-policy.md` - staged backoff intervals and normal/anomaly definitions.
- `references/task-types.md` - task-specific checks for local shell, SSH, workflow engines, schedulers, and bioinformatics outputs.
- `references/report-template.md` - concise templates for normal checks, anomalies, and completion.
- `references/submit-monitor-architecture.md` - remote long-job architecture using `tmux`, `wrapper.sh`, `RUN_ID`, `RUN_DIR`, and `MONITOR_CMD`.
- `references/codex-automation.md` - mapping from loop-style monitoring to Codex heartbeat and cron automations.
