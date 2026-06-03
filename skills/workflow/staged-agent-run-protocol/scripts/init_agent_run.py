#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
from datetime import date
from pathlib import Path

from sar_utils import (
    CLEANUP_CANDIDATE_HEADER, COMMAND_HEADER, DISK_USAGE_HEADER, ENV_HEADER,
    FILES_HEADER, HOST_HEADER, INSTALL_HEADER, JOB_HEADER, MONITOR_HEADER,
    PATH_HEADER, PATH_MAP_HEADER, PROTOCOL_NAME, PROTOCOL_VERSION, QC_HEADER,
    REFERENCE_HEADER, REMOTE_COMMAND_HEADER, REMOTE_JOB_HEADER,
    SOFTWARE_HEADER, STAGE_HEADER, STORAGE_POLICY_HEADER, SYNC_HEADER,
    TODO_HEADER, TODO_HISTORY_HEADER, ensure_tsv, now, slugify,
    write_simple_yaml,
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a staged agent run directory.")
    parser.add_argument("--task-name", required=True)
    parser.add_argument("--root", default="agent_runs")
    parser.add_argument("--profile", choices=["lite", "standard", "strict"], default="standard")
    parser.add_argument("--project", default="")
    parser.add_argument("--species", default="")
    parser.add_argument("--created-by", default=os.environ.get("USER", "agent"))
    parser.add_argument("--description", default="")
    parser.add_argument("--force", action="store_true", help="Allow using an existing run directory.")
    args = parser.parse_args()

    run_id = f"{date.today().isoformat()}_{slugify(args.task_name)}"
    run_dir = Path(args.root).expanduser().resolve() / run_id
    if run_dir.exists() and not args.force:
        raise SystemExit(f"ERROR: run directory exists: {run_dir}")

    dirs = [
        "metadata", "00_brief", "01_analysis/subagents", "02_plan/subagents",
        "03_execution/stages", "03_execution/final", "code/scripts",
        "code/configs", "code/envs", "docs", "logs", "monitoring",
        "assets/figures", "assets/tables", "local_results/figures",
        "local_results/tables", "local_results/reports",
        "local_results/checksums", "local_results/provenance",
    ]
    for item in dirs:
        (run_dir / item).mkdir(parents=True, exist_ok=True)

    skill_root = Path(__file__).resolve().parents[1]
    css_src = skill_root / "templates/staged_agent_run_protocol/assets/style.css"
    css_dst = run_dir / "assets/style.css"
    if not css_dst.exists():
        shutil.copyfile(css_src, css_dst)

    write_simple_yaml(run_dir / "metadata/run.yaml", {
        "run_id": run_id,
        "task_name": args.task_name,
        "project": args.project,
        "species": args.species,
        "protocol_name": PROTOCOL_NAME,
        "protocol_version": PROTOCOL_VERSION,
        "profile": args.profile,
        "created_time": now(),
        "created_by": args.created_by,
        "root_dir": run_dir,
        "description": args.description,
    })
    write_simple_yaml(run_dir / "metadata/status.yaml", {
        "overall_status": "Initialized",
        "current_phase": "Phase 0 Bootstrap",
        "current_stage": "",
        "last_completed_phase": "",
        "last_completed_stage": "",
        "last_updated": now(),
        "next_required_action": "Start Phase 1 Analysis",
        "blocked": "false",
        "blocked_reason": "",
    })

    write(run_dir / "README.md", f"""# Agent Run: {args.task_name}

## 当前状态

- Run ID: {run_id}
- Protocol Version: {PROTOCOL_VERSION}
- Profile: {args.profile}
- Current Phase: Phase 0 Bootstrap
- Current Stage:
- Overall Status: Initialized
- Last Updated: {now()}
- Next Required Action: Start Phase 1 Analysis

## 已锁定路径

See `02_plan/path_registry.tsv`.

## 不要修改

Raw input data is read-only by default.

## 已完成阶段

- Phase 0 Bootstrap

## 当前 TODO

See `todo.tsv`.

## 阻塞项

None recorded.

## 复现

Reproduction commands will be recorded in `03_execution/final/reproduce.sh`.

## 关键链接

- Human index: `index.html` (local-only protocol navigation)
- Protocol Markdown: local run directory only
- Status: `metadata/status.yaml`
- TODO: `todo.tsv`
""")
    write(run_dir / "TODO.md", "# TODO\n\nCanonical TODO source: `todo.tsv`.\n")
    write(run_dir / "00_brief/brief.md", f"# 任务简述\n\n任务: {args.task_name}\n\n描述: {args.description}\n")
    write(run_dir / "01_analysis/analysis.md", "# Phase 1 Analysis\n\n## 1. 目标\n\n## 2. 输入与既有上下文\n\n## 3. 预期输出\n\n## 4. 边界条件\n\n## 5. 验收标准\n\n## 6. 当前证据\n\n## 7. 风险与未知项\n\n## 8. 候选策略\n\n## 9. 策略比较\n\n## 10. 推荐策略\n\n## 11. 阻塞问题\n\n## 12. 下一阶段要求\n")
    write(run_dir / "02_plan/plan.md", "# Phase 2 Plan And Path Freeze\n\n## 1. 已选择策略\n\n## 2. 已锁定路径\n\n## 3. 执行阶段\n\n## 4. QC 标准\n\n## 5. 监控计划\n\n## 6. 最终输出\n\n## 7. 复现命令\n\n## 远程执行计划\n\n### 主机选择\n- primary_host_id:\n- fallback_host_id:\n- reason:\n- assumptions:\n\n### 远程路径契约\n- REMOTE_RUN_ROOT:\n- REMOTE_RAW_DIR:\n- REMOTE_WORK_DIR:\n- REMOTE_SCRATCH_DIR:\n- REMOTE_RESULTS_DIR:\n- REMOTE_LOG_DIR:\n- REMOTE_ENV_DIR:\n\n### 本地镜像契约\n- local_results_dir: local_results/\n- protocol_markdown_location: local run directory only\n- protocol_html_location: local run directory only\n- allowed_sync_file_types:\n- forbidden_sync_file_types: raw, work, scratch, large temporary files, protocol Markdown, protocol navigation HTML\n- max_local_mirror_size_gb:\n\n### 本地保留契约\n- keep_local_control_files: Markdown, YAML, TSV, scripts, configs, registry tables, logs, checksums, manifests\n- keep_local_review_outputs: final reports, figures, tables, selected final outputs, compressed selected logs\n- do_not_keep_local_by_default: raw FASTQ/BAM/CRAM, large references/indexes, work chunks, scratch, large intermediates\n\n### 数据传输计划\n- raw_data_source:\n- upload_required:\n- upload_command_plan:\n- checksum_plan:\n- local_raw_retention_policy:\n\n### 环境计划\n- local_env_id:\n- remote_env_id:\n- package_manager:\n- lock/export files:\n- version verification commands:\n- install_required:\n- install_risk:\n\n### 存储预算\n- expected_raw_gb:\n- expected_work_gb:\n- expected_scratch_gb:\n- expected_final_gb:\n- expected_local_mirror_gb:\n- cleanup_policy:\n\n### 远程监控计划\n- job_submission_method:\n- scheduler_or_pid:\n- monitor_interval_policy:\n- disk_threshold:\n- anomaly_actions:\n\n### 最终同步计划\n- include_patterns:\n- exclude_patterns:\n- checksum_required:\n- local final mirror path:\n")
    write(run_dir / "03_execution/execution.md", "# Phase 3 Execution And Finalization\n\n")
    write(run_dir / "docs/decisions.md", "# 决策记录\n\n")
    write(run_dir / "docs/assumptions.md", "# 假设记录\n\n")
    write(run_dir / "docs/known_issues.md", "# 已知问题\n\n")
    write(run_dir / "monitoring/monitor_plan.md", "# 监控计划\n\n")
    write(run_dir / "monitoring/remote_monitor_plan.md", """# 远程监控计划

远程任务只能通过已记录的状态检查进行监控。除非 command、host、logs、
outputs、environment、software versions、storage policy 和 disk checks 已登记，
否则不要从本 run 执行临时远程命令。

退避策略:

1. 提交后前 3 分钟：每 1 分钟检查一次。
2. 若 3 次均正常：每 10 分钟检查一次。
3. 若 3 次 10 分钟检查均正常：每 30 分钟检查一次。
4. 一旦异常：回到每 1 分钟检查，连续 3 轮，并创建或更新 TODO。

远程输出策略:

- 服务器端输出是 remote canonical outputs。
- 本地同步副本是 local mirrors，用于查看、本地渲染、报告和归档。
- Protocol navigation HTML (`index.html`, phase HTML, stage HTML, QC HTML)
  在本地 run 目录渲染，不放在远程服务器作为主入口。
- 服务器生成的 HTML 只有在属于真实 scientific/pipeline report artifact 时才允许，
  并同步到 `local_results/reports/`。
- Protocol Markdown (`README.md`, phase Markdown, stage Markdown, QC Markdown,
  provenance Markdown, decisions, assumptions) 是本地 run-control evidence。
- 服务器生成的 Markdown 只有在属于真实 scientific report 或 remote provenance artifact
  时才允许，并同步到 `local_results/reports/` 或 `local_results/provenance/`。
- 每次同步必须向 `logs/sync.tsv` 追加一行。
- 用于 final 或 frozen output 的 local mirror 必须有 checksum 证据，或明确
  `checksum_mismatch_policy`。
- Local mirrors 默认放在 `local_results/`。
- 默认不要同步 raw、work、scratch 或大型临时文件到 local mirrors。
- 启用 remote compute 时，Remote Phase 3 必须从 `00_remote_preflight` 开始。
""")
    write(run_dir / "monitoring/automation_prompt.md", "# 自动化提示词\n\n")
    write(run_dir / "monitoring/monitor_state.yaml", "current_policy: early_1min\nnormal_checks: 0\nabnormal_checks: 0\nlast_check_time:\nnext_check_time:\nlast_status:\nactive_jobs: []\n")
    write(run_dir / "monitoring/monitor_events.tsv", "time\tevent_type\tjob_id\tstage_id\tmessage\tevidence_path\tnotes\n")
    write(run_dir / "monitoring/alerts.tsv", "time\talert_id\tjob_id\tseverity\tmessage\tevidence_path\tstatus\tnotes\n")
    write(run_dir / "03_execution/final/final_report.md", f"# 最终报告: {args.task_name}\n\n## 1. 摘要\n\n## 2. 范围\n\n## 3. 输入\n\n## 4. 方法\n\n## 5. 输出\n\n## 6. QC 摘要\n\n## 7. 冻结结果\n\n## 8. 已知问题\n\n## 9. 复现\n\n## 10. 附录\n")
    write(run_dir / "03_execution/final/provenance.md", "# 最终 provenance\n\n")
    write(run_dir / "03_execution/final/cleanup_plan.md", "# 清理计划\n\n## 不可删除\n\n## 候选 work/scratch 文件\n\n## 候选废弃环境\n\n## 候选重复 local mirrors\n\n## 空间节省估计\n\n## 需要用户批准的事项\n\n## 安全清理命令\n\n## 清理后验证\n")
    write(run_dir / "03_execution/final/reproduce.sh", "#!/usr/bin/env bash\nset -euo pipefail\n\n# Fill after Phase 2 path freeze and Phase 3 execution.\n")
    os.chmod(run_dir / "03_execution/final/reproduce.sh", 0o755)

    ensure_tsv(run_dir / "todo.tsv", TODO_HEADER)
    ensure_tsv(run_dir / "todo_history.tsv", TODO_HISTORY_HEADER)
    ensure_tsv(run_dir / "02_plan/path_registry.tsv", PATH_HEADER)
    ensure_tsv(run_dir / "02_plan/files_manifest.tsv", FILES_HEADER)
    ensure_tsv(run_dir / "02_plan/stage_registry.tsv", STAGE_HEADER)
    ensure_tsv(run_dir / "02_plan/qc_criteria.tsv", QC_HEADER)
    ensure_tsv(run_dir / "02_plan/command_plan.tsv", COMMAND_HEADER)
    ensure_tsv(run_dir / "02_plan/monitoring_plan.tsv", MONITOR_HEADER)
    ensure_tsv(run_dir / "logs/commands.tsv", COMMAND_HEADER)
    ensure_tsv(run_dir / "logs/jobs.tsv", JOB_HEADER)
    ensure_tsv(run_dir / "logs/monitor.tsv", MONITOR_HEADER)
    ensure_tsv(run_dir / "metadata/hosts.tsv", HOST_HEADER)
    ensure_tsv(run_dir / "metadata/path_maps.tsv", PATH_MAP_HEADER)
    ensure_tsv(run_dir / "metadata/env_registry.tsv", ENV_HEADER)
    ensure_tsv(run_dir / "metadata/software_registry.tsv", SOFTWARE_HEADER)
    ensure_tsv(run_dir / "metadata/reference_registry.tsv", REFERENCE_HEADER)
    ensure_tsv(run_dir / "metadata/storage_policy.tsv", STORAGE_POLICY_HEADER)
    ensure_tsv(run_dir / "logs/remote_commands.tsv", REMOTE_COMMAND_HEADER)
    ensure_tsv(run_dir / "logs/remote_jobs.tsv", REMOTE_JOB_HEADER)
    ensure_tsv(run_dir / "logs/sync.tsv", SYNC_HEADER)
    ensure_tsv(run_dir / "logs/install.tsv", INSTALL_HEADER)
    ensure_tsv(run_dir / "logs/disk_usage.tsv", DISK_USAGE_HEADER)
    ensure_tsv(run_dir / "logs/cleanup_candidates.tsv", CLEANUP_CANDIDATE_HEADER)
    ensure_tsv(run_dir / "03_execution/final/frozen_outputs.tsv", [
        "file_id", "path", "file_role", "stage_id", "md5", "sha256",
        "size_bytes", "frozen_time", "freeze_decision_id", "qc_status", "notes",
    ])
    ensure_tsv(run_dir / "03_execution/final/checksums.tsv", ["path", "size_bytes", "md5", "sha256", "time"])
    ensure_tsv(run_dir / "03_execution/final/qa_summary.tsv", ["check_id", "scope", "status", "evidence_path", "notes"])

    from render_index import render
    render(run_dir)
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
