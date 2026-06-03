# Minimum Deliverables and Stop Rules

Use stop rules to avoid pretending a full audit is possible when inputs are weak.

## Output Modes

| Mode | Use when | Minimum output |
| --- | --- | --- |
| `quick_read` | User asks for a short read or no full PDF is available | TL;DR, metadata, key claims, limitations |
| `standard_deep_read` | Full PDF is readable but not all figures/supplement are accessible | main note, figure storyline, selected panel inventory, Discussion audit |
| `full_audit` | Full PDF, figures, methods, and supplement are available | full report, every Main Figure panel inventory, claim map, critical audit, Obsidian/Zotero dry-run plan |
| `figure_only` | User asks about figures | figure storyline, panel inventory, figure-specific audit |
| `discussion_only` | User asks about Discussion | Discussion claim table, Result support check, external follow-up questions |

## Stop Rules

- If no full text or PDF is available, do not produce a Figure audit. Produce intake plus retrieval needs.
- If figures are unreadable, mark `【图表解析受限】` and avoid panel-level claims.
- If supplement is missing and key claims depend on it, downgrade those claims.
- If parser output conflicts with original PDF, trust the original PDF and record parser error.
- If DOI/title/Zotero identity conflict exists, stop any write plan until resolved.
- If the paper is actually a review or perspective, stop and switch to `bio-review-paper-reading`.
- If external search is unavailable, keep original-paper audit and mark latest-context sections as pending.
- If the paper is very recent and external follow-up is minimal, report `recent_paper_no_meaningful_update_yet` instead of manufacturing a latest-progress section.

## Minimum QA

Always provide:

- what was available,
- what was not available,
- what could be concluded,
- what could not be concluded,
- which conclusions were downgraded and why.
