# Codex Automation Mapping

Use this reference when the user asks to keep watching, loop, check back later, monitor automatically, or detach a monitoring task.

## Choosing Automation Type

- Use heartbeat automation when the current thread should wake up and continue monitoring.
- Use cron automation when the monitoring job should run independently against a workspace.
- Use interactive polling only when the user wants immediate monitoring in the current turn and no scheduled follow-up.

## Tool Mapping

Use the Codex app automation tool, not a handwritten schedule directive.

Heartbeat fields:
- `mode`: `create` or `update`
- `kind`: `heartbeat`
- `destination`: `thread`
- `name`: concise monitor name
- `prompt`: the monitoring task only
- `status`: `ACTIVE`

Cron fields:
- `mode`: `create` or `update`
- `kind`: `cron`
- `cwds`: workspace directories
- `executionEnvironment`: `local` or `worktree`
- `name`: concise monitor name
- `prompt`: the monitoring task only
- `status`: `ACTIVE`

Do not put destructive repair actions in the automation prompt. The prompt may gather state, parse logs, classify normal/suspicious/anomalous, and request a user decision.

## Prompt Minimum

Include:
- host and working directory,
- job id, pid, `RUN_ID`, or `RUN_DIR`,
- `MONITOR_CMD` or log paths,
- expected outputs or checkpoints,
- normal/anomaly criteria,
- current backoff tier if continuing an existing monitor,
- explicit instruction not to resubmit, delete, overwrite, or clean locks without user approval.

## Automation Update Rules

- Prefer updating an existing matching automation over creating a duplicate.
- Preserve existing fields unless the user asks to change them.
- If an anomaly occurs, reset the next follow-up to the 1-minute stability window.
- After 3 consecutive anomalous checks without remediation, stop automatic continuation and ask the user for a decision.
