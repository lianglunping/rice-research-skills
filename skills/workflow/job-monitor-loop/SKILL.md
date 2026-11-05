---
name: job-monitor-loop
description: "Automatic supervision of authorized long-running jobs: background submission, progress-aware backoff, bounded repair and artifact acceptance. Preserve task and host boundaries."
---

# Job Monitor Loop

Use when executing or supervising an authorized long-running task. Background
submission includes actual monitoring; no separate invocation is needed. A policy
discussion or skill edit alone does not identify a live job to monitor.

## Start or resume

- Record target host, work directory, command/environment, input/output/log paths,
  logical RUN_ID, attempt and actual job/process ID. Define completion gates and
  applicable resource and recovery limits before submission. New preauthorized
  tasks under the user's renewable recovery instruction explicitly record
  RENEWABLE mode, scope fingerprint and renewal authority. Honor fixed user caps;
  missing mode on existing state retains FIXED semantics. See
  [repair-policy.md](references/repair-policy.md).
- Select OBSERVE_ONLY, REPAIR_PREAUTHORIZED or DECISION_REQUIRED. For a newly
  authorized long task, the user's standing instruction to fix errors and resubmit
  supplies bounded recovery authority; retain its evidence. Otherwise observe only.
  Preserve narrower task restrictions and paused or decision-required states.
- Submit through the appropriate background wrapper or scheduler. Capture a real
  submission receipt and baseline; submission is not the first healthy check.
- Establish one actual monitor per run with persistent state, backend ID, first
  due time and scheduling receipt/heartbeat. Resume from that record after
  disconnection or compaction; reconcile missing/overdue schedules before action.
  A background payload or computed interval does not prove active supervision.

Read [monitoring-policy.md](references/monitoring-policy.md) for timing and evidence
rules. Use [adaptive-monitor.md](references/adaptive-monitor.md) to integrate the
pure timing helper [next_check.py](scripts/next_check.py); it does not submit, sleep,
repair or schedule by itself. For Codex wakeups read
[codex-automation.md](references/codex-automation.md) and use the available automation
tool. Confirm that the backend can actually meet the requested cadence.

## Observe and adapt

Apply the user's 1 min × 3, 10 min × 2, then 30 min / 1 h / 3 h / 6 h sequence,
subject to verified whole-run progress, ETA and phase limits. Numerical defaults
are maintained in [backoff-policy.json](references/backoff-policy.json).
For a diagnosed, unchanged observability outage with no executable recovery,
use the optional evidence-bearing backoff in `references/adaptive-monitor.md`;
ordinary UNKNOWN states retain the shorter checks.

Classify explicit anomalies first, task-appropriate normal evidence second,
otherwise unknown. A RUNNING process, growing output or zero exit code cannot
cancel explicit failure or failed integrity/acceptance evidence. Keep log cursors
and attempt identity so historical errors are not mistaken for new failures.
Use [task-types.md](references/task-types.md) only for applicable task signals.

Early events can shorten an existing deadline, never defer it or advance stable
counts. Missing progress is not zero progress; retain known conservative timing
caps while checking telemetry. Recovered observability starts a fresh short
stability window. Keep unchanged normal checks quiet and deduplicate warnings.

## Diagnose and recover

Act on the first explicit failure. Preserve logs, partial outputs and attempt
history; establish the cause and whether a payload is still alive before recovery.
A failed connection is not evidence that a remote job ended.

- OBSERVE_ONLY: localize and report without changing task state.
- REPAIR_PREAUTHORIZED: perform a minimal evidence-supported repair within the
  recorded scope. Persist `record_repair(...)` before its side effects; failed
  fixes and failed submissions consume budget too. Record confirmed submission
  with `recover(..., repair_id=...)`, preserving RUN_ID and incrementing attempt.
- DECISION_REQUIRED: stop state-changing recovery and report the missing decision.

Do not repeat an identical failed fix. Revised fixes need new evidence and budget:
FIXED budgets retain maximum 3 per issue / 6 per logical run or stricter task limits.
RENEWABLE budgets review after 3 per issue / 6 per current batch. Preserve diagnosis,
progress or useful new evidence, a distinct next method and safe recovery gates,
then record renewal before resetting only current batch counts. Keep lifetime
counts, failed records, issue identity and tried-fix fingerprints. Continue within
authority until acceptance; stop on stagnation, fixed caps or actual resource
exhaustion. Renewal does not rearm frequent monitoring or prove a job ended. Deletion, input
or key-result overwrite, scope/scientific-parameter changes, ambiguous lock cleanup
and unapproved resource/environment changes require applicable authority. Monitoring
never grants those permissions. For managed wrappers read
[submit-monitor-architecture.md](references/submit-monitor-architecture.md).

## Accept and stop

A terminal success triggers artifact, integrity, semantic and provenance checks.
If any gate is missing or failed, record pending or not accepted; 100% progress is
not completion. Stop the actual monitor only after acceptance or an explicit stop
instruction, and notify once. If acceptance is deferred, retain its accountable
follow-up rather than abandoning the run when payload polling ends.

Use [report-template.md](references/report-template.md) for persistent evidence
records, not compulsory chat output. Validation:
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <SKILL_ROOT>/scripts -p 'test_*.py'`.
