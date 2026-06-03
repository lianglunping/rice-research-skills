# Assay Modes

## Supported in v1

### `indel_pcr`

- Uses the standard amplicon primer search workflow
- Reports `product_wt` and `product_mt`
- Suitable for gel-based or capillary follow-up of InDel loci

### `snp_pcr`

- Uses the same amplicon workflow
- `product_wt` and `product_mt` are identical because the allele length is unchanged
- Suitable for sequencing or generic amplicon validation of SNP loci

## Not Implemented in v1

These modes are intentionally out of scope for the current skill:

- `kasp`
- `dcaps`
- targeted enrichment primer panels
- long-amplicon PCR for third-generation sequencing
- multiplex balancing

Do not route those assays through the current scripts as if they were implemented.

## Preference Compatibility Note

The user default preferences for this skill require:

- primer length `18-22 bp`
- primer Tm `58-60 C`
- specificity
- each primer to stay at least `1000 bp` away from the target site when feasible
- panel-level similarity in Tm and product size when possible

Those defaults can be stricter than the current v1 short-amplicon implementation. If the requested
task or assay cannot satisfy them, report a preference conflict instead of pretending that the v1
workflow already implements a compatible long-amplicon design mode.
