#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import CLEANUP_CANDIDATE_HEADER, append_tsv, read_tsv


NEVER_DELETE = {"remote_raw", "remote_results", "remote_reference", "local_control"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Register a cleanup candidate; never deletes files.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--storage-class", required=True)
    parser.add_argument("--size-gb", default="")
    parser.add_argument("--reason", required=True)
    parser.add_argument("--safe-to-delete-after", default="manual_review")
    parser.add_argument("--requires-user-approval", default="true", choices=["true", "false"])
    parser.add_argument("--backup-or-checksum-evidence", default="")
    parser.add_argument("--related-stage-id", default="")
    parser.add_argument("--related-file-ids", default="")
    parser.add_argument("--status", default="Candidate")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    if args.storage_class in NEVER_DELETE and args.status != "Rejected":
        raise SystemExit(f"ERROR: storage_class {args.storage_class} is never-delete by default")

    run_dir = Path(args.run_dir).resolve()
    path = run_dir / "logs/cleanup_candidates.tsv"
    candidate_id = f"cleanup_{len(read_tsv(path)) + 1:04d}"
    append_tsv(path, CLEANUP_CANDIDATE_HEADER, {
        "candidate_id": candidate_id,
        "host_id": args.host_id,
        "path": args.path,
        "storage_class": args.storage_class,
        "size_gb": args.size_gb,
        "reason": args.reason,
        "safe_to_delete_after": args.safe_to_delete_after,
        "requires_user_approval": args.requires_user_approval,
        "backup_or_checksum_evidence": args.backup_or_checksum_evidence,
        "related_stage_id": args.related_stage_id,
        "related_file_ids": args.related_file_ids,
        "status": args.status,
        "decision_id": args.decision_id,
        "notes": args.notes,
    })
    print(candidate_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
