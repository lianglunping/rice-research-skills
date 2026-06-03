---
name: variant-primer-design
description: This skill should be used when the user asks to design SNP or InDel PCR primers from variant tables, batch-design validation amplicon primers against an arbitrary reference genome, screen primer specificity with BLAST, redesign failed or non-specific primer pairs, or build a reusable primer-design workflow for frequent wet-lab validation work. It currently supports SNP/InDel amplification primer design with BLAST specificity screening, and does not yet implement KASP, dCAPS, targeted enrichment, or long-amplicon third-generation sequencing primer schemes.
---

# Variant Primer Design

Use this skill for a reusable, reference-genome-agnostic primer workflow:

- normalize variant tables,
- build sequence context from a reference FASTA when needed,
- design SNP/InDel PCR primers,
- run BLAST specificity screening,
- redesign failed or non-specific loci with a relaxed profile,
- export final TSV/XLSX/report outputs.

The user has fixed default primer preferences for all future primer design tasks. Read
`references/USER_DEFAULT_PREFERENCES.md` before choosing or running a workflow, and treat those
preferences as higher priority than the v1 baseline script defaults.

## Boundaries

This skill is for:

- `indel_pcr`
- `snp_pcr`

This skill is not yet for:

- `kasp`
- `dcaps`
- targeted enrichment panels
- long-amplicon or third-generation sequencing primer schemes

If the user asks for one of the unsupported modes, do not fake a design workflow. Explain that v1 only implements SNP/InDel PCR amplicon design and either scope the request down or stop.

If the user default preferences conflict with the current v1 script behavior, do not silently fall
back to the baseline short-amplicon settings. Report the conflict explicitly and either switch to a
compatible custom workflow or get approval to relax the preferences.

## Default Workflow

1. Read [references/USER_DEFAULT_PREFERENCES.md](references/USER_DEFAULT_PREFERENCES.md) to load the user's standing primer design defaults.
2. Read [references/INPUT_SCHEMA.md](references/INPUT_SCHEMA.md) to confirm whether the input already has `full_seq`, or whether sequence context must be built from a reference FASTA.
3. Read [references/ASSAY_MODES.md](references/ASSAY_MODES.md) to confirm the requested assay is supported by v1 and compatible with the user defaults.
4. On first use or when dependencies are missing, run `scripts/bootstrap_env.sh`.
5. Read [references/WORKFLOW.md](references/WORKFLOW.md) and run `scripts/run_primer_workflow.py` only if the requested assay is compatible with the user defaults or the user has approved a relaxation.
6. Review `final_primers.tsv`, `final_primers.xlsx`, `primer_specificity.tsv`, `primer_order.tsv`, and `design_report.txt`.
7. If the final table still contains `non_specific` or `FAILED` loci after the relaxed round, report them explicitly instead of overstating success.

## Safety Rules

- Never overwrite the input table or the reference FASTA.
- Always write outputs into a new output directory.
- Validate that the reference allele matches the reference genome before designing primers from genomic coordinates.
- Treat BLAST specificity screening as required, not optional, for this skill.
- Keep the reason code for every failed locus.
- Treat a conflict between the user default preferences and the v1 workflow as a real blocker, not as permission to silently use incompatible defaults.

## Resources

- [references/USER_DEFAULT_PREFERENCES.md](references/USER_DEFAULT_PREFERENCES.md) - standing user defaults that take precedence over the v1 baseline settings
- [references/WORKFLOW.md](references/WORKFLOW.md) - operational read order and command examples
- [references/INPUT_SCHEMA.md](references/INPUT_SCHEMA.md) - accepted input columns and aliases
- [references/ASSAY_MODES.md](references/ASSAY_MODES.md) - supported and unsupported assay modes
- [references/REDESIGN_POLICY.md](references/REDESIGN_POLICY.md) - strict and relaxed redesign policy
- [references/TOOLCHAIN.md](references/TOOLCHAIN.md) - dedicated environment and dependency notes
- [references/OUTPUT_CONTRACT.md](references/OUTPUT_CONTRACT.md) - output files and column contract
