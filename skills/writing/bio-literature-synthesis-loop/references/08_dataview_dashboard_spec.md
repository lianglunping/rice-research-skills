# Dataview Dashboard Spec

Generate dashboard plans only. Do not assume Dataview can write notes.

## Useful Views

- due review queue,
- missing figure audit,
- missing Discussion audit,
- stale review articles,
- high-priority research seeds,
- topic evidence matrix,
- papers without Zotero key or DOI,
- papers with conflicting metadata,
- P0/P1 reading queue.

## Example Query Shapes

Keep examples conceptual unless the user's vault schema is known:

```dataview
TABLE citekey, paper_type, review_next, topics
FROM "Literature"
WHERE review_next <= date(today)
SORT review_next ASC
```

```dataview
TABLE citekey, figure_reading_status, discussion_audit_status
FROM "Literature"
WHERE paper_type = "original" AND figure_reading_status != "complete"
```

## Spaced Repetition

If an Obsidian spaced repetition plugin is present, suggest flashcards or review markers. If not, rely on `review_next` fields and periodic notes.
