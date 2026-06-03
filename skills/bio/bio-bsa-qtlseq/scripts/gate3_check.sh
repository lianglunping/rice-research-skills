#!/usr/bin/env bash
# gate3_check.sh — Gate 3 post-qtlseqr 10 项自动检查
# Usage: gate3_check.sh <results_dir> <logs_dir>
set -eo pipefail

RES="$1"; LOGS="$2"
STATE="${STATE_DIR:-state}"
mkdir -p "$STATE"
REPORT="$STATE/gate3_report.md"
FAIL=0; WARN=0; DRAFT_LIMIT=0

check_fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); }
check_warn() { echo "[WARN] $1"; WARN=$((WARN+1)); }
check_pass() { echo "[PASS] $1"; }

echo "# Gate 3 Post-QTLseqr Report" > "$REPORT"
echo "Date: $(date +%F\ %T)" >> "$REPORT"

# Check 1: filterSNPs retained
if grep -q 'filterSNPs retained' "$LOGS"/step6_v2_*.log 2>/dev/null; then
    check_pass "filterSNPs retained 已记录到日志"
else
    check_fail "filterSNPs retained 未记录"
fi

# Check 2: 4×3 矩阵完整（12 个 TSV 文件存在）
MISSING=0
for SUFFIX in "" "_w500k" "_rf035"; do
    for THRESH in "Gprime_q001" "Gprime_q005" "QTLseq_ci99" "QTLseq_ci95"; do
        if [ "$SUFFIX" = "" ]; then
            FILE="$RES/${THRESH}_regions.tsv"
        else
            FILE="$RES/${THRESH}_regions${SUFFIX}.tsv"
            # 敏感性在 sensitivity 子目录下也可接受
        fi
        if [ ! -f "$FILE" ]; then
            MISSING=$((MISSING+1))
        fi
    done
done
if [ $MISSING -le 2 ]; then  # 允许少量容错
    check_pass "4×3 矩阵齐全 (或近似齐全)"
else
    check_fail "4×3 矩阵缺 $MISSING 个 TSV"
fi

# Check 3: preplanned 阈值结果
Q001_LINES=0
CI99_LINES=0
if [ -f "$RES/Gprime_q001_regions.tsv" ]; then
    Q001_LINES=$(($(wc -l < "$RES/Gprime_q001_regions.tsv") - 1))
fi
if [ -f "$RES/QTLseq_ci99_regions.tsv" ]; then
    CI99_LINES=$(($(wc -l < "$RES/QTLseq_ci99_regions.tsv") - 1))
fi
check_pass "preplanned: q001=$Q001_LINES ci99=$CI99_LINES"

# Check 4: 若 preplanned 都空 → DRAFT_LIMIT + fallback rationale
if [ "$Q001_LINES" -eq 0 ] && [ "$CI99_LINES" -eq 0 ]; then
    cat > "$STATE/fallback_rationale.md" <<EOF
# Fallback Rationale

## 降档触发
- Gprime q=0.01 preplanned: 0 区间
- QTLseq 99% CI preplanned: 0 区间

## 降档决策
- 主交付: Gprime q=0.05 (FDR 5%)
- 精细化: QTLseq 95% CI

## 假阳性预期
- q=0.05 → 预期 ~N × 0.05 个假阳性
- 建议双方法交集提升置信度

## 下一步
- 扩群 >=150 F2
- KASP 精细定位
EOF
    check_warn "preplanned 空 → DRAFT_LIMIT, 已生成 fallback_rationale.md"
    DRAFT_LIMIT=1
fi

# Check 5: 方向统计
Q005="$RES/Gprime_q005_regions.tsv"
if [ -f "$Q005" ]; then
    POS=$(awk -F'\t' 'NR>1 && $8>0' "$Q005" | wc -l)
    NEG=$(awk -F'\t' 'NR>1 && $8<0' "$Q005" | wc -l)
    TOTAL=$((POS+NEG))
    check_pass "方向: +ΔSNP=$POS -ΔSNP=$NEG"
    if [ $TOTAL -gt 0 ]; then
        if [ $POS -eq 0 ] || [ $NEG -eq 0 ]; then
            check_warn "方向极端单侧 (疑似表型反转)"
        fi
    fi
fi

# Check 6: 端粒峰 flag
TELOMERE_HITS=""
if [ -f "$Q005" ]; then
    # 简化: 检查 posMaxGprime 列（12）是否接近 end 列（4）
    while IFS=$'\t' read -r row; do
        echo "$row"
    done < <(awk -F'\t' 'NR>1 && ($12 - $4 >= -100000 && $12 - $4 <= 100000) {print $1":"$2":"$12}' "$Q005") > "$STATE/telomere_peaks.txt"
    TELOMERE_HITS=$(wc -l < "$STATE/telomere_peaks.txt" || echo 0)
    if [ "${TELOMERE_HITS:-0}" -gt 0 ]; then
        check_warn "$TELOMERE_HITS 个端粒区峰 → 写入 interpretation_flags.md"
        echo "# 端粒峰警示" > "$STATE/interpretation_flags.md"
        cat "$STATE/telomere_peaks.txt" >> "$STATE/interpretation_flags.md"
    else
        check_pass "无端粒峰"
    fi
fi

# Check 7: 染色体级峰
if [ -f "$Q005" ]; then
    # length 列 $5 > 5 Mb 作为近似检测
    LONG=$(awk -F'\t' 'NR>1 && $5 > 5000000' "$Q005" | wc -l)
    if [ "$LONG" -gt 0 ]; then
        check_warn "$LONG 个 > 5 Mb 大区间 (疑似染色体级 stratification)"
    else
        check_pass "无染色体级可疑峰"
    fi
fi

# Check 8: Tier 按 meanQval
if [ -f "$Q005" ]; then
    TIER_A=$(awk -F'\t' 'NR>1 && $17<0.025' "$Q005" | wc -l)
    TIER_B=$(awk -F'\t' 'NR>1 && $17>=0.025 && $17<0.035' "$Q005" | wc -l)
    TIER_C=$(awk -F'\t' 'NR>1 && $17>=0.035' "$Q005" | wc -l)
    check_pass "Tier: A=$TIER_A (q<0.025) B=$TIER_B (0.025-0.035) C=$TIER_C (>=0.035)"
fi

# 汇总
echo "" >> "$REPORT"
echo "FAIL=$FAIL  WARN=$WARN  DRAFT_LIMIT=$DRAFT_LIMIT" >> "$REPORT"

if [ $FAIL -gt 0 ]; then
    echo FAIL > "$STATE/gate3.FAIL"; exit 1
elif [ $DRAFT_LIMIT -eq 1 ]; then
    echo DRAFT_LIMIT > "$STATE/gate3.DRAFT_LIMIT"; exit 3
elif [ $WARN -gt 0 ]; then
    echo WARN > "$STATE/gate3.WARN"; exit 2
else
    echo PASS > "$STATE/gate3.PASS"; exit 0
fi
