#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: run_xi_gj_site_fst_v3.sh CONFIG SOURCE_RESULT RESULT_DIR" >&2
  exit 2
fi

CONFIG="$1"
SOURCE_RESULT="$2"
RESULT_DIR="$3"
: "${NGS_PREFIX:?Set NGS_PREFIX to the validated project NGS environment prefix}"
VCFTOOLS="$NGS_PREFIX/bin/vcftools"
[[ -x "$VCFTOOLS" ]] || { echo "Missing executable: $VCFTOOLS" >&2; exit 2; }

cfg() {
  awk -F '\t' -v key="$1" 'NR>1 && $1==key {print $2; found=1; exit} END{if(!found) exit 1}' "$CONFIG"
}

GENE_ID="$(cfg gene_id)"
MAX_MISSING="$(cfg popgen_max_missing)"
VCF_GZ="$SOURCE_RESULT/vcf/$GENE_ID.superrice_biallelic_SNP_wide.vcf.gz"
SOURCE_GROUPS="$SOURCE_RESULT/popgen/groups"
OUT_DIR="$RESULT_DIR/popgen/vcftools_raw"
GROUP_DIR="$RESULT_DIR/popgen/groups"
LOG_DIR="$RESULT_DIR/logs"
mkdir -p "$OUT_DIR" "$GROUP_DIR" "$LOG_DIR"

for group in XI GJ; do
  cp "$SOURCE_GROUPS/$group.list" "$GROUP_DIR/$group.list"
done
cat "$GROUP_DIR/XI.list" "$GROUP_DIR/GJ.list" > "$GROUP_DIR/XI_vs_GJ.list"

"$VCFTOOLS" \
  --gzvcf "$VCF_GZ" \
  --keep "$GROUP_DIR/XI_vs_GJ.list" \
  --max-missing "$MAX_MISSING" \
  --weir-fst-pop "$GROUP_DIR/XI.list" \
  --weir-fst-pop "$GROUP_DIR/GJ.list" \
  --out "$OUT_DIR/XI_vs_GJ.site" \
  > "$LOG_DIR/vcftools_XI_vs_GJ_site_fst.stdout.log" \
  2> "$LOG_DIR/vcftools_XI_vs_GJ_site_fst.stderr.log"

test -s "$OUT_DIR/XI_vs_GJ.site.weir.fst"
printf '[site-fst] estimator=Weir-Cockerham max_missing=%s output=%s\n' \
  "$MAX_MISSING" "$OUT_DIR/XI_vs_GJ.site.weir.fst"
