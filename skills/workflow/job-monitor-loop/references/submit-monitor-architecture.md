# Submit-Monitor Architecture

Use this reference for remote or detached work managed by a RUN_ID, RUN_DIR,
wrapper state machine, tmux/session, scheduler, or equivalent persistent
harness.

## Three-Layer Model

| Layer | Responsibility |
|---|---|
| Execution | Keep the payload alive, write heartbeat and terminal state, and preserve attempt logs |
| Transport | Use the available supported remote session, SSH, scheduler interface, or project monitor command |
| Supervision | Apply backoff, parse state, preserve evidence, enforce authority, and verify acceptance |

## Submission Contract

Record:

- JOB_NAME and payload command or command file;
- HOST and working directory;
- environment and key versions;
- logical RUN_ID and RUN_DIR;
- attempt identifier and scheduler/process/session ID;
- MONITOR_CMD or equivalent state-query interface;
- expected outputs, checkpoints, and acceptance criteria.

Run the payload under one accountable wrapper or scheduler attempt. Avoid
nested untracked backgrounding that hides the real exit state.

## Monitoring Contract

Run MONITOR_CMD through the available transport and prefer machine-readable
state. Collect when available:

- terminal state;
- live payload and session state;
- lock owner/state;
- heartbeat age;
- current attempt;
- stdout/stderr locations or tails;
- output sizes, times, and checkpoints;
- resource and disk signals.

Do not use free-text grep or session presence as the primary state detector when
structured state exists.

## State Rules

- Terminal SUCCESS or FAILED overrides session presence.
- state/attempt identifies the current attempt; last_attempt is not authoritative.
- A released lock should be accompanied by a terminal state.
- A held lock with no live payload is anomalous.
- FAILED plus no live payload plus released lock satisfies only the structural
  recovery gate; authorization mode still controls action.

## Failure and Recovery

- Never perform unauthorized or blind resubmission.
- Preserve terminal state, stdout/stderr, failed command, environment clues,
  scheduler/process ID, and failed attempt before repair.
- In OBSERVE_ONLY, gather evidence and report.
- In REPAIR_PREAUTHORIZED, recover only when:
  - the failure is sufficiently localized;
  - no payload remains active;
  - wrapper/session cleanup is complete;
  - the lock is released or its handling was separately authorized and proved
    safe;
  - scientific inputs, parameters, coordinate conventions, and deliverables
    remain unchanged.
- Keep the same logical RUN_ID and RUN_DIR. Create a new attempt and preserve
  every prior attempt. Record any new scheduler or process ID.
- Reserve repair budget before the smallest supported repair; failed repairs
  and failed submissions count. Record confirmed recovery without double counting,
  resume or resubmit, and reset
  monitoring to the early stability window.
- Do not repeat an identical failed fix. A revised fix needs new evidence and
  remaining repair budget. FIXED retains 3 per issue / 6 per logical run or
  stricter limits; RENEWABLE reviews at 3 per issue / 6 per current batch and may
  renew only with a recorded diagnosis, useful next method and verified safe
  recovery/resource evidence. Preserve lifetime counters, failure history and
  fix fingerprints across attempts and renewals; do not reset the monitor streak
  just for a budget review. Read [repair-policy.md](repair-policy.md).
  Change to DECISION_REQUIRED when the cause
  is ambiguous, no supported bounded fix remains, scientific meaning would
  change, evidence would be deleted or overwritten, scope would expand, or
  attempt history cannot be preserved.

## Same-Run Recovery Record

Record:

- logical RUN_ID and RUN_DIR;
- failed and new attempt identifiers;
- old and new scheduler/process/session IDs;
- immutable failed logs and state paths;
- exact repair and supporting evidence;
- proof that key inputs and scientific parameters were unchanged;
- recovery command and validation evidence.

## Residual Risk

Shell wrappers, sessions, schedulers, filesystems, and payload process groups can
leave ambiguous state after OOM, SIGKILL, node reboot, storage stall, or network
failure. Classify ambiguity as unknown. Repair only through an explicitly
authorized, evidence-supported safe action; otherwise use DECISION_REQUIRED.

## Persistent adaptive timing

Use `adaptive-monitor.md` and `backoff-policy.json` for timing. Record the actual
monitor backend ID, state path, due time and scheduling receipt at submission.
Keep progress denominator, ETA method, normal/anomaly counters and repair history
under the same RUN_DIR. After process restart, reconcile state with live job and
monitor evidence instead of reinitializing timing or submitting a duplicate job.
