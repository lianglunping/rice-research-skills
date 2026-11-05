#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 3 ]]; then echo "Usage: $0 CONFIG PROJECT_ROOT SOURCE_RESULT" >&2; exit 2; fi
CONFIG="$1"; PROJECT_ROOT="$2"; SOURCE_RESULT="$3"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cfg(){ awk -F $'\t' -v k="$1" 'NR>1&&$1==k{print $2;exit}' "$CONFIG"; }
[[ "$(cfg major_set_mode)" == "phased_chromosome_count_ge" ]] || { echo "v4 requires phased_chromosome_count_ge" >&2; exit 3; }
RESULT_DIR="$PROJECT_ROOT/results/$(cfg run_id)"
mkdir -p "$RESULT_DIR"
"${PYTHON:-python3}" "$SCRIPT_DIR/build_publication_tables_v5.py" --config "$CONFIG" --project-root "$PROJECT_ROOT" --source-result "$SOURCE_RESULT" --result-dir "$RESULT_DIR"
bash "$SCRIPT_DIR/build_sample_ibs_tree_v5.sh" "$CONFIG" "$SOURCE_RESULT" "$RESULT_DIR"
