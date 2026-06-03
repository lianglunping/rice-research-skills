# Staged Agent Run Protocol v0.1

作者：梁博 / GPT-5.5 Pro 修改稿
日期：2026-05-12
协议名：`staged_agent_run_protocol`
版本：`0.1.0`
默认 profile：`standard`
目的：为复杂科研、生信、分子育种、诱变育种和可复现数据分析任务建立一套可审计、可接续、可复现的 Agent 执行协议。

---

## 0. 核心原则

本协议用于约束复杂科研任务中的 Agent 行为，避免 Agent 在未完成分析、方案锁定、路径注册、质控标准定义和 provenance 规划前，直接进入写代码、跑流程或产出结果。

核心原则：

1. 复杂任务必须先建立独立 run 目录，再按阶段推进。
2. 正式结果必须可追溯到输入、命令、参数、环境、日志、QC 证据和 checksum。
3. Phase 1 只分析问题；Phase 2 锁定方案、路径、stage、QC 和监控；Phase 3 执行方案并冻结结果。
4. Phase 3 可以包含多个 execution stage；每个 stage 必须独立记录、独立 QC、独立 provenance。
5. 一个 stage 不能进入下一个 stage，除非前一 stage 的 `gate_status` 为 `QC_Passed` 或 `Waived_With_Decision`。
6. `Markdown`、`TSV`、`YAML` 是 canonical source；`HTML` 是渲染产物，不作为状态源。
7. `index.html` 只作为人类导航入口，不能作为状态或审计的唯一依据。
8. `TODO` 是动态 action layer，不替代 Phase 2 plan，也不替代 stage 状态表。
9. 原始数据默认只读；任何正式输出不得写入未注册路径。
10. 最终结果必须冻结，并写入 `frozen_outputs.tsv` 与 checksum 文件。

---

## 1. 适用范围

### 1.1 适用任务

适用于以下任务：

- 生信分析流程设计与执行。
- 水稻分子育种、诱变育种、群体分析、候选基因筛选。
- 多文件、多目录、多阶段的数据处理任务。
- 需要生成论文图表、结果表、报告或可复现分析包的任务。
- 预计运行超过 10 分钟的长时间任务。
- 涉及代码修改、测试、审计、路径冻结和结果归档的任务。
- 需要在多个会话、多个 Agent 或多个机器之间接续执行的任务。

### 1.2 不适用任务

不适用于以下任务：

- 简单问答。
- 单次解释、翻译、润色。
- 不涉及文件产物的轻量讨论。
- 不需要路径、日志、QC 或 provenance 的一次性任务。

### 1.3 触发规则

当任务满足以下任一条件时，应启用本协议：

```text
涉及多个输入文件
涉及多个输出文件
涉及代码修改或流程执行
涉及正式图表或结果表生成
涉及长时间运行任务
涉及下游论文、报告、归档或审计
涉及已有结果复现或历史结果比较
```

---

## 2. Profile 分级

为避免协议过重，本协议定义三个运行级别。

### 2.1 `lite`

适合中等复杂任务或探索性任务。

要求：

- 必须创建 run 目录。
- 必须产出 `README.md`、`analysis.md`、`plan.md`、`execution.md`。
- 必须记录正式命令、输入、输出、QC 结果。
- 不强制每个 stage 生成 HTML。
- 不强制启用自动监控脚本，但长任务仍需记录在 `jobs.tsv`。

### 2.2 `standard`

默认级别，适合常规生信流程和科研分析。

要求：

- 必须创建完整 run 目录。
- 必须产出 phase-level Markdown。
- 必须产出 `index.html`，由 Markdown、TSV、YAML 渲染生成。
- 必须产出 stage-level `stage.md`、`provenance.md`、`qc_report.md`、`outputs_manifest.tsv`。
- 必须记录 `commands.tsv`、`jobs.tsv`、`monitor.tsv`。
- HTML 可以只在 phase-level 和最终报告中强制生成。

### 2.3 `strict`

适合论文核心结果、长期归档结果、关键流程、多人接续任务或高风险任务。

要求：

- 所有 phase 和 stage 均产出 Markdown 与 HTML。
- 每个 formal stage 必须产出完整 provenance、QC report、outputs manifest。
- 必须生成 `frozen_outputs.tsv`、`checksums.tsv`、`qa_summary.tsv`、`reproduce.sh`。
- 必须启用长任务监控和最终审计。
- 必须记录数据版本、参考基因组/注释版本、代码版本和环境快照。

---

## 3. 总体阶段模型

本协议采用 `Phase 0 + Phase 1 + Phase 2 + Phase 3` 模型。

```text
Phase 0: Bootstrap
Phase 1: Analysis
Phase 2: Plan And Path Freeze
Phase 3: Execution And Finalization
```

默认每个正式会话只推进一个 protocol phase。Phase 0 可以与 Phase 1 同会话完成，但必须明确 Phase boundary。Phase 3 内部可以包含多个 execution stage；如果多个 stage 在同一会话内完成，每个 stage 仍必须独立记录、独立 QC、独立 provenance。

对于高风险、长时间、论文核心结果或大规模文件修改任务，Phase 1、Phase 2、Phase 3 应分会话执行。

---

## 4. Phase 0：Bootstrap

Phase 0 是启动层，不属于正式三阶段。它允许自由讨论、澄清目标和规划后续 run，但不得直接执行正式分析或生产正式结果。

### 4.1 职责

- 理解任务背景。
- 判断是否启用本协议。
- 选择 profile：`lite`、`standard` 或 `strict`。
- 创建 run 目录。
- 创建初始 `README.md`、`index.html`、`metadata/run.yaml`、`metadata/status.yaml`。
- 创建 `00_brief/brief.md`。
- 初始化 TODO、logs、monitoring 和 docs 文件。

### 4.2 禁止事项

- 不得运行正式流程。
- 不得生成正式结果。
- 不得覆盖已有数据或历史结果。
- 不得将 scratch 输出标记为正式输出。

### 4.3 产物

```text
README.md
index.html
TODO.md
todo.tsv
todo_history.tsv
metadata/run.yaml
metadata/status.yaml
00_brief/brief.md
```

`standard` 和 `strict` profile 可生成：

```text
00_brief/brief.html
```

---

## 5. Phase 1：Analysis

Phase 1 只负责分析问题，不直接执行方案。

### 5.1 职责

- 复述任务目标、输入、输出、边界条件和验收标准。
- 阅读相关代码、配置、文档、已有输出和历史结果。
- 识别关键难点、风险、不确定性和阻塞信息。
- 提供 1–3 个差异化方案。
- 比较各方案的复杂度、资源成本、可维护性、侵入性和技术债务。
- 必要时调用 `explorer`、`architect`、`reviewer` 等 subagents。

### 5.2 禁止事项

- 不得修改正式代码。
- 不得运行正式流程。
- 不得生成正式结果。
- 不得进入 Phase 2 或 Phase 3。

### 5.3 产物

```text
01_analysis/analysis.md
01_analysis/subagents/*.md
```

`standard` 和 `strict` profile 可生成：

```text
01_analysis/analysis.html
```

### 5.4 `analysis.md` 最低结构

```md
# Phase 1 Analysis

## 1. Goal
## 2. Inputs And Existing Context
## 3. Expected Outputs
## 4. Boundary Conditions
## 5. Acceptance Criteria
## 6. Current Evidence
## 7. Risks And Unknowns
## 8. Candidate Strategies
## 9. Strategy Comparison
## 10. Recommended Strategy
## 11. Blocking Questions
## 12. Next Phase Requirements
```

---

## 6. Phase 2：Plan And Path Freeze

Phase 2 必须在用户明确选择或批准 Phase 1 的方案后启动。Phase 2 的目标是将 Phase 3 的执行边界提前锁定。

### 6.1 职责

- 固定 run 内所有正式路径。
- 固定输入、输出、代码、配置、环境、图表、表格和日志路径。
- 定义 execution stages。
- 定义每个 stage 的输入、输出、命令、QC 标准、失败处理和复现方式。
- 定义长任务监控计划。
- 定义最终冻结结果和验收标准。
- 定义是否允许 `Waived_With_Decision` 通过 gate。

### 6.2 禁止事项

- 不得生成完整实现。
- 不得运行正式流程。
- 不得跳过 QC 规划。
- 不得把未确认路径写入正式输出区。

### 6.3 产物

```text
02_plan/plan.md
02_plan/path_registry.tsv
02_plan/stage_registry.tsv
02_plan/qc_criteria.tsv
02_plan/command_plan.tsv
02_plan/monitoring_plan.tsv
```

可选或在 `standard`/`strict` 中推荐：

```text
02_plan/plan.html
02_plan/files_manifest.tsv
02_plan/subagents/*.md
```

### 6.4 Phase 2 必须冻结的内容

```text
run_root
input_paths
output_paths
script_paths
config_paths
environment_paths
figure_paths
table_paths
log_paths
stage_list
stage_dependencies
qc_criteria
monitoring_policy
final_outputs
reproduction_commands
```

---

## 7. Phase 3：Execution And Finalization

Phase 3 必须在用户明确批准 Phase 2 计划后启动。

Phase 3 是执行总阶段，但其内部可以包含多个 execution stage。每个 stage 必须独立记录、独立 QC、独立 provenance。一个 stage 不能进入下一个 stage，除非前一 stage 的 `gate_status` 为 `QC_Passed` 或 `Waived_With_Decision`。

### 7.1 职责

- 严格按 Phase 2 plan 执行。
- 所有正式命令写入 `logs/commands.tsv`。
- 所有长任务写入 `logs/jobs.tsv` 并启动监控。
- 每个 formal stage 产出 `stage.md`、`provenance.md`、`qc_report.md`、`outputs_manifest.tsv`。
- 正式输出写入注册路径。
- 更新 `stage_registry.tsv`、`todo.tsv`、`metadata/status.yaml`。
- 生成最终报告、checksum、冻结文件清单和复现脚本。

### 7.2 禁止事项

- 不得在未注册路径下生成正式结果。
- 不得覆盖原始数据。
- 不得以未记录命令生成正式结果。
- 不得未经 QC 声称任务完成。
- 不得将失败结果伪装为通过。
- 不得未经用户要求提交代码或推送远端。

### 7.3 Stage 产物

每个 formal stage 必须至少产出：

```text
03_execution/stages/{stage_id}/stage.md
03_execution/stages/{stage_id}/provenance.md
03_execution/stages/{stage_id}/qc_report.md
03_execution/stages/{stage_id}/outputs_manifest.tsv
03_execution/stages/{stage_id}/logs/
03_execution/stages/{stage_id}/outputs/
```

`strict` profile 还必须产出：

```text
03_execution/stages/{stage_id}/stage.html
03_execution/stages/{stage_id}/qc_report.html
```

### 7.4 Final 产物

```text
03_execution/final/final_report.md
03_execution/final/provenance.md
03_execution/final/frozen_outputs.tsv
03_execution/final/checksums.tsv
03_execution/final/qa_summary.tsv
03_execution/final/reproduce.sh
```

`standard` 和 `strict` profile 推荐或强制生成：

```text
03_execution/final/final_report.html
```

---

## 8. 推荐目录结构

```text
agent_runs/
  {YYYY-MM-DD}_{task-name}/
    README.md
    index.html
    TODO.md
    todo.tsv
    todo_history.tsv

    metadata/
      run.yaml
      status.yaml

    00_brief/
      brief.md
      brief.html

    01_analysis/
      analysis.md
      analysis.html
      subagents/

    02_plan/
      plan.md
      plan.html
      path_registry.tsv
      files_manifest.tsv
      stage_registry.tsv
      qc_criteria.tsv
      command_plan.tsv
      monitoring_plan.tsv
      subagents/

    03_execution/
      execution.md
      execution.html
      stages/
        01_prepare_inputs/
          stage.md
          stage.html
          provenance.md
          qc_report.md
          qc_report.html
          outputs_manifest.tsv
          logs/
          outputs/
        02_run_pipeline/
          stage.md
          stage.html
          provenance.md
          qc_report.md
          qc_report.html
          outputs_manifest.tsv
          logs/
          outputs/
        03_merge_results/
          stage.md
          stage.html
          provenance.md
          qc_report.md
          qc_report.html
          outputs_manifest.tsv
          logs/
          outputs/
        04_generate_figures/
          stage.md
          stage.html
          provenance.md
          qc_report.md
          qc_report.html
          outputs_manifest.tsv
          figures/
          tables/
          logs/
      final/
        final_report.md
        final_report.html
        provenance.md
        frozen_outputs.tsv
        checksums.tsv
        qa_summary.tsv
        reproduce.sh

    code/
      scripts/
      configs/
      envs/

    docs/
      decisions.md
      assumptions.md
      known_issues.md

    logs/
      commands.tsv
      jobs.tsv
      monitor.tsv

    monitoring/
      monitor_plan.md
      automation_prompt.md
      monitor_state.yaml
      monitor_events.tsv
      alerts.tsv

    assets/
      style.css
      figures/
      tables/
```

说明：

- `*.md`、`*.tsv`、`*.yaml` 是 canonical source。
- `*.html` 默认由渲染脚本生成。
- `index.html` 只能从 canonical source 渲染，不应手工维护为状态源。
- `stage.html` 和 `qc_report.html` 在 `strict` profile 中强制，在 `standard` profile 中按需生成。

---

## 9. 状态源分工

为避免状态重复和冲突，所有状态文件必须有明确职责。

| 文件 | 职责 | 是否为 canonical source |
|---|---|---|
| `metadata/run.yaml` | run 静态元信息 | 是 |
| `metadata/status.yaml` | run-level 当前状态摘要 | 是 |
| `02_plan/stage_registry.tsv` | stage 状态、依赖、QC gate 的唯一权威来源 | 是 |
| `todo.tsv` | action item 和待办事项 | 是 |
| `todo_history.tsv` | TODO 状态变更历史 | 是 |
| `logs/commands.tsv` | 正式命令审计日志 | 是 |
| `logs/jobs.tsv` | 长任务提交记录 | 是 |
| `logs/monitor.tsv` | 监控检查审计日志 | 是 |
| `monitoring/monitor_state.yaml` | 监控器运行状态缓存 | 否 |
| `index.html` | 人类导航和状态展示 | 否 |

### 9.1 `metadata/run.yaml`

```yaml
run_id:
task_name:
project:
species:
protocol_name: staged_agent_run_protocol
protocol_version: 0.1.0
profile: standard
created_time:
created_by:
root_dir:
description:
```

### 9.2 `metadata/status.yaml`

```yaml
overall_status:
current_phase:
current_stage:
last_completed_phase:
last_completed_stage:
last_updated:
next_required_action:
blocked: false
blocked_reason:
```

### 9.3 run-level 状态

```text
Initialized
Analyzing
Planning
Ready_For_Execution
Executing
Blocked
Completed
Archived
Abandoned
```

---

## 10. HTML 与 Markdown 角色划分

### 10.1 Canonical 规则

```text
Markdown / TSV / YAML are canonical.
HTML is rendered.
index.html is not a source of truth.
```

### 10.2 `index.html`

`index.html` 是人类总入口，必须展示：

- 任务目标。
- run id、task name、profile、protocol version。
- 当前 phase、当前 stage、overall status。
- 阶段导航。
- execution stage 状态。
- 当前 Active / Blocked TODO。
- 长任务监控摘要。
- QC gate 状态。
- final report、provenance、checksums、frozen outputs 链接。

### 10.3 `README.md`

`README.md` 是 Agent 接续入口，必须展示：

- 当前 run 状态。
- 上一阶段产物。
- 下一步必须执行什么。
- 哪些路径已经锁定。
- 哪些文件不能修改。
- 当前 TODO。
- 当前阻塞项。
- 如何复现。

### 10.4 HTML 样式要求

`assets/style.css` 应满足：

```text
白底
黑字
不依赖外部 CDN
不依赖外部 JS
相对路径链接
表格可横向滚动
状态既有颜色也有文字
长期归档后可直接打开
```

状态标签建议固定：

```text
Pending
Ready
Running
Blocked
QC_Passed
QC_Failed
Waived
Frozen
Done
```

---

## 11. 动态 TODO 设计

TODO 是动态 action layer，不是静态 checklist。TODO 可以更新，但不得静默删除历史。

### 11.1 文件

```text
TODO.md
todo.tsv
todo_history.tsv
```

### 11.2 `todo.tsv` 表头

```text
todo_id	phase	stage_id	title	status	priority	owner	created_time	updated_time	blocked_by	source_file	evidence_path	notes
```

### 11.3 TODO 状态

```text
Pending
Active
Blocked
Done
Skipped
Cancelled
Running
```

不建议把 `QC_Passed`、`QC_Failed`、`Frozen` 作为 TODO 主状态；这些应记录在 `stage_registry.tsv` 或 manifest 中。若 QC 失败，应新增一个状态为 `Blocked` 或 `Active` 的 TODO，并在 title 或 notes 中注明 QC failure。

### 11.4 规则

1. 每个 run 必须有 TODO。
2. 每个正式阶段开始前必须读取 TODO。
3. 每个正式阶段结束前必须更新 TODO。
4. 任何 `Blocked`、`QC_Failed`、`Failed job` 必须产生对应 TODO。
5. TODO 状态变化必须记录到 `todo_history.tsv`。
6. 取消或跳过任务必须记录原因。
7. TODO 不得替代 Phase 2 plan。
8. TODO 不得替代 `stage_registry.tsv` 的 stage 状态。

---

## 12. Stage Registry 与 QC Gate

### 12.1 `stage_registry.tsv` 表头

```text
stage_id	stage_name	stage_order	stage_status	gate_status	qc_status	required	depends_on	planned_start	planned_end	actual_start	actual_end	qc_criteria_path	qc_report_path	provenance_path	outputs_manifest_path	decision_id	blocker_todo_id	notes
```

### 12.2 Stage 状态

```text
NotStarted
Ready
Running
QC_Pending
QC_Passed
QC_Failed
Blocked
Waived_With_Decision
Frozen
Skipped
```

### 12.3 Gate 状态

```text
Gate_Not_Ready
Gate_Open
QC_Passed
QC_Failed
Waived_With_Decision
Blocked
```

### 12.4 QC Gate 规则

1. 每个 formal stage 完成后必须进入 `QC_Pending`。
2. QC 执行完成后，`qc_status` 只能是 `QC_Passed`、`QC_Failed` 或 `Waived_With_Decision`。
3. 下一个 stage 只能在前一个 required stage 的 `gate_status` 为 `QC_Passed` 或 `Waived_With_Decision` 时启动。
4. `Waived_With_Decision` 必须引用 `docs/decisions.md` 中的 `decision_id`。
5. QC 失败必须生成对应 TODO，并记录 blocker。
6. 不得将带有未解释失败项的 stage 标记为 `QC_Passed`。

### 12.5 Waiver 决策记录

`docs/decisions.md` 中的 waiver 至少包含：

```md
## Decision: {decision_id}

- Date:
- Phase:
- Stage:
- Decision Type: Waived_With_Decision
- Reason:
- Evidence:
- Affected Outputs:
- Impact On Downstream Results:
- Risk Level:
- Approved By:
- Follow-up TODO:
```

---

## 13. QC Criteria

### 13.1 `qc_criteria.tsv` 表头

```text
qc_id	stage_id	criterion	check_type	required	threshold	evidence_path	failure_action	notes
```

### 13.2 QC 类型

```text
file_exists
file_not_empty
row_count
column_count
sample_count
checksum_match
format_valid
log_no_error
exit_code_zero
statistical_threshold
biological_expectation
manual_review
```

### 13.3 QC Report 最低结构

```md
# QC Report: {stage_id}

## 1. Scope
## 2. QC Criteria
## 3. QC Commands
## 4. QC Results
## 5. Failed Checks
## 6. Waived Checks
## 7. Evidence Files
## 8. Decision
## 9. Downstream Impact
## 10. Next Action
```

---

## 14. 长时间任务自动化监控

任何预计运行超过 10 分钟的任务，必须在 Phase 2 中规划监控，并在 Phase 3 中后台提交与注册。监控属于 Phase 3 内部模块，不单独作为 Phase 4。

### 14.1 注册文件

`logs/jobs.tsv`：

```text
job_id	stage_id	submit_time	command	cwd	env	pid_or_scheduler_id	stdout_log	stderr_log	expected_outputs	status
```

`logs/monitor.tsv`：

```text
time	job_id	check_round	check_type	interval_minutes	job_status	log_size	new_log_lines	output_size	error_keywords	decision	notes
```

`monitoring/monitor_state.yaml`：

```yaml
current_policy: early_1min
normal_checks: 0
abnormal_checks: 0
last_check_time:
next_check_time:
last_status:
active_jobs: []
```

说明：`monitor_state.yaml` 只是监控器运行状态缓存，不作为最终审计依据；`logs/monitor.tsv` 才是监控审计日志。

### 14.2 退避监控策略

1. 提交后前 3 分钟，每 1 分钟检查一次，共 3 次。
2. 如果 3 次均正常，改为每 10 分钟检查一次。
3. 如果连续 3 次 10 分钟检查均正常，改为每 30 分钟检查一次。
4. 一旦异常，重置为每 1 分钟检查，并进入故障定位。

### 14.3 正常判定

正常判定必须同时满足 required conditions，并至少满足一个 progress condition。

Required conditions：

```text
job_status 为 RUNNING / ACTIVE / QUEUED，且符合预期
未检测到 fatal / error / traceback / OOM / disk full / permission denied / missing input / dependency error
运行时间未超过预设 runtime limit，或已在 decisions.md 中说明
```

Progress conditions：

```text
stdout 或 stderr 有新的有效日志行
预期输出文件大小增长
预期 checkpoint 出现
调度器显示 CPU / memory / I/O 活跃
当前阶段被记录为允许在特定窗口内无明显输出增长
```

### 14.4 异常判定

任一命中即异常：

```text
作业退出或失败
日志出现明确错误关键字或堆栈
输出长时间无变化且与预期不符
资源、权限、路径、输入或依赖错误
作业 exit code 为 0 但预期输出缺失
作业 exit code 为 0 但输出为空或行列数异常
作业完成后 QC 失败
```

### 14.5 异常报告最低要求

异常时必须记录：

```text
异常发生时间
证据位置：日志路径、行号或错误码
最可能原因排序列表，至少 2 条
最小修复动作
复现验证方式
是否产生 TODO
是否阻塞当前 stage gate
```

---

## 15. Provenance 设计

每个 formal stage 必须产出 `provenance.md`，最终结果还必须产出汇总 `03_execution/final/provenance.md`。

### 15.1 `provenance.md` 固定结构

```md
# Provenance: {stage_id}

## 1. Purpose
## 2. Run Metadata
## 3. Inputs
## 4. Outputs
## 5. Code And Config
## 6. Environment
## 7. Reference Data
## 8. Commands
## 9. Parameters
## 10. Randomness
## 11. QC Criteria
## 12. QC Results
## 13. Checksums
## 14. Known Issues
## 15. Reproduction
```

### 15.2 Run Metadata

```text
run_id
protocol_version
profile
project
task_name
operator
start_time
end_time
stage_id
stage_status
qc_status
gate_status
```

### 15.3 Code Version

```text
git_repo
git_commit
git_branch
git_dirty_status
script_path
script_hash
config_path
config_hash
```

### 15.4 Environment

```text
conda_env_name
conda_env_export_path
container_image
container_digest
module_list
hostname
os
cpu_arch
software_versions
```

### 15.5 Reference Data

```text
reference_genome_name
reference_genome_version
reference_provider
reference_release_date
reference_checksum
annotation_name
annotation_version
annotation_provider
annotation_checksum
database_name
database_release
database_checksum
```

### 15.6 Command Execution

```text
command_id
command
cwd
start_time
end_time
exit_code
stdout_log
stderr_log
runtime_seconds
resource_request
resource_usage_summary
```

### 15.7 Randomness

```text
random_seed
seed_scope
stochastic_steps
```

### 15.8 每个正式输出必须记录

```text
path
description
format
size_or_rows_columns
created_time
md5
sha256
upstream_input
generating_command
parameters
environment
qc_status
frozen_status
```

---

## 16. 数据版本管理

生信任务必须记录数据来源、同步状态、参考版本和 checksum。尤其是跨服务器、本地镜像、历史归档和参考基因组/注释版本不一致时，必须记录数据版本字段。

### 16.1 输入数据版本字段

```text
data_source_type
remote_uri
remote_host
remote_path
local_mirror_path
sync_time
sync_method
source_size_bytes
local_size_bytes
source_md5
local_md5
source_sha256
local_sha256
checksum_match
checksum_mismatch_policy
last_verified_time
```

### 16.2 参考数据版本字段

```text
reference_id
reference_name
reference_version
reference_provider
reference_release_date
annotation_id
annotation_version
annotation_provider
database_release
```

### 16.3 多服务器路径字段

```text
storage_backend
mount_point
host
absolute_path
path_validated_time
```

---

## 17. Path Registry 与 Files Manifest

`path_registry.tsv` 和 `files_manifest.tsv` 不合并。二者职责不同。

```text
path_registry.tsv = planned and allowed paths
files_manifest.tsv = observed and audited files
```

### 17.1 `path_registry.tsv`

Phase 2 规划文件，记录允许使用或写入的路径。

表头：

```text
path_id	path	path_role	phase	stage_id	owner	mutability	required	expected_pattern	description	created_by	decision_id	notes
```

`mutability` 可取：

```text
raw_readonly
planned_output
intermediate
final_candidate
frozen
scratch
```

规则：

1. 原始数据必须标记为 `raw_readonly`。
2. 正式结果不得写入未注册路径。
3. Phase 3 如确需新增路径，必须更新 `path_registry.tsv`，并写入 `docs/decisions.md`。
4. scratch 路径不得直接作为 final output。

### 17.2 `files_manifest.tsv`

Phase 3 与 final 阶段审计文件，记录实际存在的文件。

表头：

```text
file_id	path_id	file_path	file_role	format	exists	size_bytes	n_rows	n_columns	created_time	modified_time	md5	sha256	producer_stage_id	producer_command_id	upstream_file_ids	qc_status	frozen_status	notes
```

### 17.3 `outputs_manifest.tsv`

每个 stage 的输出清单，表头可与 `files_manifest.tsv` 保持一致，并增加：

```text
stage_local_role
required_for_next_stage
```

### 17.4 `frozen_outputs.tsv`

最终冻结文件清单：

```text
file_id	path	file_role	stage_id	md5	sha256	size_bytes	frozen_time	freeze_decision_id	qc_status	notes
```

---

## 18. Commands 与 Reproduction

### 18.1 `logs/commands.tsv`

```text
command_id	phase	stage_id	time	cwd	command	env	stdout_log	stderr_log	exit_code	status	notes
```

规则：

1. 所有生成正式结果的命令必须记录。
2. 命令必须包含 `cwd`、环境、stdout、stderr、exit code。
3. 多行命令应保存到脚本或 command file，并在 `commands.tsv` 中引用路径。
4. 若命令失败，应记录失败原因和对应 TODO。

### 18.2 `03_execution/final/reproduce.sh`

最终复现脚本必须满足：

```text
可读
可复制运行
包含环境激活步骤
包含关键输入路径检查
包含核心命令
包含输出路径
不删除或覆盖原始数据
```

建议开头：

```bash
#!/usr/bin/env bash
set -euo pipefail
```

---

## 19. Subagents 使用策略

### 19.1 主会话职责

- 阶段边界控制。
- 决策整合。
- 最终报告。
- 与用户确认。
- 状态源更新。

### 19.2 Subagent 职责

```text
explorer      搜索代码、配置、历史结果
architect     生成独立方案或质疑方案
reviewer      审查方案、路径、QC、风险
worker        Phase 3 中实现明确文件范围内的任务
test-runner   执行测试和 QA，收集 stdout / stderr / exit code
monitor       读取 jobs、logs、outputs，更新监控日志和状态文件
```

### 19.3 规则

1. Subagent 输出必须保存到对应 `subagents/*.md`。
2. 主会话只整合摘要，不复制大量原始日志到最终答复。
3. Worker 必须有明确文件或模块 ownership。
4. 多个 worker 不得写同一文件集合。
5. Monitor 不得修改正式结果，只能更新监控日志和状态文件。
6. Subagent 输出不能直接替代主会话决策。

---

## 20. 文档模板

### 20.1 `README.md` 模板

```md
# Agent Run: {task_name}

## Current Status

- Run ID:
- Protocol Version:
- Profile:
- Current Phase:
- Current Stage:
- Overall Status:
- Last Updated:
- Next Required Action:

## Locked Paths

## Do Not Modify

## Completed Phases

## Active TODO

## Blockers

## Reproduction

## Key Links
```

### 20.2 `stage.md` 模板

```md
# Stage: {stage_id}

## 1. Stage Goal
## 2. Inputs
## 3. Outputs
## 4. Commands
## 5. Logs
## 6. QC Summary
## 7. Decisions
## 8. Problems Encountered
## 9. Next Stage Gate
```

### 20.3 `final_report.md` 模板

```md
# Final Report: {task_name}

## 1. Summary
## 2. Scope
## 3. Inputs
## 4. Methods
## 5. Outputs
## 6. QC Summary
## 7. Frozen Results
## 8. Known Issues
## 9. Reproduction
## 10. Appendix
```

---

## 21. 建议脚本

### 21.1 最小脚本

```text
scripts/init_agent_run.py
scripts/render_index.py
scripts/check_manifest.py
scripts/hash_outputs.py
```

职责：

- `init_agent_run.py`：创建 run 目录和基础模板。
- `render_index.py`：根据 metadata、stage registry、TODO、monitor logs 渲染 `index.html`。
- `check_manifest.py`：检查路径、产物、QC、provenance 是否齐全。
- `hash_outputs.py`：生成 checksums。

### 21.2 增强脚本

```text
scripts/register_stage.py
scripts/write_command_log.py
scripts/monitor_job.py
scripts/freeze_outputs.py
```

职责：

- `register_stage.py`：新增或更新 `stage_registry.tsv`。
- `write_command_log.py`：规范化写入 `logs/commands.tsv`。
- `monitor_job.py`：按退避策略监控长任务。
- `freeze_outputs.py`：冻结最终结果并生成 `frozen_outputs.tsv`。

---

## 22. 实现方式

建议将本协议实现为四件套：

```text
1. staged_agent_run_protocol/SKILL.md
2. templates/staged_agent_run_protocol/
3. scripts/init_agent_run.py 等辅助脚本
4. 项目根目录 PROJECT_PROTOCOL.md
```

### 22.1 `SKILL.md`

负责约束 Agent 行为：

```text
何时触发协议
各阶段职责
各阶段禁止事项
必须产物
QC gate
状态源分工
长任务监控
```

### 22.2 `PROJECT_PROTOCOL.md`

负责项目级规则：

```text
项目根路径
水稻参考基因组和注释版本
服务器路径规范
图表风格
文件命名规范
原始数据保护规则
```

### 22.3 `templates/`

负责提供：

```text
目录模板
Markdown 模板
TSV 表头
YAML 模板
HTML 模板
CSS
```

### 22.4 `scripts/`

负责自动化：

```text
初始化
渲染
manifest 检查
hash
命令日志
长任务监控
结果冻结
```

---

## 23. 最小可落地版本

v0.1 的最低落地范围：

```text
P0:
  SKILL.md
  PROJECT_PROTOCOL.md
  templates/staged_agent_run_protocol/
  scripts/init_agent_run.py
  scripts/render_index.py
  scripts/check_manifest.py
  scripts/hash_outputs.py

P1:
  scripts/register_stage.py
  scripts/write_command_log.py
  scripts/freeze_outputs.py

P2:
  scripts/monitor_job.py
  HTML theme
  subagent role templates
```

v0.1 不要求一开始实现所有自动化脚本，但必须先固定以下规范：

```text
目录结构
phase 产物
stage 产物
path_registry.tsv
stage_registry.tsv
qc_criteria.tsv
commands.tsv
jobs.tsv
monitor.tsv
provenance.md
frozen_outputs.tsv
checksums.tsv
```

---

## 24. 审计检查清单

每个 run 完成前，必须检查：

```text
[ ] metadata/run.yaml 存在
[ ] metadata/status.yaml 存在且状态更新
[ ] README.md 已更新
[ ] index.html 已渲染
[ ] TODO 已更新
[ ] path_registry.tsv 存在
[ ] stage_registry.tsv 存在
[ ] qc_criteria.tsv 存在
[ ] 每个 required stage 有 stage.md
[ ] 每个 required stage 有 provenance.md
[ ] 每个 required stage 有 qc_report.md
[ ] 每个 required stage 有 outputs_manifest.tsv
[ ] 所有正式命令记录在 commands.tsv
[ ] 长任务记录在 jobs.tsv
[ ] 监控记录在 monitor.tsv
[ ] 所有 final outputs 有 checksum
[ ] frozen_outputs.tsv 已生成
[ ] reproduce.sh 已生成
[ ] known_issues.md 已更新
[ ] decisions.md 已更新
[ ] final_report.md 已生成
```

---

## 25. 协议总结

本协议的核心不是目录结构本身，而是将复杂科研任务转化为可审计的 staged run：

```text
先建立任务运行实例，
再分析问题，
再冻结方案与路径，
再分 stage 执行，
每个 stage 独立 QC 与 provenance，
最后冻结结果并保留完整复现证据。
```

最终要求：任何正式结果都必须能够回答：

```text
它从哪里来？
由哪个命令生成？
用了哪些参数？
依赖什么环境？
参考基因组、注释和数据库版本是什么？
上游输入是什么？
是否通过 QC？
如果未完全通过 QC，谁做了 waiver 决策？
checksum 是什么？
别人如何复现？
```
