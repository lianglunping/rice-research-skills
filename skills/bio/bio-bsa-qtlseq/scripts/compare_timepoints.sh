#!/usr/bin/env bash
# compare_timepoints.sh — 多时间点 QTL 对比 (phenotype_qc → bedtools → joint plot)
# Usage: compare_timepoints.sh <proj_dir_t1> <proj_dir_t2> <out_dir>
# 触发条件见 references/bsa-method-boundaries.md §4

set -eo pipefail

T1="$1"; T2="$2"; OUT="$3"
if [ -z "$T1" ] || [ -z "$T2" ] || [ -z "$OUT" ]; then
    echo "Usage: $0 <proj_dir_t1> <proj_dir_t2> <out_dir>" >&2; exit 2
fi
mkdir -p "$OUT"

SKILL_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
log() { echo "[$(date +%T)] $*"; }

# === Step A: Phenotype QC ===
log "Step A: phenotype QC"
python "$SKILL_ROOT/scripts/phenotype_qc.py" \
    --t1 "$T1/metadata/samples.tsv" --t1-meta "$T1/metadata/phenotype_source.meta.yaml" \
    --t2 "$T2/metadata/samples.tsv" --t2-meta "$T2/metadata/phenotype_source.meta.yaml" \
    --out "$OUT/compare_phenotype_qc.json"
python "$SKILL_ROOT/scripts/render_phenotype_qc_md.py" \
    --json "$OUT/compare_phenotype_qc.json" > "$OUT/compare_phenotype_qc.md"

COMPARABLE=$(python -c "import json; print(json.load(open('$OUT/compare_phenotype_qc.json'))['comparable'])")
log "Comparability: $COMPARABLE"

case "$COMPARABLE" in
    full)
        log "完全可比, 进入 Step B/C/D"
        ;;
    interval_only)
        log "仅 interval 可比, 跳过生物学解读"
        ;;
    not_comparable)
        log "不可比 (unit/batch/metadata 差异过大), 仅输出 phenotype_qc 报告"
        echo "comparable: not_comparable" > "$OUT/compare_report.md"
        cat "$OUT/compare_phenotype_qc.md" >> "$OUT/compare_report.md"
        exit 0
        ;;
esac

# === Step B: bedtools intersect / subtract ===
log "Step B: bedtools intersect"
for METH in Gprime_q005 QTLseq_ci95; do
    T1_BED="$T1/results/main/${METH}_regions.bed"
    T2_BED="$T2/results/main/${METH}_regions.bed"
    [ -f "$T1_BED" ] && [ -f "$T2_BED" ] || continue

    bedtools intersect -a "$T1_BED" -b "$T2_BED" -wa -wb > "$OUT/${METH}_shared.tsv"
    bedtools subtract -a "$T1_BED" -b "$T2_BED" -A > "$OUT/${METH}_t1_only.tsv"
    bedtools subtract -a "$T2_BED" -b "$T1_BED" -A > "$OUT/${METH}_t2_only.tsv"

    log "  $METH: shared=$(wc -l < $OUT/${METH}_shared.tsv); t1_only=$(wc -l < $OUT/${METH}_t1_only.tsv); t2_only=$(wc -l < $OUT/${METH}_t2_only.tsv)"
done

# === Step C: 联合曼哈顿图 (可选, 需 R 脚本) ===
if [ "$COMPARABLE" == "full" ] && [ -f "$SKILL_ROOT/scripts/plot_joint_manhattan.R" ]; then
    log "Step C: joint manhattan"
    Rscript "$SKILL_ROOT/scripts/plot_joint_manhattan.R" \
        --t1 "$T1/results/main/Gprime_all.rds" \
        --t2 "$T2/results/main/Gprime_all.rds" \
        --out "$OUT/compare_manhattan" || log "[WARN] joint plot 失败, 继续"
fi

# === Step D: 汇总报告 ===
log "Step D: compare_report.md"
python "$SKILL_ROOT/scripts/render_compare_report.py" \
    --intervals "$OUT" \
    --phenotype_qc "$OUT/compare_phenotype_qc.md" \
    --comparable "$COMPARABLE" \
    --out "$OUT/compare_report.md" || {
    # 兼容 fallback: 无 render 脚本时用简单拼接
    {
        echo "# Timepoint Comparison Report"
        echo
        echo "Comparability: $COMPARABLE"
        echo
        cat "$OUT/compare_phenotype_qc.md"
        echo
        echo "## Interval Intersections"
        for f in "$OUT"/*_shared.tsv "$OUT"/*_only.tsv; do
            [ -f "$f" ] && echo "- $(basename $f): $(wc -l < $f) regions"
        done
    } > "$OUT/compare_report.md"
}

log "[OK] compare_timepoints.sh 完成, 产物在 $OUT"
