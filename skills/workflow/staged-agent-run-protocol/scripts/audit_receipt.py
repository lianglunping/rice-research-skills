#!/usr/bin/env python3
"""Issue and independently validate revision-bound audit receipts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import sys
from pathlib import Path

from sar_utils import AUDIT_RECEIPT_HEADER, file_lock, now, read_simple_yaml, read_tsv, update_tsv, validate_assignment_model

FINDING_FIELDS = ["finding_id", "severity", "status", "gate", "evidence_path"]
SEVERITIES = {"Critical", "Major", "Minor", "Info"}
FINDING_STATUSES = {"resolved", "unresolved"}
VERDICTS = {"Ready", "Not Ready"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gate_fingerprint(gates: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{name}={gates[name]}\n" for name in sorted(gates)).encode()).hexdigest()


def parse_gates(values: list[str]) -> dict[str, str]:
    gates: dict[str, str] = {}
    for value in values:
        if value.count("=") != 1:
            raise ValueError("gate status must be name=status")
        name, status = value.split("=", 1)
        if not name or not status or name in gates:
            raise ValueError("gate status name must be unique and nonempty")
        gates[name] = status
    if not gates:
        raise ValueError("at least one gate status is required")
    return gates


def parse_findings(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None or any(field not in reader.fieldnames for field in FINDING_FIELDS):
            raise ValueError("findings TSV lacks required header")
        rows = list(reader)
    for row in rows:
        if any(not row.get(field, "") for field in FINDING_FIELDS):
            raise ValueError("findings TSV has empty required field")
        if row["severity"] not in SEVERITIES or row["status"] not in FINDING_STATUSES:
            raise ValueError("findings TSV has invalid severity or status")
    return rows


def ready_from(findings: list[dict[str, str]], gates: dict[str, str]) -> bool:
    return bool(gates) and all(value == "verified" for value in gates.values()) and not any(
        row["severity"] in {"Critical", "Major"} and row["status"] == "unresolved" for row in findings
    )


def expected_return_fingerprint(report_sha: str, findings_sha: str, verdict: str, gates_sha: str) -> str:
    return hashlib.sha256((report_sha + "\n" + findings_sha + "\n" + verdict + "\n" + gates_sha + "\n").encode()).hexdigest()


def verify_revision(run_dir: Path, revision_id: str) -> tuple[bool, str]:
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("snapshot_revision.py")), "verify", "--run-dir", str(run_dir), "--revision-id", revision_id], text=True, capture_output=True, check=False)
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def receipt_issues(run_dir: Path, receipt: dict[str, str]) -> list[str]:
    issues: list[str] = []
    state = read_simple_yaml(run_dir / "metadata/coordination.yaml")
    revision = receipt.get("revision_id", "")
    if receipt.get("verdict") not in VERDICTS:
        issues.append("invalid_verdict")
    if state.get("canonical_revision") != revision or state.get("sealed_revision") != revision:
        issues.append("revision_not_current_and_sealed")
    if state.get("last_manifest_sha256") != receipt.get("manifest_sha256"):
        issues.append("manifest_binding_changed")
    if state.get("sealed_scope_fingerprint") != receipt.get("scope_fingerprint"):
        issues.append("scope_binding_changed")
    report = Path(receipt.get("audit_report_path", "")); findings = Path(receipt.get("findings_path", ""))
    if not report.is_file() or sha256(report) != receipt.get("audit_report_sha256"):
        issues.append("audit_report_drift")
    if not findings.is_file() or sha256(findings) != receipt.get("findings_sha256"):
        issues.append("findings_drift")
        parsed: list[dict[str, str]] = []
    else:
        try:
            parsed = parse_findings(findings)
        except ValueError as exc:
            issues.append(f"findings_schema:{exc}"); parsed = []
    try:
        gates = parse_gates(receipt.get("gate_statuses", "").split("|"))
        if gate_fingerprint(gates) != receipt.get("gate_fingerprint"):
            issues.append("gate_fingerprint_changed")
        if receipt.get("verdict") == "Ready" and not ready_from(parsed, gates):
            issues.append("ready_policy_failed")
    except ValueError as exc:
        issues.append(f"gates:{exc}")
    assignments = read_tsv(run_dir / "coordination/agent_assignments.tsv")
    assignment = next((row for row in assignments if row.get("assignment_id") == receipt.get("auditor_assignment_id")), None)
    if assignment is None or assignment.get("role") != "AUDITOR" or assignment.get("status") != "Completed":
        issues.append("auditor_not_completed_registered")
    elif not validate_assignment_model(assignment):
        issues.append("auditor_model_role_incompatible")
    elif assignment.get("base_revision") != revision or assignment.get("agent_path") != receipt.get("auditor"):
        issues.append("auditor_identity_or_revision_mismatch")
    else:
        expected = expected_return_fingerprint(receipt.get("audit_report_sha256", ""), receipt.get("findings_sha256", ""), receipt.get("verdict", ""), receipt.get("gate_fingerprint", ""))
        if assignment.get("return_fingerprint") != expected:
            issues.append("auditor_return_fingerprint_mismatch")
    ok, detail = verify_revision(run_dir, revision)
    if not ok:
        issues.append("sealed_revision_drift:" + detail)
    return issues


def invalidate(registry: Path, receipt_id: str, reason: str) -> None:
    def mutate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
        receipt = next((row for row in rows if row.get("receipt_id") == receipt_id), None)
        if receipt is not None:
            receipt["valid_status"] = "Invalid"; receipt["invalidated_by"] = reason
        return rows
    update_tsv(registry, AUDIT_RECEIPT_HEADER, mutate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue, validate, or invalidate a revision-bound audit receipt.")
    subs = parser.add_subparsers(dest="command", required=True)
    issue = subs.add_parser("issue")
    for option in ("run-dir", "receipt-id", "audit-type", "revision-id", "scope-fingerprint", "auditor", "verdict", "finding-fingerprint", "auditor-assignment-id", "audit-report-path", "findings-path"):
        issue.add_argument("--" + option, required=True)
    issue.add_argument("--gate-status", action="append", default=[])
    issue.add_argument("--notes", default="")
    validate = subs.add_parser("validate"); validate.add_argument("--run-dir", required=True); validate.add_argument("--receipt-id", required=True)
    invalid = subs.add_parser("invalidate"); invalid.add_argument("--run-dir", required=True); invalid.add_argument("--receipt-id", required=True); invalid.add_argument("--reason", required=True)
    args = parser.parse_args(); run_dir = Path(args.run_dir).expanduser().resolve(); registry = run_dir / "coordination/audit_receipts.tsv"
    if args.command == "invalidate":
        with file_lock(run_dir / "coordination/transaction"): invalidate(registry, args.receipt_id, args.reason)
        print(f"PASS\tINVALIDATED\t{args.receipt_id}\t{args.reason}"); return 0
    if args.command == "issue":
        try:
            gates = parse_gates(args.gate_status); findings = parse_findings(Path(args.findings_path)); report = Path(args.audit_report_path); findings_path = Path(args.findings_path)
            if args.verdict not in VERDICTS: raise ValueError("verdict must be Ready or Not Ready")
            if not report.is_file() or not findings_path.is_file(): raise ValueError("receipt requires existing audit report and findings")
            if args.finding_fingerprint != sha256(findings_path): raise ValueError("finding fingerprint does not match findings bytes")
            if args.verdict == "Ready" and not ready_from(findings, gates): raise ValueError("Ready requires verified gates and no unresolved Critical/Major")
        except ValueError as exc:
            print(f"ERROR: {exc}"); return 1
        with file_lock(run_dir / "coordination/transaction"):
            state = read_simple_yaml(run_dir / "metadata/coordination.yaml")
            if state.get("canonical_revision") != args.revision_id or state.get("sealed_revision") != args.revision_id or state.get("sealed_scope_fingerprint") != args.scope_fingerprint:
                print("ERROR: audit receipt must bind to current sealed revision and scope"); return 1
            gate_sha = gate_fingerprint(gates); report_sha = sha256(report); findings_sha = sha256(findings_path)
            candidate = {"receipt_id": args.receipt_id, "audit_type": args.audit_type, "revision_id": args.revision_id, "manifest_sha256": state.get("last_manifest_sha256", ""), "scope_fingerprint": args.scope_fingerprint, "audit_cutoff": now(), "auditor": args.auditor, "verdict": args.verdict, "finding_fingerprint": args.finding_fingerprint, "gate_fingerprint": gate_sha, "gate_statuses": "|".join(f"{key}={gates[key]}" for key in sorted(gates)), "auditor_assignment_id": args.auditor_assignment_id, "audit_report_path": str(report), "audit_report_sha256": report_sha, "findings_path": str(findings_path), "findings_sha256": findings_sha, "valid_status": "Valid", "invalidated_by": "", "notes": args.notes}
            issues = receipt_issues(run_dir, candidate)
            if issues:
                print("ERROR: " + ";".join(issues)); return 1
            def mutate(rows: list[dict[str, object]]) -> list[dict[str, object]]:
                if any(row.get("receipt_id") == args.receipt_id for row in rows): raise ValueError(f"duplicate receipt_id: {args.receipt_id}")
                rows.append(candidate); return rows
            try: update_tsv(registry, AUDIT_RECEIPT_HEADER, mutate)
            except ValueError as exc: print(f"ERROR: {exc}"); return 1
        print(f"PASS\tISSUED\t{args.receipt_id}\t{args.revision_id}"); return 0
    with file_lock(run_dir / "coordination/transaction"):
        receipt = next((row for row in read_tsv(registry) if row.get("receipt_id") == args.receipt_id), None)
        if receipt is None: print(f"ERROR: receipt not found: {args.receipt_id}"); return 1
        if receipt.get("valid_status") != "Valid": print(f"ERROR: receipt is not valid: {args.receipt_id}"); return 1
        issues = receipt_issues(run_dir, receipt)
        if issues:
            invalidate(registry, args.receipt_id, ";".join(issues)); print("ERROR: receipt invalidated: " + ";".join(issues)); return 1
    print(f"PASS\tVALID\t{args.receipt_id}\t{receipt.get('revision_id')}"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
