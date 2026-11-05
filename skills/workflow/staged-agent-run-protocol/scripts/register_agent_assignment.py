#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from sar_utils import (
    AGENT_ASSIGNMENT_HEADER,
    file_lock,
    now,
    read_simple_yaml,
    update_tsv,
    validate_model_for_role,
)


ROLES = {
    "READ_ONLY_REVIEWER",
    "STAGING_WRITER",
    "CANONICAL_INTEGRATOR",
    "AUDITOR",
}
STATUSES = {"Planned", "Running", "Completed", "Failed", "Cancelled", "Stale"}
ACTIVE = {"Planned", "Running"}


def parse_scopes(values: list[str]) -> list[Path]:
    scopes: list[Path] = []
    for value in values:
        for item in value.split("|"):
            if item.strip():
                scopes.append(Path(item.strip()).expanduser().resolve())
    return scopes


def paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def main() -> int:
    parser = argparse.ArgumentParser(description="Register or update one bounded agent assignment.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--assignment-id", required=True)
    parser.add_argument("--agent-path", default="")
    parser.add_argument("--parent-agent", default="")
    parser.add_argument("--role", choices=sorted(ROLES))
    parser.add_argument("--model", default="")
    parser.add_argument("--base-revision", default="")
    parser.add_argument("--read-scope", action="append", default=[])
    parser.add_argument("--write-scope", action="append", default=[])
    parser.add_argument("--forbidden-paths", action="append", default=[])
    parser.add_argument("--expected-outputs", action="append", default=[])
    parser.add_argument("--status", choices=sorted(STATUSES), required=True)
    parser.add_argument("--return-fingerprint", default="")
    parser.add_argument("--notes", default="")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--runtime-evidence", type=Path)
    parser.add_argument("--capability-evidence", type=Path)
    parser.add_argument("--delegation-authorized", action="store_true")
    parser.add_argument("--delegation-evidence")
    parser.add_argument("--workflow-stage", choices=["ANALYZE", "REFINE", "EXECUTE"])
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    registry = run_dir / "coordination/agent_assignments.tsv"
    canonical_revision = ""
    runtime = capabilities = None
    evidence_note = ""
    if args.runtime_evidence or args.capability_evidence:
        try:
            if not args.runtime_evidence or not args.capability_evidence:
                raise ValueError("both runtime and independent task capability evidence are required")
            runtime = json.loads(args.runtime_evidence.read_text(encoding="utf-8"))
            if not isinstance(runtime, dict):
                raise ValueError("runtime evidence must be an object")
            capabilities = json.loads(args.capability_evidence.read_text(encoding="utf-8"))
            evidence_note = "model_evidence=" + json.dumps({
                "runtime": {"path": str(args.runtime_evidence.resolve()),
                    "sha256": hashlib.sha256(args.runtime_evidence.read_bytes()).hexdigest()},
                "capabilities": {"path": str(args.capability_evidence.resolve()),
                    "sha256": hashlib.sha256(args.capability_evidence.read_bytes()).hexdigest()},
                "stage": args.workflow_stage,
                "delegation_authorized": args.delegation_authorized,
                "delegation_evidence": args.delegation_evidence,
            }, sort_keys=True)
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 1

    def mutate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        existing = next((row for row in rows if row.get("assignment_id") == args.assignment_id), None)
        if args.update:
            if existing is None:
                raise ValueError(f"assignment not found: {args.assignment_id}")
            if args.model and args.model != existing.get("model"):
                raise ValueError("update model must match registered model")
            if existing.get("status") in {"Completed", "Failed", "Cancelled", "Stale"} and args.status in ACTIVE:
                raise ValueError("terminal assignment cannot be reopened")
            if existing.get("status") in {"Completed", "Failed", "Cancelled", "Stale"} and args.status != existing.get("status"):
                raise ValueError("terminal assignment status is immutable")
            if args.status == "Completed" and not args.return_fingerprint:
                raise ValueError("Completed assignment requires return-fingerprint")
            existing["status"] = args.status
            if args.status in {"Completed", "Failed", "Cancelled", "Stale"}:
                existing["finished_time"] = now()
            if args.return_fingerprint:
                existing["return_fingerprint"] = args.return_fingerprint
            if args.notes:
                existing["notes"] = args.notes
            return rows

        if existing is not None:
            raise ValueError(f"duplicate assignment_id: {args.assignment_id}")
        if not args.agent_path or not args.role or not args.base_revision or not args.model:
            raise ValueError("new assignment requires agent-path, role, model, and base-revision")
        if runtime is not None and args.workflow_stage is None:
            raise ValueError("dynamic assignment requires workflow-stage")
        if runtime is not None and args.agent_path not in {"root", "/root"}:
            if not args.delegation_authorized or not args.delegation_evidence:
                raise ValueError("dynamic child assignment requires independent delegation authority evidence")
            if runtime.get("delegation_tool_available") is not True:
                raise ValueError("delegation tool unavailable")
        if args.workflow_stage in {"ANALYZE", "REFINE"} and args.role not in {"READ_ONLY_REVIEWER", "AUDITOR"}:
            raise ValueError("planning stages cannot register write roles")
        if not validate_model_for_role(args.model, args.role, runtime, capabilities):
            raise ValueError("model is absent, unsupported, or incompatible with role")
        if args.base_revision != canonical_revision:
            raise ValueError(
                f"stale base revision: expected {canonical_revision}, got {args.base_revision}"
            )
        if args.status == "Completed" and not args.return_fingerprint:
            raise ValueError("Completed assignment requires return-fingerprint")

        read_scopes = parse_scopes(args.read_scope)
        write_scopes = parse_scopes(args.write_scope)
        forbidden = parse_scopes(args.forbidden_paths)
        if args.role in {"READ_ONLY_REVIEWER", "AUDITOR"} and write_scopes:
            raise ValueError(f"{args.role} cannot have write scope")
        if args.role == "CANONICAL_INTEGRATOR":
            if args.agent_path not in {"root", "/root"}:
                raise ValueError("CANONICAL_INTEGRATOR is reserved for root")
        if args.role == "STAGING_WRITER":
            if not write_scopes:
                raise ValueError("STAGING_WRITER requires a write scope")
            owned_root = (run_dir / "coordination/staging" / args.assignment_id).resolve()
            for scope in write_scopes:
                if scope != owned_root and owned_root not in scope.parents:
                    raise ValueError(
                        f"staging writer scope must be inside {owned_root}: {scope}"
                    )
        for scope in write_scopes:
            if any(paths_overlap(scope, blocked) for blocked in forbidden):
                raise ValueError(f"write scope overlaps forbidden path: {scope}")

        if args.status in ACTIVE:
            if args.role in {"STAGING_WRITER", "CANONICAL_INTEGRATOR"} and any(
                row.get("status") in ACTIVE and row.get("role") in {"STAGING_WRITER", "CANONICAL_INTEGRATOR"}
                for row in rows
            ):
                raise ValueError("at most one active writer is permitted")
            if args.role == "CANONICAL_INTEGRATOR" and any(
                row.get("status") in ACTIVE and row.get("role") == "CANONICAL_INTEGRATOR"
                for row in rows
            ):
                raise ValueError("another canonical integrator is active")
            for row in rows:
                if row.get("status") not in ACTIVE:
                    continue
                other_scopes = parse_scopes([str(row.get("write_scope", ""))])
                for scope in write_scopes:
                    if any(paths_overlap(scope, other) for other in other_scopes):
                        raise ValueError(
                            f"write scope overlaps active assignment {row.get('assignment_id')}: {scope}"
                        )

        row = {
            "assignment_id": args.assignment_id,
            "agent_path": args.agent_path,
            "parent_agent": args.parent_agent,
            "role": args.role,
            "model": args.model,
            "base_revision": args.base_revision,
            "read_scope": "|".join(str(path) for path in read_scopes),
            "write_scope": "|".join(str(path) for path in write_scopes),
            "forbidden_paths": "|".join(str(path) for path in forbidden),
            "expected_outputs": "|".join(args.expected_outputs),
            "status": args.status,
            "started_time": now() if args.status in ACTIVE else "",
            "finished_time": now() if args.status not in ACTIVE else "",
            "return_fingerprint": args.return_fingerprint,
            "notes": " | ".join(v for v in (args.notes, evidence_note) if v),
        }
        rows.append(row)
        return rows

    try:
        with file_lock(run_dir / "coordination/transaction"):
            coordination = read_simple_yaml(run_dir / "metadata/coordination.yaml")
            canonical_revision = coordination.get("canonical_revision", "r0000")
            update_tsv(registry, AGENT_ASSIGNMENT_HEADER, mutate)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"PASS\t{args.assignment_id}\t{args.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
