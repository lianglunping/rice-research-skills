# Literature State Model

Normalize literature notes before synthesis.

## Core Fields

```yaml
citekey:
doi:
zotero_item_key:
title:
year:
journal:
paper_type:
status:
topics:
organism:
crop:
trait:
gene_or_gene_family:
method:
data_type:
evidence_strength:
critical_flags:
research_seed_count:
review_next:
last_reviewed:
zotero_collection:
obsidian_note_path:
related_figures:
related_seeds:
```

## Status Values

- `new`
- `first_pass`
- `deep_read`
- `figure_audited`
- `discussion_audited`
- `critical_audited`
- `synthesized`
- `archived`

## Delta Detection

Identify:

- new papers,
- updated notes,
- papers missing figure cards,
- papers missing Discussion audit,
- papers with weak metadata,
- papers due for review,
- stale review articles,
- research seeds not ranked,
- topic clusters with changed evidence.
