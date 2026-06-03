#!/usr/bin/env bash
# gate2_check.sh — Gate 2 post-pool 9 项自动检查
# Usage: gate2_check.sh <step34_log> <pooled_vcf_gz>
set -eo pipefail

LOG="$1"; VCF="$2"
STATE="${STATE_DIR:-state}"
mkdir -p "$STATE"
REPORT="$STATE/gate2_report.md"
FAIL=0; WARN=0

check_fail() { echo "[FAIL] $1"; FAIL=$((FAIL+1)); }
check_warn() { echo "[WARN] $1"; WARN=$((WARN+1)); }
check_pass() { echo "[PASS] $1"; }

echo "# Gate 2 Post-Pool Report" > "$REPORT"
echo "Date: $(date +%F\ %T)" >> "$REPORT"

# Check 1: [CHECK] 统计闭环
if grep -q '\[CHECK\] 统计闭环通过' "$LOG" 2>/dev/null; then
    check_pass "统计闭环通过"
else
    check_fail "统计闭环断"
fi

# Check 2/3/4: 从 [STATS] 行解析
STATS=$(grep '^\[STATS\]' "$LOG" 2>/dev/null | tail -1)
if [ -n "$STATS" ]; then
    KEPT=$(echo "$STATS" | grep -oE 'kept=[0-9]+' | cut -d= -f2)
    POLARIZED=$(echo "$STATS" | grep -oE 'polarized=[0-9]+' | cut -d= -f2)
    IN=$(echo "$STATS" | grep -oE 'in=[0-9]+' | cut -d= -f2)

    [ "${KEPT:-0}" -ge 1000000 ] && check_pass "kept=$KEPT >= 1M" || check_fail "kept=$KEPT < 1M"

    if [ -n "$IN" ] && [ "$IN" -gt 0 ]; then
        RATIO=$(python -c "print(${KEPT:-0}/$IN)" 2>/dev/null || echo 0)
        python -c "exit(0 if 0.05 <= ${RATIO:-0} <= 0.50 else 1)" && check_pass "kept/in 比例 $RATIO" || check_warn "kept/in 比例 $RATIO 偏离 [0.05, 0.50]"
    fi

    if [ -n "$POLARIZED" ] && [ "${KEPT:-0}" -gt 0 ]; then
        POL_RATIO=$(python -c "print($POLARIZED/$KEPT)" 2>/dev/null || echo 0)
        python -c "exit(0 if 0.05 <= ${POL_RATIO:-0} <= 0.95 else 1)" && check_pass "polarized 比例 $POL_RATIO" || check_warn "polarized 比例 $POL_RATIO 极端 (提示参考基因组偏好)"
    fi

    HALF=$(echo "$STATS" | grep -oE 'parent_half_call=[0-9]+' | cut -d= -f2)
    if [ -n "$HALF" ] && [ "${HALF:-0}" -le "${KEPT:-1}" ]; then
        check_pass "half_call=$HALF <= kept=$KEPT"
    else
        check_warn "half_call 计数大 ($HALF), 亲本 GT 质量可能差"
    fi
else
    check_fail "未找到 [STATS] 行"
fi

# Check 6: pooled VCF 两样本
if [ -f "$VCF" ] && command -v bcftools > /dev/null; then
    SAMPLES_IN_VCF=$(bcftools query -l "$VCF" 2>/dev/null | tr '\n' ',' | sed 's/,$//')
    if echo "$SAMPLES_IN_VCF" | grep -q "HighBulk" && echo "$SAMPLES_IN_VCF" | grep -q "LowBulk"; then
        check_pass "pooled VCF 含 HighBulk + LowBulk"
    else
        check_fail "pooled VCF 样本异常: $SAMPLES_IN_VCF"
    fi
fi

# Check 7: VA_HOM + POLARIZED INFO 字段存在
if [ -f "$VCF" ] && command -v bcftools > /dev/null; then
    HDR=$(bcftools view -h "$VCF" 2>/dev/null | grep -E '^##INFO=<ID=(VA_HOM|POLARIZED)')
    if echo "$HDR" | grep -q VA_HOM && echo "$HDR" | grep -q POLARIZED; then
        check_pass "VA_HOM + POLARIZED INFO 字段存在"
    else
        check_fail "VCF 缺 VA_HOM 或 POLARIZED 字段 (脚本版本错)"
    fi
fi

# 汇总
echo "" >> "$REPORT"
echo "FAIL=$FAIL  WARN=$WARN" >> "$REPORT"

if [ $FAIL -gt 0 ]; then
    echo FAIL > "$STATE/gate2.FAIL"; exit 1
elif [ $WARN -gt 0 ]; then
    echo WARN > "$STATE/gate2.WARN"; exit 2
else
    echo PASS > "$STATE/gate2.PASS"; exit 0
fi
