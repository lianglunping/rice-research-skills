# Obsidian Note Templates

Use these as concrete note skeletons for dry-run output.

## Review Main Note Template

```md
---
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
---

# {title}

## TL;DR

## Field Framework

## Route Divergence

## Consensus, Controversies, and Gaps

## Published-After Update

## Research Seeds

## Backtracking Queue
```

## Framework Note Template

```md
---
type: framework_note
citekey:
paper_type: review
source_note:
core_routes:
tags:
---

# {citekey} Field Framework

## Core Question

## Historical Stages

## Mechanism and Technology Layers

## Breeding or Application Relevance
```

## Backtracking Queue Template

```md
---
type: backtracking_queue
citekey:
paper_type: review
source_note:
tags:
---

# {citekey} Original Papers To Check

| claim_id | claim | why_backtrack | target_papers | priority |
| --- | --- | --- | --- | --- |
```

## Proposal Seed Template

```md
---
type: research_seed_note
citekey:
paper_type: review
source_note:
source_gap:
tags:
---

# {citekey} Proposal Seeds

## Seed 1
- source_gap:
- core_question:
- why_now:
- minimum_next_step:
- main_risk:
```

## Naming Rules

- Main note: `{citekey}.md`
- Framework note: `{citekey}-field-framework.md`
- Gap IDs: `{citekey}-G01`
- Route IDs: `{citekey}-R01`
- Seed IDs: `{citekey}-S01`
