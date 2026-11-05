# Domestication-Style Common Haplotype Network Module

This reference adapts the haplotypic-analysis idea from Zhang et al. 2023, "Multiple domestications of Asian rice" (DOI: 10.1038/s41477-023-01476-z), for the local rice candidate-gene haplotype workflow.

## Source Anchors

- Paper: Nature Plants 2023, DOI `10.1038/s41477-023-01476-z`.
- Code repository: `https://github.com/zhangfumin/domestication`, branch `rice`, verified commit `d9329cc88d92f193568eaf43a0333044979f7135`.
- Relevant upstream scripts:
  - `haplotypic-analysis/step2-get.target.segment.vcf.pl`
  - `haplotypic-analysis/step3-cal.site.diversity.and.filtering.pl`
  - `haplotypic-analysis/step4-filter.sample.pl`
  - `haplotypic-analysis/step5-phasing.gene.segment.pl`
  - `haplotypic-analysis/step6-sta.for.hap.pl`

Local verification on 2026-07-06 confirmed the local `domestication-rice/haplotypic-analysis` copies matched GitHub raw files by SHA256.

## What To Reuse

Reuse the analytical concepts, not the Perl implementation verbatim:

1. Extract the target gene interval from a genome-wide genotype source.
2. Track wild/cultivar group composition explicitly.
3. Use phased haplotypes where phase is available.
4. Define common haplotypes by frequency `>0.5%`.
5. Build a network from haplotype pattern distances.
6. Export node and edge tables so the figure is auditable.

## What Not To Copy Blindly

- Do not assume the upstream wild/cultivar group labels (`IND`, `TEJ`, `TRJ`, `RUF1`, `RUF2`, `NIV1`, `NIV2`) exist in local metadata.
- Do not assume the input is a whole-genome VCF. The current 万份水稻 source is wide genotype tables under `/path/to/reference-data/superrice`.
- Do not infer domestication origin from a network alone.
- Do not run Beagle when the genotype field is already phased with `|`.

## Local Defaults

| Field | Default |
|---|---|
| `common_haplotype_frequency_min` | `0.005` |
| `phasing_mode` | `auto` |
| `domestication_network_flank_bp` | `0` |
| SNP genotype source | `/path/to/reference-data/superrice/1.rare_SNP/Chr*.rareSNP.genotype.gz` |
| InDel genotype source | `/path/to/reference-data/superrice/2.rare_InDel/Chr*.rareINDEL.genotype.gz` |
| Metadata source | `/path/to/metadata/*.xlsx` |

## Required Outputs

For prefix `{GENE_ID}`, write TSV and XLSX pairs for:

- `{GENE_ID}.common_haplotype_counts`
- `{GENE_ID}.common_haplotype_sample_assignment`
- `{GENE_ID}.common_haplotype_node_table`
- `{GENE_ID}.common_haplotype_pairwise_distances`
- `{GENE_ID}.common_haplotype_edges`
- `{GENE_ID}.common_haplotype_variant_table`
- `{GENE_ID}.common_haplotype_skipped_samples`
- `{GENE_ID}.common_haplotype_network_audit`
- `{GENE_ID}.common_haplotype_network_qa`

Also write:

- `{GENE_ID}.common_haplotype_network.pdf`
- `{GENE_ID}.common_haplotype_network.png`
- `{GENE_ID}.network_publisher_edges.tsv`

## Evidence Boundary

The network is descriptive. It can support statements about:

- common haplotype structure in the target interval,
- wild/cultivar/undefined composition of each common haplotype,
- relative Hamming-distance relationships among common haplotypes.

It cannot alone support statements about:

- single or multiple domestication origins,
- introgression direction,
- selective sweep,
- causal variant identity,
- breeding value.

Those claims require independent selection statistics, sampling design, phenotype association, and biological or breeding validation.
