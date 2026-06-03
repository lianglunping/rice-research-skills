#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from sar_utils import COMMAND_HEADER, append_tsv, now, read_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a formal command audit row.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--phase", required=True)
    parser.add_argument("--stage-id", default="")
    parser.add_argument("--command", required=True)
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--env", default="")
    parser.add_argument("--stdout-log", default="")
    parser.add_argument("--stderr-log", default="")
    parser.add_argument("--exit-code", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    path = run_dir / "logs/commands.tsv"
    command_id = f"cmd_{len(read_tsv(path)) + 1:04d}"
    append_tsv(path, COMMAND_HEADER, {
        "command_id": command_id,
        "phase": args.phase,
        "stage_id": args.stage_id,
        "time": now(),
        "cwd": args.cwd,
        "command": args.command,
        "env": args.env,
        "stdout_log": args.stdout_log,
        "stderr_log": args.stderr_log,
        "exit_code": args.exit_code,
        "status": args.status,
        "notes": args.notes,
    })
    print(command_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
