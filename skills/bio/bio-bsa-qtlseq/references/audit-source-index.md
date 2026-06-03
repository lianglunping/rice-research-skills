# Audit Source Index — 50 项审计发现 → 4 Gate 映射

基于葡萄 5h+3h BSA 项目的两轮多 Agent 审计。本文档保留**来源 ID + 严重度 + 修复位置**，供未来追溯。

## 审计元数据

| Round | 日期 | 范围 | 发现数 | 已修 | 修复版本 |
|-------|------|------|--------|------|----------|
| 1 | 2026-04-16 | 项目整体（流水线 + Obsidian + 服务器） | 28 | 26 | v2_fixed |
| 2 | 2026-04-17 | 交付包 release/ | 22 | 22 | v2.1 |
| **合计** | | | **50** | **48** | **v2.1** |

剩 2 项延后: S1 最小可复现示例 + S3 葡萄已知抗旱基因 sanity check。

## 来源 ID 命名

- `audit1-CXX/MXX/mxx/SXX`: 第 1 轮审计 Critical/Major/Minor/Suggestion + 序号
- `audit2-CXX/MXX/mxx/SXX`: 第 2 轮
- `codex-1 盲点 #X`: Codex 第 1 轮独有发现
- `codex-2 盲点 #X`: Codex 第 2 轮
- `DEC-YYYYMMDD-NNN`: DECISION_LOG 决策
- `design-R2-XX`: Team design debate Round 2 的反馈

## Gate 映射表

### → Gate 1 (Preflight)

| 来源 ID | 问题 | Gate 1 对应 # |
|---------|------|---------------|
| audit1-D03 | cohort VCF 样本数 168 vs 155 文档漂移 | #7 样本匹配 |
| audit1-DEC-011 | 亲本 min-parent-dp=5 | #8, #9 |
| audit1-C2 | n=20 统计力不足 | #10 bulk size ≥20 |
| audit2-M10 | samples.tsv 缺 phenotype_value | #12 |
| audit2-M8 | 缺 environment.yml / QTLseqr 锁定 | #13 |
| release-M8 | schema 自校验 | #1, #2 |
| codex-1 盲点 #1 | QTLseqr moving target | #13 |
| 设计 R2 盲点 #3 | Gate 1 auto-build 记录 | #3 → autobuild_log.txt |

### → Gate 2 (Post-Pool)

| 来源 ID | 问题 | Gate 2 对应 # |
|---------|------|---------------|
| audit1-C02 | parent_skip 混合计数 | #1 统计闭环 (v2.1 已拆 4 分类) |
| audit2-C01 | is_hom_ref/alt 严格元组 | #5 half-call 独立计数 |
| DEC-014 | Pool DP = sum(AD_REF + AD_ALT) | #8 DP 一致性抽样 |
| DEC-015 | allele re-polarize by Va | #4 polarized 比例, #7 VA_HOM 字段 |
| audit1 统计闭环 | in = chr_skip + indel + multi + parent_skip + kept | #1 |

### → Gate 3 (Post-QTLseqr)

| 来源 ID | 问题 | Gate 3 对应 # |
|---------|------|---------------|
| audit1-m6 | filterSNPs retained 未记录 | #1 |
| audit2-C3 | SUMMARY 选择性汇报 4×3 矩阵 | #2 |
| audit2-C1 | q=0.05 fallback 未声明 | #3, #4, #8 |
| design-R2 盲点 #1 | allow_fallback=true 必生成 rationale | #4 fallback_rationale.md |
| audit1-M5 | chr5 端粒伪峰 | #6 端粒 flag |
| audit1-M4 | chr11 qtl5 染色体级 | #7 chromosome-level flag |
| audit2-C1 | Tier 分级错 (16 vs 实际 2) | #8 按 meanQval |
| audit2-C2 | Top 6 基因数估计偏差 +160% | #9 bedtools 实测 |

### → Gate 4 (Pre-Delivery)

| 来源 ID | 问题 | Gate 4 对应 # |
|---------|------|---------------|
| audit2-S1 | MANIFEST 完整性 | #1 |
| audit2-M5 | 内部路径泄露 | #2 grep |
| codex-1 盲点 #4 | README 数字可重算 | #3 |
| audit2-C1 | Tier 分级一致性 | #4 |
| audit2-C2 | Top QTL 基因数 | #5 |
| audit2-C3 | SUMMARY 4×3 矩阵 | #6 |
| audit2 结构 | 必需文件 + PDF/PNG 成对 | #7 |
| codex-1 盲点 #1 | QTLseqr 版本锁 | #8 |
| R2-B3 | SHA256 manifest | #9 |
| 盲点 #2 | gene_id_prefix x-doc-only | #10 |
| audit2-M2 | emoji ✅ 误导 | 人工 A1 |
| audit2-M3 | "可直接克隆"强语义 | 人工 A2 |
| audit2 LIMITATIONS | 局限 6 项 | 人工 A3 |

## 延后项（TODO）

| 来源 ID | 问题 | 延后到 |
|---------|------|--------|
| audit1-S1 | 最小可复现示例 (toy dataset) | task-bsa-report |
| audit1-S3 | 葡萄已知抗旱基因 sanity check | task-bsa-enrichment |

## DECISION_LOG 对应

15 条 DEC 决策全部在 pipeline/templates 中落地:

- DEC-011 v2 流水线
- DEC-012 A/B 分级 + 表述规范
- DEC-013 命名统一 (QTLseq_ci9X)
- DEC-014 Pool DP = sum(AD)
- DEC-015 re-polarize 方向 bug 修复
- （其他 DEC-001~010 为实施细节，不直接对应 Gate）

## 使用方式

客户或审计者询问"为什么要做 X 检查/修复"时，通过 grep 本文件找到来源:

```bash
grep -rn 'audit2-C1' ~/.codex/skills/bio-bsa-qtlseq/
# 会定位到 Gate 4 #4 和本文件
```
