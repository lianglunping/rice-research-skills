#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import DISK_USAGE_HEADER, append_tsv, now


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a disk usage audit row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--check-type", required=True)
    parser.add_argument("--df-available", default="")
    parser.add_argument("--df-used-percent", default="")
    parser.add_argument("--du-size-gb", default="")
    parser.add_argument("--file-count", default="")
    parser.add_argument("--threshold-status", default="not_checked")
    parser.add_argument("--stage-id", default="")
    parser.add_argument("--job-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    append_tsv(run_dir / "logs/disk_usage.tsv", DISK_USAGE_HEADER, {
        "time": now(),
        "host_id": args.host_id,
        "path": args.path,
        "check_type": args.check_type,
        "df_available": args.df_available,
        "df_used_percent": args.df_used_percent,
        "du_size_gb": args.du_size_gb,
        "file_count": args.file_count,
        "threshold_status": args.threshold_status,
        "stage_id": args.stage_id,
        "job_id": args.job_id,
        "notes": args.notes,
    })
    print("disk_usage_logged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
