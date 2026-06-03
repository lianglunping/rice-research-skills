---
name: bio-sanger-tracy-validation
description: This skill should be used when the user asks to "分析一代测序结果", "Sanger测序验证", "解读ab1文件", "tracy decompose", "更新验证报告", "新增一批测序结果", or needs to validate genomic variants using Sanger sequencing ab1 files. Handles pipeline setup for new projects and batch updates for ongoing validation campaigns.
tags: [Bioinformatics, Sanger, Tracy, Validation]
---

# Bio Sanger Tracy Validation

使用 `tracy decompose` 对 Sanger 测序 ab1 文件进行 INDEL 验证，输出 TSV/XLSX 综合报告。

## 核心工具

- **tracy decompose**: Sanger 测序 ab1 文件解峰，调用命令：
  ```bash
  tracy decompose -r {local_ref.fa} -v -o {output_prefix} {sample.ab1}
  ```
- **samtools faidx**: 从参考基因组提取局部参考序列（±500bp）
- **openpyxl**: 读取变异 xlsx、写入验证报告

## 判定逻辑（5步）

1. **目标匹配**: tracy JSON `variants[]` 中找到类型一致、位置偏差≤`pos_tolerance`（基础5bp + indel_len×2）的 INDEL
2. **单次判定** (`judge_single_ab1`):
   - 找到目标: PASS+qual≥30→T/high；PASS+qual≥10→T/medium；否则→T?/low
   - 近似匹配(长度差1bp): 最高T?/medium
   - 未找到但有其他INDEL: F?/low
   - 无任何INDEL: F/high(af1>0.85)或F/medium
   - tracy 失败: R/low
3. **综合判定** (`combine_calls`): 多批次多方向择优，"报告成功"批次优先，"报告取消"仅在无成功数据时启用
4. **输出**: TSV + XLSX（含各批次各方向详情列）+ MD 摘要
5. **特殊处理**: 簇状变异可额外运行 `update_clustered_variants.py`（项目特定）

## 工作流

### 场景A: 新项目初始化

1. 复制 `references/pipeline_template.py` 到项目运行脚本 scripts/tracy_pipeline.py
2. 按 `references/config_guide.md` 填写文件顶部 `CONFIG` 字典
3. 准备输入 xlsx（变异信息+人工判定，见 config_guide.md 列定义）
4. 运行项目中的 tracy_pipeline.py

### 场景B: 新增一批测序结果

1. 确认新 ab1 文件目录结构（见 `references/ab1_naming_convention.md`）
2. 在 `BATCH_DIRS` 末尾追加两行（成功/取消）
3. 在 `integrate_results` 循环中追加新 batch tag
4. 在 `OUTPUT_COLUMNS` 追加 14 列（F+R 各7列）
5. 若有新变异来源 xlsx，在 `parse_variants()` 末尾追加读取逻辑
6. 重新运行 pipeline（已处理 ab1 自动使用 JSON 缓存，仅新文件重新运行）
7. 若项目有簇状变异放宽判定，重新运行 `update_clustered_variants.py`

### 场景C: 每次新增的标准 4 处代码修改

```python
# 1. BATCH_DIRS 末尾追加
("batchN",        BASE_DIR / "一代测序第N次验证" / "报告成功"),
("batchN_cancel", BASE_DIR / "一代测序第N次验证" / "报告取消"),

# 2. integrate_results 主批次循环 (main_calls)
for batch_tag in ["batch1", ..., "batchN"]:

# 3. integrate_results cancel 循环
for batch_tag in ["batch1_cancel", ..., "batchN_cancel"]:

# 4. OUTPUT_COLUMNS 末尾、human 列之前追加
"batchN_F_call", "batchN_F_conf", "batchN_F_qual",
"batchN_F_hetindel", "batchN_F_af1", "batchN_F_af2", "batchN_F_notes",
"batchN_R_call", "batchN_R_conf", "batchN_R_qual",
"batchN_R_hetindel", "batchN_R_af1", "batchN_R_af2", "batchN_R_notes",
```

## 关键边界

- 只处理 **INDEL**（DEL/INS），不处理 SNP（tracy decompose 专为 indel 设计）
- 簇状变异放宽判定（检出任意 INDEL 即为真）是**项目特定逻辑**，写在独立脚本中
- VCF 左对齐导致的位置/序列表示差异由 `is_equivalent_indel()` 处理（只比对类型+净长度）
- ab1 命名格式见 `references/ab1_naming_convention.md`，方向解析依赖文件名第二字段

## 参考资料

- `references/pipeline_template.py` — 完整泛化 pipeline（新项目直接复制使用）
- `references/config_guide.md` — CONFIG 字典填写说明及输入 xlsx 列定义
- `references/ab1_naming_convention.md` — ab1 文件命名规则与方向解析逻辑
