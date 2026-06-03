# Research Seed Ranking

Rank research seeds by actionable value, not excitement.

## Seed Fields

```yaml
seed_id:
title:
source_papers:
source_type: original_gap|review_gap|controversy|method_transfer|external_update|expert_judgment
core_question:
minimum_next_step:
data_needed:
wet_lab_needed:
dry_lab_needed:
rice_relevance:
mutagenesis_relevance:
novelty:
feasibility:
time_to_minimum_result:
main_risk:
rank: P0|P1|P2|P3|Reject
ranking_rationale:
```

## Ranking

- `P0`: start minimum validation now.
- `P1`: worth more reading or small data check.
- `P2`: keep in backlog; dependencies not ready.
- `P3`: background only.
- `Reject`: weak evidence, not feasible, or not aligned.

Always state the failure mode.
