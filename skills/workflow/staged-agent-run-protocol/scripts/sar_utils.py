#!/usr/bin/env python3
from __future__ import annotations

import csv
import fcntl
import hashlib
import html
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

PROTOCOL_NAME = "staged_agent_run_protocol"
PROTOCOL_VERSION = "0.2.1-rc"
POLICY_NAME = "three-stage-runtime-v1.json"


def runtime_policy_path(explicit: Optional[str] = None) -> Path:
    """Resolve explicit, installed, then repository policy locations."""
    if explicit:
        return Path(explicit).expanduser()
    configured = os.environ.get("CODEX_HOME")
    codex_home = Path(configured).expanduser() if configured else Path.home() / ".codex"
    installed = codex_home / "policies" / POLICY_NAME
    if installed.is_file():
        return installed
    repository = Path(__file__).resolve().parents[3] / "runtime" / "policies" / POLICY_NAME
    return repository if repository.is_file() else installed


def runtime_policy(explicit: Optional[str] = None) -> dict:
    with runtime_policy_path(explicit).open(encoding="utf-8") as handle:
        return json.load(handle)

TODO_HEADER = [
    "todo_id", "phase", "stage_id", "title", "status", "priority", "owner",
    "created_time", "updated_time", "blocked_by", "source_file",
    "evidence_path", "notes",
]
TODO_HISTORY_HEADER = [
    "time", "todo_id", "old_status", "new_status", "changed_by", "reason",
    "evidence_path", "notes",
]
STAGE_HEADER = [
    "stage_id", "stage_name", "stage_order", "stage_status", "gate_status",
    "qc_status", "required", "depends_on", "planned_start", "planned_end",
    "actual_start", "actual_end", "qc_criteria_path", "qc_report_path",
    "provenance_path", "outputs_manifest_path", "decision_id",
    "blocker_todo_id", "notes",
]
PATH_HEADER = [
    "path_id", "path", "path_role", "phase", "stage_id", "owner",
    "mutability", "required", "expected_pattern", "description",
    "created_by", "decision_id", "notes",
]
FILES_HEADER = [
    "file_id", "path_id", "file_path", "file_role", "format", "exists",
    "size_bytes", "n_rows", "n_columns", "created_time", "modified_time",
    "md5", "sha256", "producer_stage_id", "producer_command_id",
    "upstream_file_ids", "qc_status", "frozen_status", "notes",
]
QC_HEADER = [
    "qc_id", "stage_id", "criterion", "check_type", "required",
    "threshold", "evidence_path", "failure_action", "notes",
]
COMMAND_HEADER = [
    "command_id", "phase", "stage_id", "time", "cwd", "command", "env",
    "stdout_log", "stderr_log", "exit_code", "status", "notes",
]
JOB_HEADER = [
    "job_id", "stage_id", "submit_time", "command", "cwd", "env",
    "pid_or_scheduler_id", "stdout_log", "stderr_log", "expected_outputs",
    "status",
]
MONITOR_HEADER = [
    "time", "job_id", "check_round", "check_type", "interval_minutes",
    "job_status", "log_size", "new_log_lines", "output_size",
    "error_keywords", "decision", "notes",
]
HOST_HEADER = [
    "host_id", "ssh_alias", "host_role", "access_mode", "scheduler",
    "remote_project_root", "remote_data_root", "remote_scratch_root",
    "remote_results_root", "remote_env_root", "package_managers",
    "default_shell", "status", "validated_time", "validated_by", "notes",
]
PATH_MAP_HEADER = [
    "path_map_id", "host_id", "stage_id", "remote_path", "local_path",
    "path_role", "remote_is_canonical", "local_role", "sync_direction",
    "sync_method", "include_pattern", "exclude_pattern",
    "checksum_required_before_final", "checksum_mismatch_policy",
    "retention_policy", "max_expected_gb", "status", "created_time",
    "updated_time", "decision_id", "notes",
]
ENV_HEADER = [
    "env_id", "host_id", "env_scope", "env_manager", "env_name", "env_path",
    "python_version", "r_version", "bioconda_channels", "brew_prefix",
    "lock_file", "export_file", "tool_versions_file", "env_hash",
    "created_time", "last_verified_time", "status", "retention_policy",
    "created_by", "decision_id", "notes",
]
SOFTWARE_HEADER = [
    "tool_id", "tool_name", "tool_role", "host_id", "env_id", "manager",
    "executable_path", "version_command", "observed_version",
    "version_log_path", "install_source", "install_spec", "installed_time",
    "last_verified_time", "status", "notes",
]
REFERENCE_HEADER = [
    "reference_id", "reference_type", "species", "reference_name",
    "reference_version", "annotation_version", "database_release", "host_id",
    "canonical_path", "local_mirror_path", "source_uri", "source_date", "md5",
    "sha256", "index_paths", "used_by_stage_ids", "status", "notes",
]
STORAGE_POLICY_HEADER = [
    "storage_id", "host_id", "path", "storage_class", "canonical_role",
    "allowed_file_classes", "retention_policy", "cleanup_allowed",
    "auto_cleanup_allowed", "max_expected_gb", "actual_gb", "last_du_time",
    "disk_status", "owner", "decision_id", "notes",
]
REMOTE_COMMAND_HEADER = [
    "remote_command_id", "phase", "stage_id", "host_id", "time",
    "remote_cwd", "command", "command_class", "env_id", "stdout_log",
    "stderr_log", "exit_code", "status", "expected_outputs", "decision_id",
    "notes",
]
REMOTE_JOB_HEADER = [
    "remote_job_id", "host_id", "stage_id", "submit_time", "remote_cwd",
    "remote_command", "scheduler_job_id", "remote_stdout_log",
    "remote_stderr_log", "expected_remote_outputs", "status", "last_sync_id",
    "notes",
]
SYNC_HEADER = [
    "sync_id", "host_id", "path_map_id", "sync_time", "direction",
    "remote_path", "local_path", "sync_method", "status", "bytes_synced",
    "checksum_status", "checksum_mismatch_policy", "remote_checksum_path",
    "local_checksum_path", "provenance_path", "notes",
]
INSTALL_HEADER = [
    "install_id", "time", "host_id", "env_id", "manager", "action",
    "package", "requested_version", "resolved_version", "command", "cwd",
    "stdout_log", "stderr_log", "exit_code", "status", "decision_id", "notes",
]
DISK_USAGE_HEADER = [
    "time", "host_id", "path", "check_type", "df_available",
    "df_used_percent", "du_size_gb", "file_count", "threshold_status",
    "stage_id", "job_id", "notes",
]
CLEANUP_CANDIDATE_HEADER = [
    "candidate_id", "host_id", "path", "storage_class", "size_gb", "reason",
    "safe_to_delete_after", "requires_user_approval",
    "backup_or_checksum_evidence", "related_stage_id", "related_file_ids",
    "status", "decision_id", "notes",
]
FROZEN_HEADER = [
    "file_id", "path", "file_role", "stage_id", "md5", "sha256",
    "size_bytes", "frozen_time", "freeze_decision_id", "qc_status", "notes",
]
CHECKSUM_HEADER = ["path", "size_bytes", "md5", "sha256", "time"]
AGENT_ASSIGNMENT_HEADER = [
    "assignment_id", "agent_path", "parent_agent", "role", "model",
    "base_revision", "read_scope", "write_scope", "forbidden_paths",
    "expected_outputs", "status", "started_time", "finished_time",
    "return_fingerprint", "notes",
]
FINDINGS_HEADER = ["finding_id", "severity", "status", "gate", "evidence_path"]
INTEGRATION_EVENT_HEADER = [
    "event_id", "assignment_id", "base_revision",
    "canonical_revision_before", "canonical_revision_after",
    "staged_manifest_sha256", "decision", "reason", "time",
    "integrator", "notes",
]
REVISION_MANIFEST_HEADER = [
    "revision_id", "path", "file_role", "size_bytes", "modified_time_ns",
    "sha256", "semantic_fingerprint", "equivalence_rule",
    "source_assignment_id", "status", "notes",
]
AUDIT_RECEIPT_HEADER = [
    "receipt_id", "audit_type", "revision_id", "manifest_sha256",
    "scope_fingerprint", "audit_cutoff", "auditor", "verdict",
    "finding_fingerprint", "gate_fingerprint", "gate_statuses", "auditor_assignment_id", "audit_report_path",
    "audit_report_sha256", "findings_path", "findings_sha256", "valid_status", "invalidated_by", "notes",
]


def validate_model_for_role(model: str, role: str, runtime_evidence=None,
                            capability_evidence=None) -> bool:
    """Dynamic evidence takes precedence; no evidence preserves legacy checks."""
    if runtime_evidence is not None or capability_evidence is not None:
        # Resolve the sibling skill rather than a global policy-dependent import.
        from importlib.util import spec_from_file_location, module_from_spec
        path = Path(__file__).resolve().parents[2] / "three-stage-complex-workflow/scripts/model_routing.py"
        spec = spec_from_file_location("three_stage_model_routing", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.model_supports_role(model, role, runtime_evidence, capability_evidence)
    return bool(model and role in runtime_policy().get("model_roles", {}).get(model, []))


def validate_assignment_model(assignment: dict) -> bool:
    """Recheck registered dynamic evidence, retaining legacy static semantics."""
    notes = assignment.get("notes", "")
    if "model_evidence=" not in notes:
        return validate_model_for_role(assignment.get("model", ""), assignment.get("role", ""))
    try:
        evidence = json.loads(notes.rsplit("model_evidence=", 1)[1])
        if evidence["stage"] not in {"ANALYZE", "REFINE", "EXECUTE"}:
            return False
        role = assignment.get("role", "")
        if evidence["stage"] != "EXECUTE" and role not in {"READ_ONLY_REVIEWER", "AUDITOR"}:
            return False
        inputs = []
        for key in ("runtime", "capabilities"):
            raw = Path(evidence[key]["path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != evidence[key]["sha256"]:
                return False
            inputs.append(json.loads(raw))
        if assignment.get("agent_path") not in {"root", "/root"}:
            if (evidence["delegation_authorized"] is not True
                    or not evidence["delegation_evidence"]
                    or inputs[0].get("delegation_tool_available") is not True):
                return False
        return validate_model_for_role(assignment.get("model", ""), role, *inputs)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False


def ready_from_findings(findings: list[dict[str, str]], gates: dict[str, str]) -> bool:
    """Ready requires all gates verified and no unresolved Critical or Major."""
    if not gates or any(value != "verified" for value in gates.values()):
        return False
    return not any(
        row.get("severity") in {"Critical", "Major"}
        and row.get("status", "").lower() == "unresolved"
        for row in findings
    )

VALID_TODO_STATUSES = {"Pending", "Active", "Blocked", "Done", "Skipped", "Cancelled", "Running"}
VALID_STAGE_STATUSES = {
    "NotStarted", "Ready", "Running", "QC_Pending", "QC_Passed", "QC_Failed",
    "Blocked", "Waived_With_Decision", "Frozen", "Skipped",
}
VALID_GATE_STATUSES = {
    "Gate_Not_Ready", "Gate_Open", "QC_Passed", "QC_Failed",
    "Waived_With_Decision", "Blocked",
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def slugify(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "task"


def read_simple_yaml(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, val = line.split(":", 1)
        data[key.strip()] = val.strip().strip('"')
    return data


@contextmanager
def file_lock(path: Path):
    """Serialize a complete read-modify-write transaction for a control file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + ".lock")
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def _atomic_text_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.",
        suffix=".tmp", delete=False,
    ) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def write_simple_yaml(path: Path, data: dict[str, object]) -> None:
    lines = [f"{key}: {'' if value is None else value}" for key, value in data.items()]
    with file_lock(path):
        _atomic_text_write(path, "\n".join(lines) + "\n")


def ensure_tsv(path: Path, header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.stat().st_size == 0:
        path.write_text("\t".join(header) + "\n", encoding="utf-8")


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def append_tsv(path: Path, header: list[str], row: dict[str, object]) -> None:
    with file_lock(path):
        ensure_tsv(path, header)
        with path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header, delimiter="\t", extrasaction="ignore")
            writer.writerow({key: "" if row.get(key) is None else row.get(key, "") for key in header})


def _write_tsv_unlocked(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", dir=path.parent,
        prefix=f".{path.name}.", suffix=".tmp", delete=False,
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=header, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key, "") for key in header})
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def write_tsv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    with file_lock(path):
        _write_tsv_unlocked(path, header, rows)


def update_tsv(path: Path, header: list[str], mutator) -> list[dict[str, object]]:
    """Atomically read, validate, mutate, and replace a TSV control record."""
    with file_lock(path):
        rows: list[dict[str, object]] = list(read_tsv(path))
        updated = mutator(rows)
        _write_tsv_unlocked(path, header, updated)
        return updated


def validate_tsv_header(path: Path, expected: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing\t{path}"]
    first = path.read_text(encoding="utf-8").splitlines()[0] if path.stat().st_size else ""
    observed = first.split("\t") if first else []
    missing = [col for col in expected if col not in observed]
    if missing:
        return [f"bad_header\t{path}\tmissing_columns={','.join(missing)}"]
    return []



def has_substantive_content(path: Path, min_nonheading_lines: int = 1) -> bool:
    """Return True only when a Markdown/text file contains content beyond template headings."""
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        return False
    substantive = 0
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        if set(line) <= {"-", "_", "=", "*"}:
            continue
        substantive += 1
        if substantive >= min_nonheading_lines:
            return True
    return False


def nonempty_text(path: Path, min_nonblank_lines: int = 2) -> bool:
    if not path.exists() or not path.is_file() or path.stat().st_size == 0:
        return False
    lines = [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    return sum(1 for line in lines if line) >= min_nonblank_lines


def path_in_run_or_absolute(path_value: str, run_dir: Path) -> Path:
    path = Path(path_value).expanduser()
    return path if path.is_absolute() else run_dir / path


def find_registered_path(rows: list[dict[str, str]], target: Path, run_dir: Path) -> dict[str, str] | None:
    target_resolved = target.expanduser().resolve()
    for row in rows:
        raw = row.get("path", "")
        if not raw:
            continue
        registered = path_in_run_or_absolute(raw, run_dir)
        try:
            if registered.resolve() == target_resolved:
                return row
        except FileNotFoundError:
            if registered.absolute() == target.absolute():
                return row
    return None


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def file_hashes(path: Path) -> tuple[str, str]:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest()


def rel_link(run_dir: Path, target: str) -> str:
    target_path = run_dir / target
    return html.escape(target) if target_path.exists() else ""


def html_escape(value: object) -> str:
    return html.escape("" if value is None else str(value))
