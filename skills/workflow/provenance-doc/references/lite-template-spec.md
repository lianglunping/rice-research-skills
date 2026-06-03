# Lite Template Spec — §0-5 Field Definitions
<!-- Plan Section: Chunk 7, Task 4-2 — References -->
<!-- Plan Version: 2026-04-30-provenance-doc-plan.md -->

Lite template (`lite.md.j2`) is used for one-off analysis tasks under
`analysis/{name}/provenance.md`. Does **not** require `version` or
`prior_version`. Terminal state: `verified` (not sealed).

---

## Front-Matter Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `template` | enum: `lite` | Must be literal `lite` |
| `status` | enum | One of `draft / numbers-pending / verification-ready / verified` |
| `created_at` | date | ISO-8601 date e.g. `2026-04-30` |
| `sealed_at` | null | Always null for lite (no sealing) |
| `owner` | string | Username or analyst name |
| `project` | string | Project identifier |
| `extension_sections` | array | List of extension slot objects (may be empty `[]`) |
| `verification` | object | Verification policy settings |

Note: `version` and `prior_version` are **not** used in lite template.

---

## §0 — Status and Scope

- **Current status**: one of the five state-machine values
- **Task objective**: one-sentence goal of this analysis
- **Directory**: working directory relative to repo root
- **Owner**: same as front-matter `owner`
- **Applicable boundary**: what this document covers vs. what it excludes
  (e.g., "covers filtering step only; variant calling covered by run_config.yaml")

---

## §1 — Inputs and Assumptions

### 1.1 Inputs
Bulleted list: `` `path` — purpose ``. Each input that a claim depends on must
be listed. Paths should be relative or parameterized, not absolute.

### 1.2 Key Assumptions
Numbered list of assumptions baked into the analysis. If an assumption is
invalidated later, link to the `evolution.md` entry.

### 1.3 Known Gaps
Bulleted list of things **not** covered by this document or analysis.
Each gap should have a one-line rationale for why it is out of scope.

---

## §2 — Code Path, Module Structure, and Runtime Environment

### 2.1 Code Root
Three fields: `repo`, `commit`, `local`. Commit must be a SHA or tag.

### 2.2 Key Scripts/Module Tree
`tree -L 2` output scoped to the relevant subdirectory.

### 2.3 Entry Functions
Table: `name | path | description`. Minimal — top 3-5 entry points only.

### 2.4 Software Versions (Top 5-10)
Two-column table: `software | version`. Exact pinned versions only.

### 2.5 Config Links
Bulleted list of config file paths. No inline content — link only.

---

## §3 — Usage and Reproduction Steps

### 3.1 Minimal Reproduce Command
Single copy-pasteable command. Must be runnable from repo root.

### 3.2 Parameters
Bulleted list: `` `name` = `value` (explanation) ``. Only the most
consequential parameters. Full config lives in `run_config.yaml`.

### 3.3 Random Seeds
All seeds, one per tool. If deterministic by construction, state that
explicitly: `seed = N/A — deterministic`.

### 3.4 Expected Output Paths
Directory tree of expected artifacts. Must match §4 artifact table.

### 3.5 Runtime Notes
Memory/CPU floor, OS constraints, any required environment variables.

---

## §4 — Output Artifacts and Verified Claims

### 4.1 Artifact Table
Six-column table matching lite template columns:
`artifact_id | path | format | size | record_count | checksum`

Size and checksum are populated by `aggregate_meta.py`. Record count is
the number of logical records (rows, variants, images, etc.).

### 4.2 Claim Verification Table (Merged)
Six-column table: `claim_id | claim_text | value | command | observed_result | status`

Lite template merges claim and artifact into a single table for simplicity.
All numeric assertions must appear here. `status` ∈ {`verified`, `unverified`, `waived`}.

---

## §5 — Relations, Changes, and Limitations

### 5.1 Related Documents
Bulleted list with relation type: `audit_*.md`, `evolution.md`,
`DECISION_LOG.md`, `run_config.yaml`. Format: `kind: path`.

### 5.2 Change Summary
One-paragraph description of what changed from the previous state of this
analysis (or "Initial creation" for new documents).

### 5.3 Known Limitations / TODO
Checklist of outstanding items. Items are not blocking for `verified` status
but must be tracked for future reference.

---

## Extension Sections (Optional)

Optional domain-specific statistics appended after §5. Declared in
front-matter `extension_sections`. See `references/extension-mechanism.md`.
Extension content is rendered inline from `_extensions/{id}.md`.
