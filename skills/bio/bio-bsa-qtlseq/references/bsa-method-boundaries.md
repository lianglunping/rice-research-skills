# BSA Method Boundaries — 方法学边界声明

本 skill 的方法学基础是 **QTL-seq (Takagi 2013) + G' 统计 (Magwene 2011) + QTLseqr R 实现 (Mansfeld 2018)**。以下是严格的假设与适用范围。

## 1. 适用数据类型

✅ **支持**:
- 物种: 任何二倍体（ploidy=2）植物 / 动物 / 真菌，F2 / BC / RIL 分离群体
- 起点: cohort VCF (DeepVariant / GATK / bcftools)
- 表型: 连续数值（如失水率、产量、抗病评分）或等级（rank）
- 混池: ≥10 个体/池（推荐 ≥50, 理想 ≥400）

❌ **不支持（或需特殊处理）**:
- 多倍体（四倍体、六倍体）—— 需改造 SNPindex 计算
- 混合倍性（如马铃薯四倍体 × 二倍体）
- 自然群体（无亲本对照时，QTLseqr 不直接适用，需 ED 算法）
- 低深度测序（每个体 < 10× 时，pseudo-pool 信号噪声过大）

## 2. 核心假设

1. **亲本纯合且差异**: Va (高表型亲本) 与 Vv (低表型亲本) 在关注位点应分别为 0/0 和 1/1（或反之）
2. **群体随机分离**: F2/BC 遵循孟德尔分离律，无选择偏好
3. **Pseudo-pool 近似**: 逐个体测序后 AD/DP 求和 ≈ 物理混池 DNA 一次测序（前提: 个体间测序深度均一，±2× 以内）
4. **允许的小样本偏差**: bulkSize < 50 时，QTL 定位分辨率降低，置信区间扩大，是方法学**固有限制**，不是本 skill bug

## 3. 与其他分析方法的边界

### 本 skill 不做
- **QTL fine-mapping**（需扩群 + 单 QTL 效应量估计 + KASP 验证，转其他流程）
- **基因克隆**（需转录组 + 表型互补 + gene editing）
- **功能验证**（RNA-seq / 差异表达）
- **GWAS**（本 skill 是**家系定位**，非群体关联）
- **单细胞 / 空间组学**（不适用）
- **多性状联合定位**（需改造，非默认）

### 本 skill 补充
- `project-audit`: 交付前自动强制调用
- `variant-primer-design`: KASP 引物留给下游
- `bio-genome-annotation-functional-annotation`: GO/KEGG 执行留给下游

## 4. 多时间点 / 多批次限制

- **时间点 (timepoint)**: 必须在 `phenotype_source.meta.yaml` 声明，且测定方法一致
- **批次 (batch)**: 不同批次不允许直接合并 QTL 区间；可做 interval QC 但不做生物学跨批次解读
- **自动触发对比条件** (AND):
  - 同 project.id
  - 同 reference.assembly_id
  - 同亲本
  - 样本交集 ≥ 50%
  - phenotype_unit 一致
- 不满足 → 生成 warning 提示客户确认，不自动跨时间点解读

## 5. 已知方法学漏洞与缓解

| 漏洞 | 缓解 | 触发条件 |
|------|------|---------|
| 小样本统计力不足 (n<50) | 报告中显式声明 + A/B/C Tier 分级 | bulk_size[i] < 50 |
| Preplanned 阈值 (q=0.01) 全空 | allow_fallback=true 触发降档 + fallback_rationale.md | Gate 3 #4 |
| 端粒低重组区伪宽峰 | interpretation_flags.md 标记 + 候选基因按距峰距离分层 | posMaxGprime == chrom_end |
| 染色体级 stratification | interpretation_flags.md 标记 + 建议剔除 | 区间长 > chrom × 50% |
| pseudo-pool 方法学边界 | LIMITATIONS §3.1 强制声明 | 所有项目都适用 |
| DeepVariant DP ≠ sum(AD) | v2.1 代码已修 (DEC-014), Gate 2 #8 核验 | 永久修复 |
| ΔSNP 方向性误读 | v2.1 re-polarize (DEC-015), +ΔSNP 恒代表 Va 富集 | 永久修复 |

## 6. 不可规避的限制（客户必须接受）

1. BSA 只定位 **主效 QTL**（效应量 > 20%）；小效应多基因难检出
2. 混池规模远小于群体遗传学理想（400/池），实际使用 20/池只能是"候选筛选"，**不能替代精细定位**
3. 参考基因组质量决定上限：gap / 错误组装 / 低重组区 无法通过统计方法弥补
4. 表型测量误差会直接传导到 QTL 定位：客户必须提供可靠表型

## 7. 引用基础

- Takagi H, et al. (2013). QTL-seq: rapid mapping of quantitative trait loci in rice by whole genome resequencing of DNA from two bulked populations. _Plant J_ 74:174-183.
- Magwene PM, et al. (2011). The statistics of bulk segregant analysis using next generation sequencing. _PLoS Comput Biol_ 7:e1002255.
- Mansfeld BN, Grumet R. (2018). QTLseqr: An R Package for Bulk Segregant Analysis with Next-Generation Sequencing. _Plant Genome_ 11:180006.
