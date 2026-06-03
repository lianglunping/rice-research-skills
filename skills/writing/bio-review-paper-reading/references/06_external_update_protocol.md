# External Update Protocol

Use external search to see the whole field, not to overwrite the review's original claims.

External update is enabled by default for review reading unless the user disables browsing. It is especially important for older reviews, fast-moving technologies, controversies, and author-team follow-up.

If the review is very recent and no meaningful follow-up literature is detectable, say so explicitly instead of padding the section with weak update noise.

## Search Targets

- the review title/DOI,
- author team follow-up,
- core genes, technologies, theories, or datasets,
- major controversies identified by the review,
- new methods or resources since publication,
- high-quality original research from the last 3 years when relevant.

## Update Categories

```yaml
confirmatory:
corrective:
contradictory:
method_replacement:
major_dataset_or_resource:
author_team_follow_up:
still_unresolved:
```

## Reporting

For each update:

```yaml
source_label: "[外部检索补充]"
searched_on:
query_or_source:
paper_or_resource:
what_changed:
relationship_to_review:
confidence:
```

Keep external updates in dedicated sections: latest progress, controversy status, research seeds, or note addendum.

Do not expand into unrelated subfields just because new papers are available. Stay anchored to the review's core question and the user's domain focus.
