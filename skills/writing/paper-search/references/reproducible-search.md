# Reproducible Search Record

## Directory Layout

Use a dated or task-specific directory under the project workspace, for example:

```text
outputs/literature/20260419_rice_heavy_ion/
  raw_search.json
  raw_search.stderr.log
  papers.tsv
  papers.xlsx
  manifest.yaml
  downloads/
```

For temporary smoke tests, use `temp_tests/` and delete it after verification.

## Manifest Fields

Record at least:

- `query`
- `sources`
- `year_filter`
- `retrieved_at`
- `command`
- `paper_search_mcp_repo`
- `paper_search_mcp_commit`
- `python_version`
- `raw_input`
- `tsv_output`
- `xlsx_output`
- `total_raw_records`
- `total_normalized_records`
- `total_deduplicated_records`
- `source_results`
- `errors`

## Normalization Rules

Preferred output columns:

- `title`
- `authors`
- `year`
- `source`
- `paper_id`
- `doi`
- `pmid`
- `pmcid`
- `url`
- `pdf_url`
- `abstract`
- `query`
- `sources`
- `retrieved_at`
- `record_hash`

## Deduplication Rules

1. If DOI exists, deduplicate by normalized DOI.
2. If DOI is missing, deduplicate by normalized title plus year.
3. Preserve multi-source provenance in the `source` column when records merge.
4. Never delete the raw JSON; use normalized outputs only as analysis views.
