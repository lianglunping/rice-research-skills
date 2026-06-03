# Minimum Deliverables and Stop Rules

Use stop rules when the knowledge base is too thin or inconsistent.

## Output Modes

| Mode | Use when | Minimum output |
| --- | --- | --- |
| `intake_planning` | No usable notes or Zotero collection yet | note schema, reading queue, tag plan |
| `micro_corpus` | Two to five notes exist and cross-paper trends would be premature | cautious topic matrix, recall questions, seed shortlist, next reading plan |
| `weekly_synthesis` | Recent notes exist | new papers, key learning changes, recall questions, next reading |
| `monthly_synthesis` | Enough notes for clustering | topic matrix, gaps, stale claims, seed ranking |
| `project_review` | User names a project/topic | topic-specific matrix, evidence gaps, validation actions |
| `annual_roadmap` | Long time range and enough notes | route map, major shifts, proposal backlog |

## Stop Rules

- If no notes, collection, BibTeX, or reading log is available, do not invent a synthesis; produce intake planning.
- If note metadata are inconsistent, create a repair queue before ranking seeds.
- If only one paper exists for a topic, call it a single-paper claim, not a trend.
- If source notes lack evidence labels, mark synthesis confidence as low.
- If Zotero or Obsidian is unavailable, produce Markdown-only dry-run outputs.
- If only two to five notes exist, avoid trend language and switch to `micro_corpus`.

## Minimum QA

Always state:

- source coverage,
- missing or weak metadata,
- synthesis confidence,
- what could not be concluded,
- next data/notes needed for better synthesis.
