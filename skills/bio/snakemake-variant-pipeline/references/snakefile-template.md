# Snakefile Module Templates

## Contents

- Config schema
- `rules/common.smk`
- `rules/qc.smk`
- `rules/align.smk`
- `rules/markdup.smk`
- `rules/bamstat.smk`
- `rules/alignment_qc.smk`
- `rules/gatk_gvcf.smk`
- `rules/gatk_joint.smk`
- `rules/gatk_filter.smk`
- `rules/bcftools_call.smk`
- `rules/sv_calling.smk`
- `rules/sv_merge.smk`
- `main.smk` combinations
- Drop-mode checkpoint pattern

## Config Schema

Keep one config schema across the entire skill. Do not let examples drift.

```yaml
ref: /path/to/reference.fa
fq_dir: /path/to/fastq
bam_dir: /path/to/bams
base_dir: /path/to/output
samples: samples.tsv
fq_r1: "{sample}_R1.fastq.gz"
fq_r2: "{sample}_R2.fastq.gz"
bam_suffix: sorted.rmdup
tmpdir: /data/tmp

conda:
  align: ngs
  gatk: gatk4
  sv_manta: sv_manta
  sv_delly: SV_PROD
  sv_merge: sv_consensus
  bcftools: ngs

conda_init: "source /path/to/remote-home/miniconda3/etc/profile.d/conda.sh"

resources:
  qc:
    threads: 4
  align:
    threads: 8
    sort_memory: 2G
  markdup:
    threads: 8
  bamstat:
    threads: 4
  alignment_qc:
    threads: 2
  gatk_hc:
    threads: 4
    memory: 10g
  gatk_joint:
    threads: 4
    memory: 160g
  gatk_filter:
    threads: 4
    memory: 100g
  bcftools_call:
    threads: 4
  sv_manta:
    threads: 8
  sv_delly:
    threads: 1

mapping_qc:
  enabled: true
  metric: picard_pct_pf_reads_aligned
  action: mark
  warn_below: 0.85
  drop_below: null
  use_flagstat: true

gatk_filters:
  snp: "QD < 2.0 || FS > 60.0 || MQ < 40.0 || SOR > 3.0 || MQRankSum < -12.5 || ReadPosRankSum < -8.0"
  indel: "QD < 2.0 || FS > 200.0 || SOR > 10.0 || MQRankSum < -12.5 || ReadPosRankSum < -20.0"

sv:
  callers: [manta, delly]
  delly_mapq: 20
  manta_callregions: null
  octopusv_max_distance: 300
  octopusv_min_support: 2
```

## `rules/common.smk`

```python
from pathlib import Path

configfile: "config.yaml"

SAMPLES = [line.strip() for line in open(config["samples"]) if line.strip()]
REF = config["ref"]
BASE = Path(config["base_dir"])
FQ_DIR = Path(config["fq_dir"])
BAM_DIR = Path(config.get("bam_dir", BASE / "01.BWA/bam"))
CONDA_INIT = config.get("conda_init", "")
BAM_SUFFIX = config.get("bam_suffix", "sorted.rmdup")


def conda_cmd(env_key):
    env_name = config.get("conda", {}).get(env_key, "")
    if not env_name:
        return ""
    return f"{CONDA_INIT} && conda activate {env_name} &&"


def res(rule_key, field, default):
    return config.get("resources", {}).get(rule_key, {}).get(field, default)


def get_fq(sample, read):
    key = "fq_r1" if read == 1 else "fq_r2"
    pattern = config.get(key, "{sample}_R" + str(read) + ".fastq.gz")
    fname = pattern.format(sample=sample)
    for subdir in ["", "cleandata", sample]:
        candidate = FQ_DIR / subdir / fname if subdir else FQ_DIR / fname
        if candidate.exists():
            return str(candidate)
    return str(FQ_DIR / fname)


def bam_path(sample, suffix=None, bam_dir=None):
    bam_root = Path(bam_dir) if bam_dir else BAM_DIR
    bam_suffix = suffix or BAM_SUFFIX
    return str(bam_root / f"{sample}.{bam_suffix}.bam")


def bam_index_path(sample, suffix=None, bam_dir=None):
    return bam_path(sample, suffix=suffix, bam_dir=bam_dir) + ".bai"


def selected_samples(wildcards=None):
    if not config.get("mapping_qc", {}).get("enabled", False):
        return SAMPLES
    if config.get("mapping_qc", {}).get("action", "mark") != "drop":
        return SAMPLES
    ckpt = checkpoints.filter_samples.get()
    with open(ckpt.output.passed) as handle:
        return [line.strip() for line in handle if line.strip()]
```

## `rules/qc.smk`

```python
rule fastp:
    input:
        r1=lambda wc: get_fq(wc.sample, 1),
        r2=lambda wc: get_fq(wc.sample, 2),
    output:
        r1=BASE / "00.QC/{sample}_1.clean.fq.gz",
        r2=BASE / "00.QC/{sample}_2.clean.fq.gz",
        json=BASE / "00.QC/{sample}_fastp.json",
        html=BASE / "00.QC/{sample}_fastp.html",
    threads: res("qc", "threads", 4)
    log: "logs/qc/{sample}.log"
    benchmark: "benchmarks/qc/{sample}.bm"
    params:
        conda=conda_cmd("align"),
    shell:
        r"""
        {params.conda} fastp \
            -i {input.r1} -I {input.r2} \
            -o {output.r1} -O {output.r2} \
            --thread {threads} \
            --json {output.json} --html {output.html} \
            > {log} 2>&1
        """
```

## `rules/align.smk`

```python
rule bwa_mem2:
    input:
        r1=BASE / "00.QC/{sample}_1.clean.fq.gz",
        r2=BASE / "00.QC/{sample}_2.clean.fq.gz",
    output:
        bam=BASE / "01.BWA/bam/{sample}.sorted.bam",
        bai=BASE / "01.BWA/bam/{sample}.sorted.bam.bai",
    threads: res("align", "threads", 8)
    log: "logs/align/{sample}.log"
    benchmark: "benchmarks/align/{sample}.bm"
    params:
        conda=conda_cmd("align"),
        rg="@RG\\tID:{sample}\\tPL:illumina\\tSM:{sample}",
        ref=REF,
        sort_mem=res("align", "sort_memory", "2G"),
    shell:
        r"""
        {params.conda} bwa-mem2 mem -t {threads} -R '{params.rg}' \
            {params.ref} {input.r1} {input.r2} 2>> {log} | \
            samtools sort -@ {threads} -m {params.sort_mem} -O BAM -o {output.bam} 2>> {log}
        samtools index -@ {threads} {output.bam} 2>> {log}
        samtools quickcheck {output.bam} || {{ echo "BAM quickcheck failed" >> {log}; exit 1; }}
        """
```

## `rules/markdup.smk`

```python
rule sambamba_markdup:
    input:
        bam=BASE / "01.BWA/bam/{sample}.sorted.bam",
        bai=BASE / "01.BWA/bam/{sample}.sorted.bam.bai",
    output:
        bam=BASE / "01.BWA/bam/{sample}.sorted.rmdup.bam",
        bai=BASE / "01.BWA/bam/{sample}.sorted.rmdup.bam.bai",
    threads: res("markdup", "threads", 8)
    log: "logs/markdup/{sample}.log"
    benchmark: "benchmarks/markdup/{sample}.bm"
    params:
        conda=conda_cmd("align"),
        tmpdir=config.get("tmpdir", "/tmp"),
    shell:
        r"""
        {params.conda} sambamba markdup -r -t {threads} -p \
            --tmpdir {params.tmpdir} {input.bam} {output.bam} > {log} 2>&1
        samtools index -@ {threads} {output.bam} 2>> {log}
        samtools quickcheck {output.bam} || {{ echo "rmdup BAM quickcheck failed" >> {log}; exit 1; }}
        """
```

## `rules/bamstat.smk`

```python
rule bam_stat:
    input:
        bam=lambda wc: bam_path(wc.sample),
    output:
        stat=BASE / "01.BWA/stat/{sample}.bwa.stat",
    threads: res("bamstat", "threads", 4)
    log: "logs/bamstat/{sample}.log"
    benchmark: "benchmarks/bamstat/{sample}.bm"
    params:
        conda=conda_cmd("align"),
    shell:
        r"""
        {params.conda} samtools stats -@ {threads} {input.bam} > {output.stat} 2> {log}
        """
```

## `rules/alignment_qc.smk`

Use Picard/GATK as the default mapping-rate source. Only enable sample dropping when `mapping_qc.action: drop` is explicitly configured.

```python
rule alignment_qc:
    input:
        bam=lambda wc: bam_path(wc.sample),
        bai=lambda wc: bam_index_path(wc.sample),
    output:
        picard=BASE / "01.BWA/qc/{sample}.alignment_metrics.txt",
        flagstat=BASE / "01.BWA/qc/{sample}.flagstat.json",
        summary=BASE / "01.BWA/qc/{sample}.mapping_qc.tsv",
        summary_json=BASE / "01.BWA/qc/{sample}.mapping_qc.json",
    threads: res("alignment_qc", "threads", 2)
    log: "logs/alignment_qc/{sample}.log"
    benchmark: "benchmarks/alignment_qc/{sample}.bm"
    params:
        gatk_conda=conda_cmd("gatk"),
        align_conda=conda_cmd("align"),
        ref=REF,
        warn=config.get("mapping_qc", {}).get("warn_below", 0.85),
        metric=config.get("mapping_qc", {}).get("metric", "picard_pct_pf_reads_aligned"),
        drop_arg=(lambda: (
            f"--drop-below {config.get('mapping_qc', {}).get('drop_below')}"
            if config.get("mapping_qc", {}).get("drop_below") is not None else ""
        ))(),
        use_flagstat=config.get("mapping_qc", {}).get("use_flagstat", True),
        script="scripts/evaluate_mapping_qc.py",
    shell:
        r"""
        {params.gatk_conda} gatk CollectAlignmentSummaryMetrics \
            -R {params.ref} -I {input.bam} -O {output.picard} > {log} 2>&1

        if [ "{params.use_flagstat}" = "True" ]; then
            {params.align_conda} samtools flagstat -O json {input.bam} > {output.flagstat} 2>> {log}
            FLAGSTAT_ARG="--flagstat {output.flagstat}"
        else
            printf '{{}}' > {output.flagstat}
            FLAGSTAT_ARG=""
        fi

        python {params.script} evaluate \
            --sample {wildcards.sample} \
            --picard {output.picard} \
            $FLAGSTAT_ARG \
            --metric {params.metric} \
            --warn-below {params.warn} \
            {params.drop_arg} \
            --output-tsv {output.summary} \
            --output-json {output.summary_json} >> {log} 2>&1
        """


checkpoint filter_samples:
    input:
        expand(str(BASE / "01.BWA/qc/{sample}.mapping_qc.tsv"), sample=SAMPLES)
    output:
        passed=BASE / "01.BWA/qc/passing_samples.tsv",
        excluded=BASE / "01.BWA/qc/excluded_samples.tsv",
        summary=BASE / "01.BWA/qc/mapping_qc.summary.tsv",
    params:
        action=config.get("mapping_qc", {}).get("action", "mark"),
        script="scripts/evaluate_mapping_qc.py",
    shell:
        r"""
        python {params.script} aggregate \
            --inputs {input} \
            --action {params.action} \
            --output-passing {output.passed} \
            --output-excluded {output.excluded} \
            --output-summary {output.summary}
        """
```

## `rules/gatk_gvcf.smk`

```python
rule haplotype_caller:
    input:
        bam=lambda wc: bam_path(wc.sample),
        bai=lambda wc: bam_index_path(wc.sample),
    output:
        gvcf=BASE / "02.VCF/gvcf/{sample}.g.vcf.gz",
        tbi=BASE / "02.VCF/gvcf/{sample}.g.vcf.gz.tbi",
    threads: res("gatk_hc", "threads", 4)
    log: "logs/gatk_hc/{sample}.log"
    benchmark: "benchmarks/gatk_hc/{sample}.bm"
    params:
        conda=conda_cmd("gatk"),
        ref=REF,
        mem=res("gatk_hc", "memory", "10g"),
        tmpdir=config.get("tmpdir", "/tmp"),
    shell:
        r"""
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            HaplotypeCaller -R {params.ref} -I {input.bam} -ERC GVCF -O {output.gvcf} > {log} 2>&1
        """
```

## `rules/gatk_joint.smk`

```python
rule combine_gvcfs:
    input:
        lambda wc: expand(str(BASE / "02.VCF/gvcf/{sample}.g.vcf.gz"), sample=selected_samples(wc))
    output:
        merged=BASE / "02.VCF/gvcf/merge.g.vcf.gz",
    threads: res("gatk_joint", "threads", 4)
    log: "logs/gatk_joint/combine.log"
    benchmark: "benchmarks/gatk_joint/combine.bm"
    params:
        conda=conda_cmd("gatk"),
        ref=REF,
        mem=res("gatk_joint", "memory", "160g"),
        tmpdir=config.get("tmpdir", "/tmp"),
        gvcf_args=lambda wc, input: " ".join(f"-V {f}" for f in input),
    shell:
        r"""
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            CombineGVCFs -R {params.ref} {params.gvcf_args} -O {output.merged} > {log} 2>&1
        """


rule genotype_gvcfs:
    input:
        merged=BASE / "02.VCF/gvcf/merge.g.vcf.gz",
    output:
        vcf=BASE / "02.VCF/raw/merge.raw_variant.vcf.gz",
    threads: res("gatk_joint", "threads", 4)
    log: "logs/gatk_joint/genotype.log"
    benchmark: "benchmarks/gatk_joint/genotype.bm"
    params:
        conda=conda_cmd("gatk"),
        ref=REF,
        mem=res("gatk_joint", "memory", "160g"),
        tmpdir=config.get("tmpdir", "/tmp"),
    shell:
        r"""
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            GenotypeGVCFs -R {params.ref} -V {input.merged} -O {output.vcf} > {log} 2>&1
        """
```

## `rules/gatk_filter.smk`

```python
rule select_snp_indel:
    input:
        vcf=BASE / "02.VCF/raw/merge.raw_variant.vcf.gz",
    output:
        snp=BASE / "02.VCF/raw/merge.SNP.vcf.gz",
        indel=BASE / "02.VCF/raw/merge.INDEL.vcf.gz",
    log: "logs/gatk_filter/select.log"
    params:
        conda=conda_cmd("gatk"),
        ref=REF,
        mem=res("gatk_filter", "memory", "100g"),
        tmpdir=config.get("tmpdir", "/tmp"),
    shell:
        r"""
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            SelectVariants -R {params.ref} -V {input.vcf} --select-type-to-include SNP -O {output.snp} > {log} 2>&1
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            SelectVariants -R {params.ref} -V {input.vcf} --select-type-to-include INDEL -O {output.indel} >> {log} 2>&1
        """


rule hard_filter:
    input:
        snp=BASE / "02.VCF/raw/merge.SNP.vcf.gz",
        indel=BASE / "02.VCF/raw/merge.INDEL.vcf.gz",
    output:
        snp=BASE / "02.VCF/filter/merge.filter.SNP.vcf.gz",
        indel=BASE / "02.VCF/filter/merge.filter.INDEL.vcf.gz",
    log: "logs/gatk_filter/filter.log"
    params:
        conda=conda_cmd("gatk"),
        ref=REF,
        mem=res("gatk_filter", "memory", "100g"),
        tmpdir=config.get("tmpdir", "/tmp"),
        snp_expr=lambda wc: '"' + config.get("gatk_filters", {}).get("snp", "QD < 2.0") + '"',
        indel_expr=lambda wc: '"' + config.get("gatk_filters", {}).get("indel", "QD < 2.0") + '"',
    shell:
        r"""
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            VariantFiltration -R {params.ref} -V {input.snp} \
            --filter-expression {params.snp_expr} --filter-name SNP_FILTER \
            -O {output.snp} > {log} 2>&1
        {params.conda} gatk --java-options "-Djava.io.tmpdir={params.tmpdir} -Xmx{params.mem}" \
            VariantFiltration -R {params.ref} -V {input.indel} \
            --filter-expression {params.indel_expr} --filter-name INDEL_FILTER \
            -O {output.indel} >> {log} 2>&1
        """
```

## `rules/bcftools_call.smk`

Include this module only when the user explicitly wants `bcftools`.

```python
rule bcftools_call:
    input:
        bam=lambda wc: bam_path(wc.sample),
        bai=lambda wc: bam_index_path(wc.sample),
    output:
        vcf=BASE / "02.VCF/bcftools/{sample}.vcf.gz",
        tbi=BASE / "02.VCF/bcftools/{sample}.vcf.gz.tbi",
    threads: res("bcftools_call", "threads", 4)
    log: "logs/bcftools/{sample}.log"
    benchmark: "benchmarks/bcftools/{sample}.bm"
    params:
        conda=conda_cmd("bcftools"),
        ref=REF,
    shell:
        r"""
        set -o pipefail
        {params.conda} bcftools mpileup -Ou -f {params.ref} {input.bam} 2>> {log} | \
            bcftools call -mv -Oz -o {output.vcf} >> {log} 2>&1
        {params.conda} bcftools index {output.vcf} >> {log} 2>&1
        """
```

## `rules/sv_calling.smk`

```python
SV_CALLERS = config.get("sv", {}).get("callers", ["manta", "delly"])

if "manta" in SV_CALLERS:
    rule manta:
        input:
            bam=lambda wc: bam_path(wc.sample),
        output:
            BASE / "03.SV/manta/{sample}/results/variants/diploidSV.vcf.gz"
        threads: res("sv_manta", "threads", 8)
        log: "logs/sv_manta/{sample}.log"
        benchmark: "benchmarks/sv_manta/{sample}.bm"
        params:
            conda=conda_cmd("sv_manta"),
            ref=REF,
            rundir=str(BASE / "03.SV/manta/{sample}"),
            callregions=config.get("sv", {}).get("manta_callregions", None),
        shell:
            r"""
            {params.conda} configManta.py --bam {input.bam} --referenceFasta {params.ref} \
                --runDir {params.rundir} > {log} 2>&1
            {params.rundir}/runWorkflow.py -j {threads} >> {log} 2>&1
            """

if "delly" in SV_CALLERS:
    rule delly:
        input:
            bam=lambda wc: bam_path(wc.sample),
        output:
            BASE / "03.SV/delly/{sample}.sv.vcf.gz"
        threads: res("sv_delly", "threads", 1)
        log: "logs/sv_delly/{sample}.log"
        benchmark: "benchmarks/sv_delly/{sample}.bm"
        params:
            conda=conda_cmd("sv_delly"),
            ref=REF,
            mapq=config.get("sv", {}).get("delly_mapq", 20),
            bcf=str(BASE / "03.SV/delly/{sample}.sv.bcf"),
        shell:
            r"""
            {params.conda} delly call -g {params.ref} -q {params.mapq} -o {params.bcf} {input.bam} > {log} 2>&1
            bcftools view {params.bcf} -Oz -o {output} >> {log} 2>&1
            tabix -p vcf {output} >> {log} 2>&1
            """
```

## `rules/sv_merge.smk`

```python
def get_sv_inputs(sample):
    paths = []
    callers = config.get("sv", {}).get("callers", [])
    if "manta" in callers:
        paths.append(str(BASE / f"03.SV/manta/{sample}/results/variants/diploidSV.vcf.gz"))
    if "delly" in callers:
        paths.append(str(BASE / f"03.SV/delly/{sample}.sv.vcf.gz"))
    return paths


rule octopusv_merge:
    input:
        lambda wc: get_sv_inputs(wc.sample)
    output:
        BASE / "03.SV/octopusv/{sample}/consensus.svcf"
    log: "logs/sv_merge/{sample}.log"
    benchmark: "benchmarks/sv_merge/{sample}.bm"
    params:
        conda=conda_cmd("sv_merge"),
        max_dist=config.get("sv", {}).get("octopusv_max_distance", 300),
        min_supp=config.get("sv", {}).get("octopusv_min_support", 2),
        workdir=str(BASE / "03.SV/octopusv/{sample}"),
    shell:
        r"""
        {params.conda} mkdir -p {params.workdir} && \
        octopusv merge -i {input} -o {output} \
            --max-distance {params.max_dist} --min-support {params.min_supp} > {log} 2>&1
        """
```

## `main.smk` Combinations

### QC-only

```python
include: "rules/common.smk"
include: "rules/qc.smk"

rule all:
    input:
        expand(str(BASE / "00.QC/{sample}_1.clean.fq.gz"), sample=SAMPLES),
        expand(str(BASE / "00.QC/{sample}_2.clean.fq.gz"), sample=SAMPLES)
```

### BAM-only

```python
include: "rules/common.smk"
include: "rules/qc.smk"
include: "rules/align.smk"
include: "rules/markdup.smk"
include: "rules/alignment_qc.smk"

rule all:
    input:
        lambda wc: expand(str(BASE / "01.BWA/qc/{sample}.mapping_qc.tsv"), sample=SAMPLES) + [
            bam_path(sample) for sample in selected_samples(wc)
        ]
```

### GATK default

```python
include: "rules/common.smk"
include: "rules/qc.smk"
include: "rules/align.smk"
include: "rules/markdup.smk"
include: "rules/alignment_qc.smk"
include: "rules/gatk_gvcf.smk"
include: "rules/gatk_joint.smk"
include: "rules/gatk_filter.smk"

rule all:
    input:
        lambda wc: [
            BASE / "02.VCF/filter/merge.filter.SNP.vcf.gz",
            BASE / "02.VCF/filter/merge.filter.INDEL.vcf.gz",
        ]
```

### bcftools explicit-only

```python
include: "rules/common.smk"
include: "rules/qc.smk"
include: "rules/align.smk"
include: "rules/markdup.smk"
include: "rules/alignment_qc.smk"
include: "rules/bcftools_call.smk"

rule all:
    input:
        lambda wc: expand(str(BASE / "02.VCF/bcftools/{sample}.vcf.gz"), sample=selected_samples(wc))
```

### SV-only

```python
include: "rules/common.smk"
include: "rules/alignment_qc.smk"
include: "rules/sv_calling.smk"
include: "rules/sv_merge.smk"

rule all:
    input:
        lambda wc: expand(str(BASE / "03.SV/octopusv/{sample}/consensus.svcf"), sample=selected_samples(wc))
```

## Drop-mode Checkpoint Pattern

`checkpoint filter_samples` now lives inside `rules/alignment_qc.smk`, so any workflow that includes `alignment_qc.smk` can make `action: drop` executable. The key rule is unchanged:

- downstream cohort rules and sample-expanded `rule all` blocks should call `selected_samples(wc)` from `rules/common.smk`
- if `mapping_qc.action` remains `mark`, `selected_samples(wc)` falls back to `SAMPLES`
- if `mapping_qc.action` is `drop`, `selected_samples(wc)` reads `passing_samples.tsv` emitted by the checkpoint above
