# Dry-Run Patch Spec

Use this when proposing review-note write-back without actually writing.

## Obsidian Patch Object

```yaml
vault_path:
mode: dry_run
files_to_create:
files_to_update:
conflicts:
backups_required:
patches:
  - target_file:
    action: create|append_section|replace_frontmatter|insert_table|insert_link|no_change
    reason:
    source_citekey:
    preview:
```

## Zotero Patch Object

```yaml
mode: dry_run
target_item:
proposed_tags_add:
proposed_collections:
proposed_note_title:
proposed_note_markdown:
conflicts:
risk_level:
requires_confirmation: true
```

## Review-Specific Rules

- Keep original review claims, external updates, and expert judgments in distinct sections.
- Backtracking queue previews should be separate from the main note preview.
- If external update evidence is still incomplete, mark the patch as provisional rather than complete.
