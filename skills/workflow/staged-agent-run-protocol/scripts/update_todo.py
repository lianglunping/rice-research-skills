#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from sar_utils import (
    TODO_HEADER, TODO_HISTORY_HEADER, VALID_TODO_STATUSES, append_tsv, now,
    read_tsv, write_tsv,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or update TODO with history.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--todo-id", default="")
    parser.add_argument("--phase", default="")
    parser.add_argument("--stage-id", default="")
    parser.add_argument("--title", required=True)
    parser.add_argument("--status", required=True, choices=sorted(VALID_TODO_STATUSES))
    parser.add_argument("--priority", default="P2")
    parser.add_argument("--owner", default=os.environ.get("USER", "agent"))
    parser.add_argument("--blocked-by", default="")
    parser.add_argument("--source-file", default="")
    parser.add_argument("--evidence-path", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    todo_path = run_dir / "todo.tsv"
    hist_path = run_dir / "todo_history.tsv"
    rows = read_tsv(todo_path)
    todo_id = args.todo_id or f"todo_{len(rows) + 1:04d}"
    timestamp = now()
    old_status = ""
    updated = False
    new_row = {
        "todo_id": todo_id,
        "phase": args.phase,
        "stage_id": args.stage_id,
        "title": args.title,
        "status": args.status,
        "priority": args.priority,
        "owner": args.owner,
        "created_time": timestamp,
        "updated_time": timestamp,
        "blocked_by": args.blocked_by,
        "source_file": args.source_file,
        "evidence_path": args.evidence_path,
        "notes": args.notes,
    }
    for i, row in enumerate(rows):
        if row.get("todo_id") == todo_id:
            old_status = row.get("status", "")
            created = row.get("created_time") or timestamp
            merged = {**row, **{k: v for k, v in new_row.items() if v != ""}}
            merged["created_time"] = created
            merged["updated_time"] = timestamp
            rows[i] = merged
            updated = True
            break
    if not updated:
        rows.append(new_row)
    write_tsv(todo_path, TODO_HEADER, rows)
    append_tsv(hist_path, TODO_HISTORY_HEADER, {
        "time": timestamp,
        "todo_id": todo_id,
        "old_status": old_status,
        "new_status": args.status,
        "changed_by": args.owner,
        "reason": args.reason,
        "evidence_path": args.evidence_path,
        "notes": args.notes,
    })
    print(todo_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
