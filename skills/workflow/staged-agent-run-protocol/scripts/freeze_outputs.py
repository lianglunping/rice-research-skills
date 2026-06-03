#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import (
    CHECKSUM_HEADER, FROZEN_HEADER, append_tsv, file_hashes, find_registered_path,
    now, read_tsv,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze final outputs with checksums.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--stage-id", default="")
    parser.add_argument("--file-role", default="final_output")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--qc-status", default="QC_Passed")
    parser.add_argument("--allow-unregistered", action="store_true")
    parser.add_argument("--notes", default="")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    frozen = run_dir / "03_execution/final/frozen_outputs.tsv"
    checksums = run_dir / "03_execution/final/checksums.tsv"
    registry = read_tsv(run_dir / "02_plan/path_registry.tsv")
    stages = read_tsv(run_dir / "02_plan/stage_registry.tsv")
    stage = next((r for r in stages if r.get("stage_id") == args.stage_id), None) if args.stage_id else None
    if args.stage_id and not stage:
        raise SystemExit(f"ERROR: stage not registered: {args.stage_id}")
    if stage and stage.get("gate_status") not in {"QC_Passed", "Waived_With_Decision", "Frozen"}:
        raise SystemExit(f"ERROR: stage gate is not open for freezing: {args.stage_id} {stage.get('gate_status')}")
    for idx, raw in enumerate(args.paths, start=1):
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = run_dir / path
        if not path.exists() or not path.is_file():
            print(f"skip_missing\t{path}")
            continue
        registered = find_registered_path(registry, path, run_dir)
        if not registered and not args.allow_unregistered:
            raise SystemExit(f"ERROR: output path not registered in 02_plan/path_registry.tsv: {path}")
        if registered and registered.get("mutability") not in {"final_candidate", "frozen", "planned_output"}:
            raise SystemExit(f"ERROR: registered path mutability is not freezable: {path} {registered.get('mutability')}")
        md5, sha256 = file_hashes(path)
        file_id = f"frozen_{idx:04d}"
        row_time = now()
        append_tsv(frozen, FROZEN_HEADER, {
            "file_id": file_id,
            "path": str(path),
            "file_role": args.file_role,
            "stage_id": args.stage_id,
            "md5": md5,
            "sha256": sha256,
            "size_bytes": path.stat().st_size,
            "frozen_time": row_time,
            "freeze_decision_id": args.decision_id,
            "qc_status": args.qc_status,
            "notes": args.notes,
        })
        append_tsv(checksums, CHECKSUM_HEADER, {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "md5": md5,
            "sha256": sha256,
            "time": row_time,
        })
        print(f"{file_id}\t{path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
