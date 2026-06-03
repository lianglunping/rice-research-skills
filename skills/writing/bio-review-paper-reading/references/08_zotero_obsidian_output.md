# Zotero and Obsidian Output

Zotero and Obsidian are first-class targets, but writes are not default.

## Write Safety

- Default mode is `dry_run`.
- Do not delete, overwrite, move, retag, or rename Zotero or Obsidian content without explicit user confirmation.
- If the target note exists, prepare a preview patch or conflict report.
- If citekey, DOI, title, or Zotero item key conflict, stop write planning.

## Obsidian Main Note Frontmatter

```yaml
type: literature_note
paper_type: review
review_type:
citekey:
doi:
zotero_item_key:
title:
year:
journal:
authors:
field:
scope:
core_routes:
consensus_count:
controversy_count:
gap_count:
external_update_status:
research_seed_count:
review_next:
last_reviewed:
related_seeds:
related_original_papers_to_backtrack:
source_note:
review_chain:
tags:
```

## Suggested Files

```text
Literature/Reviews/{citekey}.md
Literature/Frameworks/{citekey}-field-framework.md
Literature/Research Seeds/{citekey}-proposal-seeds.md
Literature/Backtracking Queue/{citekey}-original-papers-to-check.md
```

## Obsidian Link Contract

Use stable links:

```text
Review main note -> [[{citekey}-field-framework]], [[{citekey}-proposal-seeds]]
Framework note -> source_note: [[{citekey}]]
Research seed -> source_note: [[{citekey}]], source_gap: gap ID
Backtracking queue -> source_note: [[{citekey}]], target_original_papers: citekeys or provisional IDs
Periodic review -> review_chain: [[{citekey}]]
```

Use IDs such as `{citekey}-G01` for gaps, `{citekey}-R01` for routes, and `{citekey}-S01` for research seeds.

## Zotero Tag Proposals

Use cautious tags:

```text
paper/review
status/framework-reconstructed
status/external-update-needed
gap/has-research-seeds
backtrack/original-evidence-needed
```

For concrete Markdown note skeletons, read [12_obsidian_note_templates.md](12_obsidian_note_templates.md).
For dry-run patch object shape, read [13_dry_run_patch_spec.md](13_dry_run_patch_spec.md).
