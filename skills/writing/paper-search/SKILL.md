---
name: paper-search
description: "Academic literature retrieval and lawful full-text access: search scholarly databases, verify paper identity and retrieve available open-access sources."
---

# Paper Search

Use this skill for reproducible academic literature search. Prefer a verified
local `paper-search-mcp` CLI when configured; otherwise use web search or
source APIs and preserve equivalent provenance.

## Goal

Search, download, and read academic papers from public and open academic
sources while preserving enough provenance to reproduce the query later.

## Boundaries

- Prefer public and open sources: PubMed, PMC, Europe PMC, Crossref, OpenAlex,
  Semantic Scholar, arXiv, bioRxiv, medRxiv, Zenodo, HAL, and DOAJ.
- Do not use Sci-Hub or any access-bypass workflow.
- Treat Google Scholar as a discovery fallback only; it is bot-detection prone
  and should not be the primary reproducible source.
- Do not claim that search results prove a biological conclusion. Search
  results are evidence candidates until papers are read and assessed.
- Record query, sources, date, filters, command, and output paths for any
  literature result used in a report, thesis, or analysis decision.

## Backend Selection

1. Use the local wrapper only when `PAPER_SEARCH_WRAPPER` names an executable
   file. Do not guess a home-directory location.
2. If the wrapper is unavailable, use web search against the requested
   scholarly sources or their official APIs. Record queries, URLs, retrieval
   dates, filters, and source-specific errors.
3. Use `export_paper_search_results.py` only when a compatible raw JSON payload
   has been saved. The normalizer does not provide literature retrieval.

Local-backend preflight:

```bash
: "${PAPER_SEARCH_WRAPPER:?Set PAPER_SEARCH_WRAPPER to an executable local wrapper}"
test -x "$PAPER_SEARCH_WRAPPER"
```

## Local Commands

List available sources:

```bash
"$PAPER_SEARCH_WRAPPER" sources
```

Search papers:

```bash
"$PAPER_SEARCH_WRAPPER" search "rice heavy ion mutagenesis" -n 5 -s pubmed,crossref,openalex,semantic -y 2018-2026
```

Download an open-access PDF:

```bash
"$PAPER_SEARCH_WRAPPER" download <source> <paper_id> -o <output_dir>
```

Read extractable full text:

```bash
"$PAPER_SEARCH_WRAPPER" read <source> <paper_id> -o <output_dir>
```

Normalize a saved search JSON:

```bash
python "${CODEX_HOME:?Set CODEX_HOME to the Codex configuration root}/skills/paper-search/scripts/export_paper_search_results.py" \
  --input <raw_json> \
  --outdir <output_dir> \
  --query "<query>" \
  --sources pubmed,crossref,openalex,semantic \
  --command "<exact command>"
```

## Default Workflow

1. Define the research question, organism, target genes/traits, method terms,
   year range, and inclusion boundaries.
2. Choose targeted sources. For biology and bioinformatics, start with
   `pubmed,pmc,europepmc,crossref,openalex,semantic,biorxiv,medrxiv`; add
   `arxiv` for computational methods and preprints.
3. Use the verified local wrapper when available; otherwise use web search or
   official source APIs with a small per-source limit first. Save raw JSON and
   stderr logs when the selected backend provides them.
4. For compatible saved JSON, run `export_paper_search_results.py` to create
   TSV, XLSX, and manifest outputs. Otherwise build the same fields directly
   from the cited web results without inventing unavailable backend metadata.
5. Review titles and abstracts, then read or download only papers needed for
   the user's decision.
6. Report the search strategy, source coverage, result count, and any upstream
   errors or rate limits.

## Output Requirements

For any non-trivial search, keep:

- raw JSON and stderr log when produced by the selected backend
- normalized TSV
- normalized XLSX
- manifest YAML with command, query, sources, year filter, retrieved time,
  tool commit, Python version, and record counts

## References

Load only as needed:

- `references/source-policy.md` - source reliability and access rules
- `references/reproducible-search.md` - provenance fields and output layout
- `examples/rice-literature-search.md` - rice mutagenesis search example
