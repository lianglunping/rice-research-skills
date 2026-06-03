---
name: bio-bsa-qtlseq
description: |
  BSA (Bulk Segregant Analysis) 全流程 skill，基于 QTLseqr + DeepVariant 的
  v2.1 审计通过流程。自动触发于: "BSA", "QTLseqr", "QTL-seq", "G'",
  "bulk segregant", "混池分析", "混池重测序", "极端表型", "F2 分离群体定位",
  "抗旱 QTL", "抗病 QTL" 等场景。提供 contract-first 4-gate 流程、
  species profile overlay、50 项审计经验索引、完整交付包打包。
license: MIT
---

# bio-bsa-qtlseq — BSA 全流程 Skill

## 1. 触发条件

自动在以下场景激活：
- 用户提到: **BSA / QTLseqr / QTL-seq / G' / bulk segregant / 混池 / 极端表型 / 分离群体定位**
- 用户有 cohort VCF + 两组极端表型样本 + 亲本信息
- 用户询问"混池 QTL 定位"、"抗旱/抗病/产量 QTL 候选"

## 2. 职责边界 (严格)

### ✅ 本 skill 覆盖
- **输入起点**: cohort VCF (DeepVariant / GATK / bcftools joint-call) 或 QTLseqr input.table
- **核心流程**: 42 样本子集 → 亲本纯合差异过滤 → allele re-polarize → 按池合并 → QTLseqr G'+QTL-seq → 候选基因注释
- **交付**: release v2.x 结构（含审计自检 + 双签名 MANIFEST）
- **多时间点对比**: 同项目多 timepoint/batch 时自动触发区间 overlap

### ❌ 本 skill 不做（转其他 skill）
| 上游 | 转 |
|------|----|
| FASTQ → BAM → VCF | `snakemake-variant-pipeline` / `bio-variant-calling-*` |
| 群体关联分析 (GWAS) | `bio-gwas-gwas-pipeline` |
| GO/KEGG 功能富集执行 | 本 skill 只提供 HOWTO，不执行；见 `bio-genome-annotation-functional-annotation` |
| KASP 标记引物设计 | `variant-primer-design` |
| 基因组注释 | `bio-genome-annotation-*` |

## 3. 入口命令

```bash
# 交互式初始化（推荐新项目）
/bsa-init

# 非交互 YAML 模式（批处理/CI）
/bsa-init --config bsa.yaml --profile <species-profile> --non-interactive

# 恢复中断的流水线
/bsa-init --resume-from gate3 --config bsa.yaml

# 多时间点对比（项目存在多个 timepoint 子项目时）
/bsa-init --compare-timepoints t1_dir t2_dir [t3_dir ...]
```

## 4. 按需加载索引

**SKILL.md 仅提供导航**，具体知识按阶段加载对应文件：

| 当前阶段 | 应读 | 用途 |
|---------|------|------|
| 启动期 (解析配置) | `schemas/bsa-config.schema.json` + 具体物种 profile, 如 `profiles/rice-msu7.yaml` | 配置校验 |
| Gate 1 preflight | `checklists/gate1_preflight.md` | 7 项启动前检查 |
| Gate 2 post-pool | `checklists/gate2_post_pool.md` | 5 项合并后检查 |
| Gate 3 post-QTLseqr | `checklists/gate3_post_qtlseqr.md` | 6 项分析后检查 |
| Gate 4 pre-delivery | `checklists/gate4_pre_delivery.md` + `scripts/pre_delivery_check.sh` | 10 项交付前机器检查 |
| 方法学争议 | `references/bsa-method-boundaries.md` | 边界与假设 |
| 结果解读 | `references/interpretation-rules.md` | Tier / 方向 / 端粒 / stratification |
| 输出格式 | `references/output-contract.md` | release 结构 + 字段字典 + 图形规格 |
| 审计追溯 | `references/audit-source-index.md` | 50 项审计来源 → 4 gate 映射 |

## 5. 强制 Contract (编译时不可违反)

基于 v1→v2.1 两轮审计的 48/50 修复固化：

1. **Allele re-polarization by Va** — Va=0/0 位点必须交换 AD，使 SNPindex 恒等于 Va 频率（DEC-015）
2. **Random seed** — `set.seed(42)` 在 QTLseqr bootstrap 前必执行
3. **4×3 敏感性矩阵** — 主 + window=500kb + refAF=0.35，输出完整矩阵到 SUMMARY
4. **Tier 按 meanQval 实际阈值** — 禁止手工估计 Tier 边界
5. **Pool DP = sum(AD_ref + AD_alt)** — 不用原始 DeepVariant DP，保持 SNPindex 分母一致
6. **parent_skip 四分类计数** — `gt_missing / half_call / dp_low / not_homdiff` 分开
7. **fallback rationale** — `allow_fallback=true` 降档时必须生成 `fallback_rationale.md`
8. **PDF+PNG 双格式** — 图形必须同时输出 PDF（矢量）+ PNG（600 dpi）
9. **MD5 + SHA256 双签名** — release 打包必含两种 manifest
10. **Release 未过项目审计只能 draft** — P0 清 0 后才能 final

## 6. 状态机概览

```
INIT → GATE_1 → RUN_STEP2 → GATE_2 → RUN_STEP5 → GATE_3 → RELEASE_DRAFT
 → GATE_4 → project-audit review → [FIX_LOOP if P0] → RELEASE_FINAL → DECISION_LOG handover
```

详见 `checklists/gate1_preflight.md`、`checklists/gate2_post_pool.md`、`checklists/gate3_post_qtlseqr.md`、`checklists/gate4_pre_delivery.md` 每个 gate 的失败矩阵。

## 7. 与其他 skill 的协同

- **启动前**: `project-structure` skill 提供目录规范
- **完成后**: 建议执行 `project-audit` 或等价项目审计流程 — 必过 gate
- **完成后**: 将关键结论写入 `DECISION_LOG.md` 或项目交接文档
- **并行**: 若项目使用 Obsidian, 仅在用户授权后同步项目记忆或项目笔记
- **共存**: `bio-gwas-gwas-pipeline` / `snakemake-variant-pipeline` 等不冲突（职责互斥）

### 7.1 Bio-* Skill 触发优先级（Codex Eval Round 1 E 项修复）

当多个 bio-* skill 关键词同时出现时，按以下优先级：

| 场景 | 优先激活 | 拒绝激活 | 原因 |
|------|----------|----------|------|
| 用户有 **cohort VCF** + **极端表型样本** + 谈论 BSA/QTL-seq | ✅ `bio-bsa-qtlseq` | `bio-variant-calling-joint-calling` | BSA 起点是 cohort VCF, joint-calling 是生成 VCF |
| 用户需要**生成 cohort VCF**（从 GVCF/BAM） | ✅ `bio-variant-calling-joint-calling` | `bio-bsa-qtlseq` | BSA skill 不做 variant calling |
| 用户要 **GWAS 关联分析** | ✅ `bio-gwas-gwas-pipeline` | `bio-bsa-qtlseq` | BSA 是家系定位, GWAS 是群体关联, 方法不同 |
| 用户要 **FASTQ → VCF** 全流程 | ✅ `snakemake-variant-pipeline` | — | BSA skill 起点是 VCF |
| 用户要 **GO/KEGG 富集** | ✅ `bio-genome-annotation-functional-annotation` | `bio-bsa-qtlseq` | BSA skill 只提供 HOWTO, 不执行富集 |
| 用户 **多时间点 BSA 对比** | ✅ `bio-bsa-qtlseq` (--compare-timepoints) | — | 本 skill 独有功能 |

**关键判别词**:
- "BSA / QTL-seq / G' / 混池 / bulk segregant / F2 分离群体 / 极端表型定位 / 失水率 QTL / 抗旱 QTL" → 本 skill
- "joint genotype / GVCF combine / GenotypeGVCFs / 联合分型" → joint-calling skill
- "GWAS / 群体关联 / association test / PLINK / 全基因组关联" → gwas-pipeline skill

## 8. 审计继承

本 skill **编译**了以下审计发现（共 50 项，详见 `references/audit-source-index.md`）:

- Round 1 项目整体审计 (2026-04-16): 28 项 → 26 项 fixed → v2_fixed
- Round 2 交付包审计 (2026-04-17): 22 项 → 22 项 fixed → v2.1
- 共计 48/50 = **96% 修复率**（剩 2 项归入 follow-up task）

## 9. 快速上手（新项目 5 分钟）

```bash
# 1. 建项目目录
mkdir -p my-bsa-project && cd $_

# 2. 启动（交互模式会问 10 个关键问题）
/bsa-init

# 3. 等流水线跑完（约 45 min on 112-CPU server, 3 路并行 R）
# Gate 1 → Step 2 → Gate 2 → Step 5+6 → Gate 3 → 打包 → Gate 4

# 4. project-audit 或等价审计通过后 → release final
ls release/grape_BSA_*_release_v2.1.tar.gz
```

## 10. 版本

- **Skill version**: v2.1 (2026-04-18)
- **Pipeline version**: v2.1_fixed
- **Based on**: 葡萄 5h+3h BSA 项目两轮审计经验
- **Contract frozen**: 2026-04-18 (Team design debate 3 rounds)
