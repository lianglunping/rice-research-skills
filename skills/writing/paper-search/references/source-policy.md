# Source Policy

## Preferred Sources

Use these sources first for reproducible academic searches:

- PubMed: reliable biomedical metadata; usually no direct PDF.
- PMC: open-access biomedical full text when available.
- Europe PMC: biomedical metadata and open-access full text when available.
- Crossref: DOI and publisher metadata.
- OpenAlex: broad open scholarly metadata and citation context.
- Semantic Scholar: useful abstracts and citation metadata; API key improves
  rate limits.
- arXiv: reliable preprint search and PDF access.
- bioRxiv and medRxiv: life-science and medical preprints.
- Zenodo, HAL, DOAJ, CORE: open repository or journal records when available.

## Fallback Sources

- Google Scholar is useful for discovery but unstable because of bot detection.
  Use it only when public APIs miss likely papers, and record the limitation.
- Unpaywall requires `PAPER_SEARCH_MCP_UNPAYWALL_EMAIL`. Without an email,
  DOI-to-open-access fallback is expected to be disabled.

## Disallowed Sources

- Do not use Sci-Hub, mirror URLs, or access-bypass instructions.
- Do not suggest circumventing paywalls.
- Do not treat unavailable full text as missing evidence; mark it as not
  retrieved and explain the access limitation.

## Reporting Rule

Every literature claim should be tied to a citation candidate with at least
title, year, source, DOI/PMID/PMCID or URL, and retrieval date.
