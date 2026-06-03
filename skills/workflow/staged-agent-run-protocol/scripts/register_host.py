#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import HOST_HEADER, now, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a remote host record.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--host-id", required=True)
    parser.add_argument("--ssh-alias", default="")
    parser.add_argument("--host-label", default="", help="Deprecated alias for --ssh-alias.")
    parser.add_argument("--hostname", default="", help="Deprecated alias for --ssh-alias.")
    parser.add_argument("--host-role", default="primary_compute")
    parser.add_argument("--access-mode", default="manual", choices=["manual", "ssh", "scheduler", "other"])
    parser.add_argument("--scheduler", default="")
    parser.add_argument("--remote-project-root", default="")
    parser.add_argument("--remote-data-root", default="")
    parser.add_argument("--remote-scratch-root", default="")
    parser.add_argument("--remote-results-root", default="")
    parser.add_argument("--remote-env-root", default="")
    parser.add_argument("--work-root", default="", help="Deprecated alias for --remote-project-root.")
    parser.add_argument("--data-root", default="", help="Deprecated alias for --remote-data-root.")
    parser.add_argument("--scratch-root", default="", help="Deprecated alias for --remote-scratch-root.")
    parser.add_argument("--package-managers", default="")
    parser.add_argument("--default-shell", default="")
    parser.add_argument("--status", default="Planned")
    parser.add_argument("--validated-by", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    path = run_dir / "metadata/hosts.tsv"
    rows = read_tsv(path)
    timestamp = now()
    ssh_alias = args.ssh_alias or args.hostname or args.host_label or args.host_id
    row = {
        "host_id": args.host_id,
        "ssh_alias": ssh_alias,
        "host_role": args.host_role,
        "access_mode": args.access_mode,
        "scheduler": args.scheduler,
        "remote_project_root": args.remote_project_root or args.work_root,
        "remote_data_root": args.remote_data_root or args.data_root,
        "remote_scratch_root": args.remote_scratch_root or args.scratch_root,
        "remote_results_root": args.remote_results_root,
        "remote_env_root": args.remote_env_root,
        "package_managers": args.package_managers,
        "default_shell": args.default_shell,
        "status": args.status,
        "validated_time": timestamp if args.status in {"Active", "Validated"} else "",
        "validated_by": args.validated_by,
        "notes": args.notes,
    }
    for i, existing in enumerate(rows):
        if existing.get("host_id") == args.host_id:
            if not row["validated_time"]:
                row["validated_time"] = existing.get("validated_time", "")
            rows[i] = {**existing, **row}
            break
    else:
        rows.append(row)

    write_tsv(path, HOST_HEADER, rows)
    print(args.host_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
