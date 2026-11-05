#!/usr/bin/env python3
"""Write a Chinese-first, data-bound manuscript for the two-main-figure mode."""
from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def config(path: Path) -> dict[str, str]:
    return {row["field"]: row["value"] for row in read_tsv(path)}


def metric_map(path: Path) -> dict[str, str]:
    return {row["metric"]: row["value"] for row in read_tsv(path)}


def integer(value: str | float | int) -> str:
    return f"{int(float(value)):,}"


def percent(value: str | float, digits: int = 2) -> str:
    return f"{100 * float(value):.{digits}f}%"


def numeric_range(rows: list[dict[str, str]], field: str, label_field: str) -> str:
    groups: dict[str, list[float]] = {}
    for row in rows:
        if row.get("overlaps_analysis_interval", "").upper() != "TRUE":
            continue
        try:
            value = float(row[field])
        except (KeyError, ValueError):
            continue
        if math.isfinite(value):
            groups.setdefault(row[label_field], []).append(value)
    parts = []
    for label in sorted(groups):
        values = groups[label]
        parts.append(f"{label} 为 {min(values):.4g} 至 {max(values):.4g}")
    return "；".join(parts) if parts else "目标区间无有限窗口值"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--result-dir", required=True)
    args = parser.parse_args()

    cfg = config(Path(args.config).resolve())
    result = Path(args.result_dir).resolve()
    manuscript = result / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    gene = cfg["gene_id"]
    strand_cn = "正链" if cfg["gene_strand"] == "+" else "负链"

    primary = read_tsv(result / "haplotype/primary_haplotype_summary.tsv")
    all_haps = read_tsv(result / "haplotype/all_haplotype_summary.tsv")
    retention = read_tsv(result / "summary/sample_retention_by_detailed_group.tsv")
    promoter = read_tsv(result / "plot_data/promoter_site_audit.tsv")
    sites = read_tsv(result / "plot_data/major_haplotype_display_sites.tsv")
    carrier_tests = read_tsv(result / "haplotype/XI_GJ_carrier_tests.tsv")
    tree_audit = metric_map(result / "tree/sample_tree_audit.tsv")
    cohort = {row["population_group"]: int(row["accession_count"]) for row in read_tsv(result / "plot_data/cohort_population_counts.tsv")}
    map_rows = read_tsv(result / "map/primary_haplotype_area_centroid_counts.tsv")
    mst_edges = read_tsv(result / "tree/major_haplotype_mst_edges.tsv")

    complete = int(cfg["expected_complete_accessions"])
    total_source = int(cfg["expected_formal_vcf_samples"])
    copies = complete * 2
    post_snp = int(cfg["expected_post_qc_snp_count"])
    post_indel = int(cfg["expected_post_qc_indel_site_count"])
    post_total = int(cfg["expected_post_qc_variant_count"])
    major_copies = sum(int(row["haplotype_chromosome_count"]) for row in primary)
    major_coverage = major_copies / copies
    major_ids = [row["primary_haplotype_id"] for row in primary]
    major_label = f"{major_ids[0]}-{major_ids[-1]}"
    promoter_diff = sum(row.get("differentiates_primary_haplotypes", "").upper() == "TRUE" for row in promoter)
    threshold_values = sorted({row.get("site_bad_rate_threshold", "") for row in promoter if row.get("site_bad_rate_threshold", "")})
    site_bad_threshold = threshold_values[0] if len(threshold_values) == 1 else "项目敏感性分析所选阈值"
    feature_counts = Counter(row.get("feature_class", "Unknown") for row in sites)
    feature_text = "、".join(f"{name} {count} 个" for name, count in sorted(feature_counts.items()))

    mapped_copies = 0
    for row in map_rows:
        if row.get("longitude", "") and row.get("latitude", ""):
            mapped_copies += int(float(row["haplotype_chromosome_count"]))
    unmapped_copies = major_copies - mapped_copies

    retention_text = "；".join(
        f"{row['detailed_group']} 保留 {integer(row['complete_samples'])}/{integer(row['total_samples'])}（{percent(row['complete_rate'])}）"
        for row in retention
    )
    hap_abundance = "；".join(
        f"{row['primary_haplotype_id']} 为 {integer(row['haplotype_chromosome_count'])} 条（{percent(row['global_chromosome_frequency'])}）"
        for row in primary
    )
    carrier_text = "；".join(
        f"{row['primary_haplotype_id']}：XI {integer(row['XI_carrier_accessions'])}/{integer(row['XI_complete_accessions'])}（{percent(row['XI_carrier_rate'])}），"
        f"GJ {integer(row['GJ_carrier_accessions'])}/{integer(row['GJ_complete_accessions'])}（{percent(row['GJ_carrier_rate'])}），BH q={float(row['BH_q']):.3g}"
        for row in carrier_tests
    )

    pi_rows = read_tsv(result / "popgen/pi_tidy.tsv")
    tajima_rows = read_tsv(result / "popgen/tajimad_tidy.tsv")
    fst_rows = read_tsv(result / "popgen/fst_tidy.tsv")
    ratio_rows = read_tsv(result / "popgen/pi_ratio_tidy.tsv")
    pi_range = numeric_range(pi_rows, "pi", "group")
    tajima_range = numeric_range(tajima_rows, "tajima_d", "group")
    fst_range = numeric_range(fst_rows, "weighted_fst", "pair_id")
    ratio_range = numeric_range(ratio_rows, "log2_pi_ratio", "pair_id")

    methods = f"""# 2.X *{gene}* 单倍型分析

## 2.X.1 数据来源、参考版本与分析区间

本研究采用万份水稻变异图数据库的 10,548 份水稻材料基因型数据分析候选基因 *{gene}* 的单倍型组成和保留队列内群体分布[1]。参考基因组、基因坐标和主转录本注释采用 MSU Rice Genome Annotation Project Release 7（{cfg['reference_assembly']}）[2]；参考基因组序列、CDS 序列和 GFF3 注释均采用该版本的配套资源，目标基因条目由项目冻结的 GFF3 提取并核对主转录本。坐标按 1-based closed VCF 坐标报告，软件产生的窗口坐标保留其原生定义。

*{gene}* 位于第 {cfg['gene_chr_vcf']} 染色体{strand_cn}，基因区间为 {integer(cfg['gene_start'])}-{integer(cfg['gene_end'])} bp，主转录本为 *{cfg['reference_primary_transcript']}*。按转录方向取上游 2 kb 作为启动子，启动子区间为 {integer(cfg['promoter_start'])}-{integer(cfg['promoter_end'])} bp，最终分析区间为 Chr{cfg['gene_chr_vcf']}:{integer(cfg['analysis_start'])}-{integer(cfg['analysis_end'])}。材料按数据库详细群体标签归并为籼稻 XI、粳稻 GJ、普通野生稻 Or（*Oryza rufipogon*）和 Undefined；不将信息不充分的材料主观并入 XI、GJ 或 Or。

## 2.X.2 变异质量控制、完整材料和相位单倍型构建

从万份水稻数据库分别提取分析区间内 SNP 与 InDel 基因型。源基因型使用 `|` 保存相位，因此本分析不额外运行 Beagle 或进行统计定相。位点 bad-rate 定义为缺失及不能用于相位单倍型判定的基因型占全部 10,548 份材料的比例；本项目采用阈值 {site_bad_threshold}，该阈值来自既有 sensitivity audit，而不是跨基因套用。过滤后保留 {post_total} 个 post-QC 变异记录，包括 {post_snp} 个 SNP 和 {post_indel} 个 InDel。仅保留全部 post-QC 位点均可判定两条相位染色体单倍型的材料，共 {complete:,} 份材料、{copies:,} 条相位染色体拷贝；各群体保留情况为：{retention_text}。由于保留率不均，后续频率与窗口统计限定为 retained complete-case cohort。

以每条相位染色体在“启动子+完整基因”区间全部 {post_total} 个位点上的 SNP+InDel 等位基因组合定义单倍型，相同组合归为同一类。共得到 {len(all_haps)} 个未筛选单倍型；正式 Fig1 的 major set 按预设 `phased chromosome-copy n >= {cfg['major_haplotype_min_chromosome_count']}` 筛选，得到 {len(primary)} 个主要单倍型（{major_label}）。染色体拷贝数用于单倍型总体丰度、网络节点和地理组成的描述；XI/GJ 两群体差异检验以唯一材料的 carrier/non-carrier 状态为统计单位，采用双侧 Fisher 精确检验、Benjamini-Hochberg 校正，并以 Newcombe hybrid-score（Wilson）法计算携带率差值的 95% 置信区间，避免把同一二倍体材料的两条染色体当作独立重复。

## 2.X.3 主要单倍型网络、全材料样本关系树与地理汇总

主要单倍型网络以 {major_label} 的全位点等位基因模式距离构建最小生成树（MST）。节点面积表示相位染色体拷贝数，节点扇区表示 XI、GJ、Or 和 Undefined 的染色体拷贝组成；网络仅描述等位基因步数关系，不定义出现时间或祖先-后代方向。

样本关系树覆盖全部 {complete:,} 份 retained accessions，tip 为材料编号而不是 Hap ID。使用 {cfg['tree_expected_snps']} 个 post-QC SNP 计算候选区域的 diploid allele-sharing `1-IBS` 距离，以 RapidNJ {cfg['software_rapidnj']} 构建邻接树[3]，并用 PLINK {cfg['software_plink']} 对其中 {cfg['tree_plink_biallelic_validation_snps']} 个标准双等位 SNP 的距离口径进行交叉核对[4]。Newick 由 ape {cfg['software_ape']} 读取，并以 `ape::plot.phylo(type="fan")` 绘制全部材料的环形样本关系树。树枝只在全部后代属于同一群体时着色；混合后代内部枝为灰色。外环表示主要二倍型，低于 {cfg['tree_diplotype_min_accessions']} 份材料的组合并入 Other diplotypes。环形图按拓扑绘制、径向分支长度不按比例，带 branch length 的 Newick 另行交付；该树是 locus-level sample relationship tree，不能解释为 genome-wide phylogeny。

地理图依据 Original Area 注释和版本化区域质心表汇总。一个绘图点表示“区域质心×主要单倍型”的聚合记录，颜色与点形共同表示 Hap ID，大小为该质心的相位染色体拷贝数。区域质心不是材料的精确采样经纬度，未可靠映射的记录保留在 Source Data 而不在地图上伪造位置。

## 2.X.4 群体遗传与选择消除相关描述性分析

正式 SNP+InDel 单倍型 VCF、population-genetics VCF 和 tree SNP VCF 分别承担不同角色，不相互替代。Pi、Tajima's D 和 Weir-Cockerham weighted Fst 使用 canonical biallelic SNP-only VCF，由 VCFtools {cfg['software_vcftools']} 计算[5-7]；群体 VCF 使用 `--max-missing {cfg['popgen_max_missing']}`，未施加 MAF filter（`{cfg['popgen_maf_filter']}`）。Pi ratio 按比较名中的方向计算：`A_vs_B = Pi_A / Pi_B`，Fig2 显示 `log2(Pi_A / Pi_B)`。宽区间为 Chr{cfg['gene_chr_vcf']}:{integer(cfg['popgen_all_start'])}-{integer(cfg['popgen_all_end'])}，用于邻近背景；局部区间为 Chr{cfg['gene_chr_vcf']}:{integer(cfg['popgen_filter_start'])}-{integer(cfg['popgen_filter_end'])}，用于放大候选区域附近变化。

本项目 `callable-site mask={cfg['popgen_callable_mask']}`。当 mask unavailable 时，Pi 与 Tajima's D 只能作为相同过滤口径下的 nominal-window descriptive summary；局部峰谷、Pi ratio 或 Fst 差异本身不能证明选择、群体扩张/瓶颈、驯化起源或渐渗。

## 2.X.5 软件、绘图、矢量 PDF 与质量控制

数据整理与文稿生成使用 Python {cfg['software_python']}。图形绘制与矢量输出中，基因结构和主要单倍型矩阵使用 Matplotlib {cfg['software_matplotlib']}；R {cfg['software_r']} 与 ggplot2 {cfg['software_ggplot2']} 用于网络、地图和窗口图，ape {cfg['software_ape']} 的 `plot.phylo(type="fan")` 用于样本树，Cairo {cfg['software_cairo']} 用于 R 矢量 PDF 输出；BCFtools {cfg['software_bcftools']} 用于 VCF 检查；pypdf {cfg['software_pypdf']} 用于不栅格化文字与几何对象的 PDF panel 合成。分析不包含随机抽样，MST、IBS、RapidNJ 和绘图顺序均由冻结输入与配置决定。

Fig1 和 Fig2 按最终物理宽度 {cfg['figure_final_width_mm']} mm 直接设计，普通文字不低于 {cfg['figure_min_font_pt']} pt、panel label 不低于 {cfg['figure_panel_label_pt']} pt。图中文字仅使用 {cfg['pdf_allowed_fonts']}，PDF 保留可编辑矢量 text layer，拒绝 Type 3、Helvetica、Symbol、未嵌入字体和 `/Image` XObject；同时输出 {cfg['png_dpi']} dpi PNG。程序 QA 核对 major set、MST `N-1`、Newick tips、树注释、地图 ID、broad/local 窗口、PDF 字体与文字层、Source Data、release manifest、ZIP 成员和输入 SHA。人工 QA 在 100% 最终尺寸、灰度、protan、deutan 和 tritan 条件下逐 panel 检查可读性、裁切、拥挤和图例理解。
"""

    results_text = f"""# 3.X *{gene}* 单倍型鉴定及群体分布

## 3.X.1 目标区域变异、完整材料与单倍型组成

对万份水稻数据库中 *{gene}* 的 2 kb 启动子和完整基因区域进行联合分析。{total_source:,} 份源材料中有 {complete:,} 份通过全部 {post_total} 个 post-QC 位点的完整基因型要求，保留率为 {complete/total_source:.2%}，对应 {copies:,} 条相位染色体拷贝。保留位点包括 {post_snp} 个 SNP 和 {post_indel} 个 InDel。基于全部位点的相位组合，共鉴定 {len(all_haps)} 个未筛选单倍型。

按照“相位染色体拷贝数不少于 {cfg['major_haplotype_min_chromosome_count']}”的预设标准，获得 {len(primary)} 个主要单倍型（{major_label}）。它们合计 {major_copies:,} 条染色体拷贝，占 retained phased copies 的 {major_coverage:.2%}。各单倍型丰度为：{hap_abundance}。其余低频单倍型未并入 Fig1 的网络、矩阵和地图，但保留在完整结果表中。因此，“主要单倍型”是显示和汇总阈值，不代表低频单倍型不存在或没有潜在生物学意义。

## 3.X.2 启动子和基因区域对主要单倍型差异的贡献

启动子区域共有 {len(promoter)} 个 post-QC 记录接受逐位点核对，其中 {promoter_diff} 个能够区分 {major_label}。Fig1a 最终显示 {len(sites)} 个在主要单倍型之间发生变化的位点，功能区域构成为：{feature_text}。表格使用 A/C/G/T、REF、INSn、DELn 或 MNV 等简写提高可读性，完整 REF/ALT 序列、变异 ID、坐标和功能标签保留在 Fig1 Source Data。

这一结果仅描述 {major_label} 之间的等位基因差异。若某个启动子位点在主要 set 中不变，不能据此推断万份水稻全部材料不存在该启动子变异；低频单倍型及被完整基因型筛选排除的材料仍可能携带其他等位基因。

## 3.X.3 主要单倍型的 XI/GJ carrier 组成

以 retained complete accessions 为分母，主要单倍型的 XI/GJ carrier 结果为：{carrier_text}。双侧 Fisher 精确检验及 BH 校正描述的是 retained XI/GJ 材料中“是否携带该 Hap”的统计关联，不能把染色体拷贝频率当作独立重复。

样本保留率在群体间不完全一致：{retention_text}。因此 carrier 差异应限定于当前 complete-case cohort；即使特定 Hap 在 XI 或 GJ 中呈现显著富集，也不能直接升级为强区域分化、已受到选择、驯化起源、渐渗、功能因果或育种价值。

## 3.X.4 单倍型网络、全材料样本关系树与地理分布

{major_label} 的 MST 包含 {len(primary)} 个节点和 {len(mst_edges)} 条边，符合连通树的 `Hmajor-1` 结构（Fig1b）。节点大小和扇区分别反映相位染色体拷贝总数及群体组成；边长标签反映单倍型模式距离，而不是年代或进化方向。

候选区域样本关系树包含 {tree_audit.get('tree_tip_count', str(complete))} 个 tips，且 tip 集合与 retained accession 集合完全一致（Fig1c）。树输入为 {tree_audit.get('tree_input_snp_count', cfg['tree_expected_snps'])} 个 post-QC SNP；群体分母为 XI {cohort.get('XI', 0):,}、GJ {cohort.get('GJ', 0):,}、Or {cohort.get('Or', 0):,}、Undefined {cohort.get('Undefined', 0):,}。外环只用主要二倍型和 Other diplotypes 注释，不把非主要 Hap ID 暴露为独立类别。该树是候选区域内的样本关系拓扑，不是全基因组系统发育树，环形显示的径向 branch length 不按比例。

Original Area 质心地图中，有 {mapped_copies:,}/{major_copies:,} 条主要单倍型染色体拷贝获得可用区域质心，{unmapped_copies:,} 条因区域信息不足而不绘制（Fig1d）。点位是区域级聚合坐标，不能解释为材料精确采样地点；点大小反映该质心处的相位染色体拷贝数而非独立地理重复。

## 3.X.5 目标区域的核苷酸多样性和群体分化

与启动子或基因区间重叠的窗口中，核苷酸多样性 Pi：{pi_range}。Tajima's D：{tajima_range}。Weir-Cockerham weighted Fst：{fst_range}。群体间 log2 Pi ratio：{ratio_range}（Fig2；完整窗口见 Fig2 Source Data）。broad 面板用于观察约 400 kb 邻近背景，local 面板放大约 100 kb 的候选区域邻域，两者窗口范围和纳入窗口数真实不同。

这些窗口值与特定 Hap 的 carrier 率回答不同层面的问题：前者描述区域 SNP 变异和群体分化，后者描述特定相位组合在 retained accessions 中的携带状态。两类结果方向不必一致。由于没有覆盖全队列的 callable-site mask，Pi 与 Tajima's D 仅是 nominal-window 描述性证据；负值可与方向性选择或群体扩张相容，正值可与平衡选择或瓶颈相容，但当前数据不能在这些机制之间作出验证性判断。Fst、Pi ratio、网络、树和地图也不能单独证明选择消除、驯化起源、渐渗或因果效应。
"""

    legends = f"""# 图注

**图1  *{gene}* 的主要单倍型结构、关系和区域分布。** a、上部为 2 kb 启动子和 MSU7 主转录本结构；黑色矩形表示 CDS，白色矩形表示 UTR，连线表示内含子，箭头表示 5' 到 3' 转录方向，灰色短线表示启动子中的 {len(promoter)} 个 post-QC 位点。连接线对应下方 {len(sites)} 个区分 {major_label} 的位点；表格行为主要单倍型，列为物理位置、功能区、主要等位基因和 XI/GJ/Or/Total carrier n。carrier n 的统计单位为唯一材料，分母分别为 XI {cohort.get('XI', 0):,}、GJ {cohort.get('GJ', 0):,}、Or {cohort.get('Or', 0):,} 和 Total {complete:,}；完整 REF/ALT 见 Source Data。b、主要单倍型 MST，仅包含 `phased chromosome-copy n >= {cfg['major_haplotype_min_chromosome_count']}` 的 {major_label}。节点面积表示相位染色体拷贝数，扇区颜色表示 XI、GJ、Or 和 Undefined 的拷贝组成，边及数字表示主要单倍型模式距离；{len(primary)} 个节点以 {len(mst_edges)} 条边连接。c、全部 {complete:,} 份 retained accessions 的 locus-level 1-IBS/RapidNJ 样本关系树。tip 是材料而非单倍型；枝条颜色与线型共同表示后代均属于 XI、GJ、Or 或 Undefined 的纯群体分支，混合内部枝为灰色实线；外环表示主要二倍型，低于 {cfg['tree_diplotype_min_accessions']} 份材料的组合归为 Other diplotypes。环形图显示拓扑，径向 branch length 不按比例，带分支长度的 Newick 见 Source Data；该图不是 genome-wide phylogeny。d、主要单倍型的 Original Area 质心分布。颜色与点形共同表示 Hap ID，点大小表示该区域质心的相位染色体拷贝数；映射分母为主要单倍型 {major_copies:,} 条拷贝，其中 {mapped_copies:,} 条可绘制。点位是区域质心而非材料精确采样坐标。Fig1 所有 matrix/network/map Hap ID 均严格等于 major set，详细数值见 `table/SourceData/TSV/`。

**图2  *{gene}* 周边的群体遗传与选择消除相关描述性统计。** a、b，分别为 broad 区间 Chr{cfg['gene_chr_vcf']}:{integer(cfg['popgen_all_start'])}-{integer(cfg['popgen_all_end'])} 和 local 区间 Chr{cfg['gene_chr_vcf']}:{integer(cfg['popgen_filter_start'])}-{integer(cfg['popgen_filter_end'])} 的核苷酸多样性 Pi；颜色、线型和稀疏点形共同区分 XI、GJ、Or，统计分母为各群体 retained complete accessions。c、d，相同 broad/local 区间的 Tajima's D。e、f，相同区间的 Weir-Cockerham weighted Fst；颜色、线型和稀疏点形共同区分 XI_vs_GJ、XI_vs_Or 和 GJ_vs_Or，0 水平线用于辅助读取。g、h，相同区间的 log2 Pi ratio；比较名 `A_vs_B` 定义为 `Pi_A / Pi_B`，图中显示 `log2(Pi_A / Pi_B)`，0 表示两群体 Pi 相等，正值表示 A 群体 Pi 较高，负值表示 B 群体 Pi 较高。每个点/折线位置对应软件原生窗口中点，灰色竖线标记启动子起点、基因起点和基因终点。窗口统计来自 canonical biallelic SNP-only VCF、`--max-missing {cfg['popgen_max_missing']}` 且不进行 MAF filtering。由于 callable-site mask 为 `{cfg['popgen_callable_mask']}`，Pi 与 Tajima's D 仅作 nominal-window descriptive summary，任何局部峰谷均不能单独证明选择或群体历史机制。各 panel 的窗口坐标、窗口数、有限值、群体/比较、原始统计量和 log2 变换见 `table/SourceData/TSV/`。
"""

    references = """# 参考文献

[1] Wang T, He W, Li X, et al. A rice variation map derived from 10 548 rice accessions reveals the importance of rare variants. Nucleic Acids Research, 51(20): 10924-10933. DOI: 10.1093/nar/gkad840.

[2] Kawahara Y, de la Bastide M, Hamilton J P, et al. Improvement of the Oryza sativa Nipponbare reference genome using next generation sequence and optical map data. Rice, 6: 4. DOI: 10.1186/1939-8433-6-4.

[3] Simonsen M, Mailund T, Pedersen C N S. Rapid Neighbour-Joining. Algorithms in Bioinformatics, LNCS 5251: 113-122. DOI: 10.1007/978-3-540-87361-7_10.

[4] Purcell S, Neale B, Todd-Brown K, et al. PLINK: a tool set for whole-genome association and population-based linkage analyses. American Journal of Human Genetics, 81(3): 559-575. DOI: 10.1086/519795.

[5] Danecek P, Auton A, Abecasis G, et al. The variant call format and VCFtools. Bioinformatics, 27(15): 2156-2158. DOI: 10.1093/bioinformatics/btr330.

[6] Weir B S, Cockerham C C. Estimating F-statistics for the analysis of population structure. Evolution, 38(6): 1358-1370. DOI: 10.1111/j.1558-5646.1984.tb05657.x.

[7] Tajima F. Statistical method for testing the neutral mutation hypothesis by DNA polymorphism. Genetics, 123(3): 585-595. DOI: 10.1093/genetics/123.3.585.
"""

    (manuscript / "材料与方法.md").write_text(methods)
    (manuscript / "结果与分析.md").write_text(results_text)
    (manuscript / "图注.md").write_text(legends)
    (manuscript / "参考文献.md").write_text(references)
    print(f"[manuscript-v4] gene={gene} methods={len(methods)} results={len(results_text)} legends={len(legends)}")


if __name__ == "__main__":
    main()
