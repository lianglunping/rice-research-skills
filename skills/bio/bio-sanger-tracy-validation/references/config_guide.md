# Config Guide — Tracy Pipeline 新项目配置说明

## CONFIG 字典字段

```python
CONFIG = {
    # ---- 必填 ----
    "xlsx_path": "M1需要验证的InDel（含引物及扩增长度）.xlsx",  # 主变异信息 xlsx
    "ref_genome": "/path/to/reference.fa",                       # samtools faidx 已建索引
    "tracy_bin": str(Path.home() / "tracy_v0.8.9_macos_arm64"),  # ~/tracy_v0.8.9_macos_arm64

    # ---- 批次目录（按顺序追加）----
    "batches": [
        ("batch1",        "一代测序第一次验证/报告成功"),
        ("batch1_cancel", "一代测序第一次验证/报告取消"),
        # 每次新增：追加两行
    ],

    # ---- 可选参数（有默认值）----
    "flank_size": 500,            # 局部参考序列两端各取 N bp
    "pos_tolerance_base": 5,      # 坐标容许偏差基础值(bp)
    "pos_tolerance_scale": 2,     # 额外容许 = indel_len * scale
    "min_qual_pass": 30,          # T/high 质量阈值
    "min_qual_marginal": 10,      # T/medium 质量阈值
}
```

## 输入 xlsx 结构（"第一次检测" sheet）

| 列序 | 字段 | 说明 |
|------|------|------|
| 0 | name | 变异唯一编号，如 H31-5 |
| 1 | chrom | 染色体，如 Chr01 |
| 2 | pos | 1-based 基因组位置 |
| 5 | ref | 参考等位基因 |
| 6 | alt | 变异等位基因 |
| 9 | var_type | SNP/DEL/INS/COMPLEX |
| 10 | indel_len | INDEL净长度变化（正=插入，负=缺失，0=SNP） |
| 11 | carrier | 携带者样本 |
| 20 | gene | 基因名 |
| 23 | location | 精细位置分类 |

> 列序号可在 parse_variants() 中按实际 xlsx 调整。

## 人工判定 sheet（"人工判定" sheet）

| 列序 | 字段 | 说明 |
|------|------|------|
| 0 | name | 变异编号（与第一次检测一致）|
| 1 | human_result | 人工判定结果（T/F）|
| 2 | human_actual | 实际测序结果描述（可空）|

"人工确认真实" sheet：只有一列，每行为一个经人工确认为真实变异的 name。

## 追加新变异来源 xlsx

当有独立的新变异 xlsx 时，在 `parse_variants()` 末尾追加：

```python
EXTRA_XLSX_PATH = BASE_DIR / "新变异文件.xlsx"
if EXTRA_XLSX_PATH.exists():
    existing_names = {v["name"] for v in variants}
    wb2 = openpyxl.load_workbook(str(EXTRA_XLSX_PATH), read_only=True)
    ws2 = wb2["Data"]  # 替换为实际 sheet 名
    for row in ws2.iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        name = str(row[0]).strip()
        if name in existing_names:
            continue
        variants.append({
            "name": name,
            "chrom": str(row[1]).strip(),
            "pos": int(row[2]),
            "ref": str(row[5]).strip(),
            "alt": str(row[6]).strip(),
            "var_type": str(row[7]).strip() if row[7] else "",
            "indel_len": int(row[8]) if row[8] is not None else 0,
            "carrier": str(row[9]).strip() if row[9] else "",
            "gene": str(row[17]).strip() if row[17] else "",
            "location": str(row[18]).strip() if row[18] else "",
            "human_result": "",
            "human_actual": "",
            "human_confirmed": False,
        })
    wb2.close()
```

> 列序号需按实际文件调整。

## 输出目录结构

```
{project}/
├── scripts/
│   └── tracy_pipeline.py        # 本 pipeline
├── outputs/
│   ├── tracy_results/           # tracy JSON 缓存（不要删除）
│   ├── tracy_local_refs/        # 局部参考 FASTA 缓存
│   ├── tracy_validation_report.tsv
│   ├── m1_tracy_validation_report.xlsx
│   └── tracy_validation_summary.md
```

## tracy 安装

```bash
# macOS ARM64
curl -L https://github.com/gear-genomics/tracy/releases/download/v0.8.9/tracy_v0.8.9_macos_arm64.tar.gz | tar xz
mv tracy scripts/

# Linux x86_64
curl -L https://github.com/gear-genomics/tracy/releases/download/v0.8.9/tracy_v0.8.9_linux_x86_64.tar.gz | tar xz
```

参考基因组需预先建 samtools faidx 索引：
```bash
samtools faidx /path/to/ref.fa
```
