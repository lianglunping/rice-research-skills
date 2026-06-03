#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import REMOTE_COMMAND_HEADER, append_tsv, now, read_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a formal remote command audit row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--stage-id", default="")
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--remote-cwd", required=True)
    parser.add_argument("--command", required=True)
    parser.add_argument("--command-class", required=True)
    parser.add_argument("--env-id", default="")
    parser.add_argument("--stdout-log", default="")
    parser.add_argument("--stderr-log", default="")
    parser.add_argument("--exit-code", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--expected-outputs", default="")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    hosts = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    envs = {row.get("env_id", "") for row in read_tsv(run_dir / "metadata/env_registry.tsv")}
    if args.host_id not in hosts:
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")
    if args.env_id and args.env_id not in envs:
        raise SystemExit(f"ERROR: unknown env_id: {args.env_id}")

    path = run_dir / "logs/remote_commands.tsv"
    remote_command_id = f"rcmd_{len(read_tsv(path)) + 1:04d}"
    append_tsv(path, REMOTE_COMMAND_HEADER, {
        "remote_command_id": remote_command_id,
        "phase": args.phase,
        "stage_id": args.stage_id,
        "host_id": args.host_id,
        "time": now(),
        "remote_cwd": args.remote_cwd,
        "command": args.command,
        "command_class": args.command_class,
        "env_id": args.env_id,
        "stdout_log": args.stdout_log,
        "stderr_log": args.stderr_log,
        "exit_code": args.exit_code,
        "status": args.status,
        "expected_outputs": args.expected_outputs,
        "decision_id": args.decision_id,
        "notes": args.notes,
    })
    print(remote_command_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
