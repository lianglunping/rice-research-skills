#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import STAGE_HEADER, VALID_GATE_STATUSES, VALID_STAGE_STATUSES, now, read_tsv, write_tsv


def main() -> int:
    parser = argparse.ArgumentParser(description="Add or update a stage in stage_registry.tsv.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--stage-id", required=True)
    parser.add_argument("--stage-name", required=True)
    parser.add_argument("--stage-order", default="")
    parser.add_argument("--stage-status", default="NotStarted")
    parser.add_argument("--gate-status", default="Gate_Not_Ready")
    parser.add_argument("--qc-status", default="")
    parser.add_argument("--required", default="true")
    parser.add_argument("--depends-on", default="")
    parser.add_argument("--decision-id", default="")
    parser.add_argument("--blocker-todo-id", default="")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    if args.stage_status not in VALID_STAGE_STATUSES:
        raise SystemExit(f"ERROR: invalid stage_status: {args.stage_status}")
    if args.gate_status not in VALID_GATE_STATUSES:
        raise SystemExit(f"ERROR: invalid gate_status: {args.gate_status}")
    if args.gate_status == "QC_Passed" and args.qc_status != "QC_Passed":
        raise SystemExit("ERROR: gate_status QC_Passed requires qc_status QC_Passed")
    if args.gate_status == "Waived_With_Decision" and not args.decision_id:
        raise SystemExit("ERROR: Waived_With_Decision requires --decision-id")
    path = run_dir / "02_plan/stage_registry.tsv"
    rows = read_tsv(path)
    row = {
        "stage_id": args.stage_id,
        "stage_name": args.stage_name,
        "stage_order": args.stage_order,
        "stage_status": args.stage_status,
        "gate_status": args.gate_status,
        "qc_status": args.qc_status,
        "required": args.required,
        "depends_on": args.depends_on,
        "planned_start": "",
        "planned_end": "",
        "actual_start": now() if args.stage_status == "Running" else "",
        "actual_end": "",
        "qc_criteria_path": "02_plan/qc_criteria.tsv",
        "qc_report_path": f"03_execution/stages/{args.stage_id}/qc_report.md",
        "provenance_path": f"03_execution/stages/{args.stage_id}/provenance.md",
        "outputs_manifest_path": f"03_execution/stages/{args.stage_id}/outputs_manifest.tsv",
        "decision_id": args.decision_id,
        "blocker_todo_id": args.blocker_todo_id,
        "notes": args.notes,
    }
    updated = False
    for i, existing in enumerate(rows):
        if existing.get("stage_id") == args.stage_id:
            merged = {**existing, **{k: v for k, v in row.items() if v != ""}}
            rows[i] = merged
            updated = True
            break
    if not updated:
        rows.append(row)

    stage_dir = run_dir / "03_execution/stages" / args.stage_id
    (stage_dir / "logs").mkdir(parents=True, exist_ok=True)
    (stage_dir / "outputs").mkdir(parents=True, exist_ok=True)
    for name, text in {
        "stage.md": f"# 阶段记录: {args.stage_id}\n\n## 1. 阶段目标\n\n## 2. 输入\n\n## 3. 输出\n\n## 4. 命令\n\n## 5. 日志\n\n## 6. QC 摘要\n\n## 7. 决策\n\n## 8. 遇到的问题\n\n## 9. 下一阶段 gate\n",
        "provenance.md": f"# Provenance: {args.stage_id}\n\n## 1. 目的\n\n## 2. Run 元数据\n\n## 3. 输入\n\n## 4. 输出\n\n## 5. 代码与配置\n\n## 6. 环境\n\n## 7. 参考数据\n\n## 8. 命令\n\n## 9. 参数\n\n## 10. 随机性\n\n## 11. QC 标准\n\n## 12. QC 结果\n\n## 13. Checksums\n\n## 14. 已知问题\n\n## 15. 复现\n",
        "qc_report.md": f"# QC 报告: {args.stage_id}\n\n## 1. 范围\n\n## 2. QC 标准\n\n## 3. QC 命令\n\n## 4. QC 结果\n\n## 5. 失败检查\n\n## 6. 豁免检查\n\n## 7. 证据文件\n\n## 8. 决策\n\n## 9. 下游影响\n\n## 10. 下一步动作\n",
        "outputs_manifest.tsv": "file_id\tpath_id\tfile_path\tfile_role\tformat\texists\tsize_bytes\tn_rows\tn_columns\tcreated_time\tmodified_time\tmd5\tsha256\tproducer_stage_id\tproducer_command_id\tupstream_file_ids\tqc_status\tfrozen_status\tnotes\tstage_local_role\trequired_for_next_stage\n",
    }.items():
        p = stage_dir / name
        if not p.exists():
            p.write_text(text, encoding="utf-8")
    write_tsv(path, STAGE_HEADER, rows)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
