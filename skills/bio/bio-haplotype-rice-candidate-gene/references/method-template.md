# 水稻候选基因单倍型分析文稿模板（模式感知）

本模板用于生成客户 `manuscript/` 中的中文材料与方法、结果与分析、逐 panel 图注和参考文献。文稿必须由冻结配置、结果 TSV/XLSX、软件版本记录和 QA 证据动态生成；不得从旧基因复制数字、坐标、软件或结论。

## 1. 先冻结分析模式

写作前读取项目 `formal_mode`，不得跨模式套用阈值、群体、树 tip 单位、VCF 角色或图形变换。

| formal_mode | 数据与写作入口 |
|---|---|
| 3K 正式模式 | 使用 3K RGP VCF、K5 分组和项目配置的 missing/MAF/site bad-rate 规则 |
| superrice_reference_compatible_v2 | 使用万份水稻变异图数据库、详细 XI/GJ/Or/Undefined 分组和 reference-compatible 合同 |
| superrice_publication_compact_v3 | 使用 accession carrier 阈值与 XI/GJ 推断单位合同 |
| superrice_reference_two_mainfig_v4 | 使用 phased chromosome-copy `n >= 30` major set、全 retained-accession 样本树和两张主图合同 |

必须从项目 sensitivity audit 读取万份水稻 site bad-rate 阈值；不得把 3%、10% 或任一旧项目阈值写成通用规则。Pi 使用交付数据的原始量纲；除非配置和 Source Data 明确规定，否则不得默认写成 -log10(Pi)。

## 2. 冻结字段

至少从配置和结果表读取以下字段，并在写作前核对分母和单位：

- `{GENE_ID}`、`{PRIMARY_TRANSCRIPT}`、`{REFERENCE_BUILD}`、`{ANNOTATION_RELEASE}`；
- `{CHR}`、`{STRAND}`、`{GENE_START}`、`{GENE_END}`、`{PROMOTER_START}`、`{PROMOTER_END}`、`{ANALYSIS_START}`、`{ANALYSIS_END}`；
- `{SOURCE_ACCESSION_N}`、`{RETAINED_ACCESSION_N}`、`{RETAINED_PHASED_COPY_N}` 及各群体 retained/source 分母；
- `{SITE_BAD_RATE}`、`{POST_QC_SNP_N}`、`{POST_QC_INDEL_N}`、`{ALL_HAP_N}`、`{MAJOR_HAP_N}`、`{MAJOR_COPY_N}`；
- `{TREE_SNP_N}`、`{TREE_TIP_N}`、`{MST_NODE_N}`、`{MST_EDGE_N}`；
- `{MAPPED_COPY_N}`、`{MAPPING_DENOMINATOR}`、`{CALLABLE_MASK_STATUS}`；
- `{POPGEN_BROAD_INTERVAL}`、`{POPGEN_LOCAL_INTERVAL}`、各指标的窗口数和 target-overlap range；
- 实际运行的软件、包、数据库和版本，而不是计划版本。

坐标必须注明参考版本和坐标基准。基因与启动子坐标按 strand-aware 规则计算；窗口坐标保留软件原生定义并在 Source Data README 中说明。

## 3. `superrice_reference_two_mainfig_v4` 材料与方法结构

### 3.1 数据来源、参考版本与分析区间

写明使用万份水稻变异图数据库及其 10,548 份源材料口径，引用数据库原始论文；参考基因组、基因坐标、主转录本、CDS 和 GFF3 注释使用 MSU Rice Genome Annotation Project Release 7（MSU_osa1r7）。报告目标基因、染色体、正负链、基因区间、strand-aware 上游 2 kb 启动子和最终分析区间。

写明群体归并规则：详细标签映射为 XI、GJ、Or（*Oryza rufipogon*）和 Undefined；不得把信息不足的材料强行归组。说明后续分母来自 retained complete-case cohort。

### 3.2 变异质量控制、完整材料与单倍型构建

说明从 SNP 与 InDel wide genotype 表提取目标区间。若基因型以 `|` 保存相位，明确未额外运行 Beagle；若存在分析所需的未定相杂合，记录排除或定相规则。

定义 site bad-rate、项目 sensitivity audit 选择的阈值、post-QC SNP/InDel 数和完整材料规则。分别报告源材料、retained accessions、phased chromosome copies，以及 XI/GJ/Or/Undefined 的 retained/source 分母与保留率。保留率不均时，将比较限定为 retained cohort。

以全部批准 post-QC SNP+InDel 等位基因组合定义相位单倍型。对 `superrice_reference_two_mainfig_v4`，major set 使用 phased chromosome-copy `n >= 30`；说明这是显示/汇总阈值，不代表低频单倍型不存在。carrier 检验必须以唯一 accession presence/absence 为统计单位，不能把两条染色体拷贝当作独立重复。

### 3.3 主要单倍型网络、全材料样本关系树与地理汇总

描述 major-only MST：节点为主要单倍型，面积为 phased chromosome-copy count，扇区为群体拷贝组成，边为批准位点上的模式距离；网络只描述关系，不定义年代或祖先方向。

描述 locus-level 1-IBS/RapidNJ 样本关系树：tip 为全部 retained accessions，不是 Hap ID；列出 tree SNP 数、距离口径、RapidNJ 版本和交叉核对工具。外环只显示 major diplotype 与 Other diplotypes。若环形图径向分支长度不按比例，必须明示并交付带 branch length 的 Newick。该树不是 genome-wide phylogeny。

描述地理汇总使用版本化 Original Area 质心表。报告 mapped numerator/denominator/rate；明确区域质心不是 accession sampling coordinates，未可靠映射的记录不能伪造位置。

### 3.4 群体遗传与选择消除相关描述性分析

区分三个 VCF 角色：正式 post-QC SNP+InDel haplotype VCF、canonical biallelic SNP-only population-genetics VCF 和 tree SNP VCF。客户交付的正式 VCF 不得被后两者替代。

写明 VCFtools 版本和实际参数：missingness、MAF 是否使用、Pi、Tajima's D、Weir-Cockerham weighted Fst，以及 `A_vs_B = Pi_A / Pi_B` 和 `log2(Pi_A / Pi_B)` 的方向。分别报告 broad/local 区间，确认二者坐标跨度和窗口数真实不同。

写明 callable-site mask 状态。若 callable-site mask 为 unavailable，Pi 和 Tajima's D 仅为 nominal-window descriptive summary；局部峰谷、Fst 或 Pi ratio 不能单独证明选择、群体历史、驯化或渐渗。

### 3.5 软件、绘图和质量控制

列出数据库、参考、命令行软件、Python/R、绘图库、树工具、VCF 工具、PDF 合成工具及实际软件版本。未实际使用的软件不得写入 Methods。

说明 Fig1/Fig2 的最终物理尺寸、普通文字下限、panel label 下限、Arial/Times New Roman 字体、可编辑矢量 PDF、600 dpi PNG、字体嵌入、无 Type 3/Helvetica/Symbol、无 `/Image` XObject，以及 native/grayscale/protan/deutan/tritan 人工审阅。机械 QA 必须包括 panel label、PDF 文字框重叠、裁切、字体和 release/ZIP 完整性。

## 4. 结果与分析合同

结果不得写成“图1展示……图2展示……”的摘要。至少按以下顺序分节，并从结果表动态写入实际数字与分母：

1. 目标区域 post-QC SNP/InDel、retained accessions/phased copies、all haplotypes；
2. major set、各主要单倍型 copy count/frequency、major coverage 和 promoter contribution；
3. XI/GJ carrier numerator/denominator、Fisher/BH/Newcombe 结果及 complete-case 限制；
4. MST nodes/edges、全材料 tree tips/group counts、Original Area mapped numerator/denominator；
5. target-overlap Pi、Tajima's D、weighted Fst、log2 Pi ratio range 及 callable-mask 限制。

每节区分观察、统计关联、可相容的解释和需要额外验证的机制。网络、树、地图和 nominal-window 统计不得升级为已证实的选择、起源、渐渗、因果或育种价值。

## 5. 图注合同

图注按论文 legend 体例逐 panel 撰写，不用一句话概括整张复合图。

- Fig1 必须逐 panel 定义 a-d：对象、图形编码、统计单位、分母、major threshold、branch-length display、Original Area 限制和 Source Data。
- Fig2 必须逐 panel 定义 a-h：Pi、Tajima's D、Weir-Cockerham weighted Fst、log2 Pi ratio 的 broad/local 配对；写明群体/比较颜色与线型、窗口坐标、单位、0 线含义、Pi ratio 方向和 callable-site mask 限制。
- 图注必须能独立解释颜色、线型、点形、节点/点大小、carrier/accession/phased-copy 分母和缺失值；读者不应被迫回到 Methods 才能理解基本编码。

## 6. 参考文献与客户边界

至少引用数据集、参考基因组/注释、RapidNJ、PLINK、VCFtools、Weir-Cockerham 和 Tajima's D 的可核验来源；仅在实际使用时引用其他包或算法。

客户文稿不得出现 `/Users/`、`/home/`、`/Volumes/`、Windows drive、用户名或内部日志路径。客户文稿只报告数据库、文件角色、参考版本、参数和 Source Data 相对位置；绝对路径、SHA256、命令日志和环境记录留在内部 provenance/QA。
