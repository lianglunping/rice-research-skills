# Obsidian Note Templates

Use these as concrete note skeletons for dry-run output. Keep them concise and linkable.

## Main Note Template

```md
---
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
---

# {title}

## TL;DR

## Main Figure Storyline

## Load-Bearing Evidence

## Discussion Audit

## Critical Evidence Audit

## Transferable Lessons

## Research Seeds

## Links
- Figures:
- Seeds:
- Lessons:
```

## Figure Card Template

```md
---
type: figure_card
paper_type: original
citekey:
figure_id:
page:
paper_story_role:
evidence_strength:
source_note:
related_claims:
tags:
---

# {citekey}-{figure_id}

## Figure Role

## Panel Inventory

## Figure-Level Audit

## Why It Matters
```

## Critical Lessons Template

```md
---
type: critical_lessons
citekey:
paper_type: original
source_note:
related_figures:
related_claims:
tags:
---

# {citekey} Critical Lessons

## What This Paper Did Well

## What This Paper Overstated

## What We Should Reuse

## What We Should Avoid
```

## Research Seeds Template

```md
---
type: research_seed_note
citekey:
paper_type: original
source_note:
related_claims:
related_figures:
tags:
---

# {citekey} Research Seeds

## Seed 1
- core_question:
- why_now:
- minimum_next_step:
- main_risk:

## Seed 2
```

## Naming Rules

- Main note: `{citekey}.md`
- Figure card: `{citekey}-Fig1.md`
- Claim IDs: `{citekey}-C01`
- Seed IDs: `{citekey}-S01`
