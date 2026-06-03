---
template: lite
status: verified
created_at: 2026-04-30
sealed_at: null
owner: example_user
project: example_project

extension_sections: []

verification:
  remote_command_timeout_sec: 300
  fail_closed_on_missing_meta: true
  fail_closed_on_broken_yaml: true
---

# Example One-Off Analysis — Lite Provenance

**所有者**: example_user | **项目**: example_project | **创建**: 2026-04-30

---

## 0. 状态与范围

- **当前状态**: `verified`
- **任务目标**: Compute per-category summary statistics for a filtered output
  table and verify that the totals match the primary pipeline artifact.
- **目录**: `analysis/category-summary/`
- **负责人**: example_user
- **适用边界**: Covers only the summary aggregation step. Upstream filtering
  is covered by `archive/legacy_results/v1.0/provenance.md`.

---

## 1. 输入与假设

### 1.1 输入
- `pipelines/example-pipeline/runs/20260430_v1.0/results/filtered_output.tsv` — primary filtered table (182 records)
- `config/summary_config.yaml` — column mapping and grouping keys

### 1.2 关键假设
1. Filtered table is complete and not modified after pipeline run.
2. Category labels in the input are exhaustive — no unlabeled records.
3. Summary statistics are computed without any additional filtering.

### 1.3 已知缺口
- Confidence intervals not computed in this analysis (deferred to next iteration).
- No cross-category significance testing performed.

---

## 2. 代码路径、模块结构与运行环境

### 2.1 代码 root
- repo: `https://github.com/example_user/example_project`
- commit: `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2`
- 本地: `analysis/category-summary/`

### 2.2 关键脚本/模块树
```
analysis/category-summary/
├── src/
│   └── summarize.py
└── config/
    └── summary_config.yaml
```

### 2.3 入口函数
| 入口 | 路径 | 描述 |
|-----|------|------|
| main | `src/summarize.py` | Read filtered table, group by category, output summary TSV |

### 2.4 软件版本（最关键 5–10 个）
| 软件 | 版本 |
|-----|------|
| Python | 3.11.9 |
| pandas | 2.2.1 |

### 2.5 Config 链接
- `config/summary_config.yaml`

---

## 3. 使用方法与复现步骤

### 3.1 最小复现命令
```bash
uv run analysis/category-summary/src/summarize.py \
    --config analysis/category-summary/config/summary_config.yaml \
    --input pipelines/example-pipeline/runs/20260430_v1.0/results/filtered_output.tsv \
    --output analysis/category-summary/results/category_summary.tsv
```

### 3.2 参数
- `group_col` = `category` (column used for grouping)
- `value_col` = `quality` (column aggregated with mean/median)

### 3.3 随机种子
seed = N/A — deterministic aggregation, no sampling

### 3.4 预期输出路径
```
analysis/category-summary/results/
└── category_summary.tsv
```

### 3.5 运行注意事项
No GPU or special hardware required. Runs in under 5 seconds on any modern laptop.

---

## 4. 输出产物与已验证论断

### 4.1 产物表
| artifact_id | path | format | size | record_count | checksum |
|-------------|------|--------|-----:|-------------:|----------|
| category_summary | `analysis/category-summary/results/category_summary.tsv` | TSV | 256 | 3 | `c3d4e5f6a1b2` |

### 4.2 论断验证表（合并版）
| claim_id | claim_text | value | command | observed_result | status |
|----------|-----------|-------|---------|-----------------|--------|
| c01 | Summary table has 3 rows (one per category) | 3 | `wc -l < analysis/category-summary/results/category_summary.tsv` | 3 | verified |
| c02 | Total record count across categories equals 182 | 182 | `python3 -c "import pandas as pd; df=pd.read_csv('analysis/category-summary/results/category_summary.tsv', sep='\t'); print(int(df['count'].sum()))"` | 182 | verified |

---

## 5. 关联、变更与限制

### 5.1 关联文档
- primary pipeline: `pipelines/example-pipeline/runs/20260430_v1.0/provenance.md`
- config: `analysis/category-summary/config/summary_config.yaml`

### 5.2 变更摘要
Initial creation. Triggered by request to verify category breakdown
independently of the main pipeline provenance document.

### 5.3 已知限制 / TODO
- [ ] Add confidence intervals for mean quality by category (deferred to next analysis iteration)
- [ ] Check for label encoding consistency across pipeline versions
