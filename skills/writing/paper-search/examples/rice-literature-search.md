# Rice Literature Search Example

Goal: find recent literature on rice heavy-ion mutagenesis and molecular
breeding.

```bash
/path/to/codex-paper-search/run_paper_search.sh search \
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
  /path/to/codex/skills/paper-search/scripts/export_paper_search_results.py \
  --input outputs/literature/20260419_rice_heavy_ion/raw_search.json \
  --outdir outputs/literature/20260419_rice_heavy_ion \
  --query "rice heavy ion mutagenesis molecular breeding" \
  --sources pubmed,crossref,openalex,semantic,biorxiv \
  --year 2018-2026 \
  --command "/path/to/codex-paper-search/run_paper_search.sh search 'rice heavy ion mutagenesis molecular breeding' -n 5 -s pubmed,crossref,openalex,semantic,biorxiv -y 2018-2026"
```

Report:

- exact query
- sources
- year filter
- total records and per-source counts
- upstream errors or rate limits
- output paths
