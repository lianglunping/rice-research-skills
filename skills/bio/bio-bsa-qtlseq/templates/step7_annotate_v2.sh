#!/usr/bin/env bash
# Step 7 v2.1 (审计后脱敏 + 4×3 完整敏感性矩阵汇总版)
# 参数化 (环境变量): BSA_ROOT / CONDA_ROOT / CONDA_ENV / GFF
# 生成: $RESULTS_SUBDIR/*_candidate_genes.tsv + SUMMARY_v2.md (完整 4×3 矩阵)

set -eo pipefail
: "${CONDA_BUILD:=}"
: "${BSA_ROOT:=$(pwd)}"
: "${CONDA_ROOT:=$HOME/miniconda3}"
: "${CONDA_ENV:=bsa}"
: "${GFF:=$BSA_ROOT/ref/reference.gene.gff3}"
: "${ANALYSIS_SUBDIR:=analysis}"     # v2.1 修复 (Codex R1 F): 原硬编码
: "${RESULTS_SUBDIR:=results_v2}"

cd "$BSA_ROOT/$ANALYSIS_SUBDIR"
# shellcheck disable=SC1091
source "$CONDA_ROOT/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"
set -u

mkdir -p "$RESULTS_SUBDIR"
# 下方 $RESULTS_SUBDIR/ 引用由参数化替代

# 1. genes.bed (mawk-compatible: sub 替代 gawk match 3-arg)
if [ ! -s $RESULTS_SUBDIR/genes.bed ]; then
  awk 'BEGIN{OFS="\t"} $3=="gene" {
    id=$9; sub(/.*ID=/,"",id); sub(/;.*/,"",id);
    print $1,$4-1,$5,id
  }' "$GFF" > $RESULTS_SUBDIR/genes.bed
fi
GENE_TOTAL=$(wc -l < $RESULTS_SUBDIR/genes.bed)
echo "genes.bed lines: $GENE_TOTAL"

annotate_one() {
  local TSV=$1
  [ -s "$TSV" ] || { echo "[skip] $TSV missing"; return 0; }
  local BASE; BASE=$(basename "$TSV" .tsv)
  local BED=$RESULTS_SUBDIR/${BASE}.bed
  local OUT=$RESULTS_SUBDIR/${BASE}_candidate_genes.tsv
  awk 'BEGIN{OFS="\t"} NR==1{
    for(i=1;i<=NF;i++){
      if($i=="CHROM")ci=i; else if($i=="start")si=i;
      else if($i=="end")ei=i; else if($i=="qtl")qi=i;
      else if($i=="maxGprime")gi=i; else if($i=="peakDeltaSNP")di=i;
      else if($i=="posMaxGprime")pgi=i; else if($i=="posPeakDeltaSNP")pdi=i;
    }
    if(!ci||!si||!ei){exit 2}
    next
  } {
    name="qtl"$qi
    if(gi) name=name"_Gp"$gi
    if(di) name=name"_dSNP"$di
    if(pgi) name=name"_posMaxGp"$pgi
    if(pdi) name=name"_posPeakdSNP"$pdi
    print $ci,$si-1,$ei,name
  }' "$TSV" > "$BED"
  local N; N=$(wc -l < "$BED")
  if [ "$N" -eq 0 ]; then
    echo "[info] $BASE: no regions"
    return 0
  fi
  bedtools intersect -a "$BED" -b $RESULTS_SUBDIR/genes.bed -wa -wb > "$OUT"
  local NG UNIQ
  NG=$(wc -l < "$OUT"); UNIQ=$(cut -f8 "$OUT" | sort -u | wc -l)
  echo "[$BASE] regions=$N gene_hits=$NG unique_genes=$UNIQ"
}

# v2.1 修复 (审计 C3): 覆盖所有 4 阈值 × 3 参数组
for SUFFIX in "" "_w500k" "_rf035"; do
  for THRESH in "Gprime_q001" "Gprime_q005" "QTLseq_ci95" "QTLseq_ci99"; do
    annotate_one "$RESULTS_SUBDIR/${THRESH}_regions${SUFFIX}.tsv"
  done
done

# SUMMARY_v2.md 完整 4×3 敏感性矩阵
count_regions() {
  local F=$1
  [ -s "$F" ] && echo "$(($(wc -l < "$F") - 1))" || echo 0
}

Q1_MAIN=$(count_regions $RESULTS_SUBDIR/Gprime_q001_regions.tsv)
Q5_MAIN=$(count_regions $RESULTS_SUBDIR/Gprime_q005_regions.tsv)
C9_MAIN=$(count_regions $RESULTS_SUBDIR/QTLseq_ci99_regions.tsv)
C5_MAIN=$(count_regions $RESULTS_SUBDIR/QTLseq_ci95_regions.tsv)
Q1_W=$(count_regions $RESULTS_SUBDIR/Gprime_q001_regions_w500k.tsv)
Q5_W=$(count_regions $RESULTS_SUBDIR/Gprime_q005_regions_w500k.tsv)
C9_W=$(count_regions $RESULTS_SUBDIR/QTLseq_ci99_regions_w500k.tsv)
C5_W=$(count_regions $RESULTS_SUBDIR/QTLseq_ci95_regions_w500k.tsv)
Q1_R=$(count_regions $RESULTS_SUBDIR/Gprime_q001_regions_rf035.tsv)
Q5_R=$(count_regions $RESULTS_SUBDIR/Gprime_q005_regions_rf035.tsv)
C9_R=$(count_regions $RESULTS_SUBDIR/QTLseq_ci99_regions_rf035.tsv)
C5_R=$(count_regions $RESULTS_SUBDIR/QTLseq_ci95_regions_rf035.tsv)

cat > $RESULTS_SUBDIR/SUMMARY_v2.md <<MD
# 葡萄 5h 失水率 BSA — Pipeline Summary v2.1

生成时间: $(date +"%F %T")

## 完整 4×3 敏感性矩阵

| 参数 | Gprime q001 | Gprime q005 | QTLseq ci99 | QTLseq ci95 |
|------|-------------|-------------|-------------|-------------|
| 主 (window=1Mb, refAF=0.20) | $Q1_MAIN | **$Q5_MAIN** | $C9_MAIN | **$C5_MAIN** |
| window=500kb | $Q1_W | $Q5_W | $C9_W | $C5_W |
| refAF=0.35 | $Q1_R | $Q5_R | $C9_R | $C5_R |

详细解读见 02_LIMITATIONS §3.5 和 results/sensitivity/*/README.md。
MD

echo "SUMMARY_v2.md updated"
