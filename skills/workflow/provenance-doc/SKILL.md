---
name: provenance-doc
description: >
  This skill should be used when the user asks to "记一下这个分析"、"生成 provenance"、"生成溯源文档"、"帮我创建复现文档"、"封版"、"seal version"、"create provenance for this analysis"、"归档当前结果"、"为 v1.3.2 写溯源文档"、"provenance for analysis/foo"、or needs to bind claims/artifacts/verification commands/version lineage for reproducibility. Auto-aggregates from sibling `run_config.yaml` / `*.meta.yaml`. Two templates (full + lite) with state machine `draft → numbers-pending → verification-ready → verified → sealed`.
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Provenance Doc Skill

半自动化生成"溯源文档" (`provenance.md`)，把分析过程中的 claim ↔ artifact ↔ verification command ↔ version lineage 绑定起来。

## 何时使用

| 场景 | 模板 | 路径 | 触发词 |
|------|-----|------|--------|
| Pipeline 版本封档 | 完整版 | `archive/legacy_results/v{N}/provenance.md` | "封版"/"seal version" |
| 一次性分析任务 | 轻量版 | `analysis/{name}/provenance.md` | "记一下这个分析"/"生成 provenance" |
| 学位论文章节归档 | 轻量版+引用链 | `plans/thesis/provenance_{chapter}.md` | "为章节归档" |

**单次 pipeline 运行不写 provenance.md**（沿用 `run_config.yaml`）。

## 边界（与现有基础设施区分）

> **`provenance.md` 只在「结果要被解释、引用、交付或封版」时写。**
>
> - 运行参数 → `run_config.yaml`
> - 单文件事实（MD5、行数）→ `<result>.meta.yaml`
> - 代码审计 → `audit_*.md`
> - 过程性决策 → `evolution.md` / `DECISION_LOG.md`

详见 `references/boundary-decision-flowchart.md`。

## 状态机

```
draft → numbers-pending → verification-ready → verified → sealed
```

- `analysis/` 允许 draft~verified
- `archive/legacy_results/` 仅允许 sealed
- sealed 文件 chmod 444；解封请 `unseal_unsafe.py --reason "..."`

## 主要命令

```bash
# 创建轻量版
uv run "$HOME/.codex/skills/provenance-doc"/scripts/new_provenance.py \
    --template lite --out analysis/foo/provenance.md \
    --owner $USER --project myproj

# 创建完整版
uv run "$HOME/.codex/skills/provenance-doc"/scripts/new_provenance.py \
    --template full --out archive/legacy_results/v1.0/provenance.md \
    --owner $USER --project myproj --version v1.0

# 聚合 sibling .meta.yaml 到 §4 产物表
uv run --with pyyaml "$HOME/.codex/skills/provenance-doc"/scripts/aggregate_meta.py \
    --doc analysis/foo/provenance.md

# 跑 §5 论断验证册中的命令
uv run --with pyyaml "$HOME/.codex/skills/provenance-doc"/scripts/verify_claims.py \
    --doc analysis/foo/provenance.md [--dry-run] [--allow-remote]

# 检查 schema + 状态机
uv run --with pyyaml --with jsonschema python3 \
    "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py \
    analysis/foo/provenance.md

# 渲染（inline extensions）
uv run --with pyyaml "$HOME/.codex/skills/provenance-doc"/scripts/render_doc.py \
    --doc analysis/foo/provenance.md
```

## 扩展槽位

业务相关的项目专属统计（任何不属于通用模板 §0-9 的统计章节）放 `_extensions/{id}.md`，在主文档 front-matter 声明：

```yaml
extension_sections:
  - id: domain_stat_a
    title: "Domain stat A"
    source: _extensions/domain_stat_a.md
    status: verified
```

## References

- `references/full-template-spec.md` — 完整版 §0-9 字段定义
- `references/lite-template-spec.md` — 轻量版 §0-5 字段定义
- `references/extension-mechanism.md` — 扩展槽位机制
- `references/verification-policy.md` — 验证命令策略 + 状态机
- `references/boundary-decision-flowchart.md` — 与其他文档类型的边界

## Examples

- `examples/full-pipeline-sealed.md` — 完整版示例（中性脱敏内容）
- `examples/lite-analysis.md` — 轻量版示例
- `examples/boundary-edge-cases.md` — §8.2 边缘情形

## 安全

- `verify_claims.py` 拒绝执行 `rm -rf /`、`mkfs`、`dd if=`、fork bomb 等危险模式
- 远程命令（`ssh `/`scp `/`rsync `）默认拒绝，需 `--allow-remote`
- `--dry-run` 仅打印不执行
