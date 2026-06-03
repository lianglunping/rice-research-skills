# Panel Inventory Protocol

Create a panel inventory for every Main Figure panel. This is the core anti-hallucination device.

## Required Panel Fields

| Field | Rule |
| --- | --- |
| `paper_citekey` | Use Zotero citekey if available; otherwise provisional citekey |
| `figure_id` | Fig. 1, Fig. 2, etc. |
| `panel_id` | Fig. 1a, Fig. 1b, etc. |
| `page` | PDF page if available |
| `pdf_visual_verified` | `true` only when the panel was checked against original PDF page or screenshot |
| `parser_source` | original_pdf, parser_markdown, parser_json, OCR, screenshot, or mixed |
| `axis_confidence` | high, medium, low, or not_applicable |
| `caption_source` | Original caption location or parser source |
| `result_text_source` | Result section or paragraph that discusses the panel |
| `caption_excerpt` | Short caption evidence, not a full copied caption |
| `result_section` | Result subsection where panel is discussed |
| `data_type` | phenotype, genotype, GWAS, RNA-seq, qPCR, WB, Co-IP, EMSA, microscopy, model, etc. |
| `x_axis` | Exact x-axis label/unit; if absent, describe visual axis or set `not_applicable` |
| `y_axis` | Exact y-axis label/unit; if absent, describe visual signal or set `not_applicable` |
| `groups` | Genotypes, treatments, tissues, time points, environments, populations |
| `controls` | WT, mock, empty vector, input, IgG, loading control, housekeeping gene, etc. |
| `sample_size` | Exact n if stated; otherwise `not_reported` |
| `biological_replicates` | Exact count if stated; otherwise `not_reported` |
| `technical_replicates` | Exact count if stated; otherwise `not_reported` |
| `statistical_test` | Exact test; otherwise `not_specified` |
| `multiple_testing_correction` | FDR, Bonferroni, permutation, etc.; otherwise `not_specified` |
| `effect_size` | Use reported value only; otherwise `not_reported` |
| `visual_trend` | What is visibly higher/lower/different; avoid overclaiming |
| `author_claim` | Claim linked to this panel |
| `claim_type` | descriptive, associative, causal, mechanistic, predictive, translational |
| `evidence_strength` | strong, moderate, weak, insufficient |
| `missing_controls` | Controls or validations missing from the panel |
| `alternative_explanations` | Plausible non-author explanations |
| `depends_on_panels` | Panels needed to support the same claim |
| `notes_for_our_research` | Transferable lesson for future design |

## Axis Rules

- Copy axis labels and units exactly when visible.
- Do not infer units from common practice unless the paper states them.
- If axis labels are inferred from caption or surrounding text rather than visibly read from the figure, mark `axis_confidence: medium` or `low`.
- If panel boundaries are uncertain, mark `pdf_visual_verified: false` and do not make panel-level conclusions beyond descriptive notes.
- For heatmaps, define row/column meanings, color scale, clustering, and normalization.
- For Manhattan plots, define x-axis genome/chromosome, y-axis statistic, threshold line, and peak interpretation.
- For IGV tracks, define genomic coordinates, coverage/read depth signal, variants, and sample lanes.
- For gels/blots, x/y axes are usually visual lanes/signals rather than plot axes; decode lane order, input, IP, control, and loading marker.

## Evidence Strength

- `strong`: direct test with proper controls, replicates, statistics, and limited alternative explanations.
- `moderate`: supports the claim but lacks one important control, replication, or orthogonal validation.
- `weak`: descriptive or correlative support only.
- `insufficient`: panel cannot support the claimed inference, or key information is unreadable/missing.

## Mini Example

```yaml
figure_id: Fig3
panel_id: Fig3b
pdf_visual_verified: true
parser_source: original_pdf+screenshot
axis_confidence: high
data_type: qRT-PCR
x_axis: WT, mutant, complemented line
y_axis: Relative expression of GeneX
groups: leaf tissue under drought treatment
controls: WT and reference gene normalization
sample_size: not_reported
biological_replicates: 3
statistical_test: one-way ANOVA with Tukey test
visual_trend: mutant shows lower GeneX expression than WT; complemented line partially restores expression
author_claim: GeneX expression is disrupted in the mutant and restored by complementation
claim_type: functional
evidence_strength: moderate
missing_controls: exact primer efficiency and raw Ct distribution not shown
alternative_explanations: background mutation or drought response timing difference
```
