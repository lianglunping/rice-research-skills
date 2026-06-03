#!/usr/bin/env bash
# Plan Section: Chunk 6 — Phase 3, Task 3-3 + Fix-8 + Fix-9 + Fix-11 (run_all.sh)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#
# Run all E2E cases. Each case is self-contained; run_case increments FAIL on non-zero exit.
# Final stat line: PASS: N  FAIL: M
set -euo pipefail

SKILL="$HOME/.codex/skills/provenance-doc"
PASS=0
FAIL=0

run_case() {
    local name="$1"
    local cmd="$2"
    echo "=== $name ==="
    if bash -c "$cmd"; then
        echo "PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $name"
        FAIL=$((FAIL + 1))
    fi
    echo
}

# -----------------------------------------------------------------------
# E2E-1: v1.3.2 reverse-engineering mapping coverage check
# -----------------------------------------------------------------------
run_case "E2E-1 v132-mapping" '
    set -euo pipefail
    uv run --with pyyaml python3 "$HOME/.codex/skills/provenance-doc"/tests/check_v132_mapping.py
'

# -----------------------------------------------------------------------
# E2E-2: lite create -> status_check OK
# -----------------------------------------------------------------------
run_case "E2E-2 lite-loop" '
    set -euo pipefail
    rm -f /tmp/e2e2_prov.md
    uv run "$HOME/.codex/skills/provenance-doc"/scripts/new_provenance.py \
        --template lite --out /tmp/e2e2_prov.md --owner u --project p
    uv run --with pyyaml --with jsonschema python3 \
        "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py /tmp/e2e2_prov.md
    rm -f /tmp/e2e2_prov.md
'

# -----------------------------------------------------------------------
# E2E-3: render_doc with valid extension -> inlined
# -----------------------------------------------------------------------
run_case "E2E-3 extension-happy" '
    set -euo pipefail
    rm -rf /tmp/e2e3_dir
    mkdir -p /tmp/e2e3_dir/_extensions
    cat > /tmp/e2e3_dir/_extensions/stat_a.md <<'\''EOF'\''
| metric | value |
|--------|-------|
| n | 42 |
EOF
    cat > /tmp/e2e3_dir/prov.md <<'\''EOF'\''
---
template: lite
status: draft
created_at: 2026-04-30
sealed_at: null
owner: u
project: p
extension_sections:
  - id: stat_a
    title: "Stats A"
    source: _extensions/stat_a.md
    status: verified
---
# body
EOF
    uv run --with pyyaml \
        "$HOME/.codex/skills/provenance-doc"/scripts/render_doc.py \
        --doc /tmp/e2e3_dir/prov.md --fail-on-missing-extension
    grep -q "42" /tmp/e2e3_dir/prov.md
    rm -rf /tmp/e2e3_dir
'

# -----------------------------------------------------------------------
# E2E-4: render_doc with missing extension + --fail-on-missing-extension -> exit 1
# -----------------------------------------------------------------------
run_case "E2E-4 extension-sad" '
    set -euo pipefail
    rm -rf /tmp/e2e4_dir
    mkdir -p /tmp/e2e4_dir
    cat > /tmp/e2e4_dir/prov.md <<'\''EOF'\''
---
template: lite
status: draft
created_at: 2026-04-30
sealed_at: null
owner: u
project: p
extension_sections:
  - id: missing_ext
    title: "Missing"
    source: _extensions/missing_ext.md
    status: verified
---
EOF
    if uv run --with pyyaml \
           "$HOME/.codex/skills/provenance-doc"/scripts/render_doc.py \
           --doc /tmp/e2e4_dir/prov.md --fail-on-missing-extension; then
        rm -rf /tmp/e2e4_dir
        exit 1
    fi
    rm -rf /tmp/e2e4_dir
'

# -----------------------------------------------------------------------
# E2E-5: sealed doc with draft extension -> status_check rejects
# -----------------------------------------------------------------------
run_case "E2E-5 sealed-gate" '
    set -euo pipefail
    rm -rf /tmp/e2e5_dir
    mkdir -p /tmp/e2e5_dir/archive/legacy_results/v1.0
    cat > /tmp/e2e5_dir/archive/legacy_results/v1.0/provenance.md <<'\''EOF'\''
---
template: full
status: sealed
version: v1.0
created_at: 2026-04-30
sealed_at: 2026-04-30
owner: u
project: p
prior_version: null
delta_summary_path: null
extension_sections:
  - id: stat_a
    title: "A"
    source: _extensions/missing.md
    status: draft
---
EOF
    if uv run --with pyyaml --with jsonschema python3 \
           "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py \
           /tmp/e2e5_dir/archive/legacy_results/v1.0/provenance.md; then
        rm -rf /tmp/e2e5_dir
        exit 1
    fi
    rm -rf /tmp/e2e5_dir
'

# -----------------------------------------------------------------------
# E2E-6: sealed protection — chmod 444 passes --enforce-sealed; chmod 644 fails
# -----------------------------------------------------------------------
run_case "E2E-6 sealed-protection" '
    set -euo pipefail
    rm -rf /tmp/e2e6_dir
    mkdir -p /tmp/e2e6_dir/archive/legacy_results/v1.0
    cat > /tmp/e2e6_dir/archive/legacy_results/v1.0/provenance.md <<'\''EOF'\''
---
template: full
status: sealed
version: v1.0
created_at: 2026-04-30
sealed_at: 2026-04-30
owner: u
project: p
prior_version: null
delta_summary_path: null
extension_sections: []
---
EOF
    chmod 444 /tmp/e2e6_dir/archive/legacy_results/v1.0/provenance.md
    uv run --with pyyaml --with jsonschema python3 \
        "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py \
        /tmp/e2e6_dir/archive/legacy_results/v1.0/provenance.md --enforce-sealed
    chmod 644 /tmp/e2e6_dir/archive/legacy_results/v1.0/provenance.md
    if uv run --with pyyaml --with jsonschema python3 \
           "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py \
           /tmp/e2e6_dir/archive/legacy_results/v1.0/provenance.md --enforce-sealed; then
        rm -rf /tmp/e2e6_dir
        exit 1
    fi
    rm -rf /tmp/e2e6_dir
'

# -----------------------------------------------------------------------
# E2E-7: verify_claims with ssh command, non-interactive stdin -> DENIED on stderr
# Fix-9: verify_claims exits 1 on DENIED; capture combined output with || true,
#        then grep so pipefail does not swallow the DENIED match.
# -----------------------------------------------------------------------
run_case "E2E-7 remote-safety" '
    set -euo pipefail
    rm -f /tmp/e2e7_prov.md
    cat > /tmp/e2e7_prov.md <<'\''EOF'\''
---
template: lite
status: numbers-pending
created_at: 2026-04-30
sealed_at: null
owner: u
project: p
---
| claim_id | claim_text | value | source_artifact | command | observed_result | status | waiver_reason |
|----------|-----------|-------|-----------------|---------|-----------------|--------|---------------|
| c1 | remote ls | 1 | x | ssh remotehost ls | | unverified |  |
EOF
    combined=$(uv run --with pyyaml \
        "$HOME/.codex/skills/provenance-doc"/scripts/verify_claims.py \
        --doc /tmp/e2e7_prov.md < /dev/null 2>&1 || true)
    echo "$combined" | grep -qE "DENIED|SKIP"
    rm -f /tmp/e2e7_prov.md
'

# -----------------------------------------------------------------------
# E2E-8: high-overlap fixture -> lint_no_duplication exits 1
# -----------------------------------------------------------------------
run_case "E2E-8 duplication" '
    set -euo pipefail
    rm -rf /tmp/e2e8_dir
    mkdir -p /tmp/e2e8_dir
    cat > /tmp/e2e8_dir/prov.md <<'\''EOF'\''
---
template: lite
status: draft
created_at: 2026-04-30
sealed_at: null
owner: u
project: p
field_x: 1
field_y: 2
field_z: 3
---
EOF
    cat > /tmp/e2e8_dir/run.yaml <<'\''EOF'\''
template: x
status: y
field_x: a
field_y: b
field_z: c
EOF
    if uv run --with pyyaml \
           "$HOME/.codex/skills/provenance-doc"/scripts/lint_no_duplication.py \
           /tmp/e2e8_dir/prov.md /tmp/e2e8_dir/run.yaml; then
        rm -rf /tmp/e2e8_dir
        exit 1
    fi
    rm -rf /tmp/e2e8_dir
'

# -----------------------------------------------------------------------
# Perf-baseline: new_provenance + status_check + render_doc <= 120s wall-clock
# -----------------------------------------------------------------------
run_case "Perf-baseline <=120s" '
    set -euo pipefail
    rm -rf /tmp/perf_demo_dir
    mkdir -p /tmp/perf_demo_dir/_extensions
    printf "| metric | val |\n|--------|-----|\n| n | 1 |\n" \
        > /tmp/perf_demo_dir/_extensions/stat_a.md
    start=$(date +%s)
    uv run "$HOME/.codex/skills/provenance-doc"/scripts/new_provenance.py \
        --template lite --out /tmp/perf_demo_dir/prov.md --owner u --project p
    uv run --with pyyaml --with jsonschema python3 \
        "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py \
        /tmp/perf_demo_dir/prov.md
    uv run --with pyyaml \
        "$HOME/.codex/skills/provenance-doc"/scripts/render_doc.py \
        --doc /tmp/perf_demo_dir/prov.md
    end=$(date +%s)
    elapsed=$((end - start))
    echo "elapsed=${elapsed}s"
    rm -rf /tmp/perf_demo_dir
    [ $elapsed -le 120 ] || exit 1
'

# -----------------------------------------------------------------------
echo "==================="
echo "PASS: $PASS  FAIL: $FAIL"
exit $FAIL
