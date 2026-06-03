# Full Template Spec — §0-9 Field Definitions
<!-- Plan Section: Chunk 7, Task 4-2 — References -->
<!-- Plan Version: 2026-04-30-provenance-doc-plan.md -->

Full template (`full.md.j2`) is used for pipeline version archiving under
`archive/legacy_results/v{N}/provenance.md`. Requires `version` and
`prior_version` in front-matter. Terminal state: `sealed`.

---

## Front-Matter Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `template` | enum: `full` | Must be literal `full` |
| `status` | enum | One of `draft / numbers-pending / verification-ready / verified / sealed` |
| `version` | string | Pattern `^v[0-9]{1,3}(\.[0-9]{1,2}){0,2}$` e.g. `v1.0` |
| `created_at` | date | ISO-8601 date e.g. `2026-04-30` |
| `sealed_at` | date or null | Required when status=sealed |
| `owner` | string | Username or analyst name |
| `project` | string | Project identifier |
| `prior_version` | string or null | Previous version tag; null for first version |
| `delta_summary_path` | string or null | Relative path to delta summary file |
| `extension_sections` | array | List of extension slot objects (may be empty `[]`) |
| `verification` | object | Verification policy settings |

---

## §0 — Document Identity and Scope

### 0.1 Analysis Objective
One-paragraph description of the analysis goal. What question is being answered?

### 0.2 Data Cohort
Describe the cohort: sample count, key attributes, data types. Reference the
manifest or intake document. **Do not embed domain-specific identifiers here**
— those belong in extension sections.

### 0.3 Inclusion and Exclusion Criteria
Bulleted list of which samples/records are in scope and which are excluded,
with brief rationale. Link to `run_config.yaml` for full parameter details.

### 0.4 Known Caveats and Interpretation Limits
One-line summary of each caveat, with a link to the associated `audit_*.md`
or `evolution.md` file where the caveat is documented in detail.

---

## §1 — Workflow Overview

### 1.1 Processing Pipeline
ASCII or Mermaid diagram of the processing steps. Keep to ≤10 nodes.

### 1.2 Input Registry
Table: `data_type | path | purpose`. Paths must be relative or parameterized.

### 1.3 Output Registry (High Level)
One-line pointers to §4 artifact table. No raw numbers here.

---

## §2 — Code, Software, and Version Registry

### 2.1 Code Root
| Item | Value |
|------|-------|
| repo URL | git remote URL |
| commit SHA | 40-char hex |
| branch | branch name |
| local path | relative or parameterized path |

### 2.2 Module Tree
`tree -L 3` output, trimmed to relevant subdirs.

### 2.3 Entry Scripts
Table: `name | path | description`. Path is relative to repo root.

### 2.4 Dependency Software + Versions
Table: `software | version | install_method`. Use exact pinned versions.

### 2.5 Config File Links
Bulleted list of config file paths with one-line descriptions.

---

## §3 — Reproduction Guide

### 3.1 Minimal Reproduce Command
Single copy-pasteable shell command. Must be self-contained or reference a
documented config file.

### 3.2 Key Parameters
Table: `parameter | value | explanation`. Only the ≤10 most consequential
parameters. Full config lives in `run_config.yaml`.

### 3.3 Random Seeds
All seeds used, one per tool. Format: `tool: seed = N`.

### 3.4 Expected Output Paths
Directory tree of expected outputs after a successful run.

### 3.5 Runtime Environment Notes
GPU/CPU requirements, memory floor, OS constraints, server alias.

---

## §4 — Artifact Registry

> Auto-populated by `aggregate_meta.py`. **Do not manually edit** checksum,
> size, or record_count fields.

| Column | Type | Source |
|--------|------|--------|
| `artifact_id` | string | Unique slug, e.g. `filtered_table` |
| `role` | string | `primary / intermediate / diagnostic` |
| `path` | string | Relative path to file |
| `format` | string | File format, e.g. `TSV`, `CSV`, `JSON`, `PNG`, `PDF` |
| `size` | int (bytes) | From `.meta.yaml` |
| `record_count` | int | Number of records (rows / items / entries) |
| `checksum` | string | SHA-256 first 12 chars |
| `created_at` | date | ISO-8601 |
| `producer` | string | Script that created the artifact |
| `meta_yaml` | string | Path to companion `.meta.yaml` |

---

## §5 — Claim Verification Registry

One row per verifiable claim. All numerical claims must have an entry.

| Column | Required | Description |
|--------|----------|-------------|
| `claim_id` | yes | Unique slug, e.g. `c01` |
| `claim_text` | yes | Human-readable assertion |
| `value` | yes | The asserted number or category |
| `source_artifact` | yes | Which artifact supports the claim |
| `command` | conditional | Shell command to verify; required unless status=waived |
| `observed_result` | conditional | Result of running command; required for verified |
| `status` | yes | `verified / unverified / waived` |
| `waiver_reason` | conditional | Required if status=waived; min 10 chars |

---

## §6 — Decision Criteria and Parameters

### 6.1 Parameter Source Files
Bulleted list of config files from which parameters originate.

### 6.2 Interpretation-Critical Parameters (≤30% of full field set)
Table: `parameter | value | impact`. Subset of §3.2 focused on
result interpretation rather than reproduction.

### 6.3 Inclusion Rules (Structured)
Formal inclusion/exclusion criteria, referencing §0.3 with additional detail.

### 6.4 Parameter Deltas from Prior Version
Table: `parameter | old_value | new_value | reason`. Empty if v1.0.

---

## §7 — Version Lineage

### 7.1 Timeline
Table: `version | date | key_change`. All versions including this one.

### 7.2 Delta Summary from Prior Version
Narrative ≤500 words. Detailed evolution lives in `evolution.md` or
`DECISION_LOG.md`. Do not embed raw numbers here — reference §8.

---

## §8 — Version Delta Comparison Table

| Column | Description |
|--------|-------------|
| `metric` | Name of indicator being compared |
| `old` | Value in prior version |
| `new` | Value in this version |
| `delta` | Arithmetic or percentage change |
| `reason` | One-line explanation of why it changed |

---

## §9 — Path Reachability Map

### 9.1 Local Paths
Bulleted: `path — status (note)`. Status: `exists / missing / symlink`.

### 9.2 Remote/Server Paths
Bulleted: `host:path — status (note)`. Status same as above.

---

## Extension Sections

Domain-specific statistics tables added via extension slot mechanism. See
`references/extension-mechanism.md` for the declaration schema and status
gate rules. Extension content is rendered inline after §9.
