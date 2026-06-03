# Skill Catalog / 技能目录

This catalog provides bilingual descriptions for the curated skills in this repository.

本目录为仓库中的技能提供中英文说明，便于快速判断每个 skill 的用途和安装路径。

## Bio / 生信与水稻研究

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `bio-bsa-qtlseq` | `skills/bio/bio-bsa-qtlseq` | 用于水稻等作物的 BSA/QTL-seq 分析流程，包括表型 QC、混池策略、QTLseqr 分析、门控检查、结果解释和交付前审计。 | BSA/QTL-seq workflow for crops such as rice, covering phenotype QC, bulk design, QTLseqr analysis, gate checks, interpretation, and pre-delivery audit. |
| `bio-genome-annotation-functional-annotation` | `skills/bio/bio-genome-annotation-functional-annotation` | 用 eggNOG-mapper、InterProScan 等工具为预测基因或蛋白添加 GO、KEGG、Pfam 和 EC 功能注释。 | Adds GO, KEGG, Pfam, EC, and related functional annotations to predicted genes or proteins using tools such as eggNOG-mapper and InterProScan. |
| `bio-haplotype-rice-candidate-gene` | `skills/bio/bio-haplotype-rice-candidate-gene` | 面向水稻候选基因单倍型分析，支持配置、群体材料、变异筛选、结果解释和方法描述整理。 | Supports haplotype analysis for rice candidate genes, including configuration, population materials, variant filtering, interpretation, and method write-up. |
| `bio-sanger-tracy-validation` | `skills/bio/bio-sanger-tracy-validation` | 用于 Sanger 一代测序验证，处理 AB1 文件、tracy decompose、变异验证报告和批量更新。 | Handles Sanger validation with AB1 files, tracy decompose, variant confirmation reports, and batch updates. |
| `bio-consensus-sequences` | `skills/bio/bio-variant-calling-consensus-sequences` | 根据 VCF 变异和参考基因组生成样本特异的 consensus FASTA 序列，用于单倍型或局部序列重建。 | Generates sample-specific consensus FASTA sequences from VCF variants and a reference genome for haplotype or local sequence reconstruction. |
| `bio-variant-calling-filtering-best-practices` | `skills/bio/bio-variant-calling-filtering-best-practices` | 指导 SNP/InDel 过滤，包括 GATK VQSR、硬过滤、bcftools 表达式和质量指标解释。 | Guides SNP/InDel filtering with GATK VQSR, hard filters, bcftools expressions, and quality metric interpretation. |
| `bio-gatk-variant-calling` | `skills/bio/bio-variant-calling-gatk-variant-calling` | 使用 GATK HaplotypeCaller 进行胚系 SNP/InDel 检测，覆盖 GVCF、联合分型和质量控制。 | Germline SNP/InDel calling with GATK HaplotypeCaller, covering GVCF workflows, joint genotyping, and quality control. |
| `bio-variant-calling-joint-calling` | `skills/bio/bio-variant-calling-joint-calling` | 多样本联合分型流程，适合群体遗传、育种群体和批量重测序项目。 | Joint genotyping workflow for multi-sample cohorts, population genetics, breeding populations, and resequencing projects. |
| `bio-variant-calling-structural-variant-calling` | `skills/bio/bio-variant-calling-structural-variant-calling` | 使用 Manta、Delly、LUMPY 等短读长 SV 工具检测缺失、插入、倒位、重复和易位。 | Detects short-read structural variants such as deletions, insertions, inversions, duplications, and translocations with tools such as Manta, Delly, and LUMPY. |
| `bio-variant-annotation` | `skills/bio/bio-variant-calling-variant-annotation` | 为变异添加功能注释和数据库注释，支持 bcftools csq/annotate、VEP、SnpEff、ANNOVAR 等工具口径。 | Adds functional and database annotations to variants using workflows based on bcftools csq/annotate, VEP, SnpEff, ANNOVAR, and related tools. |
| `bio-variant-normalization` | `skills/bio/bio-variant-calling-variant-normalization` | 使用 bcftools norm 等工具标准化 InDel 表示、拆分多等位点，便于跨 caller 或跨样本比较。 | Normalizes InDel representation and splits multiallelic sites, often with bcftools norm, for cross-caller or cross-sample comparison. |
| `bio-vcf-basics` | `skills/bio/bio-variant-calling-vcf-basics` | 解释和查询 VCF/BCF 文件，适合快速检查位点、样本字段、FORMAT/INFO 信息和基本结构。 | Explains and queries VCF/BCF files, useful for inspecting sites, sample fields, FORMAT/INFO data, and file structure. |
| `bio-vcf-manipulation` | `skills/bio/bio-variant-calling-vcf-manipulation` | 合并、排序、拼接、交集和子集化 VCF 文件，适合重构或比较变异集合。 | Merges, sorts, concatenates, intersects, and subsets VCF files for restructuring or comparing variant sets. |
| `bio-vcf-statistics` | `skills/bio/bio-variant-calling-vcf-statistics` | 生成 VCF 统计、样本一致性和质量概览，如 bcftools stats、gtcheck 等。 | Produces VCF statistics, sample concordance, and quality summaries with tools such as bcftools stats and gtcheck. |
| `bioinformatics-context` | `skills/bio/bioinformatics-context` | 提供水稻分子育种、生信分析、变异检测和诱变育种任务的领域背景。 | Provides domain context for rice molecular breeding, bioinformatics, variant analysis, and mutagenesis breeding tasks. |
| `snakemake-variant-pipeline` | `skills/bio/snakemake-variant-pipeline` | 搭建模块化 Snakemake 重测序流程，覆盖 FASTQ QC、BAM、GATK SNP/InDel、Manta/Delly SV 和 bcftools 分支。 | Scaffolds modular Snakemake resequencing workflows covering FASTQ QC, BAM generation, GATK SNP/InDel calling, Manta/Delly SV calling, and bcftools branches. |
| `variant-primer-design` | `skills/bio/variant-primer-design` | 从 SNP/InDel 表格设计 PCR 验证引物，支持参考序列获取、特异性筛查和失败引物重设计。 | Designs PCR validation primers from SNP/InDel tables, with reference sequence extraction, specificity screening, and redesign support. |

## Visualization / 统计与可视化

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `bio-data-visualization-circos-plots` | `skills/visualization/bio-data-visualization-circos-plots` | 创建 Circos/环形基因组图，展示染色体、基因、变异、CNV 或互作弧线等多轨道信息。 | Creates Circos-style circular genome plots with ideograms, genes, variants, CNVs, and interaction arcs. |
| `bio-data-visualization-color-palettes` | `skills/visualization/bio-data-visualization-color-palettes` | 为科研图选择色盲友好、适合论文的配色方案，如 viridis、RColorBrewer、ggsci。 | Selects colorblind-friendly, publication-ready palettes such as viridis, RColorBrewer, and ggsci. |
| `bio-data-visualization-genome-tracks` | `skills/visualization/bio-data-visualization-genome-tracks` | 绘制基因组浏览器式多轨道图，展示覆盖度、基因结构、峰、变异或局部区域证据。 | Creates genome browser-style multi-track figures for coverage, gene models, peaks, variants, and locus-specific evidence. |
| `bio-data-visualization-ggplot2-fundamentals` | `skills/visualization/bio-data-visualization-ggplot2-fundamentals` | 使用 ggplot2 绘制散点图、箱线图、热图和基础多面板科研图。 | Builds publication-oriented scatter plots, boxplots, heatmaps, and basic multi-panel figures with ggplot2. |
| `bio-data-visualization-heatmaps-clustering` | `skills/visualization/bio-data-visualization-heatmaps-clustering` | 绘制带行列注释和聚类的热图，适合表达谱、组学矩阵和共表达模式展示。 | Creates annotated and clustered heatmaps for expression profiles, omics matrices, and co-expression patterns. |
| `bio-data-visualization-multipanel-figures` | `skills/visualization/bio-data-visualization-multipanel-figures` | 将多个图组合成论文级多面板图，处理共享图例、面板标签和版式。 | Combines multiple plots into publication-ready multi-panel figures with shared legends, panel labels, and layout control. |
| `bio-data-visualization-upset-plots` | `skills/visualization/bio-data-visualization-upset-plots` | 用 UpSet 图展示多个集合交集，适合基因集、峰集、样本组或候选列表比较。 | Uses UpSet plots to visualize intersections among gene sets, peak sets, sample groups, or candidate lists. |
| `bio-data-visualization-volcano-customization` | `skills/visualization/bio-data-visualization-volcano-customization` | 定制火山图阈值、基因标签和高亮规则，适合差异表达或关联分析结果。 | Customizes volcano plots with thresholds, labels, and highlighting for differential expression or association results. |
| `bio-reporting-figure-export` | `skills/visualization/bio-reporting-figure-export` | 规范导出论文图，如 PDF/PNG、分辨率、尺寸、字体和矢量格式。 | Standardizes figure export for manuscripts, including PDF/PNG outputs, resolution, sizing, fonts, and vector formats. |
| `results-analysis` | `skills/visualization/results-analysis` | 对实验结果进行严格统计分析、显著性检验、图表设计和可追溯结果解释。 | Performs rigorous statistical analysis, significance testing, figure design, and traceable interpretation of experimental results. |
| `results-report` | `skills/visualization/results-report` | 将已有分析结果整理成结构化实验报告或结果复盘，强调证据边界和决策价值。 | Turns completed analyses into structured experiment reports or retrospectives with evidence boundaries and decision relevance. |

## Writing / 论文、综述与学位论文

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `academic-paper-reviewer` | `skills/writing/academic-paper-reviewer` | 模拟多视角同行评审，包括主编、领域审稿人、方法审稿人和反方审稿视角。 | Simulates multi-perspective peer review with editor-in-chief, domain reviewers, methodology reviewers, and critical challenge roles. |
| `academic-paper` | `skills/writing/academic-paper` | 组织学术论文写作流程，支持计划、提纲、初稿、修订、摘要、文献综述和格式转换等模式。 | Organizes academic paper writing workflows, including planning, outlining, drafting, revision, abstracts, literature reviews, and format conversion. |
| `academic-pipeline` | `skills/writing/academic-pipeline` | 协调研究、写作、完整性检查、同行评审模拟、修订和最终核查的端到端论文流程。 | Coordinates an end-to-end research-to-paper pipeline with research, writing, integrity checks, simulated review, revision, and final verification. |
| `bio-literature-synthesis-loop` | `skills/writing/bio-literature-synthesis-loop` | 从 Zotero/Obsidian 等阅读系统做周期性文献综合、复习队列、证据矩阵和研究种子梳理。 | Runs periodic literature synthesis from systems such as Zotero/Obsidian, including review queues, evidence matrices, and research seed ranking. |
| `bio-original-paper-reading` | `skills/writing/bio-original-paper-reading` | 面向原创研究论文的深度精读，强调主图重构、图版审计、证据强度和育种/生信启发。 | Deep-reads original research papers through main figures, panel audits, evidence strength assessment, and breeding or bioinformatics lessons. |
| `bio-review-paper-reading` | `skills/writing/bio-review-paper-reading` | 面向综述、观点和路线图文章，重构领域框架、共识争议、开放问题和研究方案种子。 | Reads review, perspective, and roadmap papers by reconstructing field frameworks, consensus, controversies, open gaps, and research proposal seeds. |
| `bio-thesis-review-lanes` | `skills/writing/bio-thesis-review-lanes` | 以外审、导师、答辩委员等视角审阅生物/生信学位论文或 manuscript 内容。 | Reviews biology or bioinformatics thesis/manuscript content from external reviewer, advisor, or committee perspectives. |
| `bio-thesis-workflow` | `skills/writing/bio-thesis-workflow` | 支持生物/生信论文和学位论文的写作、重组、润色、Word/Markdown 转换和结果转正文。 | Supports biology and bioinformatics thesis/manuscript writing, restructuring, polishing, Word/Markdown conversion, and results-to-prose work. |
| `citation-verification` | `skills/writing/citation-verification` | 提供引用核验原则，帮助检查虚假引用、格式错误、来源不匹配和引用准确性。 | Provides citation verification guidance to detect fabricated citations, formatting issues, source mismatches, and reference accuracy problems. |
| `paper-search` | `skills/writing/paper-search` | 指导文献检索、开放论文下载、全文阅读入口和可复现检索记录。 | Guides literature search, open-access paper download, full-text reading entry points, and reproducible search records. |
| `review-response` | `skills/writing/review-response` | 分析审稿意见并撰写专业回复，组织 rebuttal 结构、语气和修订证据。 | Analyzes reviewer comments and drafts professional rebuttals with structure, tone, and revision evidence. |
| `rice-thesis-writing` | `skills/writing/rice-thesis-writing` | 面向水稻遗传育种、诱变育种和生信方向的中文硕博论文写作、章节组织和格式处理。 | Supports Chinese thesis writing, section organization, and formatting for rice genetics, breeding, mutagenesis, and bioinformatics topics. |

## Workflow / 复现、审计与任务管理

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `handover` | `skills/workflow/handover` | 保存任务进展、关键决策、路径、风险和恢复提示，支持长对话或多任务交接。 | Preserves task progress, decisions, paths, risks, and resume prompts for long conversations or multi-task handover. |
| `job-monitor-loop` | `skills/workflow/job-monitor-loop` | 监控长时间运行任务，按退避策略检查日志、状态、输出和异常，适合生信流水线。 | Monitors long-running jobs with backoff-based checks of logs, status, outputs, and anomalies, especially for bioinformatics pipelines. |
| `project-audit` | `skills/workflow/project-audit` | 审计项目的代码、结果、文档、方法、结论强度、复现性和交付完整性。 | Audits projects across code, results, documentation, methods, conclusion strength, reproducibility, and delivery completeness. |
| `provenance-doc` | `skills/workflow/provenance-doc` | 生成和维护分析溯源文档，记录命令、参数、输入输出、版本、证据和封版状态。 | Creates and maintains provenance documents with commands, parameters, inputs, outputs, versions, evidence, and sealing status. |
| `staged-agent-run-protocol` | `skills/workflow/staged-agent-run-protocol` | 将复杂科研/生信任务拆成阶段化 agent run，记录状态、门控、产物、环境和远程作业。 | Structures complex research or bioinformatics tasks into staged agent runs with state, gates, artifacts, environments, and remote jobs. |
| `verification-loop` | `skills/workflow/verification-loop` | 在改动后运行构建、lint、类型检查、测试、安全扫描和 diff 审查等验证步骤。 | Runs post-change verification such as build, lint, type checks, tests, security scans, and diff review. |

## Engineering / 工程协作

| Skill | Path | 中文说明 | English Description |
|---|---|---|---|
| `bug-detective` | `skills/engineering/bug-detective` | 系统化排查错误、异常、失败命令和代码缺陷，整理根因、复现和修复路径。 | Systematically investigates errors, exceptions, failing commands, and code defects with root cause, reproduction, and fix paths. |
| `code-review-excellence` | `skills/engineering/code-review-excellence` | 用于代码审查、PR 审查、安全检查和团队 review 标准化。 | Supports code reviews, PR reviews, security checks, and standardized team review practices. |
| `git-workflow` | `skills/engineering/git-workflow` | 提供 Git 分支、提交、合并、冲突处理和 Conventional Commits 工作流规范。 | Provides Git branch, commit, merge, conflict resolution, and Conventional Commits workflow guidance. |
