#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from sar_utils import MONITOR_HEADER, append_tsv, now, read_tsv, write_simple_yaml

ERROR_RE = re.compile(r"(fatal|traceback|oom|killed|disk full|permission denied|missing input|dependency error|error)", re.I)


def pid_status(pid: str) -> str:
    if not pid:
        return "UNKNOWN"
    try:
        os.kill(int(pid), 0)
        return "RUNNING"
    except ProcessLookupError:
        return "EXITED"
    except PermissionError:
        return "RUNNING"
    except ValueError:
        return "UNKNOWN"


def file_size(path: str) -> int:
    if not path:
        return 0
    p = Path(path).expanduser()
    return p.stat().st_size if p.exists() else 0


def recent_errors(path: str, max_bytes: int = 20000) -> str:
    if not path:
        return ""
    p = Path(path).expanduser()
    if not p.exists() or not p.is_file():
        return ""
    with p.open("rb") as handle:
        handle.seek(max(0, p.stat().st_size - max_bytes))
        text = handle.read().decode("utf-8", errors="replace")
    hits = sorted(set(m.group(1).lower() for m in ERROR_RE.finditer(text)))
    return ",".join(hits)


def next_policy(previous: list[dict[str, str]], abnormal: bool) -> tuple[str, int]:
    if abnormal:
        return "early_1min", 1
    consecutive_normal = 0
    for row in reversed(previous):
        if row.get("decision") != "normal":
            break
        consecutive_normal += 1
    if consecutive_normal < 3:
        return "early_1min", 1
    if consecutive_normal < 6:
        return "stable_10min", 10
    return "stable_30min", 30


def expected_outputs_status(raw: str) -> tuple[int, bool]:
    paths = [x.strip() for x in raw.split(",") if x.strip()]
    if not paths:
        return 0, True
    total = 0
    all_present = True
    for item in paths:
        p = Path(item).expanduser()
        if p.exists():
            total += p.stat().st_size if p.is_file() else 0
        else:
            all_present = False
    return total, all_present


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a local registered job and append logs/monitor.tsv.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    jobs = read_tsv(run_dir / "logs/jobs.tsv")
    job = next((r for r in jobs if r.get("job_id") == args.job_id), None)
    if not job:
        raise SystemExit(f"ERROR: job not found: {args.job_id}")

    previous = [r for r in read_tsv(run_dir / "logs/monitor.tsv") if r.get("job_id") == args.job_id]
    status = pid_status(job.get("pid_or_scheduler_id", ""))
    stdout_size = file_size(job.get("stdout_log", ""))
    stderr_size = file_size(job.get("stderr_log", ""))
    output_size, outputs_present = expected_outputs_status(job.get("expected_outputs", ""))
    errors = ",".join(x for x in [recent_errors(job.get("stdout_log", "")), recent_errors(job.get("stderr_log", ""))] if x)
    declared_status = job.get("status", "")
    completed = status == "EXITED" and declared_status in {"Completed", "Done", "Succeeded"} and outputs_present and not errors
    abnormal = (status in {"EXITED", "UNKNOWN"} and not completed) or bool(errors)
    policy, interval = next_policy(previous, abnormal)
    decision = "completed" if completed else ("abnormal" if abnormal else "normal")
    consecutive_normal = 0
    if decision == "normal":
        for row in reversed(previous):
            if row.get("decision") != "normal":
                break
            consecutive_normal += 1
        consecutive_normal += 1

    append_tsv(run_dir / "logs/monitor.tsv", MONITOR_HEADER, {
        "time": now(),
        "job_id": args.job_id,
        "check_round": len(previous) + 1,
        "check_type": "local_pid_log_output",
        "interval_minutes": interval,
        "job_status": status,
        "log_size": stdout_size + stderr_size,
        "new_log_lines": "",
        "output_size": output_size,
        "error_keywords": errors,
        "decision": decision,
        "notes": f"{args.notes}; outputs_present={outputs_present}; declared_status={declared_status}".strip("; "),
    })
    write_simple_yaml(run_dir / "monitoring/monitor_state.yaml", {
        "current_policy": policy,
        "normal_checks": consecutive_normal,
        "abnormal_checks": len([r for r in previous if r.get("decision") == "abnormal"]) + (1 if abnormal else 0),
        "last_check_time": now(),
        "next_check_time": "",
        "last_status": status,
        "active_jobs": args.job_id,
    })
    print(f"{decision}\t{status}\tnext_interval_minutes={interval}\terrors={errors}")
    return 1 if abnormal else 0


if __name__ == "__main__":
    raise SystemExit(main())
