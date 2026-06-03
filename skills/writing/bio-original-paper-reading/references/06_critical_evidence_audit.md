# Critical Evidence Audit

Adopt a skeptical but fair stance. The purpose is to learn from both strengths and weaknesses.

## Audit Dimensions

| Dimension | Questions |
| --- | --- |
| Statistical boundary | Is the test appropriate? Are multiple tests controlled? Are effect sizes shown? Is statistical significance confused with biological meaning? |
| Causal boundary | Is the evidence descriptive, associative, functional, mechanistic, or biochemical? Is causality overclaimed? |
| Genetic boundary | Are background, LD, population structure, complementation, rescue, allelism, or segregation addressed? |
| Omics boundary | Are batch effects, depth, normalization, filtering, annotation, and false positives handled? |
| Wet-lab boundary | Are controls, replicates, representative images, quantification, and orthogonal assays adequate? |
| Breeding translation boundary | Are results validated in relevant germplasm, field environments, elite backgrounds, and breeding contexts? |
| Mutagenesis relevance | Are induced variants, background mutations, off-target/background effects, and line stabilization considered? |

## Critical Audit Output

```yaml
main_conclusion:
author_story:
evidence_chain:
strongest_evidence:
weakest_link:
statistical_boundary:
causal_boundary:
genetic_boundary:
omics_boundary:
wet_lab_boundary:
breeding_translation_boundary:
missing_controls:
missing_negative_results:
alternative_models:
confidence: high|medium|low
what_we_should_learn:
```

## Transferable Lessons

Always include lessons for the user's future work:

- Which controls should not be omitted?
- Which metadata must be recorded before analysis?
- Which figure design made evidence stronger or weaker?
- Which statistical shortcut could mislead reviewers?
- Which validation step is essential before claiming breeding value?
- Which author narrative technique made weak evidence look stronger?
