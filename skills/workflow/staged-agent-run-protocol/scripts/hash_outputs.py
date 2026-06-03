#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import CHECKSUM_HEADER, append_tsv, file_hashes, now, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Hash files and write checksums.tsv.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--output", default="03_execution/final/checksums.tsv")
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--from-manifest", default="", help="Read file_path column from a TSV manifest.")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    targets = [Path(p).expanduser() for p in args.paths]
    if args.from_manifest:
        for row in read_tsv(run_dir / args.from_manifest):
            if row.get("file_path"):
                targets.append(Path(row["file_path"]).expanduser())

    out = run_dir / args.output
    rows = []
    for target in targets:
        path = target if target.is_absolute() else run_dir / target
        if not path.exists() or not path.is_file():
            print(f"skip_missing\t{path}")
            continue
        md5, sha256 = file_hashes(path)
        rows.append({
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "md5": md5,
            "sha256": sha256,
            "time": now(),
        })
    write_tsv(out, CHECKSUM_HEADER, rows)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
