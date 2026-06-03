# Examples

Use these as compact style anchors, not fixed templates.

## Gap Table Row

| gap | type | why it matters | evidence missing | minimum next step | feasibility |
| --- | --- | --- | --- | --- | --- |
| Whether SV presence/absence explains stress tolerance across rice subpopulations | data-resource + validation | GWAS peaks may miss large structural variants | matched pan-genome SV calls, phenotype, and validation lines | test one trait with existing resequencing + targeted PCR validation | medium |

## Route Row

| route | assumption | strength | limitation | best use |
| --- | --- | --- | --- | --- |
| pan-genome/SV route | causal variation may be absent from single-reference SNP maps | captures presence/absence and large variants | needs high-quality assemblies or robust SV callers | gene family expansion, resistance loci, structural haplotypes |

## Research Seed Row

```yaml
seed_id: reviewcite-S01
core_question: Do induced structural variants create novel drought-response haplotypes in elite rice backgrounds?
why_now: long-read and pan-genome resources make SV discovery more tractable
minimum_analysis: screen existing mutant resequencing data for candidate SVs near drought-response genes
minimum_validation_experiment: PCR breakpoint validation plus qRT-PCR under drought treatment
main_risk: phenotype may be background- or environment-specific
```
