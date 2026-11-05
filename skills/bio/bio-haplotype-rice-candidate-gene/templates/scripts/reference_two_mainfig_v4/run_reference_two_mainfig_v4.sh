#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 2 ]]; then echo "Usage: $0 CONFIG PROJECT_ROOT [--verify-only]" >&2; exit 2; fi
CONFIG="$1"; PROJECT_ROOT="$2"; MODE="${3:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PYTHON="${PYTHON:-python3}"; RSCRIPT="${RSCRIPT:-Rscript}"
cfg(){ awk -F $'\t' -v k="$1" 'NR>1&&$1==k{print $2;exit}' "$CONFIG"; }
RUN_ID="$(cfg run_id)"; RESULT="$PROJECT_ROOT/results/$RUN_ID"; SOURCE="$(cfg source_result_dir)"; [[ "$SOURCE" = /* ]] || SOURCE="$PROJECT_ROOT/$SOURCE"
RELEASE="$PROJECT_ROOT/release/$(cfg release_id)"; ZIP="$PROJECT_ROOT/delivery/$(cfg delivery_zip)"; MANIFEST="$RESULT/summary/release_manifest.tsv"
if [[ "$MODE" == "--verify-only" ]]; then "$PYTHON" "$SCRIPT_DIR/qa_reference_two_mainfig_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --result-dir "$RESULT"; "$PYTHON" "$SCRIPT_DIR/qa_table_readmes_v4.py" --table-root "$RELEASE/table"; "$PYTHON" "$SCRIPT_DIR/verify_release_two_mainfig_v4.py" --release-dir "$RELEASE" --zip "$ZIP" --manifest "$MANIFEST"; "$PYTHON" "$SCRIPT_DIR/source_allowlist_gate_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --receipt "$RESULT/summary/source_allowlist_before.tsv" --verify; exit 0; fi
export XDG_CACHE_HOME="$PROJECT_ROOT/.cache/two_mainfig_v4"
export MPLCONFIGDIR="$XDG_CACHE_HOME/matplotlib"
mkdir -p "$XDG_CACHE_HOME/fontconfig" "$MPLCONFIGDIR"
mkdir -p "$RESULT/logs" "$RESULT/figures/work"
"$PYTHON" "$SCRIPT_DIR/validate_config_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT"
"$PYTHON" "$SCRIPT_DIR/source_allowlist_gate_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --receipt "$RESULT/summary/source_allowlist_before.tsv"
# A04 builder followed by the dynamic all-retained-accession tree.
bash "$SCRIPT_DIR/run_major_tables_and_tree_v4.sh" "$CONFIG" "$PROJECT_ROOT" "$SOURCE"
"$PYTHON" "$SCRIPT_DIR/prepare_reference_plot_data_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --result-dir "$RESULT"
"$PYTHON" "$SCRIPT_DIR/plot_gene_variant_reference_v10.py" --config "$CONFIG" --result-dir "$RESULT" --figure-dir "$RESULT/figures/work"
"$RSCRIPT" "$SCRIPT_DIR/plot_haplotype_network_v10.R" "$CONFIG" "$RESULT" "$RESULT/figures/work"
"$RSCRIPT" "$SCRIPT_DIR/plot_hap_map_v10.R" "$CONFIG" "$RESULT" "$RESULT/figures/work"
"$RSCRIPT" "$SCRIPT_DIR/plot_sample_tree_reference_v10.R" "$CONFIG" "$RESULT" "$RESULT/figures/work"
"$RSCRIPT" "$SCRIPT_DIR/plot_selection_scan_v4.R" "$CONFIG" "$RESULT" "$RESULT/figures/work"
"$PYTHON" "$SCRIPT_DIR/stamp_png_dpi_v4.py" --dpi "$(cfg png_dpi)" "$RESULT"/figures/work/*.png
mkdir -p "$RESULT/figures/Fig1_Haplotype" "$RESULT/figures/Fig2_SelectionScan"
"$PYTHON" "$SCRIPT_DIR/compose_two_mainfig_v4.py" --config "$CONFIG" --fig1-panels "$RESULT/figures/work/var_gene_vat_tab.pdf" "$RESULT/figures/work/major_network.pdf" "$RESULT/figures/work/all_accession_tree.pdf" "$RESULT/figures/work/major_area_map.pdf" --fig1-png-panels "$RESULT/figures/work/var_gene_vat_tab.png" "$RESULT/figures/work/major_network.png" "$RESULT/figures/work/all_accession_tree.png" "$RESULT/figures/work/major_area_map.png" --fig1-output "$RESULT/figures/Fig1_Haplotype/Fig1_Haplotype.pdf" --fig1-png-output "$RESULT/figures/Fig1_Haplotype/Fig1_Haplotype.png"
cp "$RESULT/figures/work/Fig2_SelectionScan.pdf" "$RESULT/figures/Fig2_SelectionScan/Fig2_SelectionScan.pdf"; cp "$RESULT/figures/work/Fig2_SelectionScan.png" "$RESULT/figures/Fig2_SelectionScan/Fig2_SelectionScan.png"
mkdir -p "$RESULT/figures/Fig1_Haplotype/panels" "$RESULT/figures/Fig2_SelectionScan/panels"
for p in var_gene_vat_tab major_network all_accession_tree major_area_map; do cp "$RESULT/figures/work/$p.pdf" "$RESULT/figures/Fig1_Haplotype/panels/$p.pdf"; cp "$RESULT/figures/work/$p.png" "$RESULT/figures/Fig1_Haplotype/panels/$p.png"; done
for p in Pi TajimaD Fst Pi_ratio; do cp "$RESULT/figures/work/${p}_broad_local.pdf" "$RESULT/figures/Fig2_SelectionScan/panels/${p}_broad_local.pdf"; cp "$RESULT/figures/work/${p}_broad_local.png" "$RESULT/figures/Fig2_SelectionScan/panels/${p}_broad_local.png"; done
"$PYTHON" "$SCRIPT_DIR/simulate_visual_review_v4.py" --result-dir "$RESULT"
"$PYTHON" "$SCRIPT_DIR/visual_review_gate_v4.py" --result-dir "$RESULT" --template-only
"$PYTHON" "$SCRIPT_DIR/visual_review_gate_v4.py" --result-dir "$RESULT" --review "${VISUAL_REVIEW_FILE:-$RESULT/summary/figure_visual_review_template.tsv}"
"$PYTHON" "$SCRIPT_DIR/write_manuscript_two_mainfig_v4.py" --config "$CONFIG" --result-dir "$RESULT"
"$PYTHON" "$SCRIPT_DIR/source_allowlist_gate_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --receipt "$RESULT/summary/source_allowlist_before.tsv" --verify
"$PYTHON" "$SCRIPT_DIR/qa_reference_two_mainfig_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --result-dir "$RESULT"
"$PYTHON" "$SCRIPT_DIR/build_release_two_mainfig_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --result-dir "$RESULT" --release-dir "$RELEASE"
"$PYTHON" "$SCRIPT_DIR/write_table_readmes_v4.py" --config "$CONFIG" --table-root "$RELEASE/table"
"$PYTHON" "$SCRIPT_DIR/qa_table_readmes_v4.py" --table-root "$RELEASE/table"
"$PYTHON" "$SCRIPT_DIR/zip_release_v4.py" --release-dir "$RELEASE" --zip "$ZIP" --manifest "$MANIFEST"
"$PYTHON" "$SCRIPT_DIR/verify_release_two_mainfig_v4.py" --release-dir "$RELEASE" --zip "$ZIP" --manifest "$MANIFEST"
"$PYTHON" "$SCRIPT_DIR/source_allowlist_gate_v4.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --receipt "$RESULT/summary/source_allowlist_before.tsv" --verify
"$0" "$CONFIG" "$PROJECT_ROOT" --verify-only
