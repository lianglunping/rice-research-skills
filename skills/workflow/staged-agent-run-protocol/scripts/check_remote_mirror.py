#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import path_in_run_or_absolute, read_tsv


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check local mirror records without connecting to remote hosts."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--require-local-exists", action="store_true")
    parser.add_argument("--require-final-checksum", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    maps = read_tsv(run_dir / "metadata/path_maps.tsv")
    syncs = read_tsv(run_dir / "logs/sync.tsv")
    latest_by_map: dict[str, dict[str, str]] = {}
    for row in syncs:
        latest_by_map[row.get("path_map_id", "")] = row

    issues: list[str] = []
    for row in maps:
        path_map_id = row.get("path_map_id", "")
        if row.get("status") not in {"Active", "Planned"}:
            continue
        if row.get("remote_is_canonical") != "true":
            issues.append(f"remote_not_canonical\t{path_map_id}")
        if row.get("local_role") != "local_mirror":
            issues.append(f"local_not_mirror\t{path_map_id}")
        local_path = row.get("local_path", "")
        if args.require_local_exists and local_path:
            candidate = path_in_run_or_absolute(local_path, run_dir)
            if not candidate.exists():
                issues.append(f"local_mirror_missing\t{path_map_id}\t{local_path}")
        if args.require_final_checksum and row.get("path_role") in {"final", "frozen", "final_output"}:
            latest = latest_by_map.get(path_map_id, {})
            checksum_status = latest.get("checksum_status", "")
            policy = latest.get("checksum_mismatch_policy") or row.get("checksum_mismatch_policy", "")
            if checksum_status != "matched" and not policy:
                issues.append(f"final_mirror_lacks_checksum_or_policy\t{path_map_id}")

    if issues:
        print("FAIL")
        for issue in issues:
            print(issue)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
