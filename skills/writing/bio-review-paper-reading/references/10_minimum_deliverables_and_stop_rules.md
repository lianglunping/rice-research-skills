# Minimum Deliverables and Stop Rules

Use stop rules to avoid overclaiming a review's coverage.

## Output Modes

| Mode | Use when | Minimum output |
| --- | --- | --- |
| `quick_review` | User asks for short orientation | TL;DR, scope, framework sketch, top gaps |
| `standard_framework` | Full review is readable | framework, routes, consensus/controversy/gap, selected figures/tables |
| `full_field_audit` | Full review plus external update is allowed | framework, route map, gap map, latest update, seed ranking, backtracking queue |
| `gap_only` | User wants research opportunities | gap table, controversy status, seed candidates |
| `figure_table_only` | User asks about conceptual figures/tables | figure/table cards and model audit |

## Stop Rules

- If the paper is an original empirical article, stop and switch to `bio-original-paper-reading`.
- If only abstract is available, do not reconstruct a full field framework; produce intake and retrieval needs.
- If the review is narrative and has no search protocol, do not claim comprehensive coverage.
- If review claims depend heavily on cited original papers, mark `需回源` and create a backtracking queue.
- If external search is unavailable, label latest-progress sections as pending.
- If the review is old in a fast-moving field, mark `stale_review_risk` unless updated externally.
- If the review is very recent and meaningful follow-up is absent, label `recent_review_no_meaningful_update_yet`.

## Minimum QA

Always state:

- what the review explicitly covers,
- what it does not cover,
- which framework pieces are `[原文重构]`,
- which key claims need original-paper backtracking,
- which latest-context claims depend on external search.
