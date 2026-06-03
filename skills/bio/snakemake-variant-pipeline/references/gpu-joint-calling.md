# GPU-Accelerated Joint Calling

This note applies to the GATK branch of the skill. Do not use it for the optional `bcftools` branch.

## Option 1: NVIDIA Parabricks

Use after all per-sample gVCFs are generated.

```bash
pbrun germline \
  --ref ${REF} \
  --in-gvcf sample1.g.vcf.gz --in-gvcf sample2.g.vcf.gz \
  --out-variants merged.vcf.gz \
  --num-gpus 1 \
  --tmp-dir /data/tmp
```

## Option 2: GATK with GenomicsDB

Prefer this over `CombineGVCFs` for larger cohorts.

```bash
gatk --java-options "-Xmx160g" GenomicsDBImport \
    --sample-name-map sample_map.txt \
    --genomicsdb-workspace-path gendb_workspace \
    --intervals intervals.list \
    --reader-threads 4

gatk --java-options "-Xmx160g" GenotypeGVCFs \
    -R ${REF} \
    -V gendb://gendb_workspace \
    -O merged.raw.vcf.gz
```

## Option 3: CPU `CombineGVCFs` plus accelerated downstream genotyping

```bash
gatk --java-options "-Djava.io.tmpdir=/data/tmp -Xmx160g" CombineGVCFs \
    -R ${REF} ${GVCF_ARGS} -O merge.g.vcf.gz

gatk --java-options "-Djava.io.tmpdir=/data/tmp -Xmx160g" GenotypeGVCFs \
    -R ${REF} -V merge.g.vcf.gz -O merge.raw.vcf.gz
```

## Practical Guidance

| Cohort size | Suggested path |
|-------------|----------------|
| `<50` samples | Standard GATK |
| `50-200` samples | GenomicsDB plus interval parallelism |
| `>200` samples | Parabricks or carefully sharded GenomicsDB |
