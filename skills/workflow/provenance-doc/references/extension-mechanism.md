# Extension Mechanism
<!-- Plan Section: Chunk 7, Task 4-2 — References -->
<!-- Plan Version: 2026-04-30-provenance-doc-plan.md -->

Extension slots allow domain-specific statistics tables to be embedded in a
provenance document without polluting the core template with domain-specific
terms. The core templates (`full.md.j2`, `lite.md.j2`) declare extension slots
in front-matter; content lives in separate `_extensions/{id}.md` files.

---

## Front-Matter Declaration Schema

```yaml
extension_sections:
  - id: domain_stat_a           # required; pattern: ^[a-z][a-z0-9_]{2,40}$
    title: "Domain Stat A"      # required; max 80 chars; human-readable heading
    source: _extensions/domain_stat_a.md   # required; relative path
    status: verified            # required; enum: draft | verified | waived
    waiver_reason: ""           # required when status=waived; min 10 chars
```

### Field Constraints

| Field | Type | Constraint |
|-------|------|-----------|
| `id` | string | Pattern `^[a-z][a-z0-9_]{2,40}$`; must be unique within document |
| `title` | string | Max 80 characters |
| `source` | string | Relative path from document directory; no `..` traversal; no absolute path |
| `status` | enum | One of `draft`, `verified`, `waived` |
| `waiver_reason` | string | Empty string when status ≠ waived; min 10 chars when status = waived |

---

## Status Gate Rules

The parent document's state machine **blocks progression** to `verified` unless
all declared extension sections satisfy one of:

1. `status: verified` — content file exists and has been manually confirmed
2. `status: waived` — waiver_reason has ≥10 characters explaining why verification
   was skipped (e.g., "preliminary results, not cited in report")

An extension with `status: draft` blocks the parent document from reaching
`verification-ready`. The `status_check.py` guard `all_complete_and_extensions_verified`
enforces this constraint.

---

## Extension File Format

Extension files (`_extensions/{id}.md`) are plain Markdown fragments rendered
inline after the main document body. They must not contain YAML front-matter.

Recommended format for a statistics table:

```markdown
| metric | value |
|--------|-------|
| Count A | 1,234 |
| Count B | 567 |
| Ratio | 0.46 |
```

Extension files are included using Jinja2 `{% include %}` in the template.
Missing files are silently ignored at render time (`ignore missing` flag) but
flagged by `status_check.py` when status is not `waived`.

---

## Path Safety

`new_provenance.py` and `status_check.py` enforce these path safety rules:

- No `..` components in `source` path
- No absolute paths (must not start with `/`)
- Path must be a descendant of the document's parent directory

Violation causes a hard error with exit code 1.

---

## Rendering

```bash
# Render document with inline extension content
uv run --with pyyaml \
    "$HOME/.codex/skills/provenance-doc"/scripts/render_doc.py \
    --doc analysis/foo/provenance.md
```

The rendered output is written to stdout. Extensions are included verbatim.
If an extension file is missing and status is not `waived`, a warning is
printed to stderr but rendering continues with a placeholder.

---

## Lint Scope

Extension file content is **not** scanned by `lint_template.py` by default,
because extension files are the designated location for domain-specific terms.
Only the core templates and `references/*.md` are scanned.

If domain-specific terms appear in the core templates or references, the lint
check will fail with exit code 1 and list the offending lines.
