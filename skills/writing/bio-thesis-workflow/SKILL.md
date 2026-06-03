---
name: bio-thesis-workflow
description: This skill should be used when the user asks to write, reorganize, polish, or convert biology or bioinformatics thesis/manuscript content in Word or Markdown, especially for literature reviews, research-status summaries, result tables/figures to prose, figure legends, or de-AI academic polishing in rice, molecular biology, genetics, mutagenesis breeding, and omics contexts.
---

# Bio Thesis Workflow

Use this skill as the main writing orchestrator for biology and bioinformatics thesis work when the working artifacts are `.docx`, `.md`, or source tables/figures rather than a LaTeX thesis project.

## Goal

Produce writing that is:
- evidence-bounded,
- Word/Markdown friendly,
- reusable across thesis, proposal, and manuscript work,
- and adapted to plant genetics, mutagenesis breeding, and omics narratives.

## Use This Skill For

- Literature reviews and research-status summaries
- Turning result tables, figure readmes, and manifests into thesis-style prose
- Figure legends and table notes
- De-AI academic polishing for Chinese or English biology writing
- Word to Markdown extraction and Markdown to Word export

## Do Not Use

- Full LaTeX thesis compilation or GB/T 7714 layout debugging
- Variant calling, RNA-seq, ATAC-seq, or other primary analyses
- Reviewer-style critique as the main task

For those tasks, rely on sibling skills such as `rice-thesis-writing`, `bio-*` analysis skills, or `bio-thesis-review-lanes`.

## Default Workflow

1. Identify the artifact type: `.docx`, `.md`, tables, figure outputs, or mixed inputs.
2. Read [references/module-router.md](references/module-router.md) and choose exactly one primary module.
3. Always apply [references/evidence-boundaries.md](references/evidence-boundaries.md).
4. If the input is `.docx`, use `scripts/docx_extract.py` first and work from the extracted Markdown/JSON.
5. Load only the one module reference needed:
   - literature review: [references/literature-review-workflow.md](references/literature-review-workflow.md)
   - results to prose: [references/results-to-prose.md](references/results-to-prose.md)
   - de-AI polishing: [references/deai-bio-zh-en.md](references/deai-bio-zh-en.md)
   - Word bridge details: [references/docx-markdown-bridge.md](references/docx-markdown-bridge.md)
6. When the topic is plant mutagenesis, rice genetics, or omics interpretation, read [references/domain-profile-plant-mutagenesis.md](references/domain-profile-plant-mutagenesis.md).
7. If the user requests external-review, advisor-review, committee-review, pre-defense critique, or major-problem finding, switch to `bio-thesis-review-lanes`.

## Hard Rules

- Never fabricate numbers, citations, gene functions, statistical significance, or experimental settings.
- Preserve identifiers exactly: gene IDs, variant IDs, sample names, line names, M1/M2/M3 labels, and figure/table numbers.
- Distinguish clearly between:
  - direct result description,
  - interpretation supported by evidence,
  - and forward inference that still needs verification.
- When polishing, preserve quantitative meaning before improving style.
- When writing from tables or figures, cite the exact input files in the output note or metadata when feasible.

## Resource Map

- [references/module-router.md](references/module-router.md): choose the module and required inputs
- [references/literature-review-workflow.md](references/literature-review-workflow.md): topic clustering, gap extraction, review writing
- [references/results-to-prose.md](references/results-to-prose.md): convert tables and figures into result paragraphs
- [references/deai-bio-zh-en.md](references/deai-bio-zh-en.md): biology-aware de-AI heuristics
- [references/docx-markdown-bridge.md](references/docx-markdown-bridge.md): `.docx` extraction, rendering, and patch-pack workflow
- [references/evidence-boundaries.md](references/evidence-boundaries.md): reproducibility and evidence guardrails
- [references/domain-profile-plant-mutagenesis.md](references/domain-profile-plant-mutagenesis.md): rice, mutagenesis, and omics writing profile
- [examples/literature-review-example.md](examples/literature-review-example.md): literature review output example
- [examples/results-to-prose-example.md](examples/results-to-prose-example.md): results paragraph example
- [examples/deai-example.md](examples/deai-example.md): de-AI example
