# Output Contract

## Main Outputs

The workflow writes a new output directory containing:

- `final_primers.tsv`
- `final_primers.xlsx`
- `primer_specificity.tsv`
- `primer_specificity.xlsx`
- `primer_order.tsv`
- `primer_order.xlsx`
- `design_report.txt`
- `intermediate/`

## `final_primers` Columns

Expected core columns:

- `name`
- `status`
- `reason`
- `chrom`
- `pos`
- `ref`
- `alt`
- `variant_type`
- `indel_size`
- `forward_name`
- `forward_seq`
- `forward_len`
- `forward_tm`
- `forward_gc`
- `reverse_name`
- `reverse_seq`
- `reverse_len`
- `reverse_tm`
- `reverse_gc`
- `product_wt`
- `product_mt`
- `tm_diff`
- `avg_tm`
- `avg_gc`
- `var_dist_f`
- `var_dist_r`
- `center_ratio`
- `score`
- `design_params`
- `selected_round`
- `redesigned`
- `specificity_status`
- `specificity_note`
- `forward_hits`
- `reverse_hits`

Additional input metadata columns may also be preserved.

## `primer_specificity` Columns

- `name`
- `forward_name`
- `forward_hits`
- `reverse_name`
- `reverse_hits`
- `specificity_status`
- `specificity_note`

## `primer_order` Columns

- `name`
- `primer_name`
- `direction`
- `sequence`
- `length`
- `design_params`
- `specificity_status`

## Intermediate Files

`intermediate/` stores round-specific and BLAST-specific artifacts, such as:

- `round1_results.tsv`
- `round2_results.tsv`
- `round1_primers.fa`
- `round2_primers.fa`
- `round1_blast.tsv`
- `round2_blast.tsv`

Intermediate files are for audit and debugging. The final tables are the primary delivery outputs.
