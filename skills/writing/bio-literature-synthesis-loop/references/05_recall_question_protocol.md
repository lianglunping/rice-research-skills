# Recall Question Protocol

Generate active-recall questions so the user can retain the paper's logic.

## Question Types

- **Core claim**: What is the main claim and what evidence supports it?
- **Figure logic**: Which figure carried the causal burden?
- **Method boundary**: Which parameter or control was missing?
- **Statistics**: Did the result show effect size, correction, and replication?
- **Causality**: Was the evidence association, function, mechanism, or biochemical causality?
- **Discussion audit**: Which part of Discussion was overextended?
- **Transfer**: What should we copy or avoid in our own rice/breeding/bioinformatics work?
- **Gap**: What is the smallest next experiment or analysis?

## Format

```yaml
question:
answer_key:
source_citekey:
source_section_or_figure:
difficulty: easy|medium|hard
review_next:
```

Questions should force retrieval, not recognition.
