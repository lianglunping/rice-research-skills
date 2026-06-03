---
name: rice-thesis-writing
description: This skill should be used when the user asks to write, reorganize, polish, or format Chinese master's or doctoral thesis chapters, especially literature reviews, introductions, abstracts, discussions, conclusions, chapter outlines, reference formatting, or Word-ready正文 in the domain of rice genetics, crop breeding, mutagenesis breeding, heavy-ion mutagenesis, or related bioinformatics research. Also use when the user mentions “学位论文”, “博士论文”, “毕业论文”, “文献综述”, “绪论”, “参考文献格式”, or wants thesis text that can be pasted directly into Word.
---

# Rice Thesis Writing

Use this skill for **Chinese thesis chapter writing and formatting**, with emphasis on rice mutagenesis breeding, crop genetics, and bioinformatics research.

## Goal

Produce chapter text that is:
- structurally stable,
- academically restrained,
- evidence-bounded,
- ready for Word formatting,
- and safe on citations.

## Hard boundaries

- Do not fabricate facts, data, sample sizes, statistical significance, gene functions, mechanisms, or literature metadata.
- Do not guess missing authors, DOI, URL, pages, issue numbers, publishers, conference names, or access dates.
- If a literature field is missing and cannot be verified, keep the available part only and explicitly mark it for author review.
- Treat thesis writing as a **chapter-level integration task**, not a free rewrite from memory.

## Default operating order

1. Lock the chapter type and target role in the thesis.
2. Inspect existing drafts, source files, and formatting constraints before writing.
3. Build or confirm the heading hierarchy.
4. Remove workbench residue such as “执行摘要”, “整合摘要”, “可直接写入论文”, prompt-like notes, and duplicated scaffolding.
5. Reorganize text into thesis-style prose without changing evidence or core logic.
6. Normalize terminology, mixed Chinese-English formatting, figure/table labels, and chapter numbering.
7. Normalize in-text citations and the chapter reference list using `references/citation-rules.md`.
8. Apply Word-facing formatting rules from `references/format-rules.md`.

## When writing a literature review chapter

Use this order unless the user provides a fixed outline:
1. development and theoretical framing,
2. current research status,
3. mechanism or method comparisons,
4. unresolved questions or knowledge gaps,
5. the study's positioning and significance.

Load `references/chapter-patterns.md` when you need chapter-specific writing boundaries.

## Output rules

- Prefer direct thesis prose over outlines once the structure is fixed.
- Keep section purposes distinct: research status, mechanism, technical strategy, knowledge gap, and study significance should not collapse into one section.
- Default to Word-friendly structure with clear `1`, `1.1`, `1.1.1` heading levels unless the user requires another system.
- If producing a `.docx`, preserve the same section logic in the file and in any intermediate markdown.

## Resource map

- `references/format-rules.md`: Word formatting, heading, paragraph, figure/table, and mixed-language rules.
- `references/citation-rules.md`: in-text citation and reference-list normalization rules, including missing-field handling.
- `references/chapter-patterns.md`: chapter-specific boundaries for literature reviews, introductions, discussions, and thesis-style transitions.
