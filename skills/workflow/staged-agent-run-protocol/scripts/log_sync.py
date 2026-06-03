#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import SYNC_HEADER, append_tsv, now, read_tsv, slugify


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a remote/local sync provenance row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--path-map-id", required=True)
    parser.add_argument("--direction", default="remote_to_local", choices=["remote_to_local", "local_to_remote", "bidirectional", "metadata_only"])
    parser.add_argument("--remote-path", default="")
    parser.add_argument("--local-path", default="")
    parser.add_argument("--sync-method", default="")
    parser.add_argument("--status", default="Completed")
    parser.add_argument("--bytes-synced", default="")
    parser.add_argument("--checksum-status", default="not_checked", choices=["matched", "mismatched", "not_checked", "not_applicable"])
    parser.add_argument("--checksum-mismatch-policy", default="")
    parser.add_argument("--remote-checksum-path", default="")
    parser.add_argument("--local-checksum-path", default="")
    parser.add_argument("--provenance-path", default="")
    parser.add_argument("--label", default="sync")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    hosts = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    maps = {row.get("path_map_id", ""): row for row in read_tsv(run_dir / "metadata/path_maps.tsv")}
    if args.host_id not in hosts:
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")
    if args.path_map_id not in maps:
        raise SystemExit(f"ERROR: unknown path_map_id: {args.path_map_id}")
    path_map = maps[args.path_map_id]
    remote_path = args.remote_path or path_map.get("remote_path", "")
    local_path = args.local_path or path_map.get("local_path", "")
    sync_method = args.sync_method or path_map.get("sync_method", "manual")
    policy = args.checksum_mismatch_policy or path_map.get("checksum_mismatch_policy", "")
    if args.checksum_status == "mismatched" and not policy:
        raise SystemExit("ERROR: checksum_status=mismatched requires --checksum-mismatch-policy")

    sync_path = run_dir / "logs/sync.tsv"
    stamp = now().replace("-", "").replace(":", "").split("+", 1)[0].replace("T", "_")
    sync_id = f"sync_{stamp}_{args.host_id}_{args.direction}_{slugify(args.label)}"
    append_tsv(sync_path, SYNC_HEADER, {
        "sync_id": sync_id,
        "host_id": args.host_id,
        "path_map_id": args.path_map_id,
        "sync_time": now(),
        "direction": args.direction,
        "remote_path": remote_path,
        "local_path": local_path,
        "sync_method": sync_method,
        "status": args.status,
        "bytes_synced": args.bytes_synced,
        "checksum_status": args.checksum_status,
        "checksum_mismatch_policy": policy,
        "remote_checksum_path": args.remote_checksum_path,
        "local_checksum_path": args.local_checksum_path,
        "provenance_path": args.provenance_path,
        "notes": args.notes,
    })
    print(sync_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
