# Dry-Run Patch Spec

Use this when proposing note write-back without actually writing.

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
    action: create|append_section|replace_frontmatter|insert_link|no_change
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

## Markdown Preview Style

Use a compact diff-like preview:

```md
### target_file
action: create
reason: create main literature note

```yaml
frontmatter changes here
```

```md
section preview here
```
```

Hard rules:

- Never pretend a patch was applied.
- If the target file exists and structure is unknown, prefer `append_section` or emit conflict.
- Separate frontmatter patch preview from body patch preview.
