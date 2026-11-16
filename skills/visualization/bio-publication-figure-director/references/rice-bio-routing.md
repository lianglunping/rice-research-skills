# 水稻与生信绘图路由

先读数据与项目规则，再选择最小的本地 skill 组合。这里给的是路由，不是对输入数据的默认假设。

## 常见任务

| 科研问题 | 首选图型 | 必查契约 | 本地 skill |
|---|---|---|---|
| GWAS 全局信号 | Manhattan + QQ；关键位点另做区域图 | genome build、坐标、阈值、群体结构 | `bio-data-visualization-manhattan-qq-locuszoom` |
| 候选区间/基因 | gene/variant/coverage tracks | 注释版本、链、坐标基准、REF/ALT | `bio-data-visualization-genome-tracks` |
| 单倍型与表型 | haplotype frequency + phenotype distribution + population composition | 区域定义、样本归属、缺失、主单倍型阈值 | `bio-haplotype-rice-candidate-gene` |
| 变异技术证据 | VAF/strand/quality 分布 + locus evidence panel | caller、过滤、共享 read 来源、验证方法 | 多面板 + 分布 + genome tracks |
| 代表位点 read view | 对齐截图/track + 定量 read support | 样本、坐标、链、mapping/base quality、截图范围 | genome tracks；作为辅助证据 |
| M1–M2/M3 世代观察 | 家系/世代流程 + 条件分母 + 个体基因型 | 家系、选择历史、实际检测个体 | 多面板；不写“传递率”除非设计支持 |
| 田间表型 | individual points + box/violin 或 block-aware estimates | 行区、重复、区组、材料、缺失 | 分布图 + 统计标注 |
| 差异表达 | MA/volcano + effect-size distribution + selected-gene expression | contrast、normalization、FDR、样本 n | volcano/MA + distribution |
| 富集分析 | dot/bar plot；必要时 network | gene universe、数据库版本、校正 | pathway enrichment visualization |
| WGCNA/相关矩阵 | module-trait heatmap + module evidence | 样本 n、批次、相关方法、校正 | heatmaps/clustering |
| PCA/UMAP | points + explained variance/parameters + group encodings | 输入矩阵、normalization、batch | dimensionality-reduction plots |
| 多集合交集 | UpSet | 各集合定义、总体 universe | `bio-data-visualization-upset-plots` |
| 跨染色体连接/SV | Circos 或 chromosome ideogram | 坐标、事件类型、过滤与密度 | `bio-data-visualization-circos-plots` |
| GS 模型 | cross-validation distribution + observed/predicted + calibration | fold、seed、relatedness leakage、metric | distribution + scatter + multipanel |

## 论文主图的常见结构

### 候选基因/单倍型

- 主要证据：主单倍型与表型或群体分化的直接结果。
- 辅助证据：区域结构、变异定义、群体组成。
- 补充材料：完整单倍型矩阵、全部位点、QC。

### 诱变变异证据

- 主要证据：候选变异在限定材料/世代中的核心观察。
- 辅助证据：检测深度、VAF、链平衡、背景误差、家系结构。
- 补充材料：完整 locus × sample 矩阵与 read views。
- 边界：共享 Readcount–caller reads 是一致性，不是独立准确性；后代少量被测个体只证明被测个体。
- read view 必须与冻结的定量表对应；不能只凭“看起来像变异”升级结论。

### GWAS/GS

- 主要证据：主分析结果或外部/嵌套验证性能。
- 辅助证据：群体结构、QQ、CV 分布、候选区间。
- 补充材料：全模型参数、完整 sensitivity 与样本 QC。
- 边界：候选位点不是验证基因；训练内 CV 不是独立外部验证。

## FigureYa 检索映射

这些模块可在单独取得的 FigureYa 参考中检索。

| 图型 | FigureYa 模块 |
|---|---|
| genome view | `FigureYa3genomeView` |
| chromosome ideogram | `FigureYa10chromosomeV2_update` |
| Manhattan | `FigureYa43ManhattanV2` |
| heatmap | `FigureYa9heatmap` |
| WGCNA heatmap | `FigureYa17WGCNA_heatmap` |
| PCA | `FigureYa38PCA` |
| volcano | `FigureYa59volcanoV2` |
| boxplot | `FigureYa12box` |
| lollipop | `FigureYa19Lollipop` |
| Sankey | `FigureYa25Sankey_update` |
| Venn | `FigureYa112venn` |
| association heatmap | `FigureYa124AssociationHeatmap` |
| ggplot2 genome tracks | `FigureYa172ggplot2Gviz` |
| enrichment | `FigureYa83enrichment` |
| tree + heatmap + MSA | `FigureYa2ggtree+pheatmap+msa` |

这些模块多为人类生物医学示例。对水稻任务必须替换物种数据库、染色体命名、注释和输入契约；不要直接运行其自动安装脚本。
