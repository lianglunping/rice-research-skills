# Troubleshooting (provenance-doc FAQ)

Common errors, what they mean, and how to fix them. Read this before opening an issue.

---

## Q1. `error: UNPAYWALL_EMAIL is unset` — wait, this is a different skill?

You hit this in `paper-pdf-fetcher`, not `provenance-doc`. The two skills are unrelated; check which command path you ran.

---

## Q2. `status_check.py` says `state: status=numbers-pending but no claim has value`

The front-matter declares `status: numbers-pending`, but §5 论断验证册 has no row whose `value` column is non-empty.

**Fix one of:**

- Set `status: draft` until at least one claim has a `value`.
- Add a real claim row with a non-empty `value` cell.

---

## Q3. `status_check.py` rejects skip-state `draft -> sealed`

State machine rejects skip-states. Each step must move exactly one state forward.

**Fix:** advance through `draft → numbers-pending → verification-ready → verified → sealed` one step at a time. To force-skip during prototyping, edit `status:` directly in front-matter (status_check will still validate the new state's invariants).

---

## Q4. `verify_claims.py` prints `DENIED c1: remote command rejected`

The claim's `command` matches a remote pattern (`ssh `, `scp `, `rsync `, `mcp__ssh-session__`) and stdin is non-interactive (no TTY).

**Fix:**

- Run from an interactive terminal where you can answer `[y/N]` at the prompt, OR
- Pass `--allow-remote` to bypass confirmation when you've already audited the command, OR
- Use `--dry-run` to preview without running.

---

## Q5. `verify_claims.py` prints `REFUSE c1: dangerous pattern in command`

The command contains one of the hardcoded blacklist patterns: `rm -rf`, `> /dev/`, `mkfs`, `dd if=`, fork bomb syntax `:(){`.

**Fix:** rewrite the verification command to avoid the dangerous pattern. Use `wc -l`, `awk`, `grep -c`, `python3 -c`, etc. — the goal is to read/count, not destroy.

---

## Q6. `aggregate_meta.py` exits 1 with `broken-meta: ... mapping values are not allowed here`

A sibling `*.meta.yaml` file has invalid YAML syntax.

**Fix:** open the offending `*.meta.yaml` and fix the YAML (most often: missing space after `:`, or unquoted string with `:` inside). Spec §5.1 declares `fail_closed_on_broken_yaml` as a non-overridable invariant — there is intentionally no flag to bypass this.

---

## Q7. `render_doc.py` says `extension {id}: source not found`

The document's `extension_sections[].source` points to a relative path that doesn't exist on disk.

**Fix:**

- Check the spelling of `source:` (must be relative, no `..`, no absolute paths).
- Create the missing `_extensions/{id}.md` file. An empty file is rejected too — put at least one line of content.
- If the extension is not yet ready, set `status: waived` AND `waiver_reason: "<≥10 chars explaining why deferred>"`.

---

## Q8. `lint_template.py` reports a banned term in a file I think is generic

You probably tripped on a substring match. For example, a filename like `transitions.yaml` embeds a banned root, but `lint_template.py` applies word-boundary matching for a small set of tokens (declared in `WORD_BOUNDARY_TOKENS`), so substrings inside larger identifiers (filenames, variable names) don't trigger a hit. If you genuinely need to use a banned word in a generic context:

**Fix one of:**

- Rephrase to avoid the banned word entirely (preferred).
- Move the content into an `_extensions/{id}.md` file (extensions are not lint-checked against banned terms).
- If the term is legitimately generic English (e.g. "audit") and the lint hit is truly a false positive, add it to `WORD_BOUNDARY_TOKENS` in `scripts/lint_template.py` and document the rationale.

---

## Q9. Trying to upgrade lite → full, but my §0–4 narrative is gone

`new_provenance.py --upgrade lite-to-full` only preserves §5 论断验证册 (claim rows). The lite §0/§1/§2/§3 are free-form narratives that cannot be auto-mapped to the full template's structured fields.

**Fix:** open the new full doc, find the `TODO` placeholders in §0–§3, and copy/paste the relevant content from your lite doc by hand. The script saves you re-typing claims; the prose still needs human transfer.

---

## Q10. Sealed file got modified anyway despite chmod 444

Mode 444 only blocks writes from non-root users that respect filesystem permissions. Some editors (notably `sudo vim`, root-level scripts, `chmod +w` followed by edit) can override.

**Fix:**

- Audit who has root on the machine.
- The intentional escape hatch is `unseal_unsafe.py --reason "<≥30 chars>"` which downgrades status → `verified`, `chmod 644`, AND appends to `evolution.md` for audit trail. Use this rather than ad-hoc edits.
- For shared/multi-user systems, consider WORM storage or git-LFS with branch protection in addition to chmod.

---

## Q11. `check_v132_mapping.py` warns `source file not found locally`

The fixture references `/path/to/project/archive/legacy_results/v1.3.2/provenance.md` — a personal path on the original author's machine.

**Fix:** this is expected when running on any other machine. The warning is non-fatal; the script falls back to validating the mapping arithmetic only (covered ≥ 90%) without comparing against the actual file.

---

## Q12. uv install hangs / takes forever

Large dependency resolutions on first run. This Codex migration does not carry a skill-local .venv. Use `uv run --with pyyaml --with jsonschema --with jinja2` when dependencies are needed, or create a project-local environment explicitly.

**Fix:** prefer project-local or conda environments; for one-off validation use explicit `uv run --with ...` commands and record them in provenance.

---

## Reporting issues

If you hit something not in this FAQ:

1. Run `bash "$HOME/.codex/skills/provenance-doc"/tests/e2e/run_all.sh` first — if it fails, the install or contract is broken.
2. Check the most recent backup at `~/.codex/skills/provenance-doc.backup.*/` to compare.
3. Review the spec at `/path/to/provenance-doc-design.md` for the canonical contract.
