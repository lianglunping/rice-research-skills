---
name: bio-literature-synthesis-loop
description: Periodic literature synthesis and retention workflow for biology, genomics, plant breeding, rice, bioinformatics, and mutagenesis reading systems. Use when the user asks for weekly, biweekly, monthly, half-year, yearly, or project-specific summaries from Zotero/Obsidian notes; due-review queues; missing audit detection; topic evidence matrices; recall questions; research seed ranking; reading plans; or dry-run Zotero/Obsidian dashboard updates. Do not use for first-pass deep reading of a single paper, general literature search, Zotero setup, citation export, or Obsidian plugin troubleshooting.
---

# Bio Literature Synthesis Loop

Use this skill to turn individual literature notes into long-term understanding. It consumes already-read papers, Zotero metadata, Obsidian notes, reading logs, or BibTeX exports and produces periodic synthesis, review queues, recall questions, topic matrices, and research seed rankings.

## Boundaries

- Use for cross-paper synthesis, periodic review, knowledge-base hygiene, research seed prioritization, and reading-plan design.
- Do not use for first-pass deep reading of a single original paper; switch to `bio-original-paper-reading`.
- Do not use for first-pass deep reading of a review paper; switch to `bio-review-paper-reading`.
- Do not use for general literature search, Zotero setup, citation export, Obsidian plugin troubleshooting, or PDF parsing configuration.
- Do not claim to complete a formal systematic review or living systematic review unless actual protocol, search, screening, and update records exist.
- Do not write to Zotero or Obsidian by default. Produce dry-run write plans unless the user explicitly confirms a write action.

## Default Workflow

1. **State intake**: identify date range, topic filter, Zotero collection/tag, Obsidian vault/folder, note paths, BibTeX file, reading log, review cycle, and write mode.
2. **Evidence labels**: apply [references/00_evidence_labels.md](references/00_evidence_labels.md) to all new synthesis claims.
3. **State normalization**: read [references/01_literature_state_model.md](references/01_literature_state_model.md) and normalize paper/note fields.
4. **Sync contract**: read [references/02_zotero_obsidian_sync_contract.md](references/02_zotero_obsidian_sync_contract.md) when Zotero or Obsidian is involved.
5. **Stop-rule check**: read [references/10_minimum_deliverables_and_stop_rules.md](references/10_minimum_deliverables_and_stop_rules.md) and decide whether enough notes exist for synthesis, whether the corpus should be treated as `micro_corpus`, or whether only intake planning is possible.
6. **Periodic review**: read [references/03_periodic_review_protocol.md](references/03_periodic_review_protocol.md) and choose weekly, biweekly, monthly, half-year, yearly, or project-specific output.
7. **Review scheduling**: use [references/04_review_schedule_policy.md](references/04_review_schedule_policy.md) to identify due reviews and stale notes.
8. **Recall questions**: use [references/05_recall_question_protocol.md](references/05_recall_question_protocol.md) so the output supports active recall, not passive summary.
9. **Topic evidence matrix**: read [references/06_topic_evidence_matrix.md](references/06_topic_evidence_matrix.md) to avoid treating single-paper claims as field consensus.
10. **Research seed ranking**: read [references/07_research_seed_ranking.md](references/07_research_seed_ranking.md) for proposal backlog prioritization.
11. **Dashboard planning**: read [references/08_dataview_dashboard_spec.md](references/08_dataview_dashboard_spec.md) when the user wants Obsidian views or review queues.
12. **Final output**: follow [references/09_report_structure.md](references/09_report_structure.md), then run the QA checklist.

## Required Reading Order

Always read:

- [references/00_evidence_labels.md](references/00_evidence_labels.md)
- [references/01_literature_state_model.md](references/01_literature_state_model.md)
- [references/03_periodic_review_protocol.md](references/03_periodic_review_protocol.md)
- [references/04_review_schedule_policy.md](references/04_review_schedule_policy.md)
- [references/05_recall_question_protocol.md](references/05_recall_question_protocol.md)
- [references/06_topic_evidence_matrix.md](references/06_topic_evidence_matrix.md)
- [references/07_research_seed_ranking.md](references/07_research_seed_ranking.md)
- [references/09_report_structure.md](references/09_report_structure.md)
- [references/10_minimum_deliverables_and_stop_rules.md](references/10_minimum_deliverables_and_stop_rules.md)

Read conditionally:

- [references/02_zotero_obsidian_sync_contract.md](references/02_zotero_obsidian_sync_contract.md) for Zotero/Obsidian inputs or write plans.
- [references/08_dataview_dashboard_spec.md](references/08_dataview_dashboard_spec.md) for Obsidian Dataview/Periodic Notes/Spaced Repetition planning.
- [references/11_examples.md](references/11_examples.md) when review-note, recall-question, or seed-backlog formatting is ambiguous.
- [references/12_periodic_note_templates.md](references/12_periodic_note_templates.md) when the user wants concrete note skeletons for weekly/monthly/project-specific summaries.
- [references/13_dry_run_patch_spec.md](references/13_dry_run_patch_spec.md) when the user wants structured patch previews for periodic review notes or dashboard updates.

## QA Gate

Before finalizing, verify:

- The output synthesizes across notes or papers rather than re-summarizing one paper.
- Every new conclusion is traceable to notes, Zotero metadata, original evidence labels, or external search.
- Single-paper findings are not promoted to field consensus.
- Review-paper second-hand claims remain marked as requiring backtracking unless original papers were checked.
- Every due-review item has `review_next` or a clear scheduling recommendation.
- Every research seed has ranking rationale and failure risk.
- Zotero/Obsidian output remains dry-run unless explicit user confirmation exists.
