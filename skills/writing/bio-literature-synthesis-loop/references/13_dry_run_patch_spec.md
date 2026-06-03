# Dry-Run Patch Spec

Use this when proposing periodic-note or dashboard write-back without actually writing.

## Obsidian Patch Object

```yaml
vault_path:
mode: dry_run
files_to_create:
files_to_update:
dashboard_targets:
conflicts:
backups_required:
patches:
  - target_file:
    action: create|append_section|replace_frontmatter|insert_table|insert_link|no_change
    reason:
    source_notes:
    preview:
```

## Dashboard Patch Preview

Use a separate section for Dataview or query suggestions:

```md
### dashboard_target
action: insert_table
reason: add due-review queue

```dataview
TABLE ...
```
```

## Rules

- Keep synthesis note patches separate from dashboard query patches.
- When note metadata are incomplete, prefer a repair queue preview over a normal summary patch.
- If the corpus is `micro_corpus`, state that the patch is provisional and should not be treated as a mature literature dashboard.
