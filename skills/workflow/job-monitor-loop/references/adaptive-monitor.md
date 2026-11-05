# Timing Helper and Backend Integration

`scripts/next_check.py` calculates a next due time and an action label from a
persisted state and a verified observation. It does not collect evidence, submit
jobs, execute repairs, sleep, create automations or notify the user. Those actions
remain the responsibility of the task's actual supervision backend and Codex.

## Start an authorized long task

1. Establish the task, allowed resources, expected outputs, completion gates and
   recovery authority. For this user, the standing instruction is: “任务在后台提交”
   and “如果报错就解决并重新提交”. Apply it to newly authorized long tasks, subject
   to explicit narrower restrictions. It does not revive old paused jobs.
2. Submit through the appropriate scheduler or accountable background wrapper.
   Save the submission receipt and actual job/process ID. A successful shell
   launch alone is not proof that the payload is alive.
3. Initialize timing at submission, schedule the first observation for +60 seconds,
   and establish a real monitoring backend. For queued jobs repeat the initial
   stability window when the payload actually starts.
4. Save monitor identity, heartbeat or schedule receipt, `next_check_at` and state
   paths under the same logical RUN_DIR. Confirm one live monitor per run.
5. After each observation calculate and atomically persist state, arrange the
   next due check and verify that the backend accepted it. Resume from this record
   after Codex compaction, monitor restart or host reconnection.

## State and observation

The state contains version, run/attempt identity, authority evidence, stable tier,
normal/anomaly/unknown counts, next due time, observation identity and repair
history. Initialize through `initialize(run_id, attempt, now, authority,
approval_evidence)` in the helper module. `now` and due times are Unix seconds;
store a timezone when presenting them. Submission is a baseline, not a normal
check. The function defaults to OBSERVE_ONLY when authority has not been recorded.
For new preauthorized renewable tasks, pass the keyword arguments
`repair_budget_mode='RENEWABLE'`, `scope_fingerprint` and `renewal_authority`.
The API default and legacy states without a mode remain FIXED for compatibility;
do not reinitialize an existing job to change that contract. Optional
`repair_hard_limit` records a positive fixed lifetime cap. Follow
[repair-policy.md](repair-policy.md) for cycle review and journal reconciliation.

Observation example (values must come from the real task):

```json
{
  "run_id": "example-run",
  "attempt": "attempt-1",
  "observation_id": "check-0042",
  "status": "RUNNING",
  "signal_verified": true,
  "progress_pct": 83,
  "progress_scope": "whole_run",
  "progress_reliable": true,
  "eta_seconds": 1200,
  "eta_scope": "whole_run",
  "eta_reliable": true,
  "phase_interval_cap_seconds": 600
}
```

Statuses: QUEUED, RUNNING, SUCCESS, FAILED, UNKNOWN. Set `explicit_anomaly=true`
when error evidence conflicts with apparent progress or a nominal success state.
Use a stable `issue_key` for one unresolved root-cause incident; do not put timestamps or changing
error prose in it. Keep underlying evidence paths, progress denominator, estimate
method, resource observations and error excerpts in the adjacent observation log.
The helper trusts the caller's evidence classifications; it cannot validate a
remote job or scientific result from booleans alone.

The progress and ETA fields are optional. Only finite, reliable whole-run values
control shortening; current-stage percentages do not. The last verified progress retains its conservative interval cap when a later
observation omits progress; it is not reported as a fresh measurement. Progress
regression returns VERIFY_PROGRESS and caps checks at 10 minutes (or an already
stricter cap), pending denominator verification. A verified return from unknown
evidence restarts the one-minute stability window. `phase_interval_cap_seconds`
provides a verified stage-specific upper bound (at least 60 seconds), for example
for final indexing. Invalid percentage or ETA values are ignored, never guessed.

Each actual observation needs a new ID. Replaying the most recently committed ID
is idempotent; the single-writer backend must reject older/reordered messages.
Early normal, unknown and anomaly events cannot postpone the existing due time.
Early repeats also do not advance normal/unknown/anomaly counters.

For a diagnosed, unchanged observability outage whose recovery is currently
blocked, the caller may supply this optional field on each UNKNOWN observation:

```json
{"observability_gap": {"issue_key": "ssh-route-outage", "diagnosis_evidence": "diagnosis/route-outage.md", "recovery_blocked": true}}
```

The evidence must identify the observability failure and why no recovery can be
executed now. The helper trusts this supplied diagnosis; the field is not proof
by itself. Do not infer it from elapsed time, unchanged output or unknown state.
Only consecutive qualifying observations for the same issue use the optional
1/10/30/60-minute ladder. Missing or invalid fields use the existing 1/10-minute
UNKNOWN behavior; changed diagnosis starts a new optional streak. Explicit failures
retain the anomaly path. Recovered visibility restores the initial stability window.
Persisted optional counters survive restart; absent counters in version-2 state
are read as zero, so no state migration or live-job restart is needed.

The optional ladder retains known overall progress caps. Supply
`phase_interval_cap_seconds` on each observation for a stricter phase or explicit
user interval (at least 60 seconds); it also caps UNKNOWN checks. Shorter requested
cadences need a backend that supports them. An early observation never postpones
the already scheduled due time. This option changes scheduling, not repair
authority, acceptance, or the state of the monitored job.

```bash
python3 <SKILL_ROOT>/scripts/next_check.py \
  --state <RUN_DIR>/monitor_state.json \
  --observation <RUN_DIR>/observation.json
```

The result is JSON on stdout; the CLI does not mutate either input. In a wrapper,
write the result to a new temporary file and atomically replace state only after
successful parsing. Use a single-writer lock or equivalent scheduler guarantee.
Persist the intended due time before scheduling, then save the scheduling receipt;
on restart reconcile overdue or missing schedules instead of resetting the tier.
Do not count callbacks that skip the actual evidence check as observations.

## Recovery and terminal states

LOCALIZE_AND_RECOVER_WITHIN_AUTHORITY means inspect the actual cause and existing
authority before acting. It is not permission to resubmit a possibly live payload.
The actual recovery record must preserve logs, failure state and partial outputs,
identify the minimal fix, record its distinct fingerprint, verify resource/scope
limits, and prove the previous payload ended. Never blindly repeat a failed fix.

Before an actual repair, reserve its budget through
`record_repair(state, repair_id, now, issue_key, repair_evidence_path, repair_fingerprint)`
and atomically persist the result. Use a unique repair ID and a fingerprint of the
actual proposed fix. This counts failed fixes and failed submissions as well as
successful recoveries; never wait for successful resubmission to count a repair.
Replaying the same reservation is idempotent, not permission to execute it twice.
After a crash reconcile the action journal, live payload and submission receipt
before deciding whether the reserved action was executed. An already attempted fix cannot be repeated for the same incident with a new ID,
even if its previous submission succeeded. `SUBMITTED` proves launch, not that
the cause was resolved. A revised fix needs new diagnosis. A truly independent
incident may use a new issue key only with evidence that the earlier incident
was resolved; it still shares the whole-run budget. Never rename a repeating
unresolved failure merely to bypass this check.

After verified successful recovery/submission, call
`recover(state, new_attempt, now, issue_key, recovery_evidence_path, repair_id=repair_id)`.
It requires a matching reserved action and observed failure, keeps its counted
budget, and resets timing for the new attempt. In-scope repairs that fail before
resubmission remain counted under the previous attempt. Record their failure in
the adjacent repair journal before proposing a different evidenced fix. Counters
survive restarts and new attempts; never create a new RUN_ID to reset a budget.

Existing version-2 state remains compatible. The legacy `recover(...)` call without
`repair_id` still counts a successful recovery once when no repair was reserved,
but cannot account for earlier failed fixes. New integrations must use reservation
first; when resuming old integrations reconcile any external repair journal before
acting. This helper computes bookkeeping, not proof of repair execution or authority.

DECISION_REQUIRED means stop state-changing recovery, preserve evidence, report
the specific missing decision, and retain low-frequency observation if useful.
It does not justify one-minute retry loops. FIXED limits are 3 repairs per issue
and 6 per logical run unless a stricter task contract applies. For RENEWABLE
state, REVIEW_REPAIR_CYCLE triggers an internal evidence review at 3 per issue or
6 per current batch; it does not request new user permission by itself. Renew only
with a useful next method, reconciled action journal and current scope/resource
evidence. Preserve cumulative history and existing due time. A real resource,
authority or stagnation stop may be recorded as `repair_stop_reason`; that stop
and any fixed lifetime cap block new repair and renewal.

SUCCESS with verified evidence returns ACCEPTANCE_REQUIRED and stops payload
polling. Run artifact, semantic and provenance checks promptly. If they cannot complete in
the current check, persist an acceptance task and verify its actual wakeup/worker;
`next_check_at=null` stops payload polling, not responsibility for unfinished QA. Only a subsequent
verified SUCCESS observation with `acceptance_passed=true` and an
`acceptance_evidence` record returns ACCEPTED. Then stop or pause the actual monitor
and notify once. Failed acceptance must be recorded and addressed within scope;
never treat 100% progress or a quiet process as accepted completion.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s <SKILL_ROOT>/scripts -p 'test_*.py'
```

Tests simulate time and observations; they do not run live jobs or imply that an
automation is installed. Persisted run state plus the chosen backend's actual
receipt/heartbeat is required before reporting that monitoring is active.
