#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from apply_staged_bundle import apply_staged_manifest

from sar_utils import (
    INTEGRATION_EVENT_HEADER,
    append_tsv,
    file_lock,
    now,
    read_simple_yaml,
    read_tsv,
    write_simple_yaml,
)


def next_revision(current: str) -> str:
    match = re.fullmatch(r"r(\d+)", current)
    if not match:
        raise ValueError(f"invalid canonical revision: {current}")
    return f"r{int(match.group(1)) + 1:04d}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Record one sequential canonical integration decision.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--assignment-id", required=True)
    parser.add_argument("--base-revision", required=True)
    parser.add_argument("--staged-manifest-sha256", default="")
    parser.add_argument("--decision", choices=["integrated", "rejected", "stale"], required=True)
    parser.add_argument("--reason", default="")
    parser.add_argument("--integrator", default="root")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    if args.integrator not in {"root", "/root"}:
        print("ERROR: only root may integrate canonical changes")
        return 1
    state_path = run_dir / "metadata/coordination.yaml"
    with file_lock(run_dir / "coordination/transaction"):
        state = read_simple_yaml(state_path)
        current = state.get("canonical_revision", "r0000")
        if args.base_revision != current:
            print(f"ERROR: stale integration base: expected {current}, got {args.base_revision}")
            return 1
        events = read_tsv(run_dir / "coordination/integration_events.tsv")
        if any(row.get("event_id") == args.event_id for row in events):
            print(f"ERROR: duplicate event_id: {args.event_id}")
            return 1
        assignments = read_tsv(run_dir / "coordination/agent_assignments.tsv")
        assignment = next(
            (row for row in assignments if row.get("assignment_id") == args.assignment_id),
            None,
        )
        if assignment is None:
            print(f"ERROR: assignment not registered: {args.assignment_id}")
            return 1
        if args.decision == "integrated":
            if assignment.get("status") != "Completed":
                print(f"ERROR: assignment is not completed: {args.assignment_id}")
                return 1
            if assignment.get("role") != "STAGING_WRITER":
                print(f"ERROR: only a STAGING_WRITER return can be integrated: {args.assignment_id}")
                return 1
            if not args.staged_manifest_sha256:
                print("ERROR: integrated decision requires staged-manifest-sha256")
                return 1
            manifest = run_dir / "coordination/staging" / args.assignment_id / "manifest.json"
            if not manifest.exists():
                print("ERROR: staged manifest is missing")
                return 1
            actual = hashlib.sha256(manifest.read_bytes()).hexdigest()
            if actual != args.staged_manifest_sha256:
                print("ERROR: staged manifest hash does not match current staged manifest")
                return 1
            if assignment.get("return_fingerprint") != actual:
                print("ERROR: completed assignment return fingerprint does not match staged manifest")
                return 1
            try:
                # This call is deliberately inside the coordination lock.  It applies
                # target/source CAS before either event or revision can advance.
                apply_staged_manifest(manifest.parent, manifest, actual)
            except Exception as exc:
                print(f"ERROR: staged manifest application failed: {exc}")
                return 1

        after = next_revision(current) if args.decision == "integrated" else current
        append_tsv(
            run_dir / "coordination/integration_events.tsv",
            INTEGRATION_EVENT_HEADER,
            {
                "event_id": args.event_id,
                "assignment_id": args.assignment_id,
                "base_revision": args.base_revision,
                "canonical_revision_before": current,
                "canonical_revision_after": after,
                "staged_manifest_sha256": args.staged_manifest_sha256,
                "decision": args.decision,
                "reason": args.reason,
                "time": now(),
                "integrator": args.integrator,
                "notes": args.notes,
            },
        )
        if after != current:
            state["coordination_epoch"] = int(state.get("coordination_epoch", "0")) + 1
            state["canonical_revision"] = after
            state["sealed_revision"] = ""
            state["sealed_scope_fingerprint"] = ""
            state["last_manifest_sha256"] = ""
            state["last_updated"] = now()
            write_simple_yaml(state_path, state)
    print(f"PASS\t{args.event_id}\t{current}\t{after}\t{args.decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
