---
name: bio-review-paper-reading
description: Deep-reading workflow for review articles, perspectives, opinions, primers, roadmaps, and field-synthesis papers in molecular biology, genomics, omics, quantitative genetics, plant breeding, rice, and bioinformatics. Use when the user asks to interpret a review PDF, reconstruct a field framework, identify route divergence, consensus, controversies, open gaps, conceptual figures, post-publication updates, research proposal seeds, or dry-run Zotero/Obsidian literature notes. Do not use for general literature retrieval, paper download, citation export, Zotero setup, or single original-paper panel audit.
---

# Bio Review Paper Reading

Use this skill for high-level, evidence-bounded interpretation of review-type papers. The goal is not paragraph-by-paragraph summary. Reconstruct the field architecture, identify what is consensus versus tentative model, locate disputes and gaps, and convert the review into research directions.

## Boundaries

- Use for Review, Perspective, Opinion, Primer, Roadmap, Trends, Annual Review, and similar synthesis papers.
- Do not use for original empirical papers that require figure-by-figure panel evidence audit; switch to `bio-original-paper-reading`.
- Do not use for literature retrieval, paper download, citation management, Zotero configuration, or BibTeX export; use a search/Zotero workflow instead.
- Do not claim that a narrative review has systematic evidence coverage.
- Do not claim to complete a formal PRISMA systematic review unless actual search, screening, inclusion/exclusion, and extraction records are performed.
- Do not write to Zotero or Obsidian by default. Produce dry-run write plans unless the user explicitly confirms a write action.

## Default Workflow

1. **Input contract**: identify input type, review type, field, user goal, external update scope, and write mode.
2. **Review type triage**: read [references/01_review_type_triage.md](references/01_review_type_triage.md) and classify the paper.
3. **Evidence labels**: apply [references/00_evidence_labels.md](references/00_evidence_labels.md) to all important claims.
4. **Stop-rule check**: read [references/10_minimum_deliverables_and_stop_rules.md](references/10_minimum_deliverables_and_stop_rules.md) and decide whether this can be a full framework reconstruction or must downgrade.
5. **Scope and author lens**: identify the review's topic boundary, organisms, systems, technologies, citation period, and likely author perspective.
6. **Field framework reconstruction**: read [references/02_field_framework_reconstruction.md](references/02_field_framework_reconstruction.md). Build the knowledge skeleton rather than following section order.
7. **Route divergence map**: read [references/03_route_divergence_map.md](references/03_route_divergence_map.md) and separate mechanisms, technologies, data resources, algorithms, and breeding routes.
8. **Consensus, controversy, and gap map**: read [references/04_consensus_controversy_gap.md](references/04_consensus_controversy_gap.md). Mark second-hand claims that require backtracking to original papers.
9. **Conceptual figures and tables**: read [references/05_review_figures_and_tables.md](references/05_review_figures_and_tables.md). Treat review figures as conceptual maps, not direct experiments.
10. **Post-publication update**: for latest progress, stale reviews, controversies, and author-team follow-up, external search is allowed by default unless the user disables it; read [references/06_external_update_protocol.md](references/06_external_update_protocol.md).
11. **Research seeds**: read [references/07_research_seed_protocol.md](references/07_research_seed_protocol.md) and produce actionable, risk-aware proposal seeds.
12. **Knowledge output**: read [references/08_zotero_obsidian_output.md](references/08_zotero_obsidian_output.md) when note integration is requested.
13. **Final report**: follow [references/09_report_structure.md](references/09_report_structure.md), then run the QA checklist.

## Required Reading Order

Always read:

- [references/00_evidence_labels.md](references/00_evidence_labels.md)
- [references/01_review_type_triage.md](references/01_review_type_triage.md)
- [references/02_field_framework_reconstruction.md](references/02_field_framework_reconstruction.md)
- [references/03_route_divergence_map.md](references/03_route_divergence_map.md)
- [references/04_consensus_controversy_gap.md](references/04_consensus_controversy_gap.md)
- [references/05_review_figures_and_tables.md](references/05_review_figures_and_tables.md)
- [references/07_research_seed_protocol.md](references/07_research_seed_protocol.md)
- [references/09_report_structure.md](references/09_report_structure.md)
- [references/10_minimum_deliverables_and_stop_rules.md](references/10_minimum_deliverables_and_stop_rules.md)

Read conditionally:

- [references/06_external_update_protocol.md](references/06_external_update_protocol.md) for latest progress, stale reviews, author-team follow-up, or controversy updates.
- [references/08_zotero_obsidian_output.md](references/08_zotero_obsidian_output.md) for Zotero/Obsidian note planning.
- [references/11_examples.md](references/11_examples.md) when output style, gap table format, or seed format is ambiguous.
- [references/12_obsidian_note_templates.md](references/12_obsidian_note_templates.md) when the user wants concrete note skeletons for review notes, framework notes, backtracking queues, or seed notes.
- [references/13_dry_run_patch_spec.md](references/13_dry_run_patch_spec.md) when the user wants a structured patch preview for Zotero or Obsidian write-back.

## QA Gate

Before finalizing, verify:

- The output is not a section-by-section paraphrase.
- It includes field framework, route divergence, consensus, controversy, and gap analysis.
- Each major claim is labeled as `[原文结论]`, `[原文重构]`, `[外部检索补充]`, or `[专家研判]`.
- Review-paper second-hand conclusions are not treated as primary evidence unless original papers were checked.
- Post-publication updates are separated from original review claims.
- Research seeds include minimum feasible path and failure risk.
- Zotero/Obsidian output remains dry-run unless explicit user confirmation exists.
