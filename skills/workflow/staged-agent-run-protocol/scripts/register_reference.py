#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import REFERENCE_HEADER, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a reference registry row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--reference-id", required=True)
    parser.add_argument("--reference-type", required=True)
    parser.add_argument("--species", default="")
    parser.add_argument("--reference-name", required=True)
    parser.add_argument("--reference-version", default="")
    parser.add_argument("--annotation-version", default="")
    parser.add_argument("--database-release", default="")
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--canonical-path", required=True)
    parser.add_argument("--local-mirror-path", default="")
    parser.add_argument("--source-uri", default="")
    parser.add_argument("--source-date", default="")
    parser.add_argument("--md5", default="")
    parser.add_argument("--sha256", default="")
    parser.add_argument("--index-paths", default="")
    parser.add_argument("--used-by-stage-ids", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    host_ids = {row.get("host_id", "") for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    if args.host_id not in host_ids and args.host_id != "local":
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")
    path = run_dir / "metadata/reference_registry.tsv"
    rows = read_tsv(path)
    row = {
        "reference_id": args.reference_id,
        "reference_type": args.reference_type,
        "species": args.species,
        "reference_name": args.reference_name,
        "reference_version": args.reference_version,
        "annotation_version": args.annotation_version,
        "database_release": args.database_release,
        "host_id": args.host_id,
        "canonical_path": args.canonical_path,
        "local_mirror_path": args.local_mirror_path,
        "source_uri": args.source_uri,
        "source_date": args.source_date,
        "md5": args.md5,
        "sha256": args.sha256,
        "index_paths": args.index_paths,
        "used_by_stage_ids": args.used_by_stage_ids,
        "status": args.status,
        "notes": args.notes,
    }
    for i, existing in enumerate(rows):
        if existing.get("reference_id") == args.reference_id:
            rows[i] = {**existing, **row}
            break
    else:
        rows.append(row)
    write_tsv(path, REFERENCE_HEADER, rows)
    print(args.reference_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
