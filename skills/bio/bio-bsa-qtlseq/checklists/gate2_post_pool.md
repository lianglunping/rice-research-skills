# Gate 2 — Post-Pool Checklist (亲本过滤+按池合并后)

**触发时机**: `parent_filter_and_pool_v2.py` 完成后，`gatk VariantsToTable` 启动前
**失败类型**: ABORT_2（数据质量根本问题）或 WARN（记入 LIMITATIONS）
**依赖**: Gate 1 PASS + `pooled_v2.raw.vcf.gz` 已生成 + `logs/step34_v2.log` 存在

| # | 检查项 | 来源 ID | 失败动作 | 机器可判定 |
|---|--------|---------|----------|------------|
| 1 | `[CHECK] 统计闭环通过` 出现在 step34_v2.log | audit1-C02 | ABORT_2（闭环断 = 脚本 bug） | ✓ |
| 2 | kept SNP 数 ≥ 1,000,000（经验阈值）| — | ABORT_2 if <1e6, WARN if <2e6 | ✓ |
| 3 | kept / in 比例在 [0.05, 0.50] | — | WARN（过低 → 过滤过严；过高 → 亲本分辨率不足）| ✓ |
| 4 | polarized / kept 比例在 [0.05, 0.95] | DEC-015 | WARN（极端比率提示参考基因组偏好：如 0 或 1）| ✓ |
| 5 | parent_half_call 计数 ≤ kept 数 | audit2-C01 | WARN（亲本 GT 质量差）| ✓ |
| 6 | `pooled_v2.raw.vcf.gz` 含 HighBulk + LowBulk 两样本（`bcftools query -l`）| — | ABORT_2 | ✓ |
| 7 | VCF 中 `VA_HOM` + `POLARIZED` INFO 字段存在 | DEC-015 | ABORT_2（脚本版本错）| ✓ |
| 8 | Pool DP 一致性: 抽样 1000 位点验证 `DP == AD_REF + AD_ALT` | DEC-014 | ABORT_2（v2 一致性修复未生效）| ✓ |
| 9 | 染色体分布覆盖 chrom_list 的 ≥ 90% | — | WARN（部分染色体无变异 = 可能 VCF 残缺）| ✓ |

## 自动执行

```bash
# 在 orchestrator_v2.sh 的 Step B 完成后自动跑
bash $SKILL_ROOT/scripts/gate2_check.sh analysis/logs/step34_v2.log analysis/pooled_v2.raw.vcf.gz
# exit 0 = PASS; 2 = ABORT_2; 3 = WARN (继续但写 LIMITATIONS)
```

## 典型 WARN 场景处理

| 场景 | 观察 | LIMITATIONS 记录建议 |
|------|------|---------------------|
| kept < 2e6 | 亲本过滤过严或亲本 VCF 质量差 | §3.4 亲本 GT 判定严格导致位点损失 |
| polarized ≈ 0 | Va 在参考基因组上几乎全是 REF | 参考基因组选择偏好说明 |
| polarized ≈ 1 | Va 在参考基因组上几乎全是 ALT（本项目 87.9%） | 需在 §3.3 说明 Va 血统与参考品种的差异 |
| parent_half_call 大 | 亲本测序深度 / call rate 不足 | §3.4 建议亲本重测序 |

## 产出

```
state/
├── current_gate         # = "GATE_2"
├── gate2.PASS | gate2.WARN | gate2.FAIL
└── gate2_report.md      # 含 [STATS] 表格 + WARN 详情
```

## 来源索引

- audit1-C02 (parent_skip 混合计数, 已拆分为 4 分类) → #1
- audit2-C01 (half-call 严格元组匹配) → #5
- DEC-014 (Pool DP = sum(AD)) → #8
- DEC-015 (re-polarize 方向 bug 修复) → #4, #7
- audit1 亲本纯合差异 (3,653,444 位点) → #2 经验阈值

## 下一步

**PASS / WARN** → Step 5 (GATK VariantsToTable + orchestrator Step C)
**FAIL (ABORT_2)** → 回 Gate 1 检查配置或联系开发者（脚本 bug）
