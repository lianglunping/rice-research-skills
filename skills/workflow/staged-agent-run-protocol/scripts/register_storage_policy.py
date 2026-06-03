#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from sar_utils import STORAGE_POLICY_HEADER, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a storage policy row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--storage-id", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--storage-class", required=True)
    parser.add_argument("--canonical-role", default="")
    parser.add_argument("--allowed-file-classes", default="")
    parser.add_argument("--retention-policy", required=True)
    parser.add_argument("--cleanup-allowed", default="false", choices=["true", "false"])
    parser.add_argument("--auto-cleanup-allowed", default="false", choices=["true", "false"])
    parser.add_argument("--max-expected-gb", default="")
    parser.add_argument("--actual-gb", default="")
    parser.add_argument("--last-du-time", default="")
    parser.add_argument("--disk-status", default="")
    parser.add_argument("--owner", default=os.environ.get("USER", "agent"))
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if args.storage_class in {"remote_raw", "remote_results", "remote_reference"} and args.auto_cleanup_allowed == "true":
        raise SystemExit(f"ERROR: {args.storage_class} cannot enable auto cleanup")

    run_dir = Path(args.run_dir).resolve()
    host_ids = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    if args.host_id not in host_ids and args.host_id != "local":
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")

    path = run_dir / "metadata/storage_policy.tsv"
    rows = read_tsv(path)
    row = {
        "storage_id": args.storage_id,
        "host_id": args.host_id,
        "path": args.path,
        "storage_class": args.storage_class,
        "canonical_role": args.canonical_role,
        "allowed_file_classes": args.allowed_file_classes,
        "retention_policy": args.retention_policy,
        "cleanup_allowed": args.cleanup_allowed,
        "auto_cleanup_allowed": args.auto_cleanup_allowed,
        "max_expected_gb": args.max_expected_gb,
        "actual_gb": args.actual_gb,
        "last_du_time": args.last_du_time,
        "disk_status": args.disk_status,
        "owner": args.owner,
        "decision_id": args.decision_id,
        "notes": args.notes,
    }
    for i, existing in enumerate(rows):
        if existing.get("storage_id") == args.storage_id:
            rows[i] = {**existing, **row}
            break
    else:
        rows.append(row)
    write_tsv(path, STORAGE_POLICY_HEADER, rows)
    print(args.storage_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
