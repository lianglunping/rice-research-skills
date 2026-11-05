#!/usr/bin/env bash
set -euo pipefail
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

if [[ $# -ne 3 ]]; then
  echo "Usage: build_sample_ibs_tree_v5.sh CONFIG SOURCE_RESULT RESULT_DIR" >&2
  exit 2
fi

CONFIG="$1"
SOURCE_RESULT="$2"
RESULT_DIR="$3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
: "${PYTHON:?Set PYTHON to the validated project Python executable}"
: "${NGS_PREFIX:?Set NGS_PREFIX to the validated project NGS environment prefix}"
: "${TREE_PREFIX:?Set TREE_PREFIX to the validated PLINK/RapidNJ environment prefix}"
[[ -x "$PYTHON" ]] || { echo "Missing executable: $PYTHON" >&2; exit 2; }
[[ -x "$NGS_PREFIX/bin/bcftools" ]] || { echo "Missing executable: $NGS_PREFIX/bin/bcftools" >&2; exit 2; }
[[ -x "$NGS_PREFIX/bin/tabix" ]] || { echo "Missing executable: $NGS_PREFIX/bin/tabix" >&2; exit 2; }
[[ -x "$TREE_PREFIX/bin/plink" ]] || { echo "Missing executable: $TREE_PREFIX/bin/plink" >&2; exit 2; }
[[ -x "$TREE_PREFIX/bin/rapidnj" ]] || { echo "Missing executable: $TREE_PREFIX/bin/rapidnj" >&2; exit 2; }
TREE_DIR="$RESULT_DIR/tree"
mkdir -p "$TREE_DIR"

cfg() {
  awk -F '\t' -v key="$1" 'NR>1 && $1==key {print $2; found=1; exit} END{if(!found) exit 1}' "$CONFIG"
}

GENE="$(cfg gene_id)"
TREE_BASENAME="$(cfg tree_basename)"
VCF="$SOURCE_RESULT/vcf/$GENE.superrice_biallelic_SNP_wide.vcf.gz"
SUBSET_VCF="$TREE_DIR/$GENE.retained_$(cfg tree_expected_tips).postQC_$(cfg tree_expected_snps)SNP.vcf.gz"

"$PYTHON" "$SCRIPT_DIR/prepare_sample_tree_inputs_v5.py" \
  --config "$CONFIG" --source-result "$SOURCE_RESULT" --result-dir "$RESULT_DIR"

if [[ "${FORCE_TREE:-0}" != "1" \
  && -s "$TREE_DIR/${TREE_BASENAME}_1ibs_RapidNJ.newick" \
  && -s "$TREE_DIR/sample_tree_distance_audit.tsv" ]]; then
  "$PYTHON" "$SCRIPT_DIR/audit_sample_tree_v5.py" \
    --tree "$TREE_DIR/${TREE_BASENAME}_1ibs_RapidNJ.newick" \
    --metadata "$TREE_DIR/sample_tree_tip_metadata.tsv" \
    --expected-snps "$(cfg tree_expected_snps)" \
    --output "$TREE_DIR/sample_tree_audit.tsv"
  printf '[sample-tree] reused validated full matrix/tree; set FORCE_TREE=1 to rebuild\n'
  exit 0
fi

"$NGS_PREFIX/bin/bcftools" view \
  -S "$TREE_DIR/retained_accessions.list" \
  -R "$TREE_DIR/post_qc_snp_regions.tsv" \
  -m2 -M2 -v snps -Oz -o "$SUBSET_VCF" "$VCF"
"$NGS_PREFIX/bin/tabix" -f -p vcf "$SUBSET_VCF"

SAMPLE_N=$("$NGS_PREFIX/bin/bcftools" query -l "$SUBSET_VCF" | wc -l | tr -d ' ')
SNP_N=$("$NGS_PREFIX/bin/bcftools" view -H "$SUBSET_VCF" | wc -l | tr -d ' ')
[[ "$SAMPLE_N" == "$(cfg tree_expected_tips)" ]] || { echo "Unexpected tree sample count: $SAMPLE_N" >&2; exit 3; }
[[ "$SNP_N" == "$(cfg tree_plink_biallelic_validation_snps)" ]] || { echo "Unexpected PLINK validation SNP count: $SNP_N" >&2; exit 3; }

"$TREE_PREFIX/bin/plink" --vcf "$SUBSET_VCF" --double-id --allow-extra-chr \
  --make-bed --out "$TREE_DIR/$TREE_BASENAME" --threads 4
"$TREE_PREFIX/bin/plink" --bfile "$TREE_DIR/$TREE_BASENAME" --distance square 1-ibs \
  --out "$TREE_DIR/${TREE_BASENAME}_1ibs" --threads 4

"$PYTHON" "$SCRIPT_DIR/build_multiallelic_ibs_v5.py" \
  --config "$CONFIG" --source-result "$SOURCE_RESULT" --result-dir "$RESULT_DIR" \
  --plink-mdist "$TREE_DIR/${TREE_BASENAME}_1ibs.mdist" \
  --plink-ids "$TREE_DIR/${TREE_BASENAME}_1ibs.mdist.id"

"$TREE_PREFIX/bin/rapidnj" "$TREE_DIR/${TREE_BASENAME}_multiallelic_1ibs.phylip" -i pd -o t -n \
  -x "$TREE_DIR/${TREE_BASENAME}_1ibs_RapidNJ.newick"
"$PYTHON" "$SCRIPT_DIR/audit_sample_tree_v5.py" \
  --tree "$TREE_DIR/${TREE_BASENAME}_1ibs_RapidNJ.newick" \
  --metadata "$TREE_DIR/sample_tree_tip_metadata.tsv" \
  --expected-snps "$(cfg tree_expected_snps)" \
  --output "$TREE_DIR/sample_tree_audit.tsv"

shasum -a 256 "$SUBSET_VCF" "$TREE_DIR/${TREE_BASENAME}_1ibs_RapidNJ.newick" > "$TREE_DIR/sample_tree_files.sha256"
printf '[sample-tree] accessions=%s all_postQC_snps=%s plink_validation_snps=%s tree=%s\n' "$SAMPLE_N" "$(cfg tree_expected_snps)" "$SNP_N" "$TREE_DIR/${TREE_BASENAME}_1ibs_RapidNJ.newick"
