#!/usr/bin/env bash
# Orchestrator v2.1 (审计后脱敏版)
# 参数化配置（可通过环境变量覆盖）:
#   BSA_ROOT     项目根目录 (默认: 当前目录)
#   CONDA_ROOT   miniconda 安装路径 (默认: $HOME/miniconda3)
#   CONDA_ENV    conda env 名 (默认: bsa)
#   REF_FA       参考基因组 fasta 路径
#   GFF          基因注释 GFF3 路径
#
# 用法:
#   cd <project_root>
#   bash scripts/orchestrator_v2.sh
# 或:
#   BSA_ROOT=/path/to/project CONDA_ENV=bsa bash orchestrator_v2.sh

set -eo pipefail
: "${CONDA_BUILD:=}"
: "${_CONDA_OLD_PS1:=}"

: "${BSA_ROOT:=$(pwd)}"
: "${CONDA_ROOT:=$HOME/miniconda3}"
: "${CONDA_ENV:=bsa}"
: "${ANALYSIS_SUBDIR:=analysis}"      # v2.1 修复 (Codex R1 F 项): 原硬编码 "analysis"
: "${RESULTS_SUBDIR:=results_v2}"     # v2.1 修复: 原硬编码 "results_v2"
: "${FIGURES_SUBDIR:=figures_v2}"     # v2.1 修复: 原硬编码 "figures_v2"
: "${REF_FA:=$BSA_ROOT/ref/reference.fa}"   # 默认不再绑定葡萄
: "${GFF:=$BSA_ROOT/ref/reference.gene.gff3}"

cd "$BSA_ROOT/$ANALYSIS_SUBDIR"
# shellcheck disable=SC1091
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"
set -u

STATE="$(pwd)/logs/orchestrator_v2.state"
LOG="$(pwd)/logs/orchestrator_v2.log"
mkdir -p "$(dirname "$LOG")"
: > "$LOG"

log() { echo "[$(date +%F\ %T)] $*" | tee -a "$LOG"; }
fail() { echo FAILED > "$STATE"; log "FAIL: $*"; touch "$(dirname "$LOG")/orchestrator_v2.FAIL"; exit 1; }
ok() { echo DONE > "$STATE"; log "DONE"; touch "$(dirname "$LOG")/orchestrator_v2.DONE"; }

log "=== orchestrator v2.1 start ==="
log "BSA_ROOT=$BSA_ROOT  CONDA_ENV=$CONDA_ENV  REF_FA=$REF_FA"

# Step A
echo run_pfp_v2 > "$STATE"
log "[A] parent_filter_and_pool v2"
python "$BSA_ROOT/$ANALYSIS_SUBDIR/scripts/parent_filter_and_pool_v2.py" \
  subset.snp.vcf.gz high_samples.txt low_samples.txt Va Vv pooled_v2.raw.vcf \
  --chrom-regex '^chr[0-9]+$' --min-parent-dp 5 2>&1 | tee logs/step34_v2.log
[ "${PIPESTATUS[0]}" -eq 0 ] || fail "parent_filter_and_pool_v2 exit != 0"

# Step B
echo run_vtt_v2 > "$STATE"
log "[B] bgzip + tabix + VariantsToTable"
bgzip -f --threads 8 pooled_v2.raw.vcf
tabix -f -p vcf pooled_v2.raw.vcf.gz
gatk VariantsToTable \
  -R "$REF_FA" \
  -V pooled_v2.raw.vcf.gz \
  -F CHROM -F POS -F REF -F ALT -F VA_HOM -F POLARIZED \
  -GF AD -GF DP -GF GQ \
  -O input_v2.table 2>>logs/step5_v2.log
log "[B] input_v2.table rows: $(tail -n +2 input_v2.table | wc -l)"

# Step C - 3 路并行
echo run_r_parallel > "$STATE"
log "[C] R QTLseqr main + sensitivity"
(Rscript "$BSA_ROOT/$ANALYSIS_SUBDIR/scripts/qtlseqr_analysis_v2.R" input_v2.table $RESULTS_SUBDIR $FIGURES_SUBDIR 1e6 0.20 '' \
   > logs/step6_v2_main.log 2>&1) &
PID_MAIN=$!
(Rscript "$BSA_ROOT/$ANALYSIS_SUBDIR/scripts/qtlseqr_analysis_v2.R" input_v2.table $RESULTS_SUBDIR $FIGURES_SUBDIR 5e5 0.20 '_w500k' \
   > logs/step6_v2_w500k.log 2>&1) &
PID_W500K=$!
(Rscript "$BSA_ROOT/$ANALYSIS_SUBDIR/scripts/qtlseqr_analysis_v2.R" input_v2.table $RESULTS_SUBDIR $FIGURES_SUBDIR 1e6 0.35 '_rf035' \
   > logs/step6_v2_rf035.log 2>&1) &
PID_RF035=$!
wait $PID_MAIN || fail "R main failed"
wait $PID_W500K || fail "R w500k failed"
wait $PID_RF035 || fail "R rf035 failed"
log "[C] all R jobs DONE"

# Step D
echo run_annot_v2 > "$STATE"
log "[D] bedtools + SUMMARY"
GFF="$GFF" bash "$BSA_ROOT/$ANALYSIS_SUBDIR/scripts/step7_annotate_v2.sh" 2>&1 | tee -a logs/step7_v2.log
[ "${PIPESTATUS[0]}" -eq 0 ] || fail "step7 failed"
ok
