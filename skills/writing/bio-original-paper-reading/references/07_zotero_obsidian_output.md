# Zotero and Obsidian Output

Zotero and Obsidian are first-class targets, but writes are not default.

## Write Safety

- Default mode is `dry_run`.
- Do not delete, overwrite, move, retag, or rename Zotero or Obsidian content without explicit user confirmation.
- If the target note exists, prepare a preview patch or conflict report instead of overwriting.
- If citekey, DOI, title, or Zotero item key conflict, stop write planning and emit a conflict report.

## Obsidian Main Note Frontmatter

```yaml
type: literature_note
paper_type: original
citekey:
doi:
zotero_item_key:
title:
year:
journal:
authors:
organism:
trait:
genes:
methods:
data_types:
status: deep_read
figure_reading_status:
discussion_audit_status:
critical_audit_status:
evidence_strength_overall:
breeding_relevance:
mutagenesis_relevance:
review_next:
last_reviewed:
related_figures:
related_seeds:
related_claims:
source_note:
review_chain:
tags:
```

## Suggested Obsidian Files

```text
Literature/Deep Reading/{citekey}.md
Literature/Figures/{citekey}-Fig1.md
Literature/Figures/{citekey}-Fig2.md
Literature/Research Seeds/{citekey}-seeds.md
Literature/Critical Lessons/{citekey}-lessons.md
```

## Obsidian Link Contract

Use stable wiki-link targets when preparing notes:

```text
Main note -> [[{citekey}-Fig1]], [[{citekey}-Fig2]]
Figure card -> source_note: [[{citekey}]]
Research seed -> source_note: [[{citekey}]], related_claims: claim IDs
Critical lessons -> source_note: [[{citekey}]], related_figures: figure IDs
Periodic review -> review_chain: [[{citekey}]]
```

Use claim IDs such as `{citekey}-C01` and panel IDs such as `{citekey}-Fig2b` so future synthesis can link claims, figures, and research seeds.

## Zotero Update Plan

```yaml
target_item:
proposed_tags_add:
proposed_collections:
proposed_note_title:
proposed_note_body_summary:
risk_level: low|medium|high
requires_confirmation: true
```

Never default to removing tags, moving collections, overwriting notes, modifying metadata, or renaming attachments.

For concrete Markdown note skeletons, read [11_obsidian_note_templates.md](11_obsidian_note_templates.md).
For dry-run patch object shape, read [12_dry_run_patch_spec.md](12_dry_run_patch_spec.md).
