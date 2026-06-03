#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

status=0

while IFS= read -r -d '' skill_dir; do
  skill_md="$skill_dir/SKILL.md"
  if [[ ! -f "$skill_md" ]]; then
    printf 'Missing SKILL.md: %s\n' "$skill_dir" >&2
    status=1
    continue
  fi
  if ! grep -Eq '^name:[[:space:]]*.+' "$skill_md"; then
    printf 'Missing name frontmatter: %s\n' "$skill_md" >&2
    status=1
  fi
  if ! grep -Eq '^description:[[:space:]]*.+|^description:[[:space:]]*[>|]' "$skill_md"; then
    printf 'Missing description frontmatter: %s\n' "$skill_md" >&2
    status=1
  fi
done < <(find skills -mindepth 2 -maxdepth 2 -type d -print0)

if find . -name '.DS_Store' -o -name '__pycache__' -o -name '*.pyc' | grep -q .; then
  printf 'Runtime cache files are present.\n' >&2
  find . -name '.DS_Store' -o -name '__pycache__' -o -name '*.pyc' >&2
  status=1
fi

if find skills -path '*/temp_tests/*' -o -path '*/scratch/*' | grep -q .; then
  printf 'Temporary test or scratch files are present under skills/.\n' >&2
  find skills -path '*/temp_tests/*' -o -path '*/scratch/*' >&2
  status=1
fi

if [[ "$status" -eq 0 ]]; then
  printf 'Skill validation passed.\n'
fi

exit "$status"
