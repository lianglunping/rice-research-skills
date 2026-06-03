# Gate 1 — Preflight Checklist (启动前)

**触发时机**: `/bsa-init` 解析完 config 之后，Step 2 (bcftools subset) 启动前
**失败类型**: ABORT（输入/合同错误直接中断）
**依赖**: `merged_config.yaml` 已通过 `validate_config.py` 校验

| # | 检查项 | 来源 ID | 失败动作 | 自动核查 |
|---|--------|---------|----------|---------|
| 1 | `merged_config.yaml` 通过 `bsa-config.schema.json` 校验 | release-M8 | ABORT | `validate_config.py` exit==0 |
| 2 | 参考基因组 .fa + .fai + .dict 就绪（若 .fai/.dict 不存在则 auto-build + 记录 `state/autobuild_log.txt`） | project-structure + 盲点 #3 | auto-build (记录命令) | `samtools faidx` + `gatk CreateSequenceDictionary` |
| 3 | `samples.tsv` 所有 sample_id 在 cohort VCF 中（`bcftools query -l` 核对） | audit1-D03 | ABORT with diff | `grep -vFxf cohort_samples.txt samples.tsv` 应为空 |
| 4 | 亲本 DP 在 cohort VCF 中 ≥ `min_parent_dp`（默认 5, 抽样 1000 位点） | audit1-DEC-011 | WARN → LIMITATIONS | 抽样 `bcftools query` |
| 5 | 极端池 n per bulk 声明 ≥ `bulk_size[i]`（样本数量一致性） | — | ABORT if mismatch | count samples.tsv vs config |
| 6 | `phenotype.phenotype_value_column` 或 `phenotype_rank_column` 至少一列在 samples.tsv 中存在且有非 NA 值 | release-M10 | ABORT | csv header 检查 |
| 7 | `runtime.conda_env` 已装且含 QTLseqr at locked version (0.7.5.2) | codex-1 盲点 #1 | ABORT with install 指令 | `Rscript -e 'packageVersion("QTLseqr")'` |
| 8 | `output.formats` 含 `pdf` 和 `png` 两者 | R2-B3 | ABORT | YAML 字段检查 |
| 9 | bulk_size 警告：min(bulk_size) < 20 时自动写入 LIMITATIONS 小样本风险 | audit1-C2 | WARN（不阻塞） | 数值判断 |
| 10 | 可选: 多时间点配置一致性（若 `--compare-timepoints` 则校验两组 config 的 species + reference + parents 一致） | bio-bsa-method §4 | ABORT | diff config |

## 自动执行

```bash
bash $SKILL_ROOT/scripts/gate1_check.sh \
    --config merged_config.yaml \
    --samples metadata/samples.tsv \
    --cohort-vcf <cohort_vcf_path> \
    --state-dir state/
# exit 0 = PASS
# exit 1 = ABORT (任一 abort 项失败)
# exit 2 = WARN (继续, 记 LIMITATIONS)
```

## 产出

```
state/
├── current_gate                    # = "GATE_1"
├── gate1.PASS | gate1.WARN | gate1.FAIL
├── gate1_report.md                 # 10 项检查结果 + WARN 内容
└── autobuild_log.txt               # 若 #2 触发 auto-build, 记录命令与输出路径
```

## 来源索引

- audit1-D03 (样本数文档漂移) → #3
- audit1-DEC-011 (亲本 DP) → #4
- audit1-C2 (n=20 统计力) → #9
- audit2-M8 (缺 environment.yml) → #7
- audit2-M10 (samples.tsv 缺 phenotype_value) → #6
- release-M8 (schema 自校验) → #1
- 设计 R2 盲点 #3 (Gate 1 auto-build 记录) → #2
- R2-B3 (PDF+PNG) → #8

## 下一步

**PASS** → Step 2 bcftools subset
**WARN** → 同上, 但小样本风险已登记
**ABORT** → 用户修复 config 或样本列表后 `/bsa-init --resume-from gate1`
