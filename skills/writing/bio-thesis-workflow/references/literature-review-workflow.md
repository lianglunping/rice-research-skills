# Literature Review Workflow

Use this module for biology or bioinformatics review writing when the deliverable is chapter prose, a research-status summary, or a gap-oriented background section.

## Scope

Best suited for:
- thesis Chapter 1 or Chapter 2 style writing,
- plant genetics and mutagenesis research status summaries,
- mechanism-focused narrative reviews,
- and topic briefs that will later be pasted into Word.

## Default Process

1. Lock the review question and scope boundary.
2. Group literature by theme, mechanism, method, or evidence type.
3. Build a compact evidence matrix before drafting prose.
4. Write thematic synthesis, not author-by-author enumeration.
5. End with unresolved questions and the current study's positioning.

## Evidence Matrix

Before writing, capture at least these fields for each core paper:

| Field | Notes |
|---|---|
| citation key or short tag | stable handle for reference |
| system/material | rice, Arabidopsis, maize, human cell line, etc. |
| perturbation | heavy ion, EMS, CRISPR, stress, treatment |
| data type | WGS, WES, RNA-seq, ATAC-seq, phenotype, multi-omics |
| main finding | one sentence only |
| boundary | what the paper does not show |
| relation to our question | background, support, contrast, or gap |

## Writing Rules

- Organize sections by ideas:
  - mutagenesis mechanism,
  - mutation spectrum,
  - functional-region damage,
  - heritability and chimerism,
  - omics or chromatin mechanism,
  - breeding value or validation strategy.
- Do not write three or more consecutive sentences in the pattern `Author (Year) found ...`.
- When a study is outside rice but still informative, say what transfers and what does not.
- Separate:
  - current consensus,
  - conflicting evidence,
  - and open questions.

## Suggested Review Spine For Your Domain

1. mutagen source and DNA damage logic
2. repair pathway and mutation-spectrum shaping
3. M1 chimerism and cross-generation fixation
4. crop and rice mutagenesis research status
5. variant detection and evidence-chain construction
6. chromatin accessibility or functional-genome context
7. gap statement and thesis positioning

## Search and Citation Support

When the user needs new literature rather than prose-only synthesis:

- Use `openalex-database` for broad retrieval and trend checks.
- Use `pyzotero` if the papers already live in Zotero.
- Use `citation-verification` before final reference insertion.

## Output Contract

Return prose that includes:
- a topic sentence,
- evidence synthesis,
- comparison or limitation,
- and a closing sentence that points to the next subsection or study gap.

If evidence is thin, say so explicitly instead of inflating the section.
