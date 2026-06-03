# Output Contract — Release v2.x 交付物规格

本文档定义 `/bsa-init` 产出的 release 结构、必需文件、数字精度、图形规格、字段字典。所有交付物必须符合本 contract，否则 Gate 4 拒绝。

## 1. Release 目录结构（必需）

```
release/
├── 00_README.md                         # 项目入口 + 结果速览 + 立即可做
├── 01_METHODS.md                        # 方法学 + 参数 + 流程图 + 复现命令
├── 02_LIMITATIONS.md                    # 6 大局限（必含）
├── 03_COLUMN_DEFINITIONS.md             # TSV 列字典
├── HOWTO_GO_KEGG.md                     # 下游富集 3 方案指南
├── Top_QTL_annotated.md                 # Top 6 精细化 + Top 10 Gprime + Tier
├── VERSION                              # 版本标识
├── CHANGELOG.md                         # 版本修订记录
├── MANIFEST.md5                         # MD5 校验（含头注释，不含自身）
├── MANIFEST.sha256                      # SHA256 校验
├── results/
│   ├── main/                             # 主分析 (window=1Mb, refAF=0.20)
│   │   ├── Gprime_q005_regions.tsv       (fallback 主交付, 若 preplanned 空)
│   │   ├── Gprime_q005_regions_candidate_genes.tsv
│   │   ├── QTLseq_ci95_regions.tsv       (fallback 精细化)
│   │   ├── QTLseq_ci95_regions_candidate_genes.tsv
│   │   ├── Gprime_q001_regions.tsv       (preplanned, 可能空)
│   │   ├── QTLseq_ci99_regions.tsv       (preplanned, 可能空)
│   │   └── SUMMARY_v2.md
│   └── sensitivity/
│       ├── window_500kb/
│       │   ├── README.md                  # 目录级说明（必需）
│       │   └── *_w500k*.tsv
│       └── refAF_035/
│           ├── README.md
│           └── *_rf035*.tsv
├── figures/
│   ├── README.md                         # 14 PDF + 14 PNG 解读指南
│   ├── 00_diagnostic.{pdf,png}           # 2 格式对
│   ├── 01_Gprime_manhattan.{pdf,png}
│   ├── 02_negLog10Pval_manhattan.{pdf,png}
│   ├── 03_deltaSNP_manhattan.{pdf,png}
│   ├── 04_nSNPs_per_window.{pdf,png}
│   ├── (同上 5 对 × 2 敏感性 = +10 对)
│   └── ...
├── scripts/
│   ├── parent_filter_and_pool_v2.py      # 与运行时相同版本
│   ├── qtlseqr_analysis_v2.R
│   ├── orchestrator_v2.sh
│   └── step7_annotate_v2.sh
└── metadata/
    ├── samples.tsv                        # 必含 phenotype_value 或 rank
    ├── phenotype_source.meta.yaml         # 从客户原始 xlsx meta 复制
    ├── parameters.yaml                    # 完整参数（审计后实际使用值）
    ├── software_versions.txt              # 工具 + 版本锁定
    └── environment.yml                    # conda 一键重建
```

## 2. 必需文件清单（Gate 4 Check 7）

共 **14 个文件 + 目录**（忽略 README 和 figures 子内容）:
1. 00_README.md
2. 01_METHODS.md
3. 02_LIMITATIONS.md
4. 03_COLUMN_DEFINITIONS.md
5. HOWTO_GO_KEGG.md
6. Top_QTL_annotated.md
7. VERSION
8. CHANGELOG.md
9. MANIFEST.md5
10. MANIFEST.sha256
11. results/main/SUMMARY_v2.md
12. results/sensitivity/window_500kb/README.md
13. results/sensitivity/refAF_035/README.md
14. figures/README.md

## 3. TSV 列字典（核心）

### Gprime_qXXX_regions.tsv (17 列)

| 列 | 类型 | 说明 |
|----|------|------|
| CHROM | str | 染色体 ID |
| qtl | int | 内部编号（非排名） |
| start/end | int | 区间 1-based 闭区间 |
| length | int | end - start |
| nSNPs | int | 区间内参与 G' 的 SNP 数 |
| avgSNPs_Mb | int | SNP 密度 |
| peakDeltaSNP | float | 区间最大 |ΔSNP|（带符号） |
| posPeakDeltaSNP | int | peakDeltaSNP 位置 |
| avgDeltaSNP | float | 区间均值 |
| maxGprime | float | 区间 G' 最大 |
| posMaxGprime | int | maxGprime 位置（可能 ≠ posPeakDeltaSNP） |
| meanGprime / sdGprime | float | 区间 G' 均值 / SD |
| AUCaT | float | Area Under Curve above Threshold |
| meanPval | float | permutation p 均值 |
| meanQval | float | BH FDR 均值（用于 Tier 分级） |

### QTLseq_ciXX_regions.tsv (10 列)

比 Gprime 少 7 列（无 Gprime/pval/qval）。

### *_regions_candidate_genes.tsv (8 列, 无表头, bedtools intersect -wa -wb)

| 列号 | 含义 |
|------|------|
| 1 | region_chr |
| 2-3 | region_start/end (BED 0-based) |
| 4 | region_label: `qtl{N}_{stats}` |
| 5 | gene_chr |
| 6-7 | gene_start/end |
| 8 | gene_id（客户需去掉 `.v2.1` 后缀做下游分析） |

## 4. 图形规格（Codex R2 Top5）

```yaml
figures:
  formats: [pdf, png]                    # 强制双格式
  png_dpi: 600                            # ≥600
  pdf_font_embed: true
  figure_pair_check: true                 # Gate 4 核验
  naming: "{NN:02d}_{figtype}[_{sensitivity_suffix}].{ext}"
  required_panels:
    - diagnostic_5page                    # DP / REF_FRQ / SNPindex_H / SNPindex_L / DP_hex
    - Gprime_manhattan                     # plotQTLStats var=Gprime
    - negLog10Pval_manhattan               # plotQTLStats var=negLog10Pval
    - deltaSNP_manhattan                   # plotQTLStats var=deltaSNP + 95/99 CI
    - nSNPs_per_window                     # plotQTLStats var=nSNPs
```

### 阈值线绘制规则（审计发现）

QTLseqr `plotQTLStats(plotThreshold=TRUE, q=0.01)` **仅在至少一个 window meanQval<0.01 时才绘制虚线**。本项目主分析 + rf035 常无阈值线（q001=0），需在 `figures/README.md` 明确。

## 5. Manifest 规格

### MANIFEST.md5

```
# MANIFEST.md5 — 本文件不含自身
# Generated: YYYY-MM-DD HH:MM
# Version: v2.1
#
<md5sum>  ./path/to/file
...
```

### MANIFEST.sha256

同上结构，用 `sha256sum` 生成。

## 6. 版本命名

- `v2.x-draft`: Gate 4 进行中
- `v2.x-final`: project-audit 或等价审计通过 + P0 清 0
- tarball: `<project_id>_release_v<ver>-<draft|final>.tar.gz`

## 7. 数字精度（Gate 4 重算核验）

以下数字必须由 TSV 机器重算后与文档声明一致：

| 数字 | 声明位置 | 重算命令 |
|------|----------|---------|
| Gprime q=0.05 区间数 | 00_README, Top_QTL | `tail -n +2 Gprime_q005_regions.tsv \| wc -l` |
| QTLseq 95% CI 区间数 | 00_README, Top_QTL | `tail -n +2 QTLseq_ci95_regions.tsv \| wc -l` |
| Top 6 QTL 每区间基因数 | Top_QTL | `cut -f4 *_candidate_genes.tsv \| sort \| uniq -c` |
| Tier A (meanQval<0.025) 数量 | Top_QTL | `awk -F'\t' 'NR>1 && $17<0.025' \| wc -l` |
| 候选基因总数 (unique) | 00_README, SUMMARY | `cut -f8 *_candidate_genes.tsv \| sort -u \| wc -l` |
| 4×3 敏感性矩阵 12 个数字 | SUMMARY | 对应 12 个 TSV 行数 |

## 8. 禁止模式（Gate 4 grep）

| 违规 | grep 命令 |
|------|-----------|
| 内部服务器路径 | `grep -rn '/home/[a-z0-9]*/' release/` |
| SSH 别名 | `grep -rn 'sxyH3\|[a-z]*H[0-9]:' release/` |
| hardcoded conda env | `grep -rn 'conda activate ngs' release/` |
| emoji ✅ 于结果文档（误导性） | `grep -rn '✅' release/0[0-9]_*.md` |
