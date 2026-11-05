#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import time
from pathlib import Path

from sar_utils import (
    REVISION_MANIFEST_HEADER,
    file_lock,
    file_hashes,
    now,
    read_simple_yaml,
    read_tsv,
    write_simple_yaml,
    write_tsv,
)


ACTIVE_ASSIGNMENT = {"Planned", "Running"}
ACTIVE_JOB = {"Planned", "Pending", "Submitted", "Queued", "Running", "Active"}


def build_rows(revision_id: str, scopes: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for raw in sorted(set(scopes)):
        path = Path(raw).expanduser().resolve()
        if not path.exists() or not path.is_file():
            rows.append({
                "revision_id": revision_id,
                "path": str(path),
                "file_role": "canonical",
                "status": "MISSING",
            })
            continue
        _, sha256 = file_hashes(path)
        stat = path.stat()
        rows.append({
            "revision_id": revision_id,
            "path": str(path),
            "file_role": "canonical",
            "size_bytes": stat.st_size,
            "modified_time_ns": stat.st_mtime_ns,
            "sha256": sha256,
            "semantic_fingerprint": "",
            "equivalence_rule": "byte_sha256",
            "source_assignment_id": "",
            "status": "Observed",
            "notes": "",
        })
    return rows


def observation_signature(rows: list[dict[str, object]]) -> list[tuple[str, str, str, str]]:
    return sorted(
        (
            str(row.get("path", "")),
            str(row.get("size_bytes", "")),
            str(row.get("modified_time_ns", "")),
            str(row.get("sha256", "")),
        )
        for row in rows
    )


def content_signature(rows: list[dict[str, object]]) -> list[tuple[str, str, str, str]]:
    return sorted(
        (
            str(row.get("path", "")),
            str(row.get("size_bytes", "")),
            str(row.get("sha256", "")),
            str(row.get("status", "")),
        )
        for row in rows
    )


def manifest_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def quiescence_issues(run_dir: Path) -> list[str]:
    issues: list[str] = []
    assignments = read_tsv(run_dir / "coordination/agent_assignments.tsv")
    for row in assignments:
        if row.get("status") in ACTIVE_ASSIGNMENT:
            issues.append(f"active_assignment:{row.get('assignment_id')}")
    for rel, id_field in [("logs/jobs.tsv", "job_id"), ("logs/remote_jobs.tsv", "remote_job_id")]:
        for row in read_tsv(run_dir / rel):
            if row.get("status") in ACTIVE_JOB:
                issues.append(f"active_job:{row.get(id_field)}")
    return issues


def seal_revision(args: argparse.Namespace, run_dir: Path, state_path: Path) -> int:
    with file_lock(run_dir / "coordination/transaction"):
        state = read_simple_yaml(state_path)
        if args.revision_id != state.get("canonical_revision", "r0000"):
            print("ERROR: revision is not the current canonical revision")
            return 1
        issues = quiescence_issues(run_dir)
        if issues:
            print("ERROR: workspace is not quiescent: " + ",".join(issues))
            return 1
        previous_path = Path(args.previous).expanduser().resolve()
        previous = read_tsv(previous_path)
        expected_scope = sorted(str(Path(x).expanduser().resolve()) for x in args.scope)
        if not previous or any(row.get("revision_id") != args.revision_id for row in previous):
            print("ERROR: previous snapshot is not bound to requested revision")
            return 1
        if sorted(row.get("path", "") for row in previous) != expected_scope:
            print("ERROR: previous snapshot scope differs from requested scope")
            return 1
        if args.stability_seconds < 5:
            print("ERROR: stability window must be at least 5 seconds")
            return 1
        time.sleep(args.stability_seconds)
        current = build_rows(args.revision_id, args.scope)
        if any(row.get("status") == "MISSING" for row in current):
            print("ERROR: seal scope contains missing files")
            return 1
        if observation_signature(previous) != observation_signature(current):
            print("ERROR: revision changed between stability observations")
            return 1
        revision_dir = run_dir / "coordination/revisions" / args.revision_id
        manifest = revision_dir / "revision_manifest.tsv"
        write_tsv(manifest, REVISION_MANIFEST_HEADER, current)
        digest = manifest_sha256(manifest)
        write_simple_yaml(revision_dir / "seal.yaml", {
            "revision_id": args.revision_id,
            "manifest_sha256": digest,
            "scope_fingerprint": args.scope_fingerprint,
            "sealed_time": now(),
            "status": "SEALED",
        })
        state["sealed_revision"] = args.revision_id
        state["sealed_scope_fingerprint"] = args.scope_fingerprint
        state["last_manifest_sha256"] = digest
        state["last_updated"] = now()
        write_simple_yaml(state_path, state)
    print(f"PASS\tSEALED\t{args.revision_id}\t{digest}")
    return 0


def verify_revision(revision_id: str, run_dir: Path) -> int:
    manifest = run_dir / "coordination/revisions" / revision_id / "revision_manifest.tsv"
    seal_data = read_simple_yaml(run_dir / "coordination/revisions" / revision_id / "seal.yaml")
    if not manifest.exists() or seal_data.get("status") != "SEALED":
        print("ERROR: revision is not sealed")
        return 1
    if not seal_data.get("scope_fingerprint"):
        print("ERROR: sealed revision lacks a scope fingerprint")
        return 1
    observed = read_tsv(manifest)
    current = build_rows(revision_id, [row.get("path", "") for row in observed])
    if content_signature(observed) != content_signature(current):
        missing = any(row.get("status") == "MISSING" for row in current)
        drift = "LATE_WRITE_OR_MISSING" if missing else "SEMANTIC"
        print(f"ERROR: sealed revision content drifted: {drift}")
        return 1
    if manifest_sha256(manifest) != seal_data.get("manifest_sha256"):
        print("ERROR: revision manifest checksum mismatch")
        return 1
    if observation_signature(observed) != observation_signature(current):
        print(
            f"PASS\tVERIFIED_METADATA_ONLY\t{revision_id}\t"
            f"{seal_data.get('manifest_sha256')}"
        )
        return 0
    print(f"PASS\tVERIFIED\t{revision_id}\t{seal_data.get('manifest_sha256')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Snapshot, seal, or verify one canonical revision.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot")
    snapshot.add_argument("--run-dir", required=True)
    snapshot.add_argument("--snapshot-id", required=True)
    snapshot.add_argument("--scope", action="append", required=True)

    seal = subparsers.add_parser("seal")
    seal.add_argument("--run-dir", required=True)
    seal.add_argument("--revision-id", required=True)
    seal.add_argument("--scope-fingerprint", required=True)
    seal.add_argument("--previous", required=True)
    seal.add_argument("--scope", action="append", required=True)
    seal.add_argument("--stability-seconds", type=float, default=5.0)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--run-dir", required=True)
    verify.add_argument("--revision-id", required=True)

    args = parser.parse_args()
    run_dir = Path(args.run_dir).expanduser().resolve()
    state_path = run_dir / "metadata/coordination.yaml"

    if args.command == "snapshot":
        state = read_simple_yaml(state_path)
        revision = state.get("canonical_revision", "r0000")
        output = run_dir / "coordination/snapshots" / f"{args.snapshot_id}.tsv"
        rows = build_rows(revision, args.scope)
        write_tsv(output, REVISION_MANIFEST_HEADER, rows)
        print(f"PASS\tSNAPSHOT\t{output}\t{manifest_sha256(output)}")
        return 0

    if args.command == "seal":
        return seal_revision(args, run_dir, state_path)

    return verify_revision(args.revision_id, run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
