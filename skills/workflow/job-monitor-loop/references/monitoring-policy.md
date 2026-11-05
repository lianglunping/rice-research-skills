# Monitoring Policy

## Adaptive Backoff

The user's default is background submission with automatic supervision. Numerical
settings live in `backoff-policy.json`; they are local operating defaults, not
scheduler limits or scientific thresholds.

| Interval | Consecutive normal checks before extending |
|---|---:|
| 1 minute | 3 |
| 10 minutes | 2 |
| 30 minutes | 2 |
| 1 hour | 2 |
| 3 hours | 2 |
| 6 hours | hold, subject to progress and ETA |

Submission establishes the baseline; it is not the first one-minute check.
With normal signals and no earlier progress cap, checks occur at +1, +2, +3,
+13 and +23 minutes, then use the 30-minute tier. Begin the initial window again
when a queued job actually starts, observability verifiably returns after unknown
evidence, an interrupted service verifiably recovers,
or an authorized new attempt has actually been submitted. Keep repair history.

At every observation, recompute the next due time from the smallest applicable
interval: stable tier, reliable whole-run progress cap, ETA cap, stage-specific
risk limit or explicit user requirement. Early events may bring a check forward;
they cannot postpone the existing due time or count as additional stable checks.

- Retain the last verified progress-based timing cap if a later observation omits
  progress; do not present that older measurement as fresh evidence.
- At least 80% overall complete: at most 10 minutes between checks.
- At least 95%: at most 2 minutes; at least 99%: at most 1 minute.
- Reliable whole-run ETA: at most one quarter of remaining time, with a
  one-minute floor. For example, 20 minutes remaining caps the next interval at
  5 minutes. A completion event triggers acceptance immediately.
- Without reliable whole-run ETA, cap at 1 hour rather than guessing that
  3–6 hours is safe. Task-specific evidenced limits may be stricter.
- Use completed/total samples, shards, bytes or checkpoints only when their
  units are comparable. For heterogeneous phases use documented cost weights
  and observed phase durations. A step's 80% is not the entire workflow's 80%.
- ETA requires a documented estimate method and fresh rate or workload evidence;
  avoid linear extrapolation across dissimilar phases. Missing, regressing or
  inconsistent progress/denominators require verification, not a fabricated ETA.
- During final merge, indexing, upload or integrity QA, cap at 1–10 minutes as
  appropriate even if the main compute stage reported 100%. Percent complete
  never substitutes for terminal state and artifact acceptance.

## Anomalies, Unknowns and Recovery

Act on the first explicit failure: preserve its evidence, localize the cause and
perform an authorized minimal repair and recovery without waiting for three
failures. Do not resubmit while a payload may still be alive; transport failure
is not proof that a remote job failed. Preserve partial files and previous attempts.

The short anomaly window is bounded. Consecutive unresolved anomaly observations
use next intervals of 1, 1, 10, 30 and then 60 minutes; do not reset that window
for new wording of the same unresolved incident. Diagnostic actions or a verified
new failure can interrupt the due time, but changing an error string is not
recovery. These are observation intervals, not permission to repeat repairs.

Unknown evidence breaks a normal streak and does not promote a tier. Attempt a
one-minute recheck, then use at most 10-minute observation intervals while
restoring observability. For a diagnosed, unchanged observability failure with
no currently executable recovery, an evidence-bearing `observability_gap` permits
1, 10, 30, then 60-minute intervals. Reaffirm that condition at each observation;
a changed/missing diagnosis resets this optional sequence. Known near-completion
caps and explicit task/phase limits still shorten it. Do not enable it merely
because output is quiet or a job is slow. Surface a persistent evidence gap once;
unchanged warnings should not generate repeated notifications. The field contract
is in [adaptive-monitor.md](adaptive-monitor.md).

Repair only within recorded task authority, preserving scientific inputs,
meaning, output contracts, credentials and allowed resources. Diagnose OOM or
missing dependencies before changing settings; increased allocation, global
package installation or scientific parameter changes require applicable authority.
Never repeat the same failed fix blindly. A revised fix needs new discriminating
evidence. For FIXED budgets, stop at 3 repairs per issue or 6 per logical run, or a stricter project
limit. For explicitly recorded RENEWABLE mode, the same thresholds apply to the
current batch and trigger an evidenced review before renewal. Keep lifetime
counts and failed history; unchanged failures without a useful next method,
actual resource exhaustion or fixed caps still stop recovery. Follow
[repair-policy.md](repair-policy.md); legacy missing-mode records remain FIXED.
Reserve each repair against its counters before side effects; failed fixes
and failed submissions count too. Confirmed resubmission must not count the same
repair a second time. Counters survive process restarts and new attempts. When no safe supported
repair remains, use DECISION_REQUIRED and retain the observed state.

## Authorization Modes

- OBSERVE_ONLY: default. Collect evidence, classify state, localize failure, and
  report repair options without changing task state.
- REPAIR_PREAUTHORIZED: an applicable explicit task instruction or the user's
  standing automatic-monitor-and-repair instruction supplies bounded recovery
  authority for a newly authorized long task. Record the original evidence;
  honor narrower task restrictions and do not upgrade paused or observe-only
  existing jobs. Preserve failed-attempt
  evidence and recover within the same logical RUN_ID/RUN_DIR. Do not change
  scientific inputs, parameters, coordinate conventions, or deliverables.
- DECISION_REQUIRED: use when the action is destructive, changes scientific
  meaning or scope, requires ambiguous lock cleanup, lacks a supported root
  cause, or exceeds explicit repair authority.

An anomaly never expands authority. Change REPAIR_PREAUTHORIZED to
DECISION_REQUIRED whenever the minimal safe action exceeds the approved
boundary.

## Evidence Precedence

Classify in this order:

1. anomalous if any explicit anomaly criterion is met;
2. otherwise normal if at least one task-appropriate progress signal exists;
3. otherwise unknown.

A RUNNING process, advancing log, or growing output does not override a terminal
failure state, traceback, OOM, disk-full error, missing required input, or other
explicit failure evidence. Treat conflicting evidence as anomalous until it is
reconciled.

## Wrapper State

For wrapper or session-managed jobs:

- Prefer machine-readable state files and monitor output.
- Treat terminal SUCCESS or FAILED as higher priority than tmux/session
  presence.
- Treat state/attempt as authoritative for the current attempt; last_attempt is
  only a convenience pointer.
- Treat RUNNING with the session gone, stale heartbeat, or held lock without a
  live owner as anomalous.
- Treat FAILED plus no live payload plus released lock as a structural recovery
  gate, not as recovery authorization.
- Clean a stale lock only when the authority explicitly covers it and evidence
  proves that no live payload or owner remains.

## Normal Criteria

Require at least one task-appropriate progress signal and no anomaly:

- Expected RUNNING or ACTIVE state without repeated restart.
- Log growth without clear error, fatal, traceback, exception, segmentation
  fault, dependency, permission, or path failure.
- Expected output growth, new shard output, or checkpoint creation.
- Resource state without OOM, disk full, quota, permission, or input failure.
- A fresh wrapper heartbeat with a live payload during a compute-bound period.

## Anomaly Criteria

Classify anomalous when any applies:

- Unexpected exit, failure, cancellation, timeout, OOM, or dependency failure.
- Explicit error stack in the current attempt/check range, command-not-found,
  missing input, permission, resource,
  index, format, or path failure.
- Expected outputs or checkpoints remain stale beyond the stage-specific
  expectation and no valid waiting state explains it.
- State, session, lock, heartbeat, process, or scheduler evidence conflicts.
- A repair attempt reproduces the same failure.

If required evidence cannot be collected and no explicit anomaly is proven,
report unknown and identify the missing evidence.

## Completion Gates

Report accepted completion only when all applicable gates pass:

- terminal state or scheduler exit indicates expected success;
- expected artifacts exist and are complete;
- task-specific semantic QA passes;
- commands, parameters, environment, provenance, and manifest are recorded;
- original inputs remain unchanged, or an authorized change is documented.

If the process ended but any applicable gate is missing or failed, report
COMPLETION_PENDING or NOT_ACCEPTED rather than success.

## Minimum Record Per Check

Record:

- check time and timezone;
- host, working directory, job/process identifier;
- logical RUN_ID, RUN_DIR, attempt, and MONITOR_CMD when applicable;
- authorization mode;
- state, exit code, wrapper/session/lock/heartbeat evidence;
- log path and reviewed cursor or timestamp;
- output paths, sizes, timestamps, or checkpoints;
- anomaly scan and classification evidence;
- stable tier, actual interval, consecutive normal/unknown/anomaly counts, next
  due time, last observation ID, overall progress/denominator, ETA and confidence;
- monitor backend ID, actual scheduled wake or daemon state, issue fingerprint,
  per-issue and whole-run repair counts, and last notification fingerprint;
- acceptance-gate status;
- assumptions and missing evidence.

## Reproducibility Minimum

Preserve the submission or scheduler command, execution environment, key
versions, input/output/log paths, wrapper state paths, random seed when
applicable, monitoring criteria, repair record, and attempt history.
