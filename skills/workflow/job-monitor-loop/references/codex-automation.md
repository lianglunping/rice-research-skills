# Codex Automation Mapping

Use this reference when the user asks to keep watching, check back later,
monitor automatically, or detach monitoring.

## Choose the Monitoring Mechanism

- For an authorized concrete long task, establish supervision automatically. Use
  the current task's heartbeat/wakeup automation by default when Codex should
  resume. A standing policy update without a job target does not require an
  empty recurring automation.
- Use a detached workspace monitor or scheduler event mechanism when authorized
  and checks must continue independently. Verify its identity and liveness.
- Use the available automation tool to create or update app schedules. Confirm
  supported cadence; do not claim one-minute checks if the backend cannot provide
  them. For exact early checks use an actual supported task-side monitor when
  available, then hand off using the same persistent state. If no backend can
  meet the required cadence, report the concrete limitation before claiming it.
- Use bounded interactive polling only when the user requests immediate
  monitoring in the current turn.
- Use the available automation tool rather than handwritten schedule
  directives.

## Prompt Contract

Include:

- host, working directory, task identifier, RUN_ID/RUN_DIR, and attempt;
- MONITOR_CMD, scheduler query, or log/output paths;
- expected outputs, checkpoints, and semantic completion criteria;
- normal, anomalous, and unknown evidence rules;
- policy version, stable tier, consecutive normal counts, next due time, and
  reliable whole-run progress/ETA with source and estimate method;
- anomaly identity/count, unknown count, repair budget mode, current-batch review
  thresholds, cumulative attempts, renewal history and fixed/resource caps;
- backend identifier/receipt, actual scheduled wake, last observation ID and
  last notification fingerprint;
- AUTHORIZATION_MODE;
- an auditable quote or summary of repair authorization when applicable;
- allowed repair scope and actions that remain prohibited;
- immutable inputs, scientific parameters, and delivery contract;
- completion gates and reporting destination.

## Authorization Rules

- OBSERVE_ONLY: collect, classify, and report only.
- REPAIR_PREAUTHORIZED: after preserving evidence, perform at most one
  evidence-supported minimal recovery within the same logical RUN_ID/RUN_DIR,
  reserve the repair budget before side effects (including failed fixes), record
  a verified new attempt without double counting, and reset to the early stability window. Applicable
  standing user recovery authority is sufficient for new authorized tasks;
  preserve its quote and all narrower project restrictions.
- DECISION_REQUIRED: stop state-changing action and surface the decision.
- Never schedule destructive, scope-expanding, data-overwriting, credential-
  changing, or scientific-meaning-changing actions.
- An identical failed fix cannot be blindly repeated. A revised fix needs new
  evidence and remaining budget; uncertain root cause, stale-lock ambiguity,
  scope expansion, a fixed budget cap or actual resource exhaustion requires
  DECISION_REQUIRED. For configured RENEWABLE mode, REVIEW_REPAIR_CYCLE first
  requires an evidenced internal review and recorded renewal; it does not itself
  require new user permission. Preserve cumulative failures and fingerprints,
  reconcile reserved actions, and stop stagnation without a useful next method.
  Follow [repair-policy.md](repair-policy.md); renewals do not reset the timing
  streak or restart the job. Existing missing-mode states retain FIXED limits.

## Update Rules

- Update a matching monitor rather than creating a duplicate.
- Preserve fields the user did not ask to change.
- Respond to explicit failure evidence on the first observed check; do not wait
  for three identical failures.
- Use repeated suspicious or unknown checks only to decide when to stop passive
  observation and request a decision.
- Report success only after all applicable completion gates pass.
- Archive or stop recurring monitoring after accepted completion when the
  current product and user request support it.

## Scheduling and notification

Read `adaptive-monitor.md` and call the timing helper at actual checks. The target
sequence is 1 min × 3, 10 min × 2, then 30 min / 1 h / 3 h / 6 h; progress and
remaining time may shorten it. After changing the interval, update the existing
monitor's supported schedule and verify the saved result. Persist the same RUN_ID
and tier; do not create duplicate monitors at each transition.

A fixed heartbeat with a persisted next-due gate may skip premature remote checks,
but skipped wakes are not healthy checks and must not repeatedly call the model
or SSH at an unnecessarily high rate. Prefer updating the real cadence or a
supported task-side timer. State planned before scheduling must be reconciled
against the actual backend receipt after a restart.

Stay quiet while the state is normal, unchanged or non-actionable. Notify on a
meaningful failure, recovery, changed ETA that affects a decision, completion,
required user action, or loss of monitoring coverage. Deduplicate unresolved
errors and do not send a progress message for every check. Archive a task only
when that disposition is authorized; accepted completion should stop its monitor.
