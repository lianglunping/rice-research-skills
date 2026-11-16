# Skill Catalog / 技能目录

This catalog provides bilingual descriptions for the curated skills in this repository.

本目录为仓库中的技能提供中英文说明，便于快速判断每个 skill 的用途和安装路径。

## Bio / 生信与水稻研究

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `bio-bsa-qtlseq` | `skills/bio/bio-bsa-qtlseq` | 用于水稻等作物的 BSA/QTL-seq 分析流程，包括表型 QC、混池策略、QTLseqr 分析、门控检查、结果解释和交付前审计。 | BSA/QTL-seq analysis of contrasting bulks with phenotype design, pooled allele evidence, window summaries and candidate-region validation. |
| `bio-genome-annotation-functional-annotation` | `skills/bio/bio-genome-annotation-functional-annotation` | 用 eggNOG-mapper、InterProScan 等工具为预测基因或蛋白添加 GO、KEGG、Pfam 和 EC 功能注释。 | Genome annotation functional annotation: Assign GO terms, KEGG orthologs, Pfam domains, and EC numbers to predicted proteins using eggNOG-mapper and InterProScan. |
| `bio-haplotype-rice-candidate-gene` | `skills/bio/bio-haplotype-rice-candidate-gene` | 面向水稻候选基因单倍型分析，支持配置、群体材料、变异筛选、结果解释和方法描述整理。 | Rice candidate-gene haplotype analysis with reference/gene mapping, population structure, missingness and phenotype-association limits. |
| `bio-sanger-tracy-validation` | `skills/bio/bio-sanger-tracy-validation` | 用于 Sanger 一代测序验证，处理 AB1 文件、tracy decompose、变异验证报告和批量更新。 | Sanger trace validation with Tracy and explicit reference, strand, primer, allele and chromatogram evidence. |
| `bio-consensus-sequences` | `skills/bio/bio-variant-calling-consensus-sequences` | 根据 VCF 变异和参考基因组生成样本特异的 consensus FASTA 序列，用于单倍型或局部序列重建。 | Consensus sequences: Generate consensus FASTA sequences by applying VCF variants to a reference using bcftools consensus. |
| `bio-variant-calling-filtering-best-practices` | `skills/bio/bio-variant-calling-filtering-best-practices` | 指导 SNP/InDel 过滤，包括 GATK VQSR、硬过滤、bcftools 表达式和质量指标解释。 | Variant calling filtering best practices: Comprehensive variant filtering including GATK VQSR, hard filters, bcftools expressions, and quality metric interpretation for SNPs and indels. |
| `bio-gatk-variant-calling` | `skills/bio/bio-variant-calling-gatk-variant-calling` | 使用 GATK HaplotypeCaller 进行胚系 SNP/InDel 检测，覆盖 GVCF、联合分型和质量控制。 | Gatk variant calling: Variant calling with GATK HaplotypeCaller following best practices. |
| `bio-variant-calling-joint-calling` | `skills/bio/bio-variant-calling-joint-calling` | 多样本联合分型流程，适合群体遗传、育种群体和批量重测序项目。 | Variant calling joint calling: Joint genotype calling across multiple samples using GATK CombineGVCFs and GenotypeGVCFs. |
| `bio-variant-calling-structural-variant-calling` | `skills/bio/bio-variant-calling-structural-variant-calling` | 使用 Manta、Delly、LUMPY 等短读长 SV 工具检测缺失、插入、倒位、重复和易位。 | Structural-variant calling and integration with caller-specific evidence, sample/reference contracts and breakpoint representation checks. |
| `bio-variant-annotation` | `skills/bio/bio-variant-calling-variant-annotation` | 为变异添加功能注释和数据库注释，支持 bcftools csq/annotate、VEP、SnpEff、ANNOVAR 等工具口径。 | Variant annotation: Comprehensive variant annotation using bcftools annotate/csq, VEP, SnpEff, and ANNOVAR. |
| `bio-variant-normalization` | `skills/bio/bio-variant-calling-variant-normalization` | 使用 bcftools norm 等工具标准化 InDel 表示、拆分多等位点，便于跨 caller 或跨样本比较。 | Variant normalization: Normalize indel representation and split multiallelic variants using bcftools norm. |
| `bio-vcf-basics` | `skills/bio/bio-variant-calling-vcf-basics` | 解释和查询 VCF/BCF 文件，适合快速检查位点、样本字段、FORMAT/INFO 信息和基本结构。 | Vcf basics: View, query, and understand VCF/BCF variant files using bcftools and cyvcf2. |
| `bio-vcf-manipulation` | `skills/bio/bio-variant-calling-vcf-manipulation` | 合并、排序、拼接、交集和子集化 VCF 文件，适合重构或比较变异集合。 | Vcf manipulation: Merge, concatenate, sort, intersect, and subset VCF files using bcftools. |
| `bio-vcf-statistics` | `skills/bio/bio-variant-calling-vcf-statistics` | 生成 VCF 统计、样本一致性和质量概览，如 bcftools stats、gtcheck 等。 | Vcf statistics: Generate variant statistics, sample concordance, and quality metrics using bcftools stats and gtcheck. |
| `bioinformatics-context` | `skills/bio/bioinformatics-context` | 提供水稻分子育种、生信分析、变异检测和诱变育种任务的领域背景。 | 水稻分子育种与生物信息学领域背景，用于需要育种目标、材料世代、基因组变异或验证策略判断的任务。 |
| `snakemake-variant-pipeline` | `skills/bio/snakemake-variant-pipeline` | 搭建模块化 Snakemake 重测序流程，覆盖 FASTQ QC、BAM、GATK SNP/InDel、Manta/Delly SV 和 bcftools 分支。 | Modular Snakemake resequencing workflows for read QC, alignment, GATK SNP/InDel calling and Manta/Delly SV analysis with explicit data and reference contracts. |
| `variant-primer-design` | `skills/bio/variant-primer-design` | 从 SNP/InDel 表格设计 PCR 验证引物，支持参考序列获取、特异性筛查和失败引物重设计。 | SNP/InDel validation primer design against a specified reference, with variant normalization, flanking sequence checks and BLAST specificity assessment. |

## Visualization / 统计与可视化

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `bio-data-visualization-circos-plots` | `skills/visualization/bio-data-visualization-circos-plots` | 创建 Circos/环形基因组图，展示染色体、基因、变异、CNV 或互作弧线等多轨道信息。 | Data visualization circos plots: Create circular genome visualizations with Circos and pyCircos. |
| `bio-data-visualization-color-palettes` | `skills/visualization/bio-data-visualization-color-palettes` | 为科研图选择色盲友好、适合论文的配色方案，如 viridis、RColorBrewer、ggsci。 | Data visualization color palettes: Select and apply colorblind-friendly palettes for scientific figures using viridis, RColorBrewer, and custom color schemes. |
| `bio-data-visualization-genome-tracks` | `skills/visualization/bio-data-visualization-genome-tracks` | 绘制基因组浏览器式多轨道图，展示覆盖度、基因结构、峰、变异或局部区域证据。 | Data visualization genome tracks: Create genome browser-style visualizations showing multiple data tracks (coverage, peaks, genes) using pyGenomeTracks, Gviz, and IGV. |
| `bio-data-visualization-ggplot2-fundamentals` | `skills/visualization/bio-data-visualization-ggplot2-fundamentals` | 用 ggplot2 绘制常见统计图并应用统一出版样式。 | Build statistical plots in ggplot2 and apply the shared publication style. |
| `bio-data-visualization-heatmaps-clustering` | `skills/visualization/bio-data-visualization-heatmaps-clustering` | 绘制带行列注释和聚类的热图，适合表达谱、组学矩阵和共表达模式展示。 | Data visualization heatmaps clustering: Create clustered heatmaps with row/column annotations using ComplexHeatmap, pheatmap, and seaborn for gene expression and omics data visualization. |
| `bio-data-visualization-multipanel-figures` | `skills/visualization/bio-data-visualization-multipanel-figures` | 按最终尺寸组合多面板图，统一标签与图例并保留各面板可编辑源。 | Compose final-size multi-panel figures with shared legends, consistent tags and independently editable panel sources. |
| `bio-data-visualization-upset-plots` | `skills/visualization/bio-data-visualization-upset-plots` | 用 UpSet 图展示多个集合交集，适合基因集、峰集、样本组或候选列表比较。 | Data visualization upset plots: Create UpSet plots to visualize set intersections as an alternative to Venn diagrams using UpSetR or upsetplot. |
| `bio-data-visualization-volcano-customization` | `skills/visualization/bio-data-visualization-volcano-customization` | 定制火山图阈值、基因标签和高亮规则，适合差异表达或关联分析结果。 | Data visualization volcano customization: Create publication-ready volcano plots with custom thresholds, gene labels, and highlighting using ggplot2, EnhancedVolcano, or matplotlib. |
| `bio-publication-figure-director` | `skills/visualization/bio-publication-figure-director` | 根据科研问题与实际数据设计、绘制和审计投稿图，统一 R/Python 样式、版面尺寸及成图验收。 | Plan, build and audit publication figures from scientific evidence through final-size rendering and artifact checks, with shared R and Python defaults. |
| `bio-reporting-figure-export` | `skills/visualization/bio-reporting-figure-export` | 按最终尺寸导出并检查可编辑 PDF、栅格有效 DPI 和字体。 | Export and inspect final-size editable PDF, effective raster DPI and typography. |
| `results-analysis` | `skills/visualization/results-analysis` | 围绕生物学问题解释结果，按证据、效应和决策选择统计方法并保留结论边界。 | Research result interpretation for biology, genomics or ML evaluation. Choose methods from the question, statistical unit and evidence; distinguish exploration from confirmatory inference. |
| `results-report` | `skills/visualization/results-report` | 将已有分析结果整理成结构化实验报告或结果复盘，强调证据边界和决策价值。 | Concise research result reports and experiment summaries for decisions or supervisor review. Use verified artifacts and question-appropriate evidence; expand only when the deliverable requires it. |

## Writing / 论文、综述与学位论文

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `academic-paper-reviewer` | `skills/writing/academic-paper-reviewer` | 模拟多视角同行评审，包括主编、领域审稿人、方法审稿人和反方审稿视角。 | Academic peer review and re-review of manuscripts: assess evidence, methods, claims and revision priorities. Report distinct perspectives without claiming independent reviewers unless actually used. |
| `academic-paper` | `skills/writing/academic-paper` | 组织学术论文写作流程，支持计划、提纲、初稿、修订、摘要、文献综述和格式转换等模式。 | Academic manuscript drafting, outlines, revision, abstracts, citation checks and format preparation. Match the requested paper type and preserve claim-to-source traceability. |
| `academic-pipeline` | `skills/writing/academic-pipeline` | 协调研究、写作、完整性检查、同行评审模拟、修订和最终核查的端到端论文流程。 | Research-to-manuscript workflow for an explicitly requested end-to-end project. Coordinate research, drafting, integrity checks, review and revision using existing authorization. |
| `bio-literature-synthesis-loop` | `skills/writing/bio-literature-synthesis-loop` | 从 Zotero/Obsidian 等阅读系统做周期性文献综合、复习队列、证据矩阵和研究种子梳理。 | Literature synthesis loop: Periodic literature synthesis and retention workflow for biology, genomics, plant breeding, rice, bioinformatics, and mutagenesis reading systems. |
| `bio-original-paper-reading` | `skills/writing/bio-original-paper-reading` | 面向原创研究论文的深度精读，强调主图重构、图版审计、证据强度和育种/生信启发。 | Original paper reading: Deep-reading workflow for original empirical biology papers, especially molecular biology, genomics, omics, quantitative genetics, plant breeding, rice, and mutagenesis studies. |
| `bio-review-paper-reading` | `skills/writing/bio-review-paper-reading` | 面向综述、观点和路线图文章，重构领域框架、共识争议、开放问题和研究方案种子。 | Review paper reading: Deep-reading workflow for review articles, perspectives, opinions, primers, roadmaps, and field-synthesis papers in molecular biology, genomics, omics, quantitative genetics, plant breeding, rice, and bioinformatics. |
| `bio-thesis-review-lanes` | `skills/writing/bio-thesis-review-lanes` | 以外审、导师、答辩委员等视角审阅生物/生信学位论文或 manuscript 内容。 | Thesis review organized by evidence, biological logic, structure and presentation, with actionable revisions and claim-strength limits. |
| `bio-thesis-workflow` | `skills/writing/bio-thesis-workflow` | 支持生物/生信论文和学位论文的写作、重组、润色、Word/Markdown 转换和结果转正文。 | Biological thesis preparation from project evidence through chapter structure, figures, writing and final artifact verification. |
| `citation-verification` | `skills/writing/citation-verification` | 提供引用核验原则，帮助检查虚假引用、格式错误、来源不匹配和引用准确性。 | Citation verification for scientific writing: check bibliographic identity, source support, quotations and reference integrity. |
| `paper-search` | `skills/writing/paper-search` | 指导文献检索、开放论文下载、全文阅读入口和可复现检索记录。 | Academic literature retrieval and lawful full-text access: search scholarly databases, verify paper identity and retrieve available open-access sources. |
| `review-response` | `skills/writing/review-response` | 分析审稿意见并撰写专业回复，组织 rebuttal 结构、语气和修订证据。 | Reviewer rebuttal and revision planning: classify comments, map changes to evidence and draft precise, professional responses. |
| `rice-thesis-writing` | `skills/writing/rice-thesis-writing` | 面向水稻遗传育种、诱变育种和生信方向的中文硕博论文写作、章节组织和格式处理。 | Chinese rice-science thesis drafting, reorganization, revision and formatting. Preserve biological context, evidence levels, citation support and institutional requirements. |

## Workflow / 复现、审计与任务管理

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `handover` | `skills/workflow/handover` | 保存任务进展、关键决策、路径、风险和恢复提示，支持长对话或多任务交接。 | Task handoff and resumable progress records: capture authoritative paths, decisions, completed checks, current state and remaining work. |
| `job-monitor-loop` | `skills/workflow/job-monitor-loop` | 监控长时间运行任务，按退避策略检查日志、状态、输出和异常，适合生信流水线。 | Automatic supervision of authorized long-running jobs: background submission, progress-aware backoff, bounded repair and artifact acceptance. Preserve task and host boundaries. |
| `project-audit` | `skills/workflow/project-audit` | 审计项目的代码、结果、文档、方法、结论强度、复现性和交付完整性。 | This skill should be used when the user asks to audit a project, review a bioinformatics analysis deliverable, check result traceability, validate reproducibility, or perform a structured project audit across code, results, documentation, methods, and conclusion strength. |
| `provenance-doc` | `skills/workflow/provenance-doc` | 生成和维护分析溯源文档，记录命令、参数、输入输出、版本、证据和封版状态。 | Analysis provenance and release documentation: record inputs, paths, versions, parameters, commands, evidence and frozen output boundaries. |
| `staged-agent-run-protocol` | `skills/workflow/staged-agent-run-protocol` | 将复杂科研/生信任务拆成阶段化 agent run，记录状态、门控、产物、环境和远程作业。 | Approved research-run execution and recovery with auditable state, provenance, QC gates and frozen outputs. Use for an authorized run, not for planning or ordinary questions. |
| `verification-loop` | `skills/workflow/verification-loop` | 在改动后运行构建、lint、类型检查、测试、安全扫描和 diff 审查等验证步骤。 | Change verification using the relevant build, type, lint, test and artifact checks. Choose gates from actual project requirements and changed behavior. |

## Engineering / 工程协作

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `bug-detective` | `skills/engineering/bug-detective` | 系统化排查错误、异常、失败命令和代码缺陷，整理根因、复现和修复路径。 | Bug investigation: reproduce errors, trace causes through code and logs, and develop a bounded fix with relevant verification. |
| `code-review-excellence` | `skills/engineering/code-review-excellence` | 用于代码审查、PR 审查、安全检查和团队 review 标准化。 | Code and pull-request review: find actionable correctness, maintainability and regression issues with precise evidence and proportionate feedback. |
| `git-workflow` | `skills/engineering/git-workflow` | 提供 Git 分支、提交、合并、冲突处理和 Conventional Commits 工作流规范。 | Git commits, branches, merge conflicts and repository history conventions. Apply only the Git operations included in the task scope. |

## Snapshot notes / 快照说明

Updated 2026-11-05: 48 skills refreshed; `project-audit` retains its existing
public snapshot because it was absent from the selected source. See
[dependencies and validation scope](DEPENDENCIES.md).
