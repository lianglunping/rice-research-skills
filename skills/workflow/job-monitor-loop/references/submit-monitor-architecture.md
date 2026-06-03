# Submit-Monitor Architecture

Use this reference when monitoring remote commands expected to exceed 5 minutes, especially on `sxyH3`, `sxyH2`, or similar Linux hosts.

## Three-Layer Model

| Layer | Owns | Handles |
|---|---|---|
| Server | `tmux + wrapper.sh` | process persistence, wrapper-owned heartbeat, cleanup, terminal state, payload process group |
| Transport | `ssh-session` MCP | persistent remote command channel; no repeated raw SSH polling |
| Codex | heartbeat/cron automation plus this skill | staged checks, `KEY=VALUE` parsing, forensics, user escalation |

## Submission Contract

Expected inputs:
- `JOB_NAME`
- `COMMAND_FILE`
- `HOST`

Expected successful output from the submit harness:
- `RUN_ID`
- `RUN_DIR` or `DIR`
- `HOST`
- `MONITOR_CMD`, usually `bash <RUN_DIR>/monitor.sh <RUN_DIR>`

The payload command file must run in the foreground. It must not use `nohup`, `disown`, `setsid`, or a trailing background `&`.

## Monitoring Contract

Each monitoring tick should run `MONITOR_CMD` through `ssh-session` MCP and parse machine-readable `KEY=VALUE` output.

Required signals when available:
- `STATE_terminal_state`
- `TMUX`
- `LOCK`
- `HEARTBEAT_AGE`
- current attempt from `state/attempt`
- stdout/stderr tail paths or tail content keys
- output size and modification-time keys

Do not use free-text grep as the primary state detector when `KEY=VALUE` monitor output is available.

## State Rules

- State files under `state/` are the source of truth.
- `STATE_terminal_state=SUCCESS` or `STATE_terminal_state=FAILED` overrides `tmux` observations.
- `state/attempt` is authoritative. `last_attempt` is only a convenience pointer.
- `LOCK=released` implies terminal state should be written.
- `LOCK=held` with `TMUX=gone` is a stale-lock condition and requires user approval before cleanup.

## Failure and Resubmission Rules

- Auto-resubmit is forbidden.
- On failure, gather precise forensics and ask the user.
- Manual resubmit requires all three conditions:
  - `terminal_state=FAILED`
  - `TMUX=gone`
  - `LOCK=released`
- If the wrapper is still cleaning up, wait one tick rather than acting immediately.

## Residual Risk

This architecture is a shell, `tmux`, and file-state-machine pattern, not a full scheduler. SIGKILL, OOM kill, node reboot, NFS stall, and payloads that manage their own process groups can leave ambiguous state. Report ambiguity explicitly and request a user decision instead of repairing state automatically.
