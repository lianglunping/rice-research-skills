#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import REMOTE_JOB_HEADER, append_tsv, now, read_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a remote job audit row without submitting anything.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--remote-cwd", required=True)
    parser.add_argument("--remote-command", required=True)
    parser.add_argument("--scheduler-job-id", default="")
    parser.add_argument("--remote-stdout-log", default="")
    parser.add_argument("--remote-stderr-log", default="")
    parser.add_argument("--expected-remote-outputs", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--last-sync-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    hosts = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    stages = {row.get("stage_id", "") for row in read_tsv(run_dir / "02_plan/stage_registry.tsv")}
    if args.host_id not in hosts:
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")
    if args.stage_id not in stages:
        raise SystemExit(f"ERROR: unknown stage_id: {args.stage_id}")

    path = run_dir / "logs/remote_jobs.tsv"
    remote_job_id = f"rjob_{len(read_tsv(path)) + 1:04d}"
    append_tsv(path, REMOTE_JOB_HEADER, {
        "remote_job_id": remote_job_id,
        "host_id": args.host_id,
        "stage_id": args.stage_id,
        "submit_time": now(),
        "remote_cwd": args.remote_cwd,
        "remote_command": args.remote_command,
        "scheduler_job_id": args.scheduler_job_id,
        "remote_stdout_log": args.remote_stdout_log,
        "remote_stderr_log": args.remote_stderr_log,
        "expected_remote_outputs": args.expected_remote_outputs,
        "status": args.status,
        "last_sync_id": args.last_sync_id,
        "notes": args.notes,
    })
    print(remote_job_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
