# Zotero and Obsidian Sync Contract

This skill is read-first and dry-run by default.

## Input Sources

Possible sources:

- Obsidian vault path,
- folder of Markdown notes,
- Zotero collection/tag,
- Zotero citekey list,
- BibTeX file,
- reading log,
- exported TSV/CSV.

## Write Safety

- Default mode is `dry_run`.
- Do not overwrite, rename, move, delete, retag, or edit Zotero/Obsidian content without explicit confirmation.
- If note properties are missing, produce a repair queue.
- If citekey, DOI, title, or Zotero item key conflict, produce a conflict report.

## Dry-Run Plans

`obsidian_write_plan`:

```yaml
vault_path:
files_to_create:
files_to_update:
files_to_leave_unchanged:
conflicts:
backups_required:
dry_run_diff:
```

`zotero_update_plan`:

```yaml
target_items:
proposed_tags_add:
proposed_collections:
proposed_notes:
risk_level:
requires_confirmation: true
```

## Obsidian Link Contract

Use stable links across periodic summaries:

```text
Periodic note -> reviewed_notes: [[citekey1]], [[citekey2]]
Topic matrix row -> source_notes: citekeys or note links
Research seed -> source_notes, source_figures, source_gaps
Due-review queue -> note_path and citekey
Stale review queue -> source review citekey and update-needed reason
```

Do not create orphan periodic summaries. Each synthesis should link back to source notes and forward to next actions.

For concrete periodic note skeletons, read [12_periodic_note_templates.md](12_periodic_note_templates.md).
For dry-run patch object shape, read [13_dry_run_patch_spec.md](13_dry_run_patch_spec.md).
