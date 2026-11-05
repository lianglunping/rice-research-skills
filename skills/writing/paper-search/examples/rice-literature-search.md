# Rice Literature Search Example

Goal: find recent literature on rice heavy-ion mutagenesis and molecular
breeding.

```bash
: "${PAPER_SEARCH_WRAPPER:?Set PAPER_SEARCH_WRAPPER to an executable local wrapper}"
"$PAPER_SEARCH_WRAPPER" search \
  "rice heavy ion mutagenesis molecular breeding" \
  -n 5 \
  -s pubmed,crossref,openalex,semantic,biorxiv \
  -y 2018-2026 \
  > outputs/literature/20260419_rice_heavy_ion/raw_search.json \
  2> outputs/literature/20260419_rice_heavy_ion/raw_search.stderr.log
```

Normalize the result:

```bash
mamba run -n paper-search-mcp-py311 python \
  "${CODEX_HOME:?Set CODEX_HOME to the Codex configuration root}/skills/paper-search/scripts/export_paper_search_results.py" \
  --input outputs/literature/20260419_rice_heavy_ion/raw_search.json \
  --outdir outputs/literature/20260419_rice_heavy_ion \
  --query "rice heavy ion mutagenesis molecular breeding" \
  --sources pubmed,crossref,openalex,semantic,biorxiv \
  --year 2018-2026 \
  --command "${PAPER_SEARCH_WRAPPER} search 'rice heavy ion mutagenesis molecular breeding' -n 5 -s pubmed,crossref,openalex,semantic,biorxiv -y 2018-2026"
```

If `PAPER_SEARCH_WRAPPER` is unavailable, perform the same query with web
search or official source APIs and report direct source URLs, retrieval date,
filters, and any rate-limit or coverage gaps.

Report:

- exact query
- sources
- year filter
- total records and per-source counts
- upstream errors or rate limits
- output paths
