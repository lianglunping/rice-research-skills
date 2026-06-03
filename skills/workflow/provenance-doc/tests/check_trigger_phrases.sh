#!/usr/bin/env bash
# Plan Section: Chunk 6 — Phase 3, Fix-10 (check_trigger_phrases.sh)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#
# Verifies the SKILL.md description contains all trigger phrases from fixture.
# Fail-soft when SKILL.md is missing (Chunk 7 not yet written).
set -euo pipefail

SKILL_MD="$HOME/.codex/skills/provenance-doc/SKILL.md"
PHRASES="$HOME/.codex/skills/provenance-doc/tests/fixtures/trigger_phrases.txt"

# TODO: SKILL.md not yet written (Chunk 7) — fail-soft until it exists
if [ ! -f "$SKILL_MD" ]; then
    echo "WARN: SKILL.md not found at $SKILL_MD"
    echo "TODO: SKILL.md not yet written (Chunk 7) — skipping trigger phrase check"
    echo "covered=0/0 (skipped)"
    exit 0
fi

if [ ! -f "$PHRASES" ]; then
    echo "ERROR: trigger_phrases.txt not found at $PHRASES"
    exit 1
fi

miss=0
total=0
while IFS= read -r p; do
    [ -z "$p" ] && continue
    total=$((total + 1))
    if ! grep -qF "$p" "$SKILL_MD"; then
        echo "MISS: $p"
        miss=$((miss + 1))
    fi
done < "$PHRASES"

echo "covered=$((total - miss))/$total"
[ $miss -eq 0 ] || exit 1
