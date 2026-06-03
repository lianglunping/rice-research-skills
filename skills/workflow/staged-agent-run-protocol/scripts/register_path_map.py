#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import PATH_MAP_HEADER, now, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a remote/local path mapping.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--path-map-id", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--stage-id", default="")
    parser.add_argument("--remote-path", required=True)
    parser.add_argument("--local-path", required=True)
    parser.add_argument("--path-role", default="output")
    parser.add_argument("--remote-is-canonical", default="true", choices=["true", "false"])
    parser.add_argument("--local-role", default="local_mirror")
    parser.add_argument("--sync-direction", default="remote_to_local", choices=["remote_to_local", "local_to_remote", "bidirectional", "metadata_only"])
    parser.add_argument("--sync-method", default="manual")
    parser.add_argument("--include-pattern", default="")
    parser.add_argument("--exclude-pattern", default="")
    parser.add_argument("--checksum-required-before-final", default="true", choices=["true", "false"])
    parser.add_argument("--checksum-mismatch-policy", default="")
    parser.add_argument("--retention-policy", default="keep_until_manual_review")
    parser.add_argument("--max-expected-gb", default="")
    parser.add_argument("--status", default="Active")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    host_ids = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    if args.host_id not in host_ids:
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")
    if args.remote_is_canonical != "true":
        raise SystemExit("ERROR: remote layer requires remote_is_canonical=true")
    if args.local_role != "local_mirror":
        raise SystemExit("ERROR: local_role must be local_mirror")

    path = run_dir / "metadata/path_maps.tsv"
    rows = read_tsv(path)
    timestamp = now()
    row = {
        "path_map_id": args.path_map_id,
        "host_id": args.host_id,
        "stage_id": args.stage_id,
        "remote_path": args.remote_path,
        "local_path": args.local_path,
        "path_role": args.path_role,
        "remote_is_canonical": args.remote_is_canonical,
        "local_role": args.local_role,
        "sync_direction": args.sync_direction,
        "sync_method": args.sync_method,
        "include_pattern": args.include_pattern,
        "exclude_pattern": args.exclude_pattern,
        "checksum_required_before_final": args.checksum_required_before_final,
        "checksum_mismatch_policy": args.checksum_mismatch_policy,
        "retention_policy": args.retention_policy,
        "max_expected_gb": args.max_expected_gb,
        "status": args.status,
        "created_time": timestamp,
        "updated_time": timestamp,
        "decision_id": args.decision_id,
        "notes": args.notes,
    }
    for i, existing in enumerate(rows):
        if existing.get("path_map_id") == args.path_map_id:
            row["created_time"] = existing.get("created_time", timestamp)
            rows[i] = {**existing, **row}
            break
    else:
        rows.append(row)

    write_tsv(path, PATH_MAP_HEADER, rows)
    print(args.path_map_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
