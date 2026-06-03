# Monitoring Policy

## Staged Backoff

Use this sequence for long-running task monitoring:

1. Early stability window: check once per minute for the first 3 minutes after submission or attachment, for 3 checks total.
2. If all 3 early checks are normal, check every 10 minutes.
3. If 3 consecutive 10-minute checks are normal, check every 30 minutes.
4. If any check is anomalous, stop interval expansion, reset to the 1-minute window, and start failure localization.
5. If 3 consecutive anomalous or suspicious checks occur without remediation, halt automatic continuation and request a user decision.
6. After 6 consecutive normal checks at the 30-minute tier, ask whether to keep 30-minute checks, slow to a longer interval, or detach monitoring.

Do not high-frequency poll outside the early stability window unless the user explicitly asks and the task risk justifies it.

## Wrapper State Precedence

For `tmux + wrapper.sh` harness jobs:

- Parse `monitor.sh` `KEY=VALUE` output as the primary machine-readable signal.
- Treat `STATE_terminal_state=SUCCESS` or `STATE_terminal_state=FAILED` as higher priority than `tmux` observations.
- Treat `state/attempt` as authoritative for the current attempt. `last_attempt` is a convenience pointer only.
- Treat `LOCK=held` with `TMUX=gone` as a stale-lock condition requiring user approval before cleanup.
- Treat `STATE_terminal_state=FAILED`, `TMUX=gone`, and `LOCK=released` as the minimum manual-resubmit gate. Do not resubmit without user approval.

## Normal Criteria

Treat a check as normal when at least one task-appropriate progress signal is present and no anomaly criteria are hit:

- Job state is `RUNNING`, `ACTIVE`, or equivalent and the job is not repeatedly restarting.
- Logs advanced since the previous check and contain no obvious `error`, `fatal`, `traceback`, `exception`, `segmentation fault`, or dependency/path failures.
- Expected output files grew, new shard outputs appeared, or expected checkpoints were written.
- Resource status does not show an obvious blocker such as OOM, disk full, quota exceeded, permission denied, or missing input.
- For wrapper-managed jobs, `STATE_terminal_state=RUNNING`, `TMUX=alive`, and fresh heartbeat are normal even when outputs are temporarily stagnant during compute-bound phases.

## Anomaly Criteria

Treat a check as anomalous if any of these are true:

- The job exited or failed before expected completion.
- Scheduler state indicates failure, cancellation, timeout, OOM, dependency failure, or preemption that requires intervention.
- Logs contain clear error keywords, stack traces, command-not-found messages, missing file errors, permission errors, or resource limit failures.
- Outputs are absent or stale for longer than expected for the workflow stage.
- Disk, quota, memory, or permission status explains stalled progress.
- For wrapper-managed jobs, `STATE_terminal_state=RUNNING` with `TMUX=gone`, stale heartbeat, or `LOCK=held` with `TMUX=gone` is suspicious or anomalous and resets the monitor to the 1-minute window.

If evidence is incomplete, report `unknown` rather than `normal`.

## Minimal Record Per Check

Each check should record:

- Check time with timezone.
- Host and working directory.
- Job id, pid, or command identity.
- `RUN_ID`, `RUN_DIR`, `HOST`, and `MONITOR_CMD` when available.
- Job state and exit code if available.
- Wrapper `STATE_terminal_state`, `state/attempt`, `LOCK`, `TMUX`, and heartbeat age when available.
- Log path and the position or timestamp of newly reviewed lines.
- Output paths, file sizes, timestamps, or checkpoint names.
- Current monitoring tier and next scheduled check.
- Any assumptions or missing evidence.

## Reproducibility Minimum

For each monitored task, preserve:

- Submission command or scheduler command.
- Conda environment or execution environment.
- Key software versions where discoverable.
- Input paths and output paths.
- Log paths.
- Wrapper state paths and machine-readable monitor command for wrapper-managed jobs.
- Random seed if applicable.
- Monitoring criteria used for normal/anomaly decisions.
