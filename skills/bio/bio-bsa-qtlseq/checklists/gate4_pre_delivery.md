# Gate 4 — Pre-Delivery Checklist (交付前)

**触发时机**: `release_packager.sh` 生成 DRAFT release 目录后，打 tar.gz 前
**失败类型**: FIX_LOOP（机器项失败自动重试 3 次）/ 阻塞 final（`project-audit` 人工项）
**依赖**: Gate 3 PASS + `release/` 目录存在

## 机器可判定项（7 个）— 由 `pre_delivery_check.sh` 自动

| # | 检查项 | 来源 ID | 失败动作 |
|---|--------|---------|----------|
| 1 | `MANIFEST.md5` 覆盖所有 release 文件（除自身） | audit2-S1 | FIX_LOOP: 重新生成 |
| 2 | 无内部路径残留: `grep -rn 'sxyH3\|/home/[a-z0-9]*/\|conda activate ngs'` = 0 | audit2-M5 | FIX_LOOP: sed 替换 + 警告 |
| 3 | README 关键数字可由 TSV 重算（Gprime q005 区间数, QTLseq ci95 区间数, 候选基因总数） | codex-1 盲点 #4 | FIX_LOOP: 重写 README |
| 4 | Tier 分级声明与实际 `meanQval` 一致（A < 0.025 = N 个） | audit2-C1 | FIX_LOOP: 重写 Tier 段 |
| 5 | Top QTL 基因数 = `uniq -c` 实测 unique 数 | audit2-C2 | FIX_LOOP: 重写 Top QTL 表 |
| 6 | SUMMARY 含 4×3 完整矩阵（12 个数字） | audit2-C3 | FIX_LOOP: 重跑 step7_annotate |
| 7 | 必需文件存在（6 MD + 4 scripts + 4 metadata + figures 齐全）+ PDF/PNG 成对 | audit2 结构 + R2-B3 | FIX_LOOP: 补缺失文件 |
| 8 | QTLseqr 版本锁定（software_versions.txt 含 `0.7.5.2`） | codex-1 盲点 #1 | FIX_LOOP: 重写 version file |
| 9 | SHA256 manifest 存在且校验通过（`sha256sum -c MANIFEST.sha256`） | R2-B3 | FIX_LOOP: 重生 |
| 10 | 无 `x-doc-only` 字段被脚本代码依赖（`gene_id_prefix` 仅在 docs/ 中出现） | 盲点 #2 | FIX_LOOP: 检查并重写 |

## 人工判定项（由 `project-audit` 或等价审计流程处理）— 3 个

| # | 检查项 | 来源 ID |
|---|--------|---------|
| A1 | 无 emoji ✅ 暗示已验证的误导性表述 | audit2-M2 |
| A2 | "可直接克隆"等强语义词已替换为"候选/筛选/标记验证" | audit2-M3 |
| A3 | 局限声明完整（6 项: 统计力 / 阈值 fallback / 方法学边界 / 特定区间警示 / 数据追溯 / 范围外工作） | audit2 LIMITATIONS |

## FIX_LOOP 机制

```bash
# scripts/pre_delivery_check.sh 最多运行 3 次
MAX_RETRIES=3
for attempt in $(seq 1 $MAX_RETRIES); do
    bash scripts/pre_delivery_check.sh release/ && break
    # 若失败，尝试自动修复
    bash scripts/autofix_machine_items.sh release/
done
# 若 3 次仍失败 → exit 1 (ABORT_4)
```

## 人工审核切换

机器项全 PASS 后：

```bash
# 触发 project-audit 或等价审计流程
# 在 Codex 中按项目审计 skill/人工审计流程读取 release/
# 审计报告: audit_release_report_YYYYMMDD.md
# 若含 P0 → 阻塞 final，回 Gate 4 修复循环
# 若 P0 = 0 → 放行, release 重命名为 v2.x-final
```

## 产出

```
state/
├── current_gate         # = "GATE_4"
├── gate4.PASS           # 7 机器 + 3 人工全通过
├── fix_loop_attempts.log  # FIX_LOOP 尝试记录
└── audit_result.md       # project-audit 产物

release/
├── ...（v2.x-draft → v2.x-final 重命名）
├── MANIFEST.md5
├── MANIFEST.sha256
└── ...
```

## 来源索引

- audit2 交付包审计全部 22 项
- codex-1 盲点 #1 (QTLseqr 锁定) → #8
- codex-1 盲点 #4 (README 数字重算) → #3
- R2-B3 (PDF/PNG 成对 + sha256) → #7, #9

## 下一步

**PASS (全 10 + 3)** → release final + 写 DECISION_LOG / HANDOVER
**FAIL (机器)** → FIX_LOOP 最多 3 次，超限 ABORT_4
**FAIL (人工)** → 修复 P0 后回 Gate 4
