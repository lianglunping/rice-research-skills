#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import INSTALL_HEADER, append_tsv, now, read_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Append an install/update/remove audit row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--manager", required=True)
    parser.add_argument("--action", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--requested-version", default="")
    parser.add_argument("--resolved-version", default="")
    parser.add_argument("--command", required=True)
    parser.add_argument("--cwd", default="")
    parser.add_argument("--stdout-log", default="")
    parser.add_argument("--stderr-log", default="")
    parser.add_argument("--exit-code", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    envs = {row.get("env_id", "") for row in read_tsv(run_dir / "metadata/env_registry.tsv")}
    if args.env_id not in envs:
        raise SystemExit(f"ERROR: unknown env_id: {args.env_id}")
    path = run_dir / "logs/install.tsv"
    install_id = f"install_{len(read_tsv(path)) + 1:04d}"
    append_tsv(path, INSTALL_HEADER, {
        "install_id": install_id,
        "time": now(),
        "host_id": args.host_id,
        "env_id": args.env_id,
        "manager": args.manager,
        "action": args.action,
        "package": args.package,
        "requested_version": args.requested_version,
        "resolved_version": args.resolved_version,
        "command": args.command,
        "cwd": args.cwd,
        "stdout_log": args.stdout_log,
        "stderr_log": args.stderr_log,
        "exit_code": args.exit_code,
        "status": args.status,
        "decision_id": args.decision_id,
        "notes": args.notes,
    })
    print(install_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
