---
name: paper-search
description: This skill should be used when the user asks to find papers, search academic literature, run literature retrieval, search PubMed/OpenAlex/Semantic Scholar/arXiv/bioRxiv, download open-access paper PDFs, read full text, or asks in Chinese for "wenxian jiansuo", "zhao lunwen", "xiazai lunwen", or "du quanwen".
---

# Paper Search

Use this skill for reproducible academic literature search through the local
`paper-search-mcp` CLI and optional MCP server.

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

## Local Commands

List available sources:

```bash
/path/to/codex-paper-search/run_paper_search.sh sources
```

Search papers:

```bash
/path/to/codex-paper-search/run_paper_search.sh search "rice heavy ion mutagenesis" -n 5 -s pubmed,crossref,openalex,semantic -y 2018-2026
```

Download an open-access PDF:

```bash
/path/to/codex-paper-search/run_paper_search.sh download <source> <paper_id> -o <output_dir>
```

Read extractable full text:

```bash
/path/to/codex-paper-search/run_paper_search.sh read <source> <paper_id> -o <output_dir>
```

Normalize a saved search JSON:

```bash
mamba run -n paper-search-mcp-py311 python /path/to/codex/skills/paper-search/scripts/export_paper_search_results.py \
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
3. Run `search` with a small per-source limit first. Save stdout as raw JSON
   and stderr as logs.
4. Run `export_paper_search_results.py` to create TSV, XLSX, and manifest
   outputs.
5. Review titles and abstracts, then read or download only papers needed for
   the user's decision.
6. Report the search strategy, source coverage, result count, and any upstream
   errors or rate limits.

## Output Requirements

For any non-trivial search, keep:

- raw JSON from `paper-search search`
- stderr log
- normalized TSV
- normalized XLSX
- manifest YAML with command, query, sources, year filter, retrieved time,
  tool commit, Python version, and record counts

## References

Load only as needed:

- `references/source-policy.md` - source reliability and access rules
- `references/reproducible-search.md` - provenance fields and output layout
- `examples/rice-literature-search.md` - rice mutagenesis search example
