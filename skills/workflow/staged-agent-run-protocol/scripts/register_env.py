#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from sar_utils import ENV_HEADER, now, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update an environment registry row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--env-id", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--env-scope", required=True)
    parser.add_argument("--env-manager", required=True)
    parser.add_argument("--env-name", default="")
    parser.add_argument("--env-path", default="")
    parser.add_argument("--python-version", default="")
    parser.add_argument("--r-version", default="")
    parser.add_argument("--bioconda-channels", default="")
    parser.add_argument("--brew-prefix", default="")
    parser.add_argument("--lock-file", default="")
    parser.add_argument("--export-file", default="")
    parser.add_argument("--tool-versions-file", default="")
    parser.add_argument("--env-hash", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--retention-policy", default="keep_until_manual_review")
    parser.add_argument("--created-by", default=os.environ.get("USER", "agent"))
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    host_ids = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    if args.host_id not in host_ids and args.host_id != "local":
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")

    path = run_dir / "metadata/env_registry.tsv"
    rows = read_tsv(path)
    timestamp = now()
    row = {
        "env_id": args.env_id,
        "host_id": args.host_id,
        "env_scope": args.env_scope,
        "env_manager": args.env_manager,
        "env_name": args.env_name,
        "env_path": args.env_path,
        "python_version": args.python_version,
        "r_version": args.r_version,
        "bioconda_channels": args.bioconda_channels,
        "brew_prefix": args.brew_prefix,
        "lock_file": args.lock_file,
        "export_file": args.export_file,
        "tool_versions_file": args.tool_versions_file,
        "env_hash": args.env_hash,
        "created_time": timestamp,
        "last_verified_time": timestamp if args.status in {"Active", "Frozen"} else "",
        "status": args.status,
        "retention_policy": args.retention_policy,
        "created_by": args.created_by,
        "decision_id": args.decision_id,
        "notes": args.notes,
    }
    for i, existing in enumerate(rows):
        if existing.get("env_id") == args.env_id:
            row["created_time"] = existing.get("created_time", timestamp)
            if not row["last_verified_time"]:
                row["last_verified_time"] = existing.get("last_verified_time", "")
            rows[i] = {**existing, **row}
            break
    else:
        rows.append(row)
    write_tsv(path, ENV_HEADER, rows)
    print(args.env_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
