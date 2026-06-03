#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import SOFTWARE_HEADER, now, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a software registry row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--tool-id", required=True)
    parser.add_argument("--tool-name", required=True)
    parser.add_argument("--tool-role", default="")
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--manager", required=True)
    parser.add_argument("--executable-path", required=True)
    parser.add_argument("--version-command", required=True)
    parser.add_argument("--observed-version", default="")
    parser.add_argument("--version-log-path", default="")
    parser.add_argument("--install-source", default="")
    parser.add_argument("--install-spec", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    env_ids = {row.get("env_id", "") for row in read_tsv(run_dir / "metadata/env_registry.tsv")}
    if args.env_id not in env_ids:
        raise SystemExit(f"ERROR: unknown env_id: {args.env_id}")
    path = run_dir / "metadata/software_registry.tsv"
    rows = read_tsv(path)
    timestamp = now()
    row = {
        "tool_id": args.tool_id,
        "tool_name": args.tool_name,
        "tool_role": args.tool_role,
        "host_id": args.host_id,
        "env_id": args.env_id,
        "manager": args.manager,
        "executable_path": args.executable_path,
        "version_command": args.version_command,
        "observed_version": args.observed_version,
        "version_log_path": args.version_log_path,
        "install_source": args.install_source,
        "install_spec": args.install_spec,
        "installed_time": timestamp if args.status in {"Active", "Frozen"} else "",
        "last_verified_time": timestamp if args.observed_version else "",
        "status": args.status,
        "notes": args.notes,
    }
    for i, existing in enumerate(rows):
        if existing.get("tool_id") == args.tool_id:
            if not row["installed_time"]:
                row["installed_time"] = existing.get("installed_time", "")
            if not row["last_verified_time"]:
                row["last_verified_time"] = existing.get("last_verified_time", "")
            rows[i] = {**existing, **row}
            break
    else:
        rows.append(row)
    write_tsv(path, SOFTWARE_HEADER, rows)
    print(args.tool_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
