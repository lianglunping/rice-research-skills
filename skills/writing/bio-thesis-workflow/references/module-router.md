# Module Router

Choose exactly one primary module per request.

| Module | Use when | Typical inputs | Main outputs | Read next |
|---|---|---|---|---|
| `literature_review` | User wants research-status summary, literature review, knowledge-gap synthesis, or chapter background | topic statement, paper list, Zotero notes, Markdown draft, `.docx` draft | chapter prose, structured synthesis, gap list | `literature-review-workflow.md` |
| `results_to_prose` | User wants tables, figure outputs, or readmes turned into thesis prose | `tsv/xlsx`, figure README, `run_manifest.md`, image captions, result draft | result paragraphs, legends, table notes | `results-to-prose.md` |
| `deai` | User wants academic polishing, naturalization, reduced AI traces, or voice cleanup | `.docx`, `.md`, paragraph draft, chapter draft | revised prose, issue list, patch pack | `deai-bio-zh-en.md` |
| `docx_bridge` | User wants Word extraction, section export, Markdown to Word rendering, or section patching | `.docx`, `.md`, section text | extracted Markdown/JSON, rendered `.docx`, patch pack | `docx-markdown-bridge.md` |

## Input Priority

Prefer inputs in this order:

1. Direct source artifact the user is editing now
2. Structured result tables and manifests
3. Existing project draft
4. Secondary summaries or previous notes

## Required Checks Before Writing

- What is the target output: thesis chapter, proposal, manuscript section, response memo, or figure legend?
- What is the evidence base: raw table, summary table, README, paper, or user note?
- What is the language target: Chinese, English, or bilingual?
- Is the working surface `.docx`, `.md`, or both?

## Default Output Shapes

- Literature review: sectioned prose with explicit thematic grouping and gap statement
- Results to prose: paragraph plus optional legend and caveat line
- De-AI: revised text plus short explanation of what changed
- Docx bridge: extracted Markdown/JSON or rendered `.docx`

## Companion Skills

Use these only when the task requires them:

- `openalex-database` for literature search
- `pyzotero` for library retrieval
- `citation-verification` for citation checking
- `rice-thesis-writing` when the task becomes LaTeX-first thesis editing
- `bio-thesis-review-lanes` when critique becomes the primary task
