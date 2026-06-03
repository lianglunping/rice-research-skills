# Route Divergence Map

Review papers often merge different research routes. Split them explicitly.

## Route Schema

```yaml
route_id:
route_name:
core_assumption:
representative_methods:
representative_evidence:
representative_papers:
strengths:
limitations:
suitable_questions:
unsuitable_questions:
required_data:
wet_lab_dependency:
dry_lab_dependency:
translation_potential:
failure_modes:
```

## Common Routes

- candidate gene / QTL / GWAS route
- pan-genome / SV / presence-absence route
- transcriptomics / single-cell / spatial omics route
- regulatory network / GRN route
- gene editing route
- induced mutagenesis and population screening route
- microbiome or holobiont route
- algorithm/method development route
- breeding deployment route

## Relationship Types

- `complementary`: routes answer different parts of the same question.
- `competitive`: routes propose alternative explanations or methods.
- `dependency`: one route requires resources from another.
- `translation_chain`: discovery route feeds validation and breeding route.
