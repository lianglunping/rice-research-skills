#!/usr/bin/env bash
set -euo pipefail
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG="${CONFIG:-$PROJECT_ROOT/config/publication_composite_v4.tsv}"
MAMBA_EXE="${MAMBA_EXE:-}"
PY_PREFIX="${PY_PREFIX:-}"
NGS_PREFIX="${NGS_PREFIX:-}"

cfg() {
  awk -F '\t' -v key="$1" 'NR>1 && $1==key {print $2; found=1; exit} END{if(!found) exit 1}' "$CONFIG"
}

if [[ -z "$MAMBA_EXE" ]]; then
  MAMBA_EXE="$(command -v micromamba || command -v mamba || true)"
fi
PY_PREFIX="${PY_PREFIX:-$(cfg python_prefix)}"
NGS_PREFIX="${NGS_PREFIX:-$(cfg ngs_prefix)}"
[[ -x "$MAMBA_EXE" ]] || { echo "Set MAMBA_EXE to an executable micromamba or mamba binary" >&2; exit 2; }
[[ -x "$PY_PREFIX/bin/python" ]] || { echo "Invalid PY_PREFIX; missing $PY_PREFIX/bin/python" >&2; exit 2; }
[[ -x "$NGS_PREFIX/bin/vcftools" ]] || { echo "Invalid NGS_PREFIX; missing $NGS_PREFIX/bin/vcftools" >&2; exit 2; }
export PY_PREFIX NGS_PREFIX

RUN_ID="$(cfg run_id)"
GENE_ID="$(cfg gene_id)"
RESULT_DIR="$PROJECT_ROOT/results/$RUN_ID"
SOURCE_RESULT="$(cfg source_result_dir)"
REVIEW_INPUT="${REVIEW_INPUT:-$PROJECT_ROOT/config/${GENE_ID}_publication_composite_visual_review_v4.tsv}"
TEST_DIR="${TEST_DIR:-$PROJECT_ROOT/temp_tests/publication_composite_v4}"
LOG_DIR="$RESULT_DIR/logs"
mkdir -p "$LOG_DIR" "$RESULT_DIR/figures" "$RESULT_DIR/summary"

run_step() {
  local name="$1"
  shift
  printf '[v4] start %s %s\n' "$name" "$(date '+%F %T %Z')"
  "$@" 2>&1 | tee "$LOG_DIR/$name.log"
  printf '[v4] done %s %s\n' "$name" "$(date '+%F %T %Z')"
}

{
  printf 'field\tvalue\n'
  printf 'date\t%s\n' "$(date '+%F %T %Z')"
  printf 'run_id\t%s\n' "$RUN_ID"
  printf 'config\t%s\n' "$CONFIG"
  printf 'mamba_executable\t%s\n' "$MAMBA_EXE"
  printf 'mamba_version\t%s\n' "$("$MAMBA_EXE" --version)"
  "$PY_PREFIX/bin/python" -c 'import sys,openpyxl,scipy,Bio,PIL; print("python\t"+sys.version.replace("\n"," ")); print("openpyxl\t"+openpyxl.__version__); print("scipy\t"+scipy.__version__); print("biopython\t"+Bio.__version__); print("Pillow\t"+PIL.__version__)'
  "$MAMBA_EXE" run -p "$PY_PREFIX" Rscript -e 'cat("R\t",R.version.string,"\n",sep=""); for(p in c("ape","Cairo","ggplot2","ggrepel","ggtree","igraph","openxlsx","patchwork","ragg","readr","rnaturalearth","scales","scatterpie","sf","tidyr")) cat(p,"\t",as.character(packageVersion(p)),"\n",sep="")'
  "$NGS_PREFIX/bin/vcftools" --version 2>&1 | head -n 2
  pdftotext -v 2>&1 | head -n 1
} > "$LOG_DIR/00_versions.tsv"

run_step 01_site_fst "$SCRIPT_DIR/run_xi_gj_site_fst_v4.sh" "$CONFIG" "$SOURCE_RESULT" "$RESULT_DIR"
run_step 02_build_tables "$PY_PREFIX/bin/python" "$SCRIPT_DIR/build_publication_tables_v4.py" \
  --config "$CONFIG" --project-root "$PROJECT_ROOT" --source-result "$SOURCE_RESULT" --result-dir "$RESULT_DIR" \
  --site-fst "$RESULT_DIR/popgen/vcftools_raw/XI_vs_GJ.site.weir.fst"
run_step 03_plot "$MAMBA_EXE" run -p "$PY_PREFIX" Rscript "$SCRIPT_DIR/plot_publication_composite_v4.R" \
  "$CONFIG" "$RESULT_DIR" "$RESULT_DIR/figures"
run_step 04_contact_sheets "$PY_PREFIX/bin/python" "$SCRIPT_DIR/make_review_contact_sheets_v4.py" \
  --result-dir "$RESULT_DIR" --output-dir "$RESULT_DIR/summary/contact_sheets"
if [[ -d "$TEST_DIR" ]] && compgen -G "$TEST_DIR/test_*.py" > /dev/null; then
  run_step 05_contract_tests "$PY_PREFIX/bin/python" -m unittest discover \
    -s "$TEST_DIR" -p 'test_*.py' -v
fi

if [[ ! -s "$REVIEW_INPUT" ]]; then
  echo "Manual review input is required after inspecting all contact sheets and full-size panels: $REVIEW_INPUT" >&2
  exit 3
fi
run_step 06_visual_review "$PY_PREFIX/bin/python" "$SCRIPT_DIR/record_visual_review_v4.py" \
  --result-dir "$RESULT_DIR" --review-input "$REVIEW_INPUT" --out-stem "$RESULT_DIR/summary/figure_visual_review"
run_step 07_release "$PY_PREFIX/bin/python" "$SCRIPT_DIR/make_release_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT"
run_step 08_qa "$PY_PREFIX/bin/python" "$SCRIPT_DIR/qa_publication_composite_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT"
run_step 09_release_final "$PY_PREFIX/bin/python" "$SCRIPT_DIR/make_release_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT"
run_step 10_qa_verify "$PY_PREFIX/bin/python" "$SCRIPT_DIR/qa_publication_composite_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --verify-only

if [[ "$TEST_DIR" == "$PROJECT_ROOT/temp_tests/publication_composite_v4" ]]; then
  rm -rf "$TEST_DIR"
fi
printf '[v4] result=%s\n[v4] release=%s\n[v4] delivery=%s\n' \
  "$RESULT_DIR" "$PROJECT_ROOT/release/$(cfg release_id)" "$PROJECT_ROOT/delivery/$(cfg delivery_zip)"
