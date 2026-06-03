#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import has_substantive_content, nonempty_text, read_tsv


PASSING = {"QC_Passed", "Waived_With_Decision"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate that a stage gate has enough evidence to open.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--stage-id", required=True)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    stages = read_tsv(run_dir / "02_plan/stage_registry.tsv")
    stage = next((r for r in stages if r.get("stage_id") == args.stage_id), None)
    if not stage:
        print(f"FAIL\tstage_not_registered\t{args.stage_id}")
        return 1

    issues: list[str] = []
    gate = stage.get("gate_status", "")
    qc = stage.get("qc_status", "")
    if gate not in PASSING:
        issues.append(f"gate_not_open\tgate_status={gate}")
    if qc not in PASSING:
        issues.append(f"qc_not_passing\tqc_status={qc}")
    if gate == "Waived_With_Decision" or qc == "Waived_With_Decision":
        decision_id = stage.get("decision_id", "")
        decisions = run_dir / "docs/decisions.md"
        if not decision_id:
            issues.append("waiver_missing_decision_id")
        elif not decisions.exists() or decision_id not in decisions.read_text(encoding="utf-8", errors="replace"):
            issues.append(f"waiver_decision_not_found\t{decision_id}")

    required_files = {
        "qc_report": stage.get("qc_report_path") or f"03_execution/stages/{args.stage_id}/qc_report.md",
        "provenance": stage.get("provenance_path") or f"03_execution/stages/{args.stage_id}/provenance.md",
        "outputs_manifest": stage.get("outputs_manifest_path") or f"03_execution/stages/{args.stage_id}/outputs_manifest.tsv",
    }
    for label, rel in required_files.items():
        path = run_dir / rel
        if not path.exists():
            issues.append(f"missing_{label}\t{rel}")
        elif label != "outputs_manifest" and not nonempty_text(path, 3):
            issues.append(f"empty_or_placeholder_{label}\t{rel}")
        elif label != "outputs_manifest" and not has_substantive_content(path):
            issues.append(f"template_only_{label}\t{rel}")
    outputs = read_tsv(run_dir / required_files["outputs_manifest"])
    required_outputs = [r for r in outputs if r.get("required_for_next_stage", "").lower() in {"true", "yes", "1"}]
    for row in required_outputs:
        file_path = row.get("file_path", "")
        if not file_path:
            issues.append("required_output_missing_file_path")
            continue
        p = Path(file_path).expanduser()
        if not p.is_absolute():
            p = run_dir / p
        if not p.exists() or p.stat().st_size == 0:
            issues.append(f"required_output_missing_or_empty\t{file_path}")
        if row.get("qc_status") not in PASSING:
            issues.append(f"required_output_not_qc_passed\t{file_path}\t{row.get('qc_status')}")

    if issues:
        print("FAIL")
        for issue in issues:
            print(issue)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
