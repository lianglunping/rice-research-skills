# Data Sources For Trait-First Rice Haplotype Runs

Use this reference when a rice candidate-gene haplotype analysis needs to choose between 3K and 万份水稻 data by phenotype sample overlap.

## Caller-provided remote configuration

| Field | Value |
|---|---|
| Remote host | `REPLACE_HOST` |
| Conda environment | `ngs` |
| Activation | `conda activate ngs` |
| 3K VCF directory | `/path/to/reference-data/3K/3K/SNP` |
| 万份水稻 VCF directory | `/path/to/reference-data/superrice` |
| 万份水稻 SNP genotype directory | `/path/to/reference-data/superrice/1.rare_SNP` |
| 万份水稻 InDel genotype directory | `/path/to/reference-data/superrice/2.rare_InDel` |
| Preferred remote file search | `fd` |
| Preferred remote text search | `rg` |

Use `fd` and `rg` on `REPLACE_HOST` before falling back to `find` or `grep`.

All paths below are placeholders. Supply authorized input locations and verify
the reference, metadata schema and dataset release for the current task. No
remote host, installed environment or downloaded dataset is assumed to exist.

## Sample Metadata

- 3K sample grouping is caller-provided: `/path/to/metadata/population_groups.xlsx`.
- 万份水稻 sample metadata is caller-provided under `/path/to/metadata/`.
- Example metadata-table roles:
  - `/path/to/metadata/metadata_primary.xlsx`
  - `/path/to/metadata/metadata_secondary.xlsx`
- Normalize sample IDs for matching by trimming whitespace, removing non-alphanumeric separators, and uppercasing; keep the original IDs in audit tables.
- Use `Species Information` to derive 万份水稻 analysis groups:
  - `Wild`: values matching `^Or|Or-|rufipogon|nivara`
  - `Cultivar`: values matching `^XI|^GJ|^cA|^cB`
  - `Undefined`: all remaining values, including `Os-undefined`

## 万份水稻 Genotype Format

The current `superrice` files are wide tab-delimited gzip genotype tables rather than ordinary VCFs. The stable format is:

```text
CHROM  POS  REF  ALT  TK00001  TK00002  ...
```

Genotype values are phased or missing, for example `0|0`, `0|1`, `1|1`, and `.|.`. Therefore, for common-haplotype network analysis, default `phasing_mode=auto` should treat `|` genotypes as already phased and avoid unnecessary Beagle re-phasing.

Use `templates/scripts/extract_superrice_region.py` to extract the target interval and write:

- `{prefix}.superrice_region_genotype.tsv.gz`
- `{prefix}.superrice_sample_manifest.tsv/.xlsx`
- `{prefix}.superrice_group_counts.tsv/.xlsx`
- `{prefix}.superrice_extract_audit.tsv/.xlsx`

## Dataset Selection Rule

Before running the full haplotype workflow, compare phenotype sample overlap against both candidate datasets.

1. Extract or read sample IDs from the 3K VCF set and the 万份水稻 VCF set.
2. Normalize phenotype and VCF sample IDs with the same deterministic rule.
3. Select the dataset with the larger number of phenotype-matched samples: `dataset_selection_rule=max_trait_overlap`.
4. If the match count is tied, stop and ask for a project decision rather than choosing silently.
5. Write `sample_match_audit.tsv` and `sample_match_audit.xlsx` before formal analysis.

The final report must state which dataset was selected, the match count for both datasets, and the exact input paths used.
