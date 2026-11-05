#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the compact publication v3 release and delivery zip.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root", required=True)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_config(path: Path) -> dict[str, str]:
    return {row["field"]: row["value"] for row in read_tsv(path)}


def metrics(path: Path) -> dict[str, str]:
    return {row["metric"]: row["value"] for row in read_tsv(path)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(path: Path, rows: list[dict[str, Any]], fields: list[str], sheet: str) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = sheet[:31]
    worksheet.append(fields)
    for cell in worksheet[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for row in rows:
        worksheet.append([row.get(field, "") for field in fields])
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    workbook.save(path)


def percentage(value: str | float) -> str:
    return f"{100 * float(value):.2f}%"


def build_documents(config: dict[str, str], result_dir: Path, release_dir: Path) -> dict[str, str]:
    key = metrics(result_dir / "summary" / "publication_compact_key_metrics.tsv")
    retention = {row["detailed_group"]: row for row in read_tsv(result_dir / "summary" / "sample_retention_by_detailed_group.tsv")}
    tests = {row["primary_haplotype_id"]: row for row in read_tsv(result_dir / "haplotype" / "XI_GJ_carrier_tests.tsv")}
    source_popgen = Path(config["source_result_dir"]) / "summary" / "gene_overlapping_popgen_summary.tsv"
    popgen = read_tsv(source_popgen)
    fst = next(row for row in popgen if row["metric"] == "Weir_Cockerham_weighted_Fst" and row["group_or_pair"] == "XI_vs_GJ")
    gene = config["gene_id"]
    primary_rule = (
        f"carrier accession count >= {config['primary_haplotype_min_carrier_accessions']} and "
        f"max(XI, GJ chromosome frequency) > {float(config['primary_haplotype_subgroup_chr_frequency_min']):.1%}"
    )
    retention_text = "; ".join(
        f"{group}: {row['complete_samples']}/{row['total_samples']} ({percentage(row['complete_rate'])})"
        for group, row in retention.items()
    )
    methods = f"""# 方法描述

## 数据与区间

本分析使用万份水稻数据库已验证的 `{config['source_run_id']}` 结果作为只读数据源，对 *{gene}* 的 2 kb 启动子和基因本体进行单倍型展示与 XI/GJ 分化分析。参考基因组和注释版本为 `{config['reference_assembly']}`；目标区间为 `Chr{config['gene_chr_vcf']}:{config['analysis_start']}-{config['analysis_end']}`。

源分析的位点 bad-rate 阈值为 `{config['site_bad_rate_threshold']}`，由该项目的敏感性审计确定。v3 不重新进行位点过滤，也不修改 v2 文件。完整单倍型 retained cohort 为 {key['source_complete_samples']} 份材料；分组保留情况为：{retention_text}。因此所有群体频率和检验均限定于 retained complete-case cohort。

## 单倍型定义与主要展示集合

单倍型由启动子和基因区域全部 {config['expected_post_qc_variant_count']} 个 post-QC SNP+InDel 位点的 phased chromosome copies 定义。材料携带数和 chromosome-copy count 分别统计。共识别 {key['all_haplotype_count']} 个不筛选单倍型；主要单倍型按 `{primary_rule}` 选择，得到 {key['primary_haplotype_count']} 个单倍型。频率比较使用严格大于号，等于 0.5% 不纳入。

## XI/GJ 统计

每个主要单倍型在 XI 和 GJ 中按 accession 是否携带构建 2 x 2 表，使用双侧 Fisher exact test，并对 {key['primary_haplotype_count']} 次检验进行 Benjamini-Hochberg 校正。XI-GJ 携带率差使用 Newcombe hybrid-score 95% CI。Chromosome-copy frequencies 仅用于描述和主要单倍型筛选；accession 是统计推断单位。

逐位点 Fst 使用 canonical biallelic SNP VCF 和 `vcftools --weir-fst-pop` 计算 Weir-Cockerham Fst，`--max-missing {config['popgen_max_missing']}`，不使用 MAF 过滤。Pi、Tajima's D 和窗口 Fst 继承自 v2 的 vcftools 输出。由于没有 callable-site mask，Pi 和 Tajima's D 仅作同一处理口径下的局部描述。

## 图形与证据边界

主图采用两张复合图，并同时输出每个 panel。PDF 由 Cairo 直接生成，保留矢量对象和文本层；PNG 为 {config['png_dpi']} dpi。图中文字为英文、Arial，基因标签为斜体。网络、NJ tree、地理质心和群体遗传统计均为描述性证据，不能独立证明选择、驯化起源、渐渗、功能因果或育种价值。
"""
    legends = f"""# Figure Legends

**Figure 1 | Haplotype architecture and XI-GJ distribution of *{gene}*.** **a,** Primary-transcript model, the {key['primary_haplotype_count']} primary haplotypes and {key['primary_variable_site_count']} sites that vary among them. Detailed XI1-XI5 and GJ1-GJ5 columns report phased chromosome-copy counts; the final column reports unique carrier accessions. REF denotes a long reference allele, whereas DEL and INS denote deletion and insertion states; full alleles are retained in the source-data workbook. **b,** XI-GJ carrier-rate differences using accession presence/absence, Newcombe 95% confidence intervals and two-sided Fisher exact tests with BH-adjusted q values. **c,** Within-subgroup phased chromosome-copy frequencies. Frequencies describe retained complete-case accessions.

**Figure 2 | Haplotype relationships and local XI-GJ differentiation.** **a,** Minimum-spanning network of the primary haplotypes. Node area is proportional to chromosome-copy count, sectors show XI/GJ/Or/Undefined composition, and edge labels are full-pattern Hamming distances. **b,** XI-GJ alternate-allele frequency differences and per-site Weir-Cockerham Fst across the promoter and gene body. **c,** Local XI/GJ Pi, Tajima's D and windowed XI-GJ weighted Fst. These panels are descriptive and do not constitute independent selection evidence.

**Figure S1.** Rank-abundance distribution of all {key['all_haplotype_count']} unfiltered chromosome-copy haplotypes; primary haplotypes are highlighted.

**Figure S2.** Neighbor-joining tree of primary haplotypes based on the full-pattern Hamming-distance matrix. Branch lengths are shown to scale.

**Figure S3.** Area-centroid distribution of primary haplotypes. Points are Original Area centroids, not accession sampling coordinates.
"""
    example_ids = sorted(
        tests,
        key=lambda item: (-abs(float(tests[item]["rate_difference_XI_minus_GJ"])), item),
    )[: min(3, len(tests))]
    example_text = "；".join(
        f"{item} 在 XI 和 GJ 中的 accession 携带率分别为 "
        f"{percentage(tests[item]['XI_carrier_rate'])} 和 {percentage(tests[item]['GJ_carrier_rate'])}"
        for item in example_ids
    )
    results = f"""# 结果与讨论

在 {key['source_complete_samples']} 份完整材料的 retained cohort 中，共获得 {key['source_haplotype_chromosomes']} 条 phased chromosome copies，识别 {key['all_haplotype_count']} 个单倍型。依据预声明的联合阈值，{key['primary_haplotype_count']} 个单倍型进入主图，覆盖全部 chromosome copies 的 {percentage(key['primary_haplotype_chromosome_coverage'])}。

{example_text}。这些结果支持 retained cohort 中存在特定单倍型频率偏移。

与上述单倍型频率偏移同时，基因重叠窗口的 XI-GJ Weir-Cockerham weighted Fst 范围为 {float(fst['min_value']):.4f}-{float(fst['max_value']):.4f}，均值为 {float(fst['mean_value']):.5f}。因此，本项目可表述为“特定单倍型频率差异与较低的局部区域 Fst 并存”，不应表述为整个区域存在强分化。保留率在 XI、GJ 和 Or 间不均衡，尤其 Or 较低，因此不延伸至群体历史、选择或起源结论。
"""
    readme = f"""# {gene} publication-compact haplotype release v3

本 release 含 2 张复合主图、6 个独立主图 panel、3 张补充图、逐图 Source Data、正式汇总表、图注、方法、结果边界、QA 和脚本快照。

主要单倍型规则：`{primary_rule}`。全部 {key['all_haplotype_count']} 个单倍型不筛选版本保留在 Excel 表中。
"""
    reproducibility = f"""# REPRODUCIBILITY

- Generated: `{datetime.now().astimezone().isoformat(timespec='seconds')}`
- Source result: `{config['source_result_dir']}` (read only)
- Run ID: `{config['run_id']}`
- Release ID: `{config['release_id']}`
- Random seed: `{config['random_seed']}`
- Python/R environment: `{config.get('python_prefix') or 'not recorded'}`
- vcftools environment: `{config.get('ngs_prefix') or 'not recorded'}`
- Entry point: `bash scripts/publication_compact_v3/run_publication_compact_v3.sh`

输入路径、SHA256、软件版本、命令日志、TSV 中间表和完整 QA 均保留于 `results/{config['run_id']}`。
"""
    manuscript = release_dir / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    (manuscript / "方法描述.md").write_text(methods)
    (manuscript / "Figure_Legends.md").write_text(legends)
    (manuscript / "Results_Discussion.md").write_text(results)
    (release_dir / "README.md").write_text(readme)
    (release_dir / "REPRODUCIBILITY.md").write_text(reproducibility)
    return {"Fig1": legends.split("**Figure 2")[0], "Fig2": "**Figure 2" + legends.split("**Figure 2")[1].split("**Figure S1")[0]}


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve()
    config = read_config(config_path)
    result_dir = project_root / "results" / config["run_id"]
    release_dir = project_root / "release" / config["release_id"]
    delivery_dir = project_root / "delivery"
    if release_dir.exists():
        if release_dir.parent != project_root / "release" or release_dir.name != config["release_id"]:
            raise SystemExit(f"Refusing to replace unexpected release path: {release_dir}")
        shutil.rmtree(release_dir)
    for name in ("figure", "table", "manuscript", "QA", "scripts", "logs"):
        (release_dir / name).mkdir(parents=True, exist_ok=True)
    delivery_dir.mkdir(parents=True, exist_ok=True)

    manifest = read_tsv(result_dir / "summary" / "figure_manifest.tsv")
    for row in manifest:
        for suffix in (".pdf", ".png"):
            relative = Path(f"{row['relative_stem']}{suffix}")
            copy_file(result_dir / "figures" / relative, release_dir / "figure" / relative)

    source_data = {
        "Fig1_HaplotypeArchitecture_XI_GJ/Fig1_SourceData.xlsx": "Fig1_SourceData.xlsx",
        "Fig2_HaplotypeRelationships_XI_GJ/Fig2_SourceData.xlsx": "Fig2_SourceData.xlsx",
        "Supplementary/Supplementary_SourceData.xlsx": "Supplementary_SourceData.xlsx",
    }
    for destination, source_name in source_data.items():
        copy_file(result_dir / "tables" / source_name, release_dir / "figure" / destination)
    for source in sorted((result_dir / "tables").glob("*.xlsx")):
        copy_file(source, release_dir / "table" / source.name)
    copy_file(result_dir / "tree" / "primary_haplotype_NJ_tree.newick", release_dir / "table" / "primary_haplotype_NJ_tree.newick")

    legends = build_documents(config, result_dir, release_dir)
    (release_dir / "figure" / "Fig1_HaplotypeArchitecture_XI_GJ" / "Fig1_Legend.md").write_text(legends["Fig1"])
    (release_dir / "figure" / "Fig2_HaplotypeRelationships_XI_GJ" / "Fig2_Legend.md").write_text(legends["Fig2"])

    qa_sources = [
        result_dir / "summary" / name
        for name in (
            "publication_compact_key_metrics.tsv", "publication_compact_key_metrics.xlsx",
            "source_provenance.tsv", "source_provenance.xlsx", "figure_manifest.tsv", "figure_manifest.xlsx",
            "figure_visual_review.tsv", "figure_visual_review.xlsx", "formal_release_qa.tsv", "formal_release_qa.xlsx",
        )
    ]
    for source in qa_sources:
        if source.exists():
            copy_file(source, release_dir / "QA" / source.name)
    for source in sorted((project_root / "scripts" / "publication_compact_v3").glob("*")):
        if source.is_file() and source.suffix.lower() in {".py", ".r", ".sh"}:
            copy_file(source, release_dir / "scripts" / source.name)
    copy_file(config_path, release_dir / "scripts" / config_path.name)
    for source in sorted((result_dir / "logs").glob("*")):
        if source.is_file():
            copy_file(source, release_dir / "logs" / source.name)

    contract_rows = [{"field": field, "value": value} for field, value in config.items()]
    write_tsv(release_dir / "QA" / "project_contract.tsv", contract_rows, ["field", "value"])
    write_xlsx(release_dir / "QA" / "project_contract.xlsx", contract_rows, ["field", "value"], "contract")

    manifest_rows: list[dict[str, Any]] = []
    excluded = {"formal_release_file_manifest.tsv", "formal_release_file_manifest.xlsx"}
    for path in sorted(release_dir.rglob("*")):
        if path.is_file() and path.name not in excluded:
            manifest_rows.append({
                "relative_path": path.relative_to(release_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    fields = ["relative_path", "size_bytes", "sha256"]
    write_tsv(release_dir / "QA" / "formal_release_file_manifest.tsv", manifest_rows, fields)
    write_xlsx(release_dir / "QA" / "formal_release_file_manifest.xlsx", manifest_rows, fields, "manifest")

    zip_path = delivery_dir / config["delivery_zip"]
    include_png = config.get("delivery_include_png", "FALSE").upper() == "TRUE"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(release_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(release_dir)
            suffix = path.suffix.lower()
            include = False
            if len(relative.parts) == 1 and suffix == ".md":
                include = True
            elif relative.parts[0] == "figure" and suffix in ({".pdf", ".png", ".xlsx", ".md"} if include_png else {".pdf", ".xlsx", ".md"}):
                include = True
            elif relative.parts[0] == "table" and suffix in {".xlsx", ".newick"}:
                include = True
            elif relative.parts[0] == "manuscript" and suffix == ".md":
                include = True
            elif relative.parts[0] == "QA" and suffix == ".xlsx":
                include = True
            if include:
                archive.write(path, relative.as_posix())
    (delivery_dir / f"{zip_path.name}.sha256").write_text(f"{sha256(zip_path)}  {zip_path.name}\n")
    print(f"[release] figure_pairs={len(manifest)} manifest_rows={len(manifest_rows)} zip={zip_path}")


if __name__ == "__main__":
    main()
