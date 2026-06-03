---
name: bio-original-paper-reading
description: Deep-reading workflow for original empirical biology papers, especially molecular biology, genomics, omics, quantitative genetics, plant breeding, rice, and mutagenesis studies. Use when the user provides a PDF, DOI, Zotero item/citekey, title, or folder and asks to interpret an original research article, reconstruct the paper from Main Figures, audit figure panels, inspect x/y axes, explain wet-lab images, read Discussion critically, judge evidence strength, extract breeding or bioinformatics lessons, or prepare dry-run Zotero/Obsidian notes. Do not use for general literature search, paper download, Zotero setup, BibTeX export, citation insertion, or raw data analysis unless the request explicitly asks for deep reading of a specific original paper.
---

# Bio Original Paper Reading

Use this skill for single-paper deep reading of original empirical research articles. The paper may be mechanism-centric, genetics-centric, omics-centric, or method/breeding-evaluation centric. The goal is not to summarize the author's story, but to rebuild and audit the evidence chain: hypothesis -> design -> data -> statistics -> figure logic -> Discussion interpretation -> biological, methodological, and breeding implications.

## Boundaries

- Use for original research papers with Results, Methods, Figures, Tables, and empirical claims, including mechanistic papers, benchmarking/method papers, mutagenesis-evaluation papers, population-design papers, and breeding-resource papers.
- Do not use for Review, Perspective, Opinion, Roadmap, News & Views, or Protocol collection papers; switch to `bio-review-paper-reading`.
- Do not use for literature retrieval, paper download, citation management, Zotero configuration, or BibTeX export; use a search/Zotero workflow instead.
- Do not perform raw data reanalysis, variant calling, RNA-seq analysis, or pipeline implementation unless the user separately asks for that task.
- Do not write to Zotero or Obsidian by default. Produce dry-run write plans unless the user explicitly confirms a write action.
- Treat PDF-to-Markdown text as navigation evidence only. Critical claims must be checked against the original PDF, figure, table, method, supplement, or clearly identified external source.

## Default Workflow

1. **Input contract**: identify input type (`pdf`, DOI, Zotero citekey/item key, title, folder), user goal, output mode, domain focus, and external search scope.
2. **Paper type triage**: confirm this is an original empirical article. If uncertain, report uncertainty and ask whether to use original or review workflow.
3. **Metadata identity**: collect title, authors, year, journal, DOI, Zotero keys if available, organism, major traits, genes, methods, data types, and PDF path. Flag title/DOI/Zotero conflicts.
4. **Parse plan**: read [references/01_pdf_parsing_ladder.md](references/01_pdf_parsing_ladder.md) and choose a local or available parser strategy. Record parser provenance and known limitations.
5. **Evidence labels**: apply [references/00_evidence_labels.md](references/00_evidence_labels.md) to every important claim.
6. **Stop-rule check**: read [references/09_minimum_deliverables_and_stop_rules.md](references/09_minimum_deliverables_and_stop_rules.md) and decide whether the task can produce a full audit or must downgrade.
7. **External context policy**: for paper identity, latest context, author-team follow-up, and Discussion follow-up checks, external search is allowed by default unless the user turns it off. Never use external sources to fill original Methods, Results, Figure, or Supplement facts.
8. **Figure-first reconstruction**: read [references/02_main_figure_workflow.md](references/02_main_figure_workflow.md), then rebuild the paper's main logic from Main Figures before writing the narrative.
9. **Panel inventory**: use [references/03_panel_inventory_protocol.md](references/03_panel_inventory_protocol.md) for Main Figure panels. In `full_audit`, cover every Main Figure panel. In `standard_deep_read`, prioritize load-bearing or representative panels that carry the main causal or mechanistic burden. Missing sample size, replicate, or statistical test must be marked as `not_reported` or `not_specified`.
10. **Wet-lab visual decoding**: when figures contain molecular or cell biology assays, read [references/04_wetlab_figure_decoding.md](references/04_wetlab_figure_decoding.md).
11. **Discussion close reading**: read [references/05_discussion_audit.md](references/05_discussion_audit.md) and separate what Results prove from what authors infer.
12. **Critical evidence audit**: read [references/06_critical_evidence_audit.md](references/06_critical_evidence_audit.md) and identify weakest links, alternative explanations, and transferable lessons for the user's own research.
13. **Knowledge output**: read [references/07_zotero_obsidian_output.md](references/07_zotero_obsidian_output.md) and prepare dry-run Zotero/Obsidian note plans.
14. **Final report**: follow [references/08_report_structure.md](references/08_report_structure.md), then run the QA checklist before responding.

## Required Reading Order

Always read:

- [references/00_evidence_labels.md](references/00_evidence_labels.md)
- [references/01_pdf_parsing_ladder.md](references/01_pdf_parsing_ladder.md)
- [references/02_main_figure_workflow.md](references/02_main_figure_workflow.md)
- [references/03_panel_inventory_protocol.md](references/03_panel_inventory_protocol.md)
- [references/05_discussion_audit.md](references/05_discussion_audit.md)
- [references/06_critical_evidence_audit.md](references/06_critical_evidence_audit.md)
- [references/08_report_structure.md](references/08_report_structure.md)
- [references/09_minimum_deliverables_and_stop_rules.md](references/09_minimum_deliverables_and_stop_rules.md)

Read conditionally:

- [references/04_wetlab_figure_decoding.md](references/04_wetlab_figure_decoding.md) when figures include gels, blots, microscopy, interaction assays, reporter assays, genome browser views, omics plots, or genetic maps.
- [references/07_zotero_obsidian_output.md](references/07_zotero_obsidian_output.md) when the user wants note integration, Zotero tags, citekeys, Obsidian output, or long-term review scheduling.
- [references/10_examples.md](references/10_examples.md) when output style, panel table format, or Discussion audit format is ambiguous.
- [references/11_obsidian_note_templates.md](references/11_obsidian_note_templates.md) when the user wants concrete note skeletons for main notes, figure cards, lessons, or research seeds.
- [references/12_dry_run_patch_spec.md](references/12_dry_run_patch_spec.md) when the user wants a structured patch preview for Zotero or Obsidian write-back.

## QA Gate

Before finalizing, verify:

- Every main conclusion has at least one `[原文证据]` anchor.
- Every Main Figure has a figure-level role in the story.
- Every panel has data type, x/y axes or visual axes, groups, controls, visual trend, author claim, evidence strength, and missing-information markers.
- Discussion claims are split into data-supported statements, author interpretation, and expert concern.
- Statistical significance is not treated as biological relevance by default.
- Association is not described as causality unless direct causal evidence is present.
- External findings are labeled `[外部检索补充]` and never overwrite original-paper facts.
- Zotero/Obsidian output remains dry-run unless explicit user confirmation exists.
