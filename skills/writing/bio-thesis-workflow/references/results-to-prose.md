# Results To Prose

Use this module when the user provides structured outputs and needs thesis-style result language.

## Valid Inputs

- `tsv` or `xlsx` tables
- figure-level `README.md`
- `run_manifest.md`
- result draft paragraphs
- figure panels and legends

## Core Principle

Write from the evidence hierarchy below:

1. source table or manifest
2. plotted summary
3. project README
4. existing draft prose

Do not let polished prose outrun the table.

## Paragraph Template

Use this sequence unless the section needs a different order:

1. frame the comparison or analysis target
2. report the main numerical pattern
3. note the most important cross-group contrast
4. state the boundary or caveat

## Claim Strength Bands

### Descriptive

Use for direct patterns in the outputs.

Examples:
- "In the current filtered set, rice retained 10,076 variants."
- "Coding-related regions showed relative depletion under the refined assignment scheme."

### Evidence-backed interpretation

Use when the table and analysis support a cautious interpretation.

Examples:
- "These results are consistent with a relative avoidance of coding-related regions."
- "The pattern suggests that the main signal is carried by the basic-region layer rather than the special-window layer."

### Forward inference

Use only with explicit qualification.

Examples:
- "This pattern may reflect differential mutational tolerance, although dedicated validation is still required."
- "The observed enrichment could be related to chromatin state, but the present analysis is descriptive rather than causal."

## Required Guardrails

- Preserve exact counts, ratios, q values, and category names.
- Carry over essential caveats such as:
  - missing normalization,
  - sample-size imbalance,
  - descriptive-only analysis,
  - clipped plotting values,
  - or filtering-scheme dependence.
- If the figure README says a category is display-only, keep that distinction in prose.

## Legends

Figure legend or table note should contain:
- what is shown,
- panel meaning,
- units or transformed scale,
- significance definition if present,
- and display-specific handling if any.

## Domain Hints

For rice mutagenesis projects, common high-value result frames include:
- mutation burden by material or species
- substitution spectrum and Ti/Tv
- InDel composition and size distribution
- functional-region enrichment or depletion
- candidate-gene category counts
- ATAC or chromatin-context overlap

## Output Shapes

- result paragraph only
- result paragraph plus legend
- bilingual Chinese and English pair
- short "ready for Word" section block
