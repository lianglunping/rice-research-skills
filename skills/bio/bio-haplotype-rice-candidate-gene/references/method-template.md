# 方法描述模板 — 水稻候选基因单倍型与群体遗传分析

> 将 `{GENE_ID}`、`{CHR_NUM}`、`{GENE_START}`、`{GENE_END}`、`{GENE_STRAND}`、`{PROMOTER_START}`、`{PROMOTER_END}`、`{ANALYSIS_START}`、`{ANALYSIS_END}`、`{TOTAL_LEN_KB}`、`{PRE_QC_VARIANTS}`、`{POST_QC_VARIANTS}`、`{HAP_RETAINED_N}`、`{TOTAL_SAMPLE_N}`、`{HAP_COUNT}`、`{MAJOR_HAP_COUNT}`、`{MAJOR_HAP_SAMPLE_N}` 替换为实际值。

---

## 1. 数据来源

本研究基于 3,000 水稻基因组计划（3,000 Rice Genomes Project，3K RGP）的全基因组测序数据。3K RGP 收录了来自亚洲 89 个国家和地区的 3,000 份栽培稻材料，代表了籼稻（Xian/Indica）、粳稻（Geng/Japonica）、混合群（Admixture）、Aus 和 Basmati 五大亚群（K5 分组）的主要遗传多样性。基因组变异以 VCF 格式提供，参考基因组版本为水稻 MSU Release 7（MSU_osa1r7）。目标基因 {GENE_ID} 的基因结构注释来源于 MSU_osa1r7 GFF3 文件。

## 2. 样本筛选

以 K5 亚群分类信息为依据，排除 K5 缺失或未被分类（K5 = na）的样本，保留可分类样本 **{TOTAL_SAMPLE_N}** 份。

## 3. 目标区间定义

目标基因 {GENE_ID} 位于第 {CHR_NUM} 号染色体（Chr{CHR_NUM}），基因体坐标为 {GENE_START}–{GENE_END} bp（{GENE_STRAND}链）。考虑到转录调控区对基因功能的重要性，在基因体的 strand-aware 上游定义 2 kb 启动子区，启动子区坐标为 {PROMOTER_START}–{PROMOTER_END} bp。单倍型分析区间取基因体与启动子区的并集，即 **Chr{CHR_NUM}:{ANALYSIS_START}–{ANALYSIS_END} bp**，全长约 {TOTAL_LEN_KB} kb。

## 4. 变异位点过滤

从目标区间的 VCF 文件中提取变异位点，使用以下标准对 SNP 进行过滤：

- **缺失率（missing rate）< 5%**：剔除在超过 5% 样本中缺失基因型的位点；
- **最小等位基因频率（MAF）≥ 0.05**：剔除次要等位基因频率低于 5% 的低频位点。

## 5. 位点质量控制（per-site bad-rate 过滤）

在常规缺失率和 MAF 过滤之后，对每个位点进行额外的质量控制，计算位点坏率（site bad-rate）：

$$\text{bad-rate} = \frac{N_\text{missing} + N_\text{het}}{N_\text{total}}$$

其中 $N_\text{missing}$ 为缺失基因型样本数，$N_\text{het}$ 为杂合基因型样本数，$N_\text{total}$ 为总样本数。水稻为自交物种，栽培稻基因型应以纯合为主，因此高频的杂合位点通常源于测序误差或比对错误，而非真实的生物学信号。以 **bad-rate ≤ 3%** 为阈值，剔除超过该阈值的位点。

经上述两步过滤后，目标区间内保留 **{POST_QC_VARIANTS} 个高质量 SNP 位点**（过滤前 {PRE_QC_VARIANTS} 个）用于后续单倍型构建。

## 6. 单倍型构建

基于目标区间（{ANALYSIS_START}–{ANALYSIS_END} bp）内 {POST_QC_VARIANTS} 个 SNP，对每份样本进行单倍型分型。在单倍型构建中，剔除在目标区间内存在任意杂合（heterozygous）或缺失（missing）基因型的样本，保留基因型完整且纯合的样本（haplotype-retained samples）共 **{HAP_RETAINED_N} 份**。

根据 SNP 等位基因组合的不同，共识别出 **{HAP_COUNT} 种单倍型**。以样本量 **n ≥ 30** 为 major 单倍型阈值，共有 **{MAJOR_HAP_COUNT} 种 major 单倍型**，覆盖 **{MAJOR_HAP_SAMPLE_N} 份样本**。

## 7. 单倍型最小生成网络

基于 {MAJOR_HAP_COUNT} 种 major 单倍型之间的 SNP 差异数（Hamming distance），使用最小生成网络（minimum spanning network，MSN）算法描述单倍型间的进化关系。网络中每个节点代表一种 major 单倍型，节点大小与样本量成比例，节点内的扇形（pie slice）展示各 K5 亚群的样本比例。

## 8. 局部区间 IBS/NJ 进化树

为刻画样本间的遗传距离，利用 PLINK（v1.9）计算样本间的同源一致性（identity-by-state，IBS）距离矩阵。以 1 − IBS 作为遗传距离，对全部 **{TOTAL_SAMPLE_N} 份样本**基于目标区间内经 `--mac 1` 过滤后的 **{POST_QC_VARIANTS} 个 SNP** 构建邻接树（neighbor-joining tree，NJ tree），使用 R 包 `ape` 实现。进化树以环形布局（circular layout）呈现，枝条颜色标注 major 单倍型归属；在目标区间内存在杂合或缺失基因型、未能分配单倍型的样本以中性色（灰色）标注。外环（outer ring）标注 K5 亚群信息。

## 9. 群体遗传统计

在目标基因周边更宽泛的区域，利用滑动窗口（sliding window）方法计算以下群体遗传统计量，以评估局部遗传多样性与群体分化模式：

- **核苷酸多样性（Pi，π）**：以 `vcftools --window-pi` 计算，展示各 K5 亚群内的 SNP 多样性水平，图中以 −log₁₀(Pi) 形式呈现；
- **Tajima's D**：以 `vcftools --TajimaD` 计算，检测中性偏离信号，正值提示平衡选择或群体规模近期缩减（瓶颈效应），负值提示方向性选择（选择清除）或群体近期扩张；
- **群体间固定指数（Fst）**：以 `vcftools --weir-fst-pop` 计算 Weir & Cockerham 加权 Fst，评估 K5 亚群间的遗传分化；
- **Pi ratio**：以亚群间 Pi 的比值刻画相对多样性差异，辅助识别特定亚群中的选择信号。

统计量均以位置坐标为横轴展示，目标基因体及启动子区以浅色高亮带标注。基因 overlapping window（与目标区间存在位置重叠的窗口）的描述性汇总值列于结果表格中，**不作为正式统计检验依据**，仅提供描述性参考。

## 10. 地理分布可视化

基于各样本的经纬度信息，绘制 major 单倍型和 K5 亚群的地理分布图，直观展示不同单倍型在亚洲水稻种植区的空间分布规律。

## 11. 软件与版本

| 工具 / 包 | 用途 |
|-----------|------|
| bcftools | VCF 过滤与区间提取 |
| vcftools | missing rate、MAF 过滤；Pi、Tajima's D、Fst 计算 |
| PLINK v1.9 | IBS 距离矩阵计算 |
| R（≥ 4.x） | 数据整合、可视化、统计汇总 |
| R::ape | NJ 树构建 |
| R::ggtree / ggtreeExtra | 进化树可视化 |
| R::igraph | 最小生成网络计算 |
| R::rnaturalearth / sf | 地理底图与分布图 |
| R::ggplot2 / patchwork | 图件排版 |

---

> **证据边界说明**：本分析的所有统计图件和数据表格提供的是描述性证据，支持 {GENE_ID} 区间存在局部单倍型结构、地理分布差异及群体多样性/分化特征的描述性判断。Pi、Tajima's D、Fst 和单倍型网络/NJ 树**不能单独作为选择、驯化、渗入或选择性清除的统计学证明**，结论措辞应限定在"候选"或"描述性支持"层面。
