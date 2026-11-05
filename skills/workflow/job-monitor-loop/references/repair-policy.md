# Repair Cycles and Lifetime Evidence

This policy applies to long-job recovery inside existing user authority. It does
not activate the dedicated three-stage state machine. When that workflow is
already active, its approval and budget gates also apply; renewal of this monitor
ledger alone does not renew or override a parent task's budget.

New preauthorized jobs under the user's renewable recovery instruction explicitly
initialize RENEWABLE mode with a stable scope fingerprint and renewal evidence:

```python
state = initialize(run_id, attempt, now,
                   authority='REPAIR_PREAUTHORIZED', approval_evidence=user_authority,
                   repair_budget_mode='RENEWABLE', scope_fingerprint=scope_hash,
                   renewal_authority=user_renewal_authority)
```

`initialize` defaults to FIXED to keep existing callers compatible. Existing v2
states without a mode remain FIXED; do not silently migrate live or paused jobs.
A requested fixed upper limit remains binding. Optional `repair_hard_limit` is a
positive lifetime cap, honored even in RENEWABLE mode. The actual backend enforces
resource, deadline, authority and scientific boundaries; record a stop as
`repair_stop_reason` when it blocks recovery. A helper cannot infer these limits
from a remote status or verify authority from text alone.

Keep `repair_attempts_by_issue` and `total_repair_attempts` cumulative. In RENEWABLE
mode, additionally persist `repair_cycle_attempts_by_issue`,
`repair_cycle_attempts`, `repair_renewal_log`, `scope_fingerprint` and
`repair_renewal_authority`. Archived cycle counts plus current counts must equal
lifetime counts. Failed fixes and submissions count at reservation time. Preserve
`repair_history`, stable issue keys and attempted-fix fingerprints across renewals
and new scheduler attempts. An identical fix for an unresolved issue stays blocked.

At 3 repairs for one issue or 6 repairs in the current batch, `decide` returns
REVIEW_REPAIR_CYCLE for an authorized renewable job. Before any further repair:

1. Inspect failed attempts and establish the current cause, progress or useful new
   evidence, and a distinct next method. Repeating the same failure without a
   useful approach is stagnation; record the stop and report evidence.
2. Verify the previous payload ended, locks are safe, scope is unchanged, resources
   remain available and action journals are reconciled. Pending reservations may
   represent completed side effects after a crash: inspect actual receipts before
   classifying them. No guessed cleanup or duplicate submission.
3. Call `renew_repair_budget` from `next_check.py` with the same `run_id`,
   `scope_fingerprint`, current `issue_key`, finite `now`, `diagnosis`,
   `next_approach`, `evidence` and `recovery_gate`. The gate must contain true values
   for `payload_ended`, `lock_safe`, `within_scope`, `resources_available`,
   `journals_reconciled`, plus an `evidence` path. These are caller attestations;
   the pure helper does not inspect the host or evidence files.
4. Supply `reservation_outcomes`, mapping every outstanding RESERVED repair ID
   to verified failure-journal evidence, and no other IDs. If one actually
   submitted a live payload, record that submission through `recover` instead;
   do not label it failed merely to renew. A known incomplete action must be
   safely reconciled before renewal. Failed reserved actions become FAILED while
   retaining their original identity, method and evidence.
5. Atomically persist the returned state before a new repair reservation. The
   renewal receipt archives current counts, lifetime count, diagnosis, next
   method, evidence, recovery gates, authority, scope and time. Only current-batch
   counts reset. Existing anomaly counters, attempt and monitoring deadline remain.

Each verified resubmission still uses `record_repair` before side effects and
`recover(..., repair_id=...)` afterward. Renewable integrations require reservation;
legacy unreserved recovery remains available only for FIXED callers. A reserved
last permitted repair may finish submission without being counted twice. Budget
availability never replaces checking current resource and recovery gates.

There is no fixed number of renewable batches. Continue within the original scope
until applicable acceptance passes, subject to actual caps and stagnation. A
repeated renewal with identical issue, diagnosis, method and evidence is rejected.
The caller must also recognize semantically unchanged failures; changing prose or
paths does not constitute new evidence. Keep external-request retries bounded,
idempotent and subject to real deadlines and rate limits. Task repair renewal does
not authorize endless retries of an unchanged network request.

Verified SUCCESS with all acceptance gates passed returns ACCEPTED even when a
review threshold was reached; do not renew a completed job. Failed or missing QA
requires recorded follow-up and actual failure evidence before recovery. This
maintenance does not migrate job records, create monitors or submit scientific work.
