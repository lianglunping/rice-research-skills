#!/usr/bin/env bash
# Static documentation-contract check; does not measure model activation accuracy.
set -euo pipefail
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for token in 'name: provenance-doc' 'provenance.md' 'verification-ready' 'sealed' 'new_provenance.py' 'status_check.py'; do
  if ! grep -qF "$token" "$SKILL/SKILL.md"; then
    printf 'Missing documented interface: %s\n' "$token" >&2
    exit 1
  fi
done
printf 'Provenance documentation contract passed.\n'
