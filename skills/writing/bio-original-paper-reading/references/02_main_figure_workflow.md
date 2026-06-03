# Main Figure Workflow

Original research papers usually tell their strongest story through Main Figures. Rebuild that story before writing a narrative summary.

## Figure-First Story Reconstruction

For each Main Figure, identify:

| Field | Meaning |
| --- | --- |
| `figure_id` | Fig. 1, Fig. 2, etc. |
| `paper_story_role` | setup, phenotype, mapping, screening, functional validation, mechanism, omics support, model, breeding/application |
| `central_question` | What question this figure is supposed to answer |
| `author_claim` | What the authors want the reader to believe |
| `actual_evidence` | What the panels actually show |
| `evidence_gap` | What remains unproven |
| `next_figure_link` | How this figure leads to the next figure |

## Common Figure Order Patterns

- Phenotype -> mapping -> candidate gene -> validation -> mechanism -> application.
- Population/resource -> omics landscape -> association -> candidate prioritization -> wet-lab validation.
- Method benchmark -> case study -> validation -> generalization.
- Stress/trait observation -> transcriptomics/proteomics -> regulatory model -> functional test.
- Dose-response/system design -> mutation spectrum -> inheritance/stability -> elite line screening -> breeding resource evaluation.

## Figure Relationship Types

Use one or more:

- `setup`: defines material, phenotype, technology, or question.
- `discovery`: identifies candidate gene, locus, variant, pathway, or pattern.
- `validation`: tests whether the candidate affects the trait.
- `mechanistic`: tests interaction, regulation, localization, expression, or biochemical effect.
- `orthogonal_support`: independent data type supports the same model.
- `exclusion`: rules out alternative explanations.
- `application`: breeding, field, population, or translational value.
- `conceptual_model`: summarizes a mechanism or framework.

## Critical Reading Prompts

- Does the figure order create a persuasive story even if one panel is weak?
- Which figure carries the main causal burden?
- Which figure is only descriptive but written as mechanistic?
- Is this paper really about molecular mechanism, or is the main claim about experimental design, mutagen choice, dosage window, resource generation, or breeding utility?
- Which claim depends on supplementary data not currently available?
- Does the last model figure overstate what direct evidence proves?
