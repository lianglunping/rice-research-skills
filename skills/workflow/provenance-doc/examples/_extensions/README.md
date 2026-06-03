# `_extensions/` — Project-Specific Stat Section Stubs

This directory holds **example extension fragments** that the example provenance documents (`../full-pipeline-sealed.md`, `../lite-analysis.md`) reference via their YAML front-matter.

## Purpose

The provenance-doc skill keeps the **core template (§0–9) generic** — no domain-specific terms, fields, or column names are baked in. Anything project-specific (e.g. variant-class distributions, family hit counts, gene-level stats) lives outside the core in pluggable extension files.

A main provenance document declares the extensions it wants:

```yaml
extension_sections:
  - id: domain_stat_a
    title: "Domain stat A"
    source: _extensions/domain_stat_a.md
    status: verified
```

`scripts/render_doc.py` reads each `source` file and inlines its content under the document's "业务统计扩展" section.

## Files in this directory

| File | Role | Used by |
|------|------|---------|
| `domain_stat_a.md` | Generic stat-table stub (placeholder for any domain stat A) | `examples/full-pipeline-sealed.md`, `examples/lite-analysis.md` |
| `domain_stat_b.md` | Generic stat-table stub (placeholder for any domain stat B) | `examples/full-pipeline-sealed.md` |
| `domain_cohort.md` | Generic cohort-description stub | `examples/full-pipeline-sealed.md` |

These stubs are intentionally **content-free placeholders** — they exist so that:

1. The example provenance documents have a real `source:` target (preventing render_doc.py / status_check.py from reporting a missing-extension error during the skill's own E2E tests).
2. New users can copy this directory layout (`<project>/_extensions/`) and replace stub content with their actual domain statistics, without touching the core template.

## When you are using the skill (not editing it)

Create your own `_extensions/{your_id}.md` next to your provenance document, fill it with your domain stats (variant tables, model metrics, sample registries, etc.), then declare it in the document's `extension_sections` front-matter list.

The core template remains untouched and reusable across pipelines.
