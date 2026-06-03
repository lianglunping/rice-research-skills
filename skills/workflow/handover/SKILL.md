---
name: handover
description: >-
  Use this skill when the user asks for handover, session handoff, context
  preservation, clear-safe state capture, updating HANDOVER.md, saving current
  progress before /clear, or preparing a next-session restore prompt. Chinese
  trigger hints: 交接, 工作交接, 保存当前进度, 更新 HANDOVER.md, 清理上下文前持久化,
  新会话继续, 防止 clear 后丢失信息.
---

# Handover

Persist the current session's knowledge so the user can safely clear context or continue in a new Codex session without losing critical work state.

**Core principle**: first persist knowledge, then update the index. Never tell the user clearing context is safe based only on `HANDOVER.md` existing.

**Task is a first-class citizen**: each independent work stream has its own `task-id` such as `task-{verb}-{object}`. Multiple tasks may live in the same directory. Task blocks in `HANDOVER.md` never overwrite each other; completed tasks move into a `<details>` archive block or an archive pointer, never silently deleted.

## Phase 0: Task Identification

Before triage, identify which task or tasks this session touched:

1. Read the current `HANDOVER.md` `## 活跃任务` block if it exists.
2. Match the current session's work to one of the active `task-id`s.
3. If session work does not match any active task, propose a new `task-id` using `task-{verb}-{object}` and confirm if ambiguity matters.
4. If the same directory has multiple concurrent tasks, ensure each has its own task block. Never merge unrelated tasks just because they share a directory.

## Phase 1: Knowledge Triage

Scan the current conversation, tool outputs, code changes, and known project files. Classify knowledge produced this session. Every item carries the owning `task-id`.

| Category | What to look for | Destination |
|----------|------------------|-------------|
| Status | Tasks completed, blockers, progress | `HANDOVER.md` task block |
| Data | New numbers, paths, versions, file counts | `provenance.md` or task-specific provenance file |
| Decisions | Method choices, tool selections, rejected alternatives, changed approaches | `decisions/DECISION_LOG.md` with `Task:` field |
| Process | Multi-step reasoning, conclusion reversals, audit findings, literature analysis, external reviews | Dedicated doc in the relevant sub-project |

Build an internal checklist of volatile items: knowledge that exists only in chat or tool output and has not yet been persisted to a file.

## Phase 2: Persist Process and Decision Knowledge First

This phase must complete before updating `HANDOVER.md`.

### 2-pre. Concurrency Lock and Idempotency

Before any handover write, use a local lock to avoid corrupting `HANDOVER.md` from concurrent handover runs:

```bash
LOCK="$PWD/.handover.lock"
if [ -e "$LOCK" ]; then
  AGE=$(( $(date +%s) - $(stat -f %m "$LOCK" 2>/dev/null || stat -c %Y "$LOCK") ))
  if [ "$AGE" -lt 300 ]; then
    echo "ERROR: another handover is running (lock age ${AGE}s); abort or wait."
    exit 1
  fi
  echo "WARN: stale lock (${AGE}s), overriding."
fi
echo "$$ $(date -Iseconds)" > "$LOCK"
trap 'rm -f "$LOCK"' EXIT
```

Idempotency rule: every persisted record carries a stable `Fingerprint`, usually `sha1(task-id + summary + sorted impacted paths)`. On rerun, if the fingerprint matches, update in place or leave unchanged; do not append duplicates. Replace `HANDOVER.md` via temp file plus atomic rename rather than editing in place.

### 2a. Decision Log

If any decisions were made this session, append or update `decisions/DECISION_LOG.md`. Create `decisions/` if needed. Compute the fingerprint first; if a decision block with the same fingerprint already exists, update that block instead of appending a duplicate.

```markdown
### DEC-{DATE}-{SEQ}: {One-line summary}

- **Task**: {task-id}
- **Session**: {iso-timestamp + short id, e.g. 2026-04-30T22:30+08:00 / s-a4f}
- **Fingerprint**: sha1({task-id}|{summary}|{sorted impacted-paths})
- **Decision**: What was decided
- **Trigger**: What prompted it
- **Alternatives**: Options considered
- **Rationale**: Why this option
- **Trade-offs**: What was sacrificed
- **Impact**: Files/sections affected
- **Details**: -> path/to/detailed_doc.md (if exists)
```

The `Task` field enables `grep "Task: {task-id}" decisions/DECISION_LOG.md` to filter decisions per task.

### 2b. Process Documents

If significant reasoning chains exist, persist them before updating `HANDOVER.md`. Examples include:

- analysis evolution
- conclusion reversals
- audit results
- literature analysis
- external model or reviewer feedback
- method comparisons that affected the final direction

Use a dated document in the relevant sub-project directory. Recommended naming:

```text
{task-id}_{topic}_{YYYYMMDD}.md
{task-id}_evolution.md
```

The document must include what changed, why, evidence, and before/after comparison when applicable.

### 2c. Provenance Updates

If new verified numbers or paths were discovered, update the relevant `provenance.md` or task-specific provenance file. When a project hosts multiple tasks, tag each row with `task:` or keep separate provenance files per task.

Do not write unverified numbers as facts. If a value is uncertain, mark it as uncertain and state the missing evidence.

### 2d. Session Artifacts

List files created or modified this session. Capture unstaged, staged, and untracked files. Default `git diff` misses staged content.

```bash
git status --short
git diff --name-only
git diff --cached --name-only
git ls-files --others --exclude-standard
git diff --stat
git diff --cached --stat
```

For non-git projects, inspect recent files:

```bash
find . -maxdepth 4 -type f -mmin -480 ! -path '*/.git/*' ! -name '.DS_Store' | head -30
```

### 2e. Tool Handoff

Handover is the index layer. It does not replace specialized memory, provenance, monitoring, or project knowledge tools. If this session produced one of the following knowledge types, use the matching Codex capability before Phase 3 when available:

| Knowledge type | Preferred Codex capability |
|----------------|----------------------------|
| Durable global preference or cross-project fact | `memory-palace` skill / Memory Palace MCP |
| Artifact lineage, claim-to-command evidence, or reproducibility records | `provenance.md`, project provenance template, or installed provenance skill |
| Repo bound to an Obsidian project knowledge base | `obsidian-project-memory` skill |
| Long-running job state, monitor cadence, run id, or anomaly evidence | `job-monitor-loop` skill |
| Risk, reproducibility, or compliance findings | `project-audit` skill or the project's audit workflow |

Record each invoked capability under "Knowledge persisted" in the Phase 5 report.

## Phase 3: Update HANDOVER.md

`HANDOVER.md` is an index layer only.

1. Read the current `HANDOVER.md`; create it from the template if absent.
2. Update each section according to the rules below.

| Section | Rule |
|---------|------|
| YAML frontmatter | Keep machine-readable `schema_version`, `project`, `project_root`, `last_updated`, `focus_task`, and `active_task_count` |
| `> 最后更新` | Current date/time, focus `task-id`, and concise session summary |
| `活跃任务` | One block per active task. Mark the focus task with `[active]` |
| `已完成任务（归档）` | Collapsed `<details>` blocks or pointers to `archive/tasks/`; never delete silently |
| `待决策` | Open decisions only, each tagged with its `task-id`; keep the list short |
| `项目级知识索引` | Cross-task pointers such as provenance files, decision log, archives, and key docs |

### Active Task Block

```markdown
### [active] task-{verb}-{object}
- 目录: {relative-path}
- 状态: {phase + key metric}
- Blockers: {blocker or —}
- 知识索引:
  - decisions/DECISION_LOG.md `Task: task-{verb}-{object}`
  - {relative-path}/docs/{task-id}_xxx_{date}.md
- 下一步: {concrete next step}
- Restore: 读取 HANDOVER.md，继续 task-{verb}-{object}：{具体任务}
```

### Done-State Determination

A task may transition from active to archive only if all gates pass:

| Gate | Criterion |
|------|-----------|
| Deliverable | Produced or explicitly canceled by user |
| Blockers | Empty or transferred to a successor task |
| Restore | Prompt explicitly says no immediate next step, or points to a successor task |
| User confirmation | Recorded in this session, except for read-only review or audit tasks |

If any gate fails, keep the task under `活跃任务` with updated status and blockers.

### Archive Policy

- Move completed task blocks into `## 已完成任务（归档）` as `<details>` blocks.
- Always retain summary, restore prompt or successor pointer, archive pointer, and decisions pointer.
- When `<details>` blocks reach 10 or `HANDOVER.md` exceeds about 150 lines, migrate the oldest archived task into `archive/tasks/{task-id}_{YYYYMMDD}.md` and keep a one-line pointer in `HANDOVER.md`.
- Never rely on `git log` as the sole retrieval path. The next session entry point is `HANDOVER.md`.

### Atomic Archive Migration

Avoid half-archived state on interrupt. Write archive content first, verify it, then update `HANDOVER.md`.

```bash
ARC_TMP="archive/tasks/{task-id}_{YYYYMMDD}.md.tmp"
ARC_FINAL="archive/tasks/{task-id}_{YYYYMMDD}.md"
HOV_TMP="HANDOVER.md.tmp"

# 1. Write archive content to ARC_TMP:
#    full task block + restore prompt + decisions pointer + summary.

# 2. Verify tmp is non-empty and contains required anchors.
grep -q "task-id" "$ARC_TMP" \
  && grep -q "Restore" "$ARC_TMP" \
  && grep -q "DECISION_LOG" "$ARC_TMP" \
  || { rm -f "$ARC_TMP"; exit 1; }

# 3. Atomic rename: archive becomes durable.
mv "$ARC_TMP" "$ARC_FINAL"

# 4. Only now write new HANDOVER.md via temp + atomic rename.
mv "$HOV_TMP" HANDOVER.md
```

### HANDOVER.md Should Not Contain

- Detailed reasoning or audit text; point to docs instead.
- Large path or version tables; point to provenance.
- Completed task detail bodies; keep collapsed summaries and archive pointers.
- Data that duplicates provenance files, `AGENTS.md`, `CLAUDE.md`, or durable memory.

## Phase 4: Clear Safety Gate

Run this checklist before telling the user context clearing or session switching is safe:

```text
□ HANDOVER.md updated in this invocation
□ YAML frontmatter exists and has current project_root / last_updated / focus_task
□ Every active task has its own named block
□ Every active task has its own restore prompt
□ Completed tasks moved to <details> archive or archive pointer
□ All volatile knowledge items persisted to files
□ DECISION_LOG entries carry Task field
□ External reviews or audits saved if they occurred
□ Literature analyses saved if they occurred
□ Conclusion reversals documented with before / after / why
□ Session artifacts listed, including staged and untracked files when git exists
□ Pending user confirmations explicitly tracked
□ No critical claim exists only in chat
```

### Failure Recovery Loop

If any check fails:

1. Map each missing item back to its owning phase.
2. Return to the earliest failed phase, fix once, then rerun Phase 4.
3. If the second check still fails, output `CLEAR_READY: NO` and stop. Surface the unresolved checklist to the user.

If all checks pass, output `CLEAR_READY: YES` and show the restore prompts.

## Phase 5: Report to User

Use this concise report shape:

```markdown
## Handover Complete

**Tasks touched this session**:
- [list of task-ids with active / closed status]

**Knowledge persisted**:
- [docs created or updated, grouped by task-id]

**HANDOVER.md**:
- Active task blocks: [N]
- Archived this session: [N]
- Current size: [N] lines

**Clear gate**: PASS / FAIL
- Volatile items checked: [N]
- Newly persisted: [N]
- Pending user confirmations: [N]

CLEAR_READY: YES / NO

**Next-session restore prompts**:
```text
# task-call-gatk
请先读取 HANDOVER.md，然后继续 task-call-gatk：运行 GenotypeGVCFs chr4-12

# task-deepvariant
请先读取 HANDOVER.md，然后继续 task-deepvariant：启动 Docker 环境
```
```

## HANDOVER.md Template

The file must start with YAML frontmatter so external tools can parse `project_root`, `last_updated`, and `focus_task` without scraping prose.

```markdown
---
schema_version: 1
project: "<project-name>"
project_root: "<absolute-path-or-repo-root>"
last_updated: "2026-04-30T22:30:00+08:00"
focus_task: "task-{verb}-{object}"
active_task_count: 1
---

# [Project Name] - 工作交接

> 最后更新: YYYY-MM-DD HH:MM | 焦点: task-{id} | Session: [summary]

## 活跃任务

### [active] task-{verb}-{object}
- 目录: {relative-path}
- 状态: {phase + key metric}
- Blockers: —
- 知识索引:
  - decisions/DECISION_LOG.md `Task: task-{verb}-{object}`
  - {path}/docs/{task-id}_xxx_{date}.md
- 下一步: {concrete next step}
- Restore: 读取 HANDOVER.md，继续 task-{verb}-{object}：{具体任务}

### task-{another-verb}-{object}
（同结构）

## 已完成任务（归档）

<details>
<summary>task-bwa-index (done YYYY-MM-DD)</summary>

- Summary: BWA 索引构建完成，产物在 `/data/ref/rice_MSU7.fa.{amb,ann,bwt,pac,sa}`
- 决策: -> decisions/DECISION_LOG.md `Task: task-bwa-index`
- 详情: -> archive/tasks/task-bwa-index_YYYYMMDD.md
- Restore: 读取 HANDOVER.md + archive/tasks/task-bwa-index_YYYYMMDD.md，继续……
</details>

## 待决策

1. [task-call-gatk] VQSR 还是 hard filter：样本量 32 是否足够 VQSR？

## 项目级知识索引

| 类型 | 文件 | 说明 |
|------|------|------|
| 数据溯源 | path/to/provenance.md | 数字可追溯（含 task: 列） |
| 所有决策 | decisions/DECISION_LOG.md | 按 `Task:` 字段过滤 |
| 归档快照 | archive/tasks/ | 溢出归档位置 |
```

## Task-id Naming Convention

- Format: `task-{verb}-{object}`, kebab-case.
- Verbs: `call`, `filter`, `annotate`, `align`, `index`, `blast`, `validate`, `analyze`, `write`, `audit`, `monitor`.
- Objects: `gatk`, `deepvariant`, `bwa`, `kasp`, `bsa`, `indel`, `handover`, `thesis`.
- Good: `task-call-gatk`, `task-filter-vqsr`, `task-validate-kasp`.
- Bad: `task1`, `gatk`, `TaskA`, `variant-calling`.

## Notes

- Use this skill before ending a substantial session or before clearing context.
- Phase 2 must complete before Phase 3.
- Do not put detailed reasoning directly in `HANDOVER.md`; use durable docs and pointers.
- Single-task projects are still represented as one active task block.
- Soft cap triggers archive migration; never delete retrievable history.
