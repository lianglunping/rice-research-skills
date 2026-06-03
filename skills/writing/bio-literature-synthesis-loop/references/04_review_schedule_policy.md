# Review Schedule Policy

Use review scheduling to prevent one-time reading from disappearing.

## Fields

```yaml
review_status: new|first_pass|deep_read|audited|synthesized|archived
review_priority: P0|P1|P2|P3
review_next:
review_interval_days:
last_reviewed:
memory_card_created:
needs_backtracking:
needs_external_update:
```

## Default Intervals

- `first_pass`: 2 days
- `deep_read`: 7 days
- `audited`: 21 days
- `synthesized`: 60 days
- high-value research seed: monthly
- stale review article: external update every 3-6 months

Adjust intervals based on thesis relevance, active project relevance, and evidence strength.

## Priority

- `P0`: directly affects current project or experiment design.
- `P1`: likely useful for near-term analysis or writing.
- `P2`: useful background or future seed.
- `P3`: archive-level relevance.
