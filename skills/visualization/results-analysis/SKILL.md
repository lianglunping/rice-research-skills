---
name: results-analysis
description: "Research result interpretation for biology, genomics or ML evaluation. Choose methods from the question, statistical unit and evidence; distinguish exploration from confirmatory inference."
metadata:
  tags:
  - Research
  - Analysis
  - Statistics
  - Visualization
  - Scientific Reporting
  version: 0.2.0
---

# Analyze Research Results

Begin with the biological or technical question, study objects, statistical unit,
available evidence and actual decision. Identify cohort, reference, release,
sample identifiers and comparison denominators before selecting methods.

For genomics and breeding, prioritize observed effect direction and size,
replication, consistency across materials and evidence, quality, plausible
alternative explanations and validation value. Separate candidate ranking,
descriptive catalogs and exploration from confirmatory inference, causality,
inheritance and mechanism. Preserve WES/WGS, KASP, generation and cohort bounds.

For ML model evaluation, inspect evaluation protocol, metric direction, baseline,
dataset, subject/fold/run/seed units, repeated runs and comparability. Existing
ML-specific statistical and visualization references apply only to that branch.

Choose statistics from the question. Assess detectable denominators for mutation
rates, enrichment/depletion, absence claims or quantitative comparisons depending
on callable scope. Missing callable regions do not block observed variant
catalogs, annotation, candidate ranking or single-site validation; limit claims.
Use multiple-testing control and uncertainty estimates when the hypothesis family
and inference justify them. Report effect sizes and assumptions; do not force
significance tests or confidence intervals on every descriptive analysis.

Inspect actual inputs; do not invent missing metrics or biological results. Use
R for research plots unless project conventions or the user specify otherwise.
Create figures only when they answer the task; inspect final PDF/PNG semantics
and legibility. Explain each main figure's observation and decision implication.

Deliver the minimum sufficient analysis, exact source/output paths, parameters,
commands, dependency versions and seeds where relevant. Put long methods, tables
and audit trails in supporting files. An `analysis-report.md`, `stats-appendix.md`
and figure catalog are options for a substantial bundle, not universal inputs.

Load `references/statistical-methods.md` and `references/statistical-reporting.md`
only for applicable ML comparisons; `references/figure-interpretation.md` helps
connect a figure to evidence. The question-specific rules above take precedence
over generic checklist expectations in those references.
