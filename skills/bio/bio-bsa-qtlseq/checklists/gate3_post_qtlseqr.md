# Gate 3 — Post-QTLseqr Checklist (分析后)

**触发时机**: 3 路并行 R (主 + w500k + rf035) 全部完成，`step7_annotate_v2.sh` 启动前
**失败类型**: DRAFT_LIMIT（preplanned 阈值空但允许 fallback）/ WARN（QC flag 写入 LIMITATIONS）
**依赖**: Gate 2 PASS + `results_v2/*.tsv` + `logs/step6_v2_*.DONE`

| # | 检查项 | 来源 ID | 失败动作 | 机器可判定 |
|---|--------|---------|----------|------------|
| 1 | filterSNPs retained 数写入 log (`grep 'filterSNPs retained'`) | audit1-m6 | ABORT_3 (脚本 bug) | ✓ |
| 2 | 4×3 敏感性矩阵完整（12 个 TSV 齐全，含空表头文件） | audit2-C3 | ABORT_3 | ✓ |
| 3 | preplanned 阈值结果（`Gprime q001` + `QTLseq ci99`） 区间数显式记录到 SUMMARY | audit2-C1 | DRAFT_LIMIT | ✓ |
| 4 | **若 Gprime q=0.01 AND QTLseq 99% CI 均为 0 且 `allow_fallback=true`** → 触发降档，强制生成 `state/fallback_rationale.md` | design-R2 盲点 #1 | 继续 + LIMITATIONS §2 | ✓ |
| 5 | Top QTL 方向统计 (+ΔSNP 比例 + −ΔSNP 比例) 计算并写入 SUMMARY | — | WARN if 异常偏斜（如 100% 单方向） | ✓ |
| 6 | 端粒区峰 flag: 每个区间检查 `posMaxGprime == chromend ± 100kb` | audit1-M5 | WARN + 写入 `interpretation_flags.md` | ✓ |
| 7 | 染色体级峰 flag: 区间长度 / 染色体长度 > 50% | audit1-M4 | WARN + 写入 `interpretation_flags.md` | ✓ |
| 8 | Tier 分级按 `meanQval` 实际计数（A<0.025 / B<0.035 / C≤0.05） | audit2-C1 | ABORT_3 if 脚本输出与实际不符 | ✓ |
| 9 | 每个 Top QTL 的候选基因数 = `bedtools intersect` 实测 unique 数（不估计） | audit2-C2 | ABORT_3 | ✓ |
| 10 | 3 套参数下 chr5 / chr3 / chr12 等主候选峰位 ±1Mb 一致 | — | WARN if 不一致（主候选不稳健）| ✓ |

## 自动执行

```bash
bash $SKILL_ROOT/scripts/gate3_check.sh analysis/results_v2/ analysis/logs/
# exit 0 = PASS
# exit 2 = ABORT_3 (脚本 bug, 需回到 Step 5+6)
# exit 3 = DRAFT_LIMIT (preplanned 阈值空, 触发 fallback)
# exit 4 = WARN (qc flag 写入 LIMITATIONS, 继续)
```

## Fallback Rationale 生成（盲点 #1）

若触发 #4 降档，必须生成：

```markdown
# state/fallback_rationale.md

## 降档触发
- 预设主阈值 `Gprime q=0.01`: **0 区间**
- 预设主阈值 `QTLseq 99% CI`: **0 区间**
- 配置 `pipeline.allow_fallback: true` → 启用降档

## 降档决策
- 主交付阈值: **Gprime q=0.05** (FDR 5%)
- 精细化阈值: **QTLseq 95% CI**

## 假阳性预期
- q=0.05 下预期假阳性数 ≈ N × 0.05 区间
- 客户报告中必须明示"候选信号, 非已定位 QTL"

## 建议客户下一步
- 扩群 ≥ 150 F2 做二次验证
- KASP 标记精细定位
- 单 QTL 效应量验证
```

## Interpretation Flags 生成

`interpretation_flags.md`（若 #6/#7 任一触发）:

```markdown
# 结果解读警示

## 端粒峰
以下 QTL 的 posMaxGprime 位于染色体端粒区 ±100kb:
- qtl16 (chr5:25,021,533) - chr5 端粒位置 25,021,533
  → 因果变异可能位于峰值左侧 1-5 Mb

## 染色体级峰
以下 QTL 占其染色体 > 50%, 可能是 stratification 而非真 QTL:
- qtl5 (chr11: 11.16 Mb / chr11 总长 19.82 Mb = 56%)
  → 建议从候选列表剔除
```

## 产出

```
state/
├── current_gate         # = "GATE_3"
├── gate3.PASS | gate3.DRAFT_LIMIT | gate3.WARN
├── fallback_rationale.md (若触发 #4)
└── interpretation_flags.md (若触发 #6 或 #7)
```

## 来源索引

- audit1-m6 (filterSNPs retained 未记录) → #1
- audit2-C3 (选择性汇报) → #2
- audit2-C1 (q=0.05 fallback 未声明) → #3-4
- design-R2 盲点 #1 (fallback rationale) → #4
- audit1-M5 (chr5 端粒伪峰) → #6
- audit1-M4 (chr11 染色体级) → #7
- audit2-C1 (Tier 分级错) → #8
- audit2-C2 (基因数估计值偏差) → #9

## 下一步

**PASS** → step7_annotate → 打包 release DRAFT
**DRAFT_LIMIT** → 同上 + LIMITATIONS 必须含 fallback 章节
**WARN** → 同上 + LIMITATIONS 必须含 interpretation_flags 内容
**ABORT_3** → 检查 R 脚本版本，必要时回 Step 5
