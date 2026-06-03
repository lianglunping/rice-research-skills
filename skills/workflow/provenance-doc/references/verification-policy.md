# Verification Policy
<!-- Plan Section: Chunk 7, Task 4-2 — References -->
<!-- Plan Version: 2026-04-30-provenance-doc-plan.md -->

Documents the state machine, claim verification rules, waiver policy, and
remote command policy for provenance documents. See also the schema directory
for the machine-readable state-gate table (`schema/transitions.yaml`).

---

## State Machine

```
draft → numbers-pending → verification-ready → verified → sealed
```

### States

| State | Meaning |
|-------|---------|
| `draft` | Document created; no numeric claims with values yet |
| `numbers-pending` | At least one claim has a value but is missing a verify command |
| `verification-ready` | All claims have value + command; ready to run |
| `verified` | All commands run; observed_result recorded; extensions verified or waived |
| `sealed` | Document locked (chmod 444); only in `archive/legacy_results/` |

`sealed` is a **terminal state**. Use `unseal_unsafe.py --reason "..."` to
reopen a sealed document. Reopening creates an audit trail entry.

---

## Legal Transitions (9 total)

| From | To | Guard |
|------|----|-------|
| `draft` | `numbers-pending` | any claim has a value |
| `draft` | `verification-ready` | all claims have value + command (shortcut) |
| `draft` | `verified` | no claims OR all claims complete (pure-text doc) |
| `numbers-pending` | `verification-ready` | all commands filled in |
| `numbers-pending` | `draft` | all values removed (rollback) |
| `verification-ready` | `verified` | all commands run; all extensions verified/waived |
| `verification-ready` | `numbers-pending` | any claim loses its command (rollback) |
| `verified` | `sealed` | document in `archive/legacy_results/` path |
| `verified` | `numbers-pending` | new claim added without observed_result (rollback) |

### Illegal Transitions (5 examples)

| From | To | Reason |
|------|----|--------|
| `draft` | `sealed` | skip-states forbidden |
| `sealed` | `draft` | sealed is terminal; use unseal_unsafe.py |
| `sealed` | `verified` | sealed is terminal; use unseal_unsafe.py |
| `numbers-pending` | `sealed` | skip-states forbidden |
| `verification-ready` | `sealed` | skip-states forbidden |

---

## Claim Verification Rules

1. **Every numeric assertion** in the document body must have a corresponding
   row in §5 (full) or §4.2 (lite) with `claim_id`, `value`, and `command`.

2. **`command`** must be a shell command that prints the asserted value to stdout.
   The command is run by `verify_claims.py` and its output is stored in
   `observed_result`.

3. **`observed_result`** is populated automatically by `verify_claims.py`.
   Do not fill it manually — the script will flag a mismatch.

4. **`status`** is set to `verified` when the verification command exits 0 and
   produces non-empty output. The implementation in `verify_claims.py` does NOT
   automatically compare `observed_result` to `value`; the human author is
   responsible for visually confirming the match. Mismatch handling is on the
   author's roadmap (see SKILL TODO).

---

## Waiver Policy

A claim may be waived when running the verification command is not feasible
(e.g., data no longer accessible, command depends on an external service).

```yaml
status: waived
waiver_reason: "Source data decommissioned 2026-03-01; value archived in audit_decommission.md"
```

Waiver requirements:
- `waiver_reason` must be ≥ 10 characters
- Waiver must name the reason for non-verifiability
- Waiver does **not** block document progression to `verified`

For extension sections, same rules apply: `status: waived` + `waiver_reason`.

---

## Remote Command Policy

By default, `verify_claims.py` **rejects** commands containing:
- `ssh `
- `scp `
- `rsync `

To allow remote commands, pass `--allow-remote` flag. This is intentional:
remote commands depend on network availability and server state, which reduces
reproducibility. Document the reason for remote commands in `waiver_reason`
or in the relevant `audit_*.md`.

Remote command timeout is configurable per document:

```yaml
verification:
  remote_command_timeout_sec: 300   # default; max 1800
```

---

## Dangerous Command Rejection

`verify_claims.py` unconditionally rejects commands matching these patterns
regardless of `--allow-remote`:

- `rm -rf`
- `mkfs`
- `dd if=`
- `:(){:|:&};:` (fork bomb)

These patterns cannot be overridden. If a legitimate command is rejected,
use `waiver_reason` to document that the command was manually run and the
result was recorded by hand.

---

## Dry-Run Mode

```bash
uv run --with pyyaml \
    "$HOME/.codex/skills/provenance-doc"/scripts/verify_claims.py \
    --doc analysis/foo/provenance.md --dry-run
```

In dry-run mode, commands are printed but not executed. Exit code 0 always.
Use for reviewing what would be run before committing to execution.

---

## Status Check Tool

```bash
uv run --with pyyaml --with jsonschema python3 \
    "$HOME/.codex/skills/provenance-doc"/scripts/status_check.py \
    analysis/foo/provenance.md
```

Checks:
1. Front-matter validates against `schema/frontmatter.schema.yaml`
2. Current status is reachable from `draft` via legal state changes
3. Guards for the current status are satisfied by document content
4. Extension sections referenced in front-matter exist (or are waived)

Exit code 0 = valid; exit code 1 = validation failure with reason.
