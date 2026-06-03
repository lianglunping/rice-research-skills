#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
from pathlib import Path

from sar_utils import REMOTE_COMMAND_HEADER, append_tsv, now, read_tsv


PREFLIGHT_COMMAND = """set -euo pipefail
hostname
whoami
pwd
date
printf '\\n[Disk]\\n'
df -h . || true
printf '\\n[Conda]\\n'
command -v conda || true
conda --version || true
printf '\\n[Brew]\\n'
command -v brew || true
brew --version || true
printf '\\n[Python]\\n'
command -v python || true
python --version || true
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register remote preflight stage artifacts and command template without connecting."
    )
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--remote-cwd", required=True)
    parser.add_argument("--stage-id", default="00_remote_preflight")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    hosts = {row.get("host_id", ""): row for row in read_tsv(run_dir / "metadata/hosts.tsv")}
    if args.host_id not in hosts:
        raise SystemExit(f"ERROR: unknown host_id: {args.host_id}")
    ssh_alias = hosts[args.host_id].get("ssh_alias", args.host_id)

    stage_dir = run_dir / "03_execution/stages" / args.stage_id
    stage_dir.mkdir(parents=True, exist_ok=True)
    for name, title in {
        "stage.md": "# 阶段记录: 00_remote_preflight\n\n",
        "qc_report.md": "# QC 报告: 00_remote_preflight\n\n",
        "provenance.md": "# Provenance: 00_remote_preflight\n\n",
    }.items():
        path = stage_dir / name
        if not path.exists():
            path.write_text(title, encoding="utf-8")

    remote_script = f"cd {shlex.quote(args.remote_cwd)}\n{PREFLIGHT_COMMAND}"
    command = f"ssh {shlex.quote(ssh_alias)} {shlex.quote(remote_script)}"
    command_path = run_dir / "logs/remote_commands.tsv"
    remote_command_id = f"rcmd_{len(read_tsv(command_path)) + 1:04d}"
    append_tsv(command_path, REMOTE_COMMAND_HEADER, {
        "remote_command_id": remote_command_id,
        "phase": "Phase 3 Execution And Finalization",
        "stage_id": args.stage_id,
        "host_id": args.host_id,
        "time": now(),
        "remote_cwd": args.remote_cwd,
        "command": command,
        "command_class": "preflight",
        "env_id": "",
        "stdout_log": f"03_execution/stages/{args.stage_id}/logs/preflight.stdout.log",
        "stderr_log": f"03_execution/stages/{args.stage_id}/logs/preflight.stderr.log",
        "exit_code": "",
        "status": "Planned",
        "expected_outputs": f"03_execution/stages/{args.stage_id}/qc_report.md",
        "decision_id": args.decision_id,
        "notes": args.notes or "Template only; does not execute ssh.",
    })
    (stage_dir / "logs").mkdir(exist_ok=True)
    print(remote_command_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
