#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import (
    AGENT_ASSIGNMENT_HEADER, AUDIT_RECEIPT_HEADER, CLEANUP_CANDIDATE_HEADER,
    COMMAND_HEADER, DISK_USAGE_HEADER, ENV_HEADER, FILES_HEADER, HOST_HEADER,
    INSTALL_HEADER, INTEGRATION_EVENT_HEADER, JOB_HEADER, MONITOR_HEADER,
    PATH_HEADER, PATH_MAP_HEADER, QC_HEADER, REFERENCE_HEADER,
    REMOTE_COMMAND_HEADER, REMOTE_JOB_HEADER, SOFTWARE_HEADER, STAGE_HEADER,
    STORAGE_POLICY_HEADER, SYNC_HEADER, TODO_HEADER, TODO_HISTORY_HEADER,
    has_substantive_content, nonempty_text, read_simple_yaml, read_tsv,
    validate_tsv_header, validate_assignment_model,
)
from audit_receipt import receipt_issues


BASE_REQUIRED = [
    "README.md", "index.html", "TODO.md", "todo.tsv", "todo_history.tsv",
    "metadata/run.yaml", "metadata/status.yaml", "00_brief/brief.md",
    "01_analysis/analysis.md", "02_plan/plan.md",
    "02_plan/path_registry.tsv", "02_plan/stage_registry.tsv",
    "02_plan/qc_criteria.tsv", "logs/commands.tsv", "logs/jobs.tsv",
    "logs/monitor.tsv", "docs/decisions.md", "docs/assumptions.md",
    "docs/known_issues.md", "metadata/hosts.tsv", "metadata/path_maps.tsv",
    "metadata/env_registry.tsv", "metadata/software_registry.tsv",
    "metadata/reference_registry.tsv", "metadata/storage_policy.tsv",
    "logs/remote_commands.tsv", "logs/remote_jobs.tsv", "logs/sync.tsv",
    "logs/install.tsv", "logs/disk_usage.tsv", "logs/cleanup_candidates.tsv",
    "monitoring/remote_monitor_plan.md", "metadata/coordination.yaml",
    "coordination/agent_assignments.tsv", "coordination/integration_events.tsv",
    "coordination/audit_receipts.tsv",
]
FINAL_REQUIRED = [
    "03_execution/final/final_report.md", "03_execution/final/provenance.md",
    "03_execution/final/frozen_outputs.tsv", "03_execution/final/checksums.tsv",
    "03_execution/final/qa_summary.tsv", "03_execution/final/reproduce.sh",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check staged run required artifacts.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--final", action="store_true", help="Also require finalization artifacts.")
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    profile = read_simple_yaml(run_dir / "metadata/run.yaml").get("profile", "standard")

    missing: list[str] = [p for p in BASE_REQUIRED if not (run_dir / p).exists()]
    issues: list[str] = []
    if args.final or profile == "strict":
        missing.extend([p for p in FINAL_REQUIRED if not (run_dir / p).exists()])

    header_checks = [
        ("todo.tsv", TODO_HEADER),
        ("todo_history.tsv", TODO_HISTORY_HEADER),
        ("02_plan/path_registry.tsv", PATH_HEADER),
        ("02_plan/files_manifest.tsv", FILES_HEADER),
        ("02_plan/stage_registry.tsv", STAGE_HEADER),
        ("02_plan/qc_criteria.tsv", QC_HEADER),
        ("logs/commands.tsv", COMMAND_HEADER),
        ("logs/jobs.tsv", JOB_HEADER),
        ("logs/monitor.tsv", MONITOR_HEADER),
        ("metadata/hosts.tsv", HOST_HEADER),
        ("metadata/path_maps.tsv", PATH_MAP_HEADER),
        ("metadata/env_registry.tsv", ENV_HEADER),
        ("metadata/software_registry.tsv", SOFTWARE_HEADER),
        ("metadata/reference_registry.tsv", REFERENCE_HEADER),
        ("metadata/storage_policy.tsv", STORAGE_POLICY_HEADER),
        ("logs/remote_commands.tsv", REMOTE_COMMAND_HEADER),
        ("logs/remote_jobs.tsv", REMOTE_JOB_HEADER),
        ("logs/sync.tsv", SYNC_HEADER),
        ("logs/install.tsv", INSTALL_HEADER),
        ("logs/disk_usage.tsv", DISK_USAGE_HEADER),
        ("logs/cleanup_candidates.tsv", CLEANUP_CANDIDATE_HEADER),
        ("coordination/agent_assignments.tsv", AGENT_ASSIGNMENT_HEADER),
        ("coordination/integration_events.tsv", INTEGRATION_EVENT_HEADER),
        ("coordination/audit_receipts.tsv", AUDIT_RECEIPT_HEADER),
    ]
    for rel, header in header_checks:
        issues.extend(validate_tsv_header(run_dir / rel, header))

    for rel in ["README.md", "00_brief/brief.md", "01_analysis/analysis.md", "02_plan/plan.md"]:
        path = run_dir / rel
        if path.exists() and not nonempty_text(path, 3):
            issues.append(f"empty_or_placeholder\t{rel}")

    hosts = read_tsv(run_dir / "metadata/hosts.tsv")
    host_ids = {r.get("host_id", "") for r in hosts if r.get("host_id", "")}
    for row in hosts:
        for field in ["host_id", "ssh_alias", "access_mode", "status"]:
            if not row.get(field, ""):
                issues.append(f"host_missing_required_field\t{row.get('host_id', '')}\t{field}")

    path_maps = read_tsv(run_dir / "metadata/path_maps.tsv")
    path_map_ids = {r.get("path_map_id", "") for r in path_maps if r.get("path_map_id", "")}
    protocol_html_roles = {
        "html", "index_html", "navigation_html", "phase_html", "stage_html",
        "qc_html", "protocol_html",
    }
    protocol_markdown_roles = {
        "markdown", "md", "readme_md", "todo_md", "analysis_md", "plan_md",
        "execution_md", "stage_md", "qc_report_md", "provenance_md",
        "decision_md", "assumption_md", "handoff_md", "protocol_md",
    }
    allowed_remote_md_roles = {"report_artifact", "final_report_artifact", "remote_provenance_artifact"}
    for row in path_maps:
        path_map_id = row.get("path_map_id", "")
        for field in ["path_map_id", "host_id", "remote_path", "local_path", "remote_is_canonical", "local_role", "status"]:
            if not row.get(field, ""):
                issues.append(f"path_map_missing_required_field\t{path_map_id}\t{field}")
        if row.get("host_id", "") and row.get("host_id", "") not in host_ids:
            issues.append(f"path_map_unknown_host\t{path_map_id}\t{row.get('host_id', '')}")
        if row.get("remote_is_canonical", "") != "true":
            issues.append(f"path_map_remote_not_canonical\t{path_map_id}")
        if row.get("local_role", "") != "local_mirror":
            issues.append(f"path_map_local_not_mirror\t{path_map_id}")
        if row.get("sync_direction", "") not in {"remote_to_local", "local_to_remote", "bidirectional", "metadata_only"}:
            issues.append(f"path_map_bad_sync_direction\t{path_map_id}\t{row.get('sync_direction', '')}")
        remote_path = row.get("remote_path", "")
        local_path = row.get("local_path", "")
        path_role = row.get("path_role", "")
        if path_role in protocol_html_roles:
            issues.append(f"path_map_protocol_html_forbidden\t{path_map_id}\t{path_role}")
        if path_role in protocol_markdown_roles:
            issues.append(f"path_map_protocol_markdown_forbidden\t{path_map_id}\t{path_role}")
        if remote_path.endswith("/index.html") or remote_path.endswith("index.html"):
            issues.append(f"path_map_remote_index_html_forbidden\t{path_map_id}\t{remote_path}")
        if remote_path.endswith(".html") and path_role not in {"report_artifact", "final_report_artifact"}:
            issues.append(f"path_map_remote_html_requires_report_artifact_role\t{path_map_id}\t{path_role}")
        if remote_path.endswith(".html") and path_role in {"report_artifact", "final_report_artifact"} and not local_path.startswith("local_results/reports/"):
            issues.append(f"path_map_report_html_must_mirror_to_local_reports\t{path_map_id}\t{local_path}")
        if remote_path.endswith(".md") and path_role not in allowed_remote_md_roles:
            issues.append(f"path_map_remote_md_requires_artifact_role\t{path_map_id}\t{path_role}")
        if remote_path.endswith(".md") and path_role in {"report_artifact", "final_report_artifact"} and not local_path.startswith("local_results/reports/"):
            issues.append(f"path_map_report_md_must_mirror_to_local_reports\t{path_map_id}\t{local_path}")
        if remote_path.endswith(".md") and path_role == "remote_provenance_artifact" and not local_path.startswith("local_results/provenance/"):
            issues.append(f"path_map_remote_provenance_md_must_mirror_to_local_provenance\t{path_map_id}\t{local_path}")

    envs = read_tsv(run_dir / "metadata/env_registry.tsv")
    env_ids = {r.get("env_id", "") for r in envs if r.get("env_id", "")}
    forbidden_env_ids = {"base", "myenv", "test", "new", "latest", "current", "bioinfo", "project", "rice"}
    for row in envs:
        env_id = row.get("env_id", "")
        for field in ["env_id", "host_id", "env_scope", "env_manager", "status"]:
            if not row.get(field, ""):
                issues.append(f"env_missing_required_field\t{env_id}\t{field}")
        if env_id in forbidden_env_ids:
            issues.append(f"env_id_forbidden\t{env_id}")
        if row.get("host_id", "") not in host_ids and row.get("host_id", "") != "local":
            issues.append(f"env_unknown_host\t{env_id}\t{row.get('host_id', '')}")

    software = read_tsv(run_dir / "metadata/software_registry.tsv")
    active_versions: dict[tuple[str, str, str], set[str]] = {}
    for row in software:
        tool_id = row.get("tool_id", "")
        for field in ["tool_id", "tool_name", "host_id", "env_id", "manager", "executable_path", "version_command", "status"]:
            if not row.get(field, ""):
                issues.append(f"software_missing_required_field\t{tool_id}\t{field}")
        if row.get("env_id", "") and row.get("env_id", "") not in env_ids:
            issues.append(f"software_unknown_env\t{tool_id}\t{row.get('env_id', '')}")
        if row.get("status") == "Active":
            key = (row.get("tool_name", ""), row.get("host_id", ""), row.get("env_id", ""))
            active_versions.setdefault(key, set()).add(row.get("observed_version", ""))
    for key, versions in active_versions.items():
        if len(versions) > 1:
            issues.append(f"software_multiple_active_versions\t{key[0]}\t{key[1]}\t{key[2]}")

    references = read_tsv(run_dir / "metadata/reference_registry.tsv")
    for row in references:
        reference_id = row.get("reference_id", "")
        for field in ["reference_id", "reference_type", "reference_name", "host_id", "canonical_path", "status"]:
            if not row.get(field, ""):
                issues.append(f"reference_missing_required_field\t{reference_id}\t{field}")
        if row.get("host_id", "") not in host_ids and row.get("host_id", "") != "local":
            issues.append(f"reference_unknown_host\t{reference_id}\t{row.get('host_id', '')}")

    storage = read_tsv(run_dir / "metadata/storage_policy.tsv")
    for row in storage:
        storage_id = row.get("storage_id", "")
        for field in ["storage_id", "host_id", "path", "storage_class", "retention_policy", "cleanup_allowed"]:
            if not row.get(field, ""):
                issues.append(f"storage_missing_required_field\t{storage_id}\t{field}")
        protected_storage_classes = {"raw", "remote_raw", "reference", "remote_reference", "reference_index", "results", "remote_results", "final", "frozen", "remote_final", "remote_frozen"}
        if row.get("storage_class") in protected_storage_classes and row.get("auto_cleanup_allowed") == "true":
            issues.append(f"storage_forbidden_auto_cleanup\t{storage_id}\t{row.get('storage_class')}")

    remote_commands = read_tsv(run_dir / "logs/remote_commands.tsv")
    for row in remote_commands:
        remote_command_id = row.get("remote_command_id", "")
        for field in ["remote_command_id", "phase", "host_id", "time", "remote_cwd", "command", "command_class", "status"]:
            if not row.get(field, ""):
                issues.append(f"remote_command_missing_required_field\t{remote_command_id}\t{field}")
        if row.get("host_id", "") and row.get("host_id", "") not in host_ids:
            issues.append(f"remote_command_unknown_host\t{remote_command_id}\t{row.get('host_id', '')}")
        if row.get("env_id", "") and row.get("env_id", "") not in env_ids:
            issues.append(f"remote_command_unknown_env\t{remote_command_id}\t{row.get('env_id', '')}")

    installs = read_tsv(run_dir / "logs/install.tsv")
    for row in installs:
        install_id = row.get("install_id", "")
        for field in ["install_id", "time", "host_id", "env_id", "manager", "action", "package", "command", "status"]:
            if not row.get(field, ""):
                issues.append(f"install_missing_required_field\t{install_id}\t{field}")
        if row.get("env_id", "") and row.get("env_id", "") not in env_ids:
            issues.append(f"install_unknown_env\t{install_id}\t{row.get('env_id', '')}")

    cleanup_candidates = read_tsv(run_dir / "logs/cleanup_candidates.tsv")
    never_delete_classes = {"raw", "remote_raw", "reference", "remote_reference", "reference_index", "results", "remote_results", "final", "frozen", "remote_final", "remote_frozen"}
    for row in cleanup_candidates:
        candidate_id = row.get("candidate_id", "")
        for field in ["candidate_id", "host_id", "path", "storage_class", "reason", "requires_user_approval", "status"]:
            if not row.get(field, ""):
                issues.append(f"cleanup_missing_required_field\t{candidate_id}\t{field}")
        if row.get("storage_class", "") in never_delete_classes and row.get("status", "") != "Rejected":
            issues.append(f"cleanup_forbidden_never_delete_class\t{candidate_id}\t{row.get('storage_class', '')}")

    assignments = read_tsv(run_dir / "coordination/agent_assignments.tsv")
    coordination_state = read_simple_yaml(run_dir / "metadata/coordination.yaml")
    for field in ["coordination_epoch", "canonical_revision", "sealed_revision", "sealed_scope_fingerprint", "last_manifest_sha256"]:
        if field not in coordination_state:
            issues.append(f"coordination_missing_required_field\t{field}")
    active_assignments = [row for row in assignments if row.get("status") in {"Planned", "Running"}]
    active_integrators = [row for row in active_assignments if row.get("role") == "CANONICAL_INTEGRATOR"]
    if len(active_integrators) > 1:
        issues.append("coordination_multiple_active_integrators")
    active_writers = [row for row in active_assignments if row.get("role") in {"STAGING_WRITER", "CANONICAL_INTEGRATOR"}]
    if len(active_writers) > 1:
        issues.append("coordination_multiple_active_writers")
    for row in assignments:
        assignment_id = row.get("assignment_id", "")
        for field in ["assignment_id", "agent_path", "role", "base_revision", "status"]:
            if not row.get(field, ""):
                issues.append(f"assignment_missing_required_field\t{assignment_id}\t{field}")
        if row.get("role") not in {"READ_ONLY_REVIEWER", "STAGING_WRITER", "CANONICAL_INTEGRATOR", "AUDITOR"}:
            issues.append(f"assignment_invalid_role\t{assignment_id}\t{row.get('role', '')}")
        if not validate_assignment_model(row):
            issues.append(f"assignment_invalid_model_role\t{assignment_id}")
        if row.get("role") in {"READ_ONLY_REVIEWER", "AUDITOR"} and row.get("write_scope", ""):
            issues.append(f"assignment_read_only_has_write_scope\t{assignment_id}")
        if row.get("role") == "CANONICAL_INTEGRATOR":
            if row.get("agent_path") not in {"root", "/root"}:
                issues.append(f"assignment_nonroot_integrator\t{assignment_id}")
        if row.get("role") == "STAGING_WRITER":
            owned_root = (run_dir / "coordination/staging" / assignment_id).resolve()
            for raw_scope in row.get("write_scope", "").split("|"):
                if not raw_scope:
                    continue
                scope = Path(raw_scope).expanduser().resolve()
                if scope != owned_root and owned_root not in scope.parents:
                    issues.append(f"assignment_staging_scope_escape\t{assignment_id}\t{scope}")
        if row.get("status") in {"Planned", "Running"} and row.get("base_revision") != coordination_state.get("canonical_revision"):
            issues.append(f"active_assignment_stale_base\t{assignment_id}")

    receipts = read_tsv(run_dir / "coordination/audit_receipts.tsv")
    for row in receipts:
        receipt_id = row.get("receipt_id", "")
        for field in ["receipt_id", "audit_type", "revision_id", "manifest_sha256", "scope_fingerprint", "audit_cutoff", "auditor", "verdict", "valid_status"]:
            if not row.get(field, ""):
                issues.append(f"audit_receipt_missing_required_field\t{receipt_id}\t{field}")
        if row.get("valid_status") == "Valid":
            for field in ["auditor_assignment_id", "audit_report_path", "audit_report_sha256", "findings_path", "findings_sha256"]:
                if not row.get(field, ""):
                    issues.append(f"audit_receipt_missing_binding\t{receipt_id}\t{field}")
            revision_id = row.get("revision_id", "")
            seal_path = run_dir / "coordination/revisions" / revision_id / "seal.yaml"
            if not seal_path.exists():
                issues.append(f"audit_receipt_unsealed_revision\t{receipt_id}\t{revision_id}")
            else:
                seal = read_simple_yaml(seal_path)
                if seal.get("manifest_sha256") != row.get("manifest_sha256"):
                    issues.append(f"audit_receipt_manifest_binding_mismatch\t{receipt_id}")
            if revision_id != coordination_state.get("canonical_revision") or revision_id != coordination_state.get("sealed_revision"):
                issues.append(f"audit_receipt_not_current_revision\t{receipt_id}\t{revision_id}")
            if row.get("manifest_sha256") != coordination_state.get("last_manifest_sha256"):
                issues.append(f"audit_receipt_not_current_manifest\t{receipt_id}")
            if row.get("scope_fingerprint") != coordination_state.get("sealed_scope_fingerprint"):
                issues.append(f"audit_receipt_not_current_scope\t{receipt_id}")
            # This is intentionally read-only: stale receipts must fail the
            # manifest check without changing the receipt registry.
            for receipt_issue in receipt_issues(run_dir, row):
                issues.append(f"audit_receipt_live_revalidation_failed\t{receipt_id}\t{receipt_issue}")

    remote_jobs = read_tsv(run_dir / "logs/remote_jobs.tsv")
    for row in remote_jobs:
        remote_job_id = row.get("remote_job_id", "")
        for field in ["remote_job_id", "host_id", "stage_id", "submit_time", "remote_cwd", "remote_command", "status"]:
            if not row.get(field, ""):
                issues.append(f"remote_job_missing_required_field\t{remote_job_id}\t{field}")
        if row.get("host_id", "") and row.get("host_id", "") not in host_ids:
            issues.append(f"remote_job_unknown_host\t{remote_job_id}\t{row.get('host_id', '')}")

    syncs = read_tsv(run_dir / "logs/sync.tsv")
    for row in syncs:
        sync_id = row.get("sync_id", "")
        for field in ["sync_id", "host_id", "path_map_id", "sync_time", "direction", "remote_path", "local_path", "status", "checksum_status"]:
            if not row.get(field, ""):
                issues.append(f"sync_missing_required_field\t{sync_id}\t{field}")
        if row.get("host_id", "") and row.get("host_id", "") not in host_ids:
            issues.append(f"sync_unknown_host\t{sync_id}\t{row.get('host_id', '')}")
        if row.get("path_map_id", "") and row.get("path_map_id", "") not in path_map_ids:
            issues.append(f"sync_unknown_path_map\t{sync_id}\t{row.get('path_map_id', '')}")
        if row.get("checksum_status", "") == "mismatched" and not row.get("checksum_mismatch_policy", ""):
            issues.append(f"sync_mismatch_missing_policy\t{sync_id}")

    stages = read_tsv(run_dir / "02_plan/stage_registry.tsv")
    stage_ids = {r.get("stage_id", "") for r in stages}
    for row in remote_jobs:
        if row.get("stage_id", "") and row.get("stage_id", "") not in stage_ids:
            issues.append(f"remote_job_unknown_stage\t{row.get('remote_job_id', '')}\t{row.get('stage_id', '')}")
    for row in stages:
        sid = row.get("stage_id", "")
        if not sid:
            issues.append("stage_missing_id")
            continue
        for field in ["stage_name", "stage_status", "gate_status"]:
            if row.get("stage_status") not in {"NotStarted", "Ready"} and not row.get(field, ""):
                issues.append(f"stage_missing_required_field\t{sid}\t{field}")
        if row.get("stage_status") in {"QC_Pending", "QC_Passed", "QC_Failed", "Waived_With_Decision", "Frozen"} and not row.get("qc_status", ""):
            issues.append(f"stage_missing_required_field\t{sid}\tqc_status")
        depends = [x.strip() for x in row.get("depends_on", "").split(",") if x.strip()]
        for dep in depends:
            if dep not in stage_ids:
                issues.append(f"stage_unknown_dependency\t{sid}\t{dep}")
        if row.get("required", "").lower() in {"true", "yes", "1"}:
            for suffix in ["stage.md", "provenance.md", "qc_report.md", "outputs_manifest.tsv"]:
                p = run_dir / "03_execution/stages" / sid / suffix
                if not p.exists():
                    missing.append(str(p.relative_to(run_dir)))
                elif suffix.endswith(".md") and not nonempty_text(p, 3):
                    issues.append(f"empty_or_placeholder\t{p.relative_to(run_dir)}")
                elif suffix.endswith(".md") and row.get("gate_status") in {"QC_Passed", "Waived_With_Decision"} and not has_substantive_content(p):
                    issues.append(f"template_only_after_open_gate\t{p.relative_to(run_dir)}")
            if profile == "strict":
                for suffix in ["stage.html", "qc_report.html"]:
                    p = run_dir / "03_execution/stages" / sid / suffix
                    if not p.exists():
                        missing.append(str(p.relative_to(run_dir)))
        if row.get("gate_status") == "QC_Passed" and row.get("qc_status") != "QC_Passed":
            issues.append(f"gate_qc_mismatch\t{sid}\tgate={row.get('gate_status')}\tqc={row.get('qc_status')}")
        if row.get("gate_status") == "Waived_With_Decision" and not row.get("decision_id"):
            issues.append(f"waiver_missing_decision_id\t{sid}")

    if missing or issues:
        print("FAIL")
        for item in missing:
            print(f"missing\t{item}")
        for item in issues:
            print(item)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
