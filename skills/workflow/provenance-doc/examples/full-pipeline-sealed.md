---
template: full
status: verified
version: v1.0
created_at: 2026-04-30
sealed_at: null
owner: example_user
project: example_project
prior_version: null
delta_summary_path: null

extension_sections:

  - id: domain_stat_a
    title: "Domain Stat A"
    source: _extensions/domain_stat_a.md
    status: verified
    waiver_reason: ""

  - id: domain_stat_b
    title: "Domain Stat B"
    source: _extensions/domain_stat_b.md
    status: verified
    waiver_reason: ""

  - id: domain_cohort
    title: "Domain Cohort"
    source: _extensions/domain_cohort.md
    status: verified
    waiver_reason: ""


verification:
  remote_command_timeout_sec: 300
  fail_closed_on_missing_meta: true
  fail_closed_on_broken_yaml: true
---

# Example Pipeline — Full Provenance v1.0

**版本**: v1.0
**生成日期**: 2026-04-30
**所有者**: example_user
**项目**: example_project

---

## 0. 文档身份与范围

### 0.1 分析目标
Apply a multi-step quality filter to a cohort of input records, produce a
filtered output table, and verify that the record count and quality metrics
match pre-specified thresholds. This is the first versioned release of the
pipeline (v1.0).

### 0.2 数据 cohort
- Sample count: 200 individuals
- Data type: tabular, two-column paired format (left / right replicates)
- Key attributes: each record has a unique ID and a numeric quality score

### 0.3 纳入与排除标准
- **Inclusion**: records with quality score ≥ 20 in at least one replicate
- **Exclusion**: records flagged with `low_coverage` in the input manifest
- Full parameter details: `config/pipeline_v1.0.yaml`

### 0.4 已知 caveats 与解读限制
- Replicate concordance not formally tested in v1.0; see `audit_concordance_20260430.md`
- Quality threshold chosen empirically; sensitivity analysis deferred to v2.0

---

## 1. 工作流概述

### 1.1 处理流程
```
Input records (raw_input.tsv)
    → quality_filter.py   (quality score ≥ threshold)
    → dedup.py            (remove duplicate IDs)
    → annotate.py         (add category labels)
    → filtered_output.tsv
```

### 1.2 输入登记
| 数据类型 | 路径 | 用途 |
|---------|-----|------|
| Raw table | `data/raw_input.tsv` | Primary input; 200 records |
| Manifest | `data/manifest.tsv` | Coverage flags per record |
| Config | `config/pipeline_v1.0.yaml` | All threshold parameters |

### 1.3 输出登记（高层）
详见 §4 产物登记表。

---

## 2. 代码、软件与版本登记

### 2.1 代码 root
| 项 | 值 |
|----|----|
| repo URL | `https://github.com/example_user/example_project` |
| commit SHA | `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2` |
| branch | `main` |
| 本地路径 | `pipelines/example-pipeline/` |

### 2.2 模块树（前 3 层目录）
```
pipelines/example-pipeline/
├── config/
│   └── pipeline_v1.0.yaml
├── src/
│   ├── quality_filter.py
│   ├── dedup.py
│   └── annotate.py
└── runs/
    └── 20260430_v1.0/
        ├── run_config.yaml
        └── results/
```

### 2.3 入口脚本
| 入口 | 路径 | 描述 |
|-----|------|------|
| quality_filter | `src/quality_filter.py` | Apply quality threshold; output filtered records |
| dedup | `src/dedup.py` | Remove duplicate IDs; log removed count |
| annotate | `src/annotate.py` | Attach category label from reference lookup table |

### 2.4 依赖软件 + 版本号
| 软件 | 版本 | 安装方式 |
|-----|------|---------|
| Python | 3.11.9 | uv |
| pandas | 2.2.1 | uv |
| pyyaml | 6.0.1 | uv |

### 2.5 Config 文件链接
- `config/pipeline_v1.0.yaml` — main pipeline parameters

---

## 3. 复现指南

### 3.1 最小复现命令
```bash
uv run src/quality_filter.py --config config/pipeline_v1.0.yaml \
    --input data/raw_input.tsv --output runs/20260430_v1.0/results/filtered_output.tsv
```

### 3.2 关键参数
| 参数 | 值 | 说明 |
|-----|---|------|
| `quality_threshold` | 20 | Minimum quality score to retain a record |
| `allow_single_replicate` | true | Retain record if only one replicate passes |
| `dedup_key` | `record_id` | Column used as deduplication key |

### 3.3 随机种子
seed = N/A — deterministic pipeline (no random sampling)

### 3.4 预期输出路径
```
runs/20260430_v1.0/results/
├── filtered_output.tsv
└── filter_summary.txt
```

### 3.5 运行环境提示
- Minimum 4 GB RAM
- OS: Linux or macOS
- No GPU required

---

## 4. 产物登记表

> 本表由 `aggregate_meta.py` 从 sibling `*.meta.yaml` 或 `runs_manifest.yaml` 自动聚合。请勿手工修改 `checksum/size/record_count` 字段。

| artifact_id | role | path | format | size | record_count | checksum | created_at | producer | meta_yaml |
|-------------|------|------|--------|-----:|-------------:|----------|-----------:|----------|-----------|
| filtered_output | primary | `runs/20260430_v1.0/results/filtered_output.tsv` | TSV | 48200 | 182 | `a1b2c3d4e5f6` | 2026-04-30 | annotate.py | `filtered_output.tsv.meta.yaml` |
| filter_summary | diagnostic | `runs/20260430_v1.0/results/filter_summary.txt` | TXT | 512 | 4 | `b2c3d4e5f6a1` | 2026-04-30 | quality_filter.py | `filter_summary.txt.meta.yaml` |

---

## 5. 论断验证册

> 每行一个 claim。`status` ∈ {verified, unverified, waived}。`waiver_reason` 在 status=waived 时必填且长度 ≥10。

| claim_id | claim_text | value | source_artifact | command | observed_result | status | waiver_reason |
|----------|-----------|-------|-----------------|---------|-----------------|--------|---------------|
| c01 | Filtered output contains 182 records | 182 | filtered_output | `wc -l < runs/20260430_v1.0/results/filtered_output.tsv` | 182 | verified | |
| c02 | All retained records have quality score ≥ 20 | 20 | filtered_output | `python3 -c "import pandas as pd; df=pd.read_csv('runs/20260430_v1.0/results/filtered_output.tsv', sep='\t'); print(int((df['quality']>=20).all()))"` | 1 | verified | |

---

## 6. 决策准则与参数

### 6.1 参数来源文件
- `config/pipeline_v1.0.yaml` — all threshold and flag parameters

### 6.2 解读关键参数（≤30% 全字段）
| 参数 | 值 | 影响 |
|-----|---|------|
| `quality_threshold` | 20 | Directly determines how many records are retained |
| `allow_single_replicate` | true | Without this, ~15% fewer records would pass |

### 6.3 纳入排除规则
Records must pass quality threshold in at least one replicate AND not appear
in the `low_coverage` flag list in `data/manifest.tsv`.

### 6.4 与上版参数差异
*(v1.0 is initial version — no prior version)*

---

## 7. 版本谱系

### 7.1 时间线
| 版本 | 日期 | 关键变更 |
|-----|------|---------|
| v1.0 | 2026-04-30 | Initial release |

### 7.2 与上一封版差异（摘要）
Initial version. No prior version exists. See `DECISION_LOG.md` for rationale
on threshold selection.

---

## 8. 封版差异对比表

| 指标 | 上版值 | 本版值 | 差值 | 变化原因 |
|-----|-------|-------|------|---------|
| record_count | N/A | 182 | N/A | Initial version |
| pass_rate | N/A | 91% | N/A | Initial version |

---

## 9. 路径可达性图

### 9.1 本地路径
- `data/raw_input.tsv` — exists (source data)
- `runs/20260430_v1.0/results/filtered_output.tsv` — exists (primary output)
- `config/pipeline_v1.0.yaml` — exists (config)

### 9.2 服务器路径
*(no remote paths; all data local)*

---


## 业务统计扩展


### Domain Stat A

> Source: `_extensions/domain_stat_a.md` (status: verified)

| metric | value |
|--------|-------|
| Category A count | 98 |
| Category B count | 57 |
| Category C count | 27 |
| Total | 182 |




### Domain Stat B

> Source: `_extensions/domain_stat_b.md` (status: verified)

| metric | value |
|--------|-------|
| Mean quality score | 34.2 |
| Median quality score | 31.0 |
| Min retained score | 20 |
| Max retained score | 60 |




### Domain Cohort

> Source: `_extensions/domain_cohort.md` (status: verified)

| metric | value |
|--------|-------|
| Total input records | 200 |
| Passed filter | 182 |
| Excluded (low coverage) | 9 |
| Excluded (below threshold) | 9 |
