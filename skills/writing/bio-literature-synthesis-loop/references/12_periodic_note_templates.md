# Periodic Note Templates

Use these as concrete note skeletons for periodic synthesis outputs.

## Weekly Review Template

```md
---
type: periodic_literature_review
cycle: weekly
date_range:
topic_filter:
reviewed_notes:
due_notes:
seed_updates:
tags:
---

# Weekly Literature Review

## New Papers and Notes

## What Changed In Understanding

## Critical Lessons

## Recall Questions

## Research Seed Updates

## Next Reading Queue
```

## Monthly Review Template

```md
---
type: periodic_literature_review
cycle: monthly
date_range:
topic_filter:
reviewed_notes:
stale_reviews:
seed_updates:
tags:
---

# Monthly Literature Review

## Topic Evidence Matrix

## Strong Signals

## Weak or Contradictory Signals

## Backtracking Queue

## Ranked Research Seeds

## Next-Month Plan
```

## Project-Specific Review Template

```md
---
type: project_literature_review
topic:
date_range:
reviewed_notes:
related_figures:
seed_updates:
tags:
---

# Project-Specific Literature Review

## Scope

## Topic Evidence Matrix

## Gaps Blocking Decisions

## Candidate Experiments or Analyses

## Recall Questions
```

## Naming Rules

- Weekly note: `YYYY-[W]ww-literature-review.md`
- Monthly note: `YYYY-MM-literature-review.md`
- Project note: `{topic}-literature-review.md`
