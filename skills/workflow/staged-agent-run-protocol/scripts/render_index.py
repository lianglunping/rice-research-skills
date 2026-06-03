#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from sar_utils import html_escape, read_simple_yaml, read_tsv


def status_class(value: str) -> str:
    v = (value or "").lower()
    if any(x in v for x in ["passed", "done", "completed", "frozen", "active", "initialized"]):
        return "status-ok"
    if any(x in v for x in ["running", "ready", "pending", "planning", "analyzing"]):
        return "status-info"
    if any(x in v for x in ["waived", "skipped"]):
        return "status-warn"
    if any(x in v for x in ["failed", "blocked", "abandoned", "error"]):
        return "status-bad"
    return "status-info"


def link(path: Path, label: str | None = None, run_dir: Path | None = None) -> str:
    exists = (run_dir / path).exists() if run_dir else path.exists()
    if exists:
        return f'<a href="{html_escape(path.as_posix())}">{html_escape(label or path.as_posix())}</a>'
    return html_escape(label or path.as_posix())


def table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "<p>无记录。</p>"
    head = "".join(f"<th>{html_escape(c)}</th>" for c in columns)
    body = []
    for row in rows:
        cells = []
        for c in columns:
            val = row.get(c, "")
            if c.endswith("status") or c == "status":
                cells.append(f'<td><span class="status {status_class(val)}">{html_escape(val)}</span></td>')
            else:
                cells.append(f"<td>{html_escape(val)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def render(run_dir: Path) -> None:
    run_dir = run_dir.resolve()
    run = read_simple_yaml(run_dir / "metadata/run.yaml")
    status = read_simple_yaml(run_dir / "metadata/status.yaml")
    stages = read_tsv(run_dir / "02_plan/stage_registry.tsv")
    todos = [r for r in read_tsv(run_dir / "todo.tsv") if r.get("status") not in {"Done", "Cancelled", "Skipped"}]
    jobs = read_tsv(run_dir / "logs/jobs.tsv")
    monitors = read_tsv(run_dir / "logs/monitor.tsv")
    hosts = read_tsv(run_dir / "metadata/hosts.tsv")
    path_maps = read_tsv(run_dir / "metadata/path_maps.tsv")
    envs = read_tsv(run_dir / "metadata/env_registry.tsv")
    software = read_tsv(run_dir / "metadata/software_registry.tsv")
    storage = read_tsv(run_dir / "metadata/storage_policy.tsv")
    syncs = read_tsv(run_dir / "logs/sync.tsv")
    disk = read_tsv(run_dir / "logs/disk_usage.tsv")
    cleanup = read_tsv(run_dir / "logs/cleanup_candidates.tsv")

    latest_monitor = monitors[-5:] if monitors else []
    stage_cols = ["stage_id", "stage_name", "stage_status", "gate_status", "qc_status", "depends_on", "notes"]
    todo_cols = ["todo_id", "phase", "stage_id", "title", "status", "priority", "owner", "notes"]
    job_cols = ["job_id", "stage_id", "submit_time", "pid_or_scheduler_id", "stdout_log", "stderr_log", "status"]
    monitor_cols = ["time", "job_id", "check_round", "interval_minutes", "job_status", "decision", "notes"]
    host_cols = ["host_id", "ssh_alias", "host_role", "access_mode", "scheduler", "status", "notes"]
    path_map_cols = ["path_map_id", "host_id", "stage_id", "remote_path", "local_path", "sync_direction", "status"]
    env_cols = ["env_id", "host_id", "env_scope", "env_manager", "env_path", "status"]
    software_cols = ["tool_id", "tool_name", "host_id", "env_id", "observed_version", "status"]
    storage_cols = ["storage_id", "host_id", "storage_class", "path", "retention_policy", "cleanup_allowed"]
    sync_cols = ["sync_id", "host_id", "path_map_id", "sync_time", "direction", "status", "checksum_status"]
    disk_cols = ["time", "host_id", "path", "check_type", "df_available", "df_used_percent", "threshold_status"]
    cleanup_cols = ["candidate_id", "host_id", "path", "storage_class", "size_gb", "status"]

    def rlink(target: str, label: str | None = None) -> str:
        return link(Path(target), label, run_dir)

    optional_report_links = []
    phase01_zh = "local_results/reports/phase0_phase1_audit_20260512.zh.md"
    if (run_dir / phase01_zh).exists():
        optional_report_links.append(
            f'    <li>{rlink(phase01_zh, "Phase 0/1 审计中文伴随说明")}</li>'
        )
    optional_report_html = "\n".join(optional_report_links)
    if optional_report_html:
        optional_report_html = "\n" + optional_report_html

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html_escape(run.get("task_name", "Agent Run"))}</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
<main>
  <h1>{html_escape(run.get("task_name", "Agent Run"))}</h1>
  <div class="summary">
    <div><span class="label">运行 ID</span>{html_escape(run.get("run_id", ""))}</div>
    <div><span class="label">配置档</span>{html_escape(run.get("profile", ""))}</div>
    <div><span class="label">协议</span>{html_escape(run.get("protocol_name", ""))} {html_escape(run.get("protocol_version", ""))}</div>
    <div><span class="label">总体状态</span><span class="status {status_class(status.get("overall_status", ""))}">{html_escape(status.get("overall_status", ""))}</span></div>
    <div><span class="label">当前阶段</span>{html_escape(status.get("current_phase", ""))}</div>
    <div><span class="label">当前 stage</span>{html_escape(status.get("current_stage", ""))}</div>
    <div><span class="label">最后更新</span>{html_escape(status.get("last_updated", ""))}</div>
    <div><span class="label">下一步动作</span>{html_escape(status.get("next_required_action", ""))}</div>
  </div>

  <h2>阶段导航</h2>
  <ul>
    <li>{rlink("README.md", "README.md")}</li>
    <li>{rlink("00_brief/brief.md", "00 任务简述")}</li>
    <li>{rlink("01_analysis/analysis.md", "01 问题分析")}</li>
    <li>{rlink("02_plan/plan.md", "02 方案与路径冻结")}</li>
    <li>{rlink("03_execution/execution.md", "03 执行记录")}</li>
    <li>{rlink("03_execution/final/final_report.md", "最终报告")}</li>
    <li>{rlink("03_execution/final/provenance.md", "最终 provenance")}</li>
    <li>{rlink("03_execution/final/frozen_outputs.tsv", "冻结输出")}</li>
    <li>{rlink("03_execution/final/checksums.tsv", "Checksums 文件")}</li>{optional_report_html}
  </ul>

  <h2>执行阶段</h2>
  {table(stages, stage_cols)}

  <h2>当前 TODO</h2>
  {table(todos, todo_cols)}

  <h2>长任务</h2>
  {table(jobs, job_cols)}

  <h2>远程主机</h2>
  {table(hosts, host_cols)}

  <h2>远程路径映射</h2>
  {table(path_maps, path_map_cols)}

  <h2>环境登记</h2>
  {table(envs, env_cols)}

  <h2>软件版本</h2>
  {table(software, software_cols)}

  <h2>存储策略</h2>
  {table(storage, storage_cols)}

  <h2>最近同步记录</h2>
  {table(syncs[-5:] if syncs else [], sync_cols)}

  <h2>最近磁盘检查</h2>
  {table(disk[-5:] if disk else [], disk_cols)}

  <h2>清理候选项</h2>
  {table(cleanup, cleanup_cols)}

  <h2>最近监控检查</h2>
  {table(latest_monitor, monitor_cols)}

  <h2>Canonical source 文件</h2>
  <ul>
    <li>{rlink("metadata/run.yaml")}</li>
    <li>{rlink("metadata/status.yaml")}</li>
    <li>{rlink("todo.tsv")}</li>
    <li>{rlink("todo_history.tsv")}</li>
    <li>{rlink("02_plan/path_registry.tsv")}</li>
    <li>{rlink("02_plan/stage_registry.tsv")}</li>
    <li>{rlink("02_plan/qc_criteria.tsv")}</li>
    <li>{rlink("logs/commands.tsv")}</li>
    <li>{rlink("logs/jobs.tsv")}</li>
    <li>{rlink("logs/monitor.tsv")}</li>
    <li>{rlink("metadata/hosts.tsv")}</li>
    <li>{rlink("metadata/path_maps.tsv")}</li>
    <li>{rlink("metadata/env_registry.tsv")}</li>
    <li>{rlink("metadata/software_registry.tsv")}</li>
    <li>{rlink("metadata/reference_registry.tsv")}</li>
    <li>{rlink("metadata/storage_policy.tsv")}</li>
    <li>{rlink("logs/remote_commands.tsv")}</li>
    <li>{rlink("logs/remote_jobs.tsv")}</li>
    <li>{rlink("logs/sync.tsv")}</li>
    <li>{rlink("logs/install.tsv")}</li>
    <li>{rlink("logs/disk_usage.tsv")}</li>
    <li>{rlink("logs/cleanup_candidates.tsv")}</li>
    <li>{rlink("monitoring/remote_monitor_plan.md")}</li>
  </ul>
</main>
</body>
</html>
"""
    (run_dir / "index.html").write_text(html, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Render staged run index.html.")
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    render(Path(args.run_dir))
    print(Path(args.run_dir).resolve() / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
