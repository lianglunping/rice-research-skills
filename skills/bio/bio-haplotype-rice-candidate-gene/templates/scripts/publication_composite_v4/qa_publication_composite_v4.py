#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import subprocess
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from PIL import Image
from scipy.stats import fisher_exact


Image.MAX_IMAGE_PIXELS = None

def figure_contract(gene_id: str) -> dict[str, tuple[str, str]]:
    return {
        "Fig1_HaplotypeArchitecture/panels/major_haplotype_counts": ("main_panel", "Fig1"),
        "Fig1_HaplotypeArchitecture/panels/haplotype_network": ("main_panel", "Fig1"),
        "Fig1_HaplotypeArchitecture/panels/var_gene": ("main_panel", "Fig1"),
        "Fig1_HaplotypeArchitecture/panels/vat_tab": ("main_panel", "Fig1"),
        "Fig1_HaplotypeArchitecture/panels/hap_map_by_haplotype": ("main_panel", "Fig1"),
        f"Fig2_PopulationGenetics/panels/{gene_id}_Pi_all": ("main_panel", "Fig2"),
        f"Fig2_PopulationGenetics/panels/{gene_id}_Pi": ("main_panel", "Fig2"),
        f"Fig2_PopulationGenetics/panels/{gene_id}_TajimaD_all": ("main_panel", "Fig2"),
        f"Fig2_PopulationGenetics/panels/{gene_id}_TajimaD_filter": ("main_panel", "Fig2"),
        f"Fig2_PopulationGenetics/panels/{gene_id}_Fst_all": ("main_panel", "Fig2"),
        f"Fig2_PopulationGenetics/panels/{gene_id}_Fst_filter": ("main_panel", "Fig2"),
        "Fig1_HaplotypeArchitecture/Fig1_HaplotypeArchitecture": ("main_composite", "Fig1"),
        "Fig2_PopulationGenetics/Fig2_PopulationGenetics": ("main_composite", "Fig2"),
        "Supplementary/FigS1_NJTree": ("supplementary", ""),
        "Supplementary/FigS2_var_gene_all": ("supplementary", ""),
        "Supplementary/FigS3_var_gene_cds": ("supplementary", ""),
        "Supplementary/FigS4_var_gene_promoter": ("supplementary", ""),
        "Supplementary/FigS5_vat_tab_all": ("supplementary", ""),
        "Supplementary/FigS6_vat_tab_cds": ("supplementary", ""),
        "Supplementary/FigS7_vat_tab_promoter": ("supplementary", ""),
        "Supplementary/FigS8_hap_map_all": ("supplementary", ""),
        "Supplementary/FigS9_hap_map_facet": ("supplementary", ""),
        "Supplementary/FigS10_Pi_ratio": ("supplementary", ""),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comprehensive QA for original-style publication composite superrice v4.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--verify-only", action="store_true")
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_config(path: Path) -> dict[str, str]:
    return {row["field"]: row["value"] for row in read_tsv(path)}


def metric_dict(path: Path) -> dict[str, str]:
    return {row["metric"]: row["value"] for row in read_tsv(path)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_float(value: Any) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return math.nan


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - radius), min(1.0, centre + radius)


def newcombe(a: int, n_a: int, b: int, n_b: int) -> tuple[float, float]:
    p_a, p_b = a / n_a, b / n_b
    low_a, high_a = wilson(a, n_a)
    low_b, high_b = wilson(b, n_b)
    difference = p_a - p_b
    lower = difference - math.sqrt((p_a - low_a) ** 2 + (high_b - p_b) ** 2)
    upper = difference + math.sqrt((high_a - p_a) ** 2 + (p_b - low_b) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def bh_adjust(values: list[float]) -> list[float]:
    count = len(values)
    adjusted = [math.nan] * count
    running = 1.0
    for rank, index in reversed(list(enumerate(sorted(range(count), key=lambda i: values[i]), start=1))):
        running = min(running, values[index] * count / rank)
        adjusted[index] = min(1.0, running)
    return adjusted


def graph_connected(nodes: set[str], edges: list[dict[str, str]], left: str, right: str) -> bool:
    if not nodes:
        return False
    adjacency: dict[str, set[str]] = defaultdict(set)
    for row in edges:
        adjacency[row[left]].add(row[right])
        adjacency[row[right]].add(row[left])
    seen: set[str] = set()
    stack = [next(iter(nodes))]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency[node] - seen)
    return seen == nodes


def write_qa(stem: Path, rows: list[dict[str, str]]) -> None:
    fields = ["check", "status", "detail"]
    with stem.with_suffix(".tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "QA"
    worksheet.append(fields)
    for cell in worksheet[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for row in rows:
        worksheet.append([row[field] for field in fields])
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    worksheet.column_dimensions["A"].width = 46
    worksheet.column_dimensions["B"].width = 12
    worksheet.column_dimensions["C"].width = 115
    workbook.save(stem.with_suffix(".xlsx"))


def main() -> None:
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    config_path = Path(args.config).resolve()
    config = read_config(config_path)
    result = project_root / "results" / config["run_id"]
    release = project_root / "release" / config["release_id"]
    delivery = project_root / "delivery" / config["delivery_zip"]
    source = Path(config["source_result_dir"])
    expected_figures = figure_contract(config["gene_id"])
    checks: list[dict[str, str]] = []

    def add(name: str, ok: bool, detail: Any = "") -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": str(detail)})

    required = [
        result / "haplotype" / "primary_haplotype_summary.tsv",
        result / "haplotype" / "all_haplotype_summary.tsv",
        result / "haplotype" / "XI_GJ_carrier_tests.tsv",
        result / "haplotype" / "primary_haplotype_threshold_audit.tsv",
        result / "plot_data" / "primary_variable_site_summary.tsv",
        result / "plot_data" / "primary_variable_allele_matrix.tsv",
        result / "plot_data" / "all_haplotype_all_site_allele_matrix.tsv",
        result / "popgen" / "XI_GJ_site_differentiation.tsv",
        result / "tree" / "primary_haplotype_mst_edges.tsv",
        result / "tree" / "display_haplotype_NJ_tree.newick",
        result / "summary" / "publication_composite_key_metrics.tsv",
        result / "summary" / "source_provenance.tsv",
        result / "summary" / "figure_manifest.tsv",
        result / "summary" / "figure_content_decisions.tsv",
        result / "summary" / "figure_visual_review.tsv",
        result / "tables" / "Table1_HaplotypeSummary.xlsx",
        result / "tables" / "Table2_XI_GJ_Differentiation.xlsx",
        result / "tables" / "Table3_VariantMatrix.xlsx",
        result / "tables" / "TableS1_PopulationGenetics.xlsx",
        result / "tables" / "Fig1_SourceData.xlsx",
        result / "tables" / "Fig2_SourceData.xlsx",
        result / "tables" / "Supplementary_SourceData.xlsx",
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    add("required_files", not missing, f"missing={missing}")
    if missing:
        if not args.verify_only:
            write_qa(result / "summary" / "formal_release_qa", checks)
        raise SystemExit("QA stopped because required files are missing")

    source_qa = read_tsv(source / "summary" / "formal_release_qa.tsv")
    source_qa_failures = [row["check"] for row in source_qa if row["status"] != "PASS"]
    add("validated_source_run_qa", not source_qa_failures, source_qa_failures)

    provenance = read_tsv(result / "summary" / "source_provenance.tsv")
    hash_failures = []
    for row in provenance:
        if not row["bytes"]:
            continue
        path = Path(row["path"])
        if not path.exists() or sha256(path) != row["sha256"]:
            hash_failures.append(str(path))
    add("source_files_unchanged_sha256", not hash_failures, hash_failures)
    cds_match = next((row["sha256"] for row in provenance if row["path"] == "assembled_matches_reference_cds"), "FALSE")
    add("reference_cds_exact_match", cds_match == "TRUE", cds_match)

    key = metric_dict(result / "summary" / "publication_composite_key_metrics.tsv")
    expected_complete = int(config["expected_complete_accessions"])
    expected_chromosomes = int(config["expected_haplotype_chromosomes"])
    expected_xi = int(config["expected_XI_complete_accessions"])
    expected_gj = int(config["expected_GJ_complete_accessions"])
    expected_primary = int(config["expected_primary_haplotype_count"])
    expected_display = int(config["expected_display_haplotype_count"])
    expected_all = int(config["expected_all_haplotype_count"])
    expected_variable = int(config["expected_primary_variable_site_count"])
    expected_variants = int(config["expected_post_qc_variant_count"])
    expected_metrics = {
        "source_complete_samples": expected_complete,
        "source_haplotype_chromosomes": expected_chromosomes,
        "all_haplotype_count": expected_all,
        "primary_haplotype_count": expected_primary,
        "source_display_haplotype_count": expected_display,
        "primary_variable_site_count": expected_variable,
        "primary_pairwise_distance_count": expected_primary * (expected_primary - 1) // 2,
        "primary_mst_edge_count": expected_primary - 1,
        "XI_complete_samples": expected_xi,
        "GJ_complete_samples": expected_gj,
        "assignment_chromosome_copy_count": expected_chromosomes,
    }
    metric_mismatch = {
        name: (key.get(name), expected)
        for name, expected in expected_metrics.items()
        if int(float(key.get(name, -1))) != expected
    }
    add("key_metric_contract", not metric_mismatch and expected_chromosomes == 2 * expected_complete, metric_mismatch)

    source_variants = read_tsv(source / "haplotype" / f"{config['gene_id']}.superrice_variant_table.tsv")
    add("post_qc_snp_indel_count", len(source_variants) == expected_variants, len(source_variants))
    all_summary = read_tsv(result / "haplotype" / "all_haplotype_summary.tsv")
    primary = read_tsv(result / "haplotype" / "primary_haplotype_summary.tsv")
    expected_primary_ids = [f"H{index:03d}" for index in range(1, expected_primary + 1)]
    add(
        "unfiltered_and_primary_haplotype_counts",
        len(all_summary) == expected_all
        and len(primary) == expected_primary
        and [row["primary_haplotype_id"] for row in primary] == expected_primary_ids,
        {"all": len(all_summary), "primary": [row["primary_haplotype_id"] for row in primary]},
    )
    rank_order_ok = [int(row["rank"]) for row in all_summary] == list(range(1, expected_all + 1))
    rank_order_ok = rank_order_ok and all(
        int(all_summary[index]["haplotype_chromosome_count"]) >= int(all_summary[index + 1]["haplotype_chromosome_count"])
        for index in range(len(all_summary) - 1)
    )
    add("top20_and_all_rank_order", rank_order_ok, [row["haplotype_chromosome_count"] for row in all_summary[:20]])

    threshold = read_tsv(result / "haplotype" / "primary_haplotype_threshold_audit.tsv")
    minimum_carriers = int(config["primary_haplotype_min_carrier_accessions"])
    minimum_frequency = float(config["primary_haplotype_subgroup_chr_frequency_min"])
    threshold_failures = []
    for row in threshold:
        expected = int(row["carrier_accession_count"]) >= minimum_carriers and max(
            float(row["XI_chromosome_frequency"]), float(row["GJ_chromosome_frequency"])
        ) > minimum_frequency
        recorded = row["selected_primary"] == "TRUE"
        if recorded != expected or row["frequency_operator"] != ">" or float(row["frequency_threshold"]) != minimum_frequency:
            threshold_failures.append(row["all_haplotype_id"])
    selected_threshold_ids = [row["all_haplotype_id"] for row in threshold if row["selected_primary"] == "TRUE"]
    synthetic_rule_ok = (
        not (minimum_carriers >= minimum_carriers and minimum_frequency > minimum_frequency)
        and math.nextafter(minimum_frequency, math.inf) > minimum_frequency
        and not (minimum_carriers - 1 >= minimum_carriers and 0.9 > minimum_frequency)
    )
    add(
        "strict_joint_primary_threshold_recomputed",
        len(threshold) == expected_all
        and len(selected_threshold_ids) == expected_primary
        and not threshold_failures
        and synthetic_rule_ok,
        {"selected": selected_threshold_ids, "failures": threshold_failures},
    )

    source_assignments = read_tsv(source / "haplotype" / f"{config['gene_id']}.all_haplotype_sample_assignment.tsv")
    source_manifest = {
        row["sample_id"]: row
        for row in read_tsv(source / "haplotype" / f"{config['gene_id']}.superrice_sample_manifest_detailed.tsv")
    }
    copy_counts: Counter[str] = Counter()
    carrier_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in source_assignments:
        copy_counts[row["sample_id"]] += 1
        group = source_manifest[row["sample_id"]]["detailed_group"]
        carrier_by_group[(row["all_haplotype_id"], group)].add(row["sample_id"])
    add(
        "two_phased_copies_per_complete_accession",
        len(copy_counts) == expected_complete and set(copy_counts.values()) == {2},
        {"samples": len(copy_counts), "copies": sorted(set(copy_counts.values()))},
    )

    tests = read_tsv(result / "haplotype" / "XI_GJ_carrier_tests.tsv")
    p_values: list[float] = []
    test_failures: list[str] = []
    for row in tests:
        all_id = row["all_haplotype_id"]
        xi = len(carrier_by_group[(all_id, "XI")])
        gj = len(carrier_by_group[(all_id, "GJ")])
        table = [[xi, expected_xi - xi], [gj, expected_gj - gj]]
        p_value = float(fisher_exact(table, alternative="two-sided").pvalue)
        p_values.append(p_value)
        low, high = newcombe(xi, expected_xi, gj, expected_gj)
        prefix = row["primary_haplotype_id"]
        if xi != int(row["XI_carrier_accessions"]) or gj != int(row["GJ_carrier_accessions"]):
            test_failures.append(f"{prefix}:carrier")
        if int(row["XI_complete_accessions"]) != expected_xi or int(row["GJ_complete_accessions"]) != expected_gj:
            test_failures.append(f"{prefix}:denominator")
        if row["test_unit"] != "accession carrier presence/absence" or row["fisher_alternative"] != "two-sided":
            test_failures.append(f"{prefix}:method")
        if not math.isclose(p_value, float(row["fisher_exact_p"]), rel_tol=1e-11, abs_tol=1e-300):
            test_failures.append(f"{prefix}:fisher")
        if not math.isclose(low, float(row["rate_difference_CI_low"]), rel_tol=1e-11) or not math.isclose(
            high, float(row["rate_difference_CI_high"]), rel_tol=1e-11
        ):
            test_failures.append(f"{prefix}:newcombe")
    for row, expected_q in zip(tests, bh_adjust(p_values)):
        if not math.isclose(expected_q, float(row["BH_q"]), rel_tol=1e-11, abs_tol=1e-300):
            test_failures.append(f"{row['primary_haplotype_id']}:BH")
    add("accession_fisher_bh_newcombe_recomputed", len(tests) == expected_primary and not test_failures, test_failures)

    variable_sites = read_tsv(result / "plot_data" / "primary_variable_site_summary.tsv")
    primary_matrix = read_tsv(result / "plot_data" / "primary_variable_allele_matrix.tsv")
    matrix_long = read_tsv(result / "plot_data" / "primary_variable_allele_matrix_long.tsv")
    all_matrix = read_tsv(result / "plot_data" / "all_haplotype_all_site_allele_matrix.tsv")
    matrix_ok = (
        len(variable_sites) == expected_variable
        and len(primary_matrix) == expected_primary
        and len(primary_matrix[0]) == expected_variable + 2
        and len(matrix_long) == expected_primary * expected_variable
        and len(all_matrix) == expected_all
        and len(all_matrix[0]) == expected_variants + 4
    )
    add(
        "primary_and_unfiltered_matrix_dimensions",
        matrix_ok,
        {
            "sites": len(variable_sites),
            "primary": (len(primary_matrix), len(primary_matrix[0])),
            "long": len(matrix_long),
            "all": (len(all_matrix), len(all_matrix[0])),
        },
    )
    consequence_ok = (
        any(row["coding_consequence"].startswith("p.") for row in variable_sites)
        and any(row["coding_consequence"] == "in-frame InDel" for row in variable_sites)
        and all(row["coding_consequence"] != "frameshift" for row in variable_sites)
    )
    add("observed_allele_coding_consequences", consequence_ok, Counter(row["coding_consequence"] for row in variable_sites))

    primary_edges = read_tsv(result / "tree" / "primary_haplotype_mst_edges.tsv")
    primary_node_set = set(expected_primary_ids)
    primary_tree_ok = len(primary_edges) == expected_primary - 1 and graph_connected(primary_node_set, primary_edges, "hap_a", "hap_b")
    add("primary_mst_n_minus_one_connected", primary_tree_ok, len(primary_edges))

    display_counts = read_tsv(source / "haplotype" / "display_haplotype_counts_top80.tsv")
    display_nodes = read_tsv(source / "tree" / "display_haplotype_node_table.tsv")
    display_edges = read_tsv(source / "tree" / "display_haplotype_mst_edges.tsv")
    display_ids = {row["display_haplotype_id"] for row in display_counts}
    display_network_ok = (
        len(display_counts) == expected_display
        and len(display_nodes) == expected_display
        and {row["display_haplotype_id"] for row in display_nodes} == display_ids
        and len(display_edges) == expected_display - 1
        and graph_connected(display_ids, display_edges, "hap_a", "hap_b")
    )
    add("top80_network_n_minus_one_connected", display_network_ok, {"nodes": len(display_nodes), "edges": len(display_edges)})
    try:
        from Bio import Phylo

        tree = Phylo.read(result / "tree" / "display_haplotype_NJ_tree.newick", "newick")
        tips = [tip.name for tip in tree.get_terminals()]
        lengths = [clade.branch_length for clade in tree.find_clades() if clade is not tree.root]
        nj_ok = set(tips) == display_ids and len(tips) == expected_display and all(
            length is not None and math.isfinite(float(length)) for length in lengths
        )
        add("top80_nj_tip_and_branch_length_contract", nj_ok, {"tips": len(tips), "branches": len(lengths)})
    except Exception as exc:
        add("top80_nj_tip_and_branch_length_contract", False, exc)

    site_fst_raw = read_tsv(result / "popgen" / "vcftools_raw" / "XI_vs_GJ.site.weir.fst")
    site_rows = read_tsv(result / "popgen" / "XI_GJ_site_differentiation.tsv")
    finite_fst = [float(row["site_Weir_Cockerham_Fst"]) for row in site_rows if math.isfinite(as_float(row["site_Weir_Cockerham_Fst"]))]
    fst_script = (project_root / "scripts" / "publication_composite_v4" / "run_xi_gj_site_fst_v4.sh").read_text()
    fst_ok = (
        bool(site_fst_raw)
        and bool(finite_fst)
        and min(finite_fst) >= -1
        and max(finite_fst) <= 1
        and "--weir-fst-pop" in fst_script
        and "--maf" not in fst_script
    )
    add(
        "vcftools_site_fst_without_maf",
        fst_ok,
        f"raw={len(site_fst_raw)} finite={len(finite_fst)} range=({min(finite_fst):.6g},{max(finite_fst):.6g})",
    )

    workbook_expectations = {
        "Table1_HaplotypeSummary.xlsx": {
            "Publication_Table", "Primary_Haplotypes", "Top20_HaplotypeCounts", "All_Haplotypes",
            "Subgroup_Chr_Counts", "Subgroup_Frequencies", "Subgroup_Denominators", "Carrier_Assignment", "Threshold_Audit",
        },
        "Table2_XI_GJ_Differentiation.xlsx": {"Carrier_Tests", "Site_Differentiation", "Sample_Retention"},
        "Table3_VariantMatrix.xlsx": {"Display_Site_Info", "Primary_Variable", "Primary_All_Sites", "All_Haplotypes_All_Sites"},
        "TableS1_PopulationGenetics.xlsx": {"Pi", "TajimaD", "Fst", "Pi_ratio"},
        "Fig1_SourceData.xlsx": {
            "Primary_Haplotypes", "Top80_Counts", "Threshold_Audit", "Network_Nodes_Top80", "Network_Edges_Top80",
            "Gene_Sites", "Primary_Variable_Matrix", "Primary_Area_Centroids", "Retention",
        },
        "Fig2_SourceData.xlsx": {"Pi", "TajimaD", "Fst", "Pi_ratio"},
        "Supplementary_SourceData.xlsx": {
            "Top80_Distance_Matrix", "Top80_All_Site_Matrix", "All_Haplotype_Ranks", "Area_Centroids", "Primary_Distance_Matrix",
        },
    }
    workbook_failures: list[str] = []
    workbooks: dict[str, Any] = {}
    for name, expected_sheets in workbook_expectations.items():
        workbook = load_workbook(result / "tables" / name, read_only=True, data_only=True)
        workbooks[name] = workbook
        if set(workbook.sheetnames) != expected_sheets:
            workbook_failures.append(f"{name}:{workbook.sheetnames}")
    table1 = workbooks["Table1_HaplotypeSummary.xlsx"]
    table2 = workbooks["Table2_XI_GJ_Differentiation.xlsx"]
    table3 = workbooks["Table3_VariantMatrix.xlsx"]
    if table1["Top20_HaplotypeCounts"].max_row != 21 or table1["All_Haplotypes"].max_row != expected_all + 1:
        workbook_failures.append("Table1:row_counts")
    if table2["Carrier_Tests"].max_row != expected_primary + 1:
        workbook_failures.append("Table2:carrier_rows")
    if table3["Primary_Variable"].max_row != expected_primary + 1 or table3["Primary_Variable"].max_column != expected_variable + 2:
        workbook_failures.append("Table3:primary_variable_shape")
    if table3["All_Haplotypes_All_Sites"].max_row != expected_all + 1 or table3["All_Haplotypes_All_Sites"].max_column != expected_variants + 4:
        workbook_failures.append("Table3:all_matrix_shape")
    for workbook in workbooks.values():
        workbook.close()
    add("publication_workbook_and_source_data_contract", not workbook_failures, workbook_failures)

    figure_manifest = read_tsv(result / "summary" / "figure_manifest.tsv")
    observed_contract = {
        row["relative_stem"]: (row["figure_kind"], row["parent_figure"])
        for row in figure_manifest
    }
    figure_counts = Counter(row["figure_kind"] for row in figure_manifest)
    manifest_ok = (
        observed_contract == expected_figures
        and len(figure_manifest) == int(config["target_figure_pair_count"])
        and figure_counts == Counter({
            "main_panel": int(config["main_panel_figure_count"]),
            "main_composite": int(config["main_composite_figure_count"]),
            "supplementary": int(config["supplementary_figure_count"]),
        })
    )
    add("exact_23_pair_figure_manifest", manifest_ok, dict(figure_counts))
    actual_pdf = {path.relative_to(result / "figures").with_suffix("").as_posix() for path in (result / "figures").rglob("*.pdf")}
    actual_png = {path.relative_to(result / "figures").with_suffix("").as_posix() for path in (result / "figures").rglob("*.png")}
    add(
        "no_extra_or_missing_figure_files",
        actual_pdf == set(expected_figures) and actual_png == set(expected_figures),
        {"pdf_extra": sorted(actual_pdf - set(expected_figures)), "png_extra": sorted(actual_png - set(expected_figures))},
    )
    decisions = read_tsv(result / "summary" / "figure_content_decisions.tsv")
    omitted = {row["legacy_figure"] for row in decisions if row["v4_role"] == "omitted"}
    forbidden_views = {"local_popgen_profiles", "all_filter"}
    add(
        "redundant_legacy_views_explicitly_omitted",
        omitted == forbidden_views and not any(any(term in stem for term in forbidden_views) for stem in expected_figures),
        omitted,
    )

    figure_missing: list[str] = []
    png_mismatch: list[str] = []
    png_dpi_failures: list[str] = []
    pdf_size_failures: list[str] = []
    text_failures: list[str] = []
    font_failures: list[str] = []
    italic_missing: list[str] = []
    vector_failures: list[str] = []
    gene_text_missing: list[str] = []
    combined_text = ""
    for row in figure_manifest:
        stem = result / "figures" / row["relative_stem"]
        pdf, png = stem.with_suffix(".pdf"), stem.with_suffix(".png")
        if not pdf.exists() or not png.exists():
            figure_missing.append(row["relative_stem"])
            continue
        expected_width = round(float(row["width_mm"]) / 25.4 * float(config["png_dpi"]))
        expected_height = round(float(row["height_mm"]) / 25.4 * float(config["png_dpi"]))
        with Image.open(png) as image:
            if abs(image.width - expected_width) > 2 or abs(image.height - expected_height) > 2:
                png_mismatch.append(f"{row['relative_stem']}:{image.width}x{image.height}!={expected_width}x{expected_height}")
            dpi = image.info.get("dpi")
            if not dpi or min(dpi) < float(config["png_dpi"]) - 1:
                png_dpi_failures.append(f"{row['relative_stem']}:{dpi}")
        info = subprocess.run(["pdfinfo", str(pdf)], text=True, capture_output=True)
        size_match = re.search(r"Page size:\s+([0-9.]+) x ([0-9.]+) pts", info.stdout)
        pages_match = re.search(r"Pages:\s+(\d+)", info.stdout)
        if info.returncode != 0 or not size_match or not pages_match:
            pdf_size_failures.append(f"{row['relative_stem']}:pdfinfo")
        else:
            width_mm = float(size_match.group(1)) / 72 * 25.4
            height_mm = float(size_match.group(2)) / 72 * 25.4
            if abs(width_mm - float(row["width_mm"])) > 0.3 or abs(height_mm - float(row["height_mm"])) > 0.3 or int(pages_match.group(1)) != 1:
                pdf_size_failures.append(f"{row['relative_stem']}:{width_mm:.2f}x{height_mm:.2f}mm")
        text_proc = subprocess.run(["pdftotext", str(pdf), "-"], text=True, capture_output=True)
        if text_proc.returncode != 0 or not text_proc.stdout.strip():
            text_failures.append(row["relative_stem"])
        elif config["gene_id"] not in text_proc.stdout:
            gene_text_missing.append(row["relative_stem"])
        combined_text += "\n" + text_proc.stdout
        font_proc = subprocess.run(["pdffonts", str(pdf)], text=True, capture_output=True)
        font_lines = [line for line in font_proc.stdout.splitlines()[2:] if line.strip()]
        allowed_font_tokens = ("arial", "times", "symbol", "zapfdingbats")
        for line in font_lines:
            tokens = line.split()
            name = tokens[0].split("+")[-1].lower() if tokens else ""
            embedded = len(tokens) >= 5 and tokens[-5].lower() == "yes"
            if not any(token in name for token in allowed_font_tokens) or not embedded:
                font_failures.append(f"{row['relative_stem']}:{line}")
        if not font_lines:
            font_failures.append(f"{row['relative_stem']}:no-fonts")
        italic_token = "Arial-Italic" if config["figure_font_family"] == "Arial" else "Times-Italic"
        if italic_token not in font_proc.stdout:
            italic_missing.append(row["relative_stem"])
        images_proc = subprocess.run(["pdfimages", "-list", str(pdf)], text=True, capture_output=True)
        embedded_images = [line for line in images_proc.stdout.splitlines()[2:] if line.strip()]
        if embedded_images:
            vector_failures.append(f"{row['relative_stem']}:{embedded_images}")
    add("figure_pdf_png_pairs", not figure_missing, figure_missing)
    add("png_600dpi_dimensions", not png_mismatch and not png_dpi_failures, {"size": png_mismatch, "dpi": png_dpi_failures})
    add("single_page_pdf_dimensions", not pdf_size_failures, pdf_size_failures)
    add("pdf_text_layers_and_gene_labels", not text_failures and not gene_text_missing, {"text": text_failures, "gene": gene_text_missing})
    add("embedded_arial_or_times_fonts_only", not font_failures, font_failures)
    add("italic_gene_font_embedded", not italic_missing, italic_missing)
    add("editable_vector_pdf_no_embedded_raster", not vector_failures, vector_failures)
    cjk = re.findall(r"[\u3400-\u9fff]", combined_text)
    add("figure_text_english_only", not cjk, sorted(set(cjk)))
    unexpected_chr = [
        term
        for number in range(1, 13)
        if str(number) != config["gene_chr_vcf"]
        for term in (f"Chr{number}", f"Chromosome {number}", f"chromosome {number}")
        if term in combined_text
    ]
    observed_gene_ids = set(re.findall(r"LOC_Os\d{2}g\d+", combined_text))
    unexpected_gene_ids = sorted(observed_gene_ids - {config["gene_id"]})
    add(
        "figure_chromosome_and_old_project_guard",
        not unexpected_chr and not unexpected_gene_ids,
        {"chromosome": unexpected_chr, "old_ids": unexpected_gene_ids},
    )

    visual = read_tsv(result / "summary" / "figure_visual_review.tsv")
    visual_ok = (
        len(visual) == len(expected_figures)
        and {row["relative_stem"] for row in visual} == set(expected_figures)
        and all(
            row["visual_status"] in {"PASS", "PASS_AFTER_FIX"}
            and row["review_focus"].strip()
            and row["action_taken"].strip()
            and Path(row["evidence_png"]).exists()
            for row in visual
        )
    )
    add("manual_publication_visual_review_23_figures", visual_ok, f"rows={len(visual)}")

    document_paths = [
        release / "README.md",
        release / "REPRODUCIBILITY.md",
        release / "manuscript" / "方法描述.md",
        release / "manuscript" / "Figure_Legends.md",
        release / "manuscript" / "Results_Discussion.md",
    ]
    documents_present = all(path.exists() and path.stat().st_size > 0 for path in document_paths)
    if documents_present:
        methods_text = (release / "manuscript" / "方法描述.md").read_text()
        results_text = (release / "manuscript" / "Results_Discussion.md").read_text()
        legends_text = (release / "manuscript" / "Figure_Legends.md").read_text()
        required_terms = ["retained complete-case cohort", "Newcombe", "Weir-Cockerham", "不能独立证明"]
        boundary_ok = (
            all(term in methods_text for term in required_terms)
            and "较低的局部区域 Fst" in results_text
            and "不应表述为整个区域存在强分化" in results_text
            and "points are not accession sampling coordinates" in legends_text
            and "v3" not in methods_text
        )
        add("manuscript_evidence_boundaries", boundary_ok, [term for term in required_terms if term not in methods_text])
    else:
        add("manuscript_evidence_boundaries", False, "release documents missing")

    release_required = [
        release / "figure" / "Fig1_HaplotypeArchitecture" / "Fig1_SourceData.xlsx",
        release / "figure" / "Fig1_HaplotypeArchitecture" / "Fig1_Legend.md",
        release / "figure" / "Fig2_PopulationGenetics" / "Fig2_SourceData.xlsx",
        release / "figure" / "Fig2_PopulationGenetics" / "Fig2_Legend.md",
        release / "figure" / "Supplementary" / "Supplementary_SourceData.xlsx",
        release / "table" / "Table1_HaplotypeSummary.xlsx",
        release / "table" / "Table2_XI_GJ_Differentiation.xlsx",
        release / "table" / "Table3_VariantMatrix.xlsx",
        release / "table" / "TableS1_PopulationGenetics.xlsx",
        release / "table" / "display_haplotype_NJ_tree.newick",
        release / "scripts" / "plot_publication_composite_v4.R",
        release / "scripts" / "qa_publication_composite_v4.py",
        release / "QA" / "project_contract.xlsx",
    ]
    if args.verify_only:
        release_required.append(release / "QA" / "formal_release_qa.xlsx")
    release_pdf = {path.relative_to(release / "figure").with_suffix("").as_posix() for path in (release / "figure").rglob("*.pdf")} if release.exists() else set()
    release_png = {path.relative_to(release / "figure").with_suffix("").as_posix() for path in (release / "figure").rglob("*.png")} if release.exists() else set()
    release_ok = (
        all(path.exists() and path.stat().st_size > 0 for path in release_required)
        and release_pdf == set(expected_figures)
        and release_png == set(expected_figures)
    )
    add("release_structure_and_per_figure_source_data", release_ok, [str(path) for path in release_required if not path.exists()])

    release_manifest = release / "QA" / "formal_release_file_manifest.tsv"
    if release_manifest.exists():
        manifest_rows = read_tsv(release_manifest)
        mismatches = [
            row["relative_path"]
            for row in manifest_rows
            if not (release / row["relative_path"]).exists() or sha256(release / row["relative_path"]) != row["sha256"]
        ]
        add("release_manifest_sha256", not mismatches, mismatches)
    else:
        add("release_manifest_sha256", False, "release manifest missing")

    if delivery.exists():
        try:
            with zipfile.ZipFile(delivery) as archive:
                bad_member = archive.testzip()
                names = archive.namelist()
            blocked = [name for name in names if Path(name).suffix.lower() in {".py", ".r", ".sh", ".log", ".tsv", ".vcf", ".gz"}]
            unsafe = [name for name in names if Path(name).is_absolute() or ".." in Path(name).parts]
            pdf_names = {str(Path(name).with_suffix("")) for name in names if name.endswith(".pdf")}
            png_names = {str(Path(name).with_suffix("")) for name in names if name.endswith(".png")}
            expected_zip_stems = {f"figure/{stem}" for stem in expected_figures}
            expected_png = expected_zip_stems if config.get("delivery_include_png", "FALSE").upper() == "TRUE" else set()
            qa_in_zip = "QA/formal_release_qa.xlsx" in names
            key_tables = {
                "table/Table1_HaplotypeSummary.xlsx",
                "table/Table2_XI_GJ_Differentiation.xlsx",
                "table/Table3_VariantMatrix.xlsx",
                "figure/Fig1_HaplotypeArchitecture/Fig1_SourceData.xlsx",
                "figure/Fig2_PopulationGenetics/Fig2_SourceData.xlsx",
            }
            zip_ok = (
                bad_member is None
                and not blocked
                and not unsafe
                and pdf_names == expected_zip_stems
                and png_names == expected_png
                and key_tables.issubset(names)
                and (qa_in_zip if args.verify_only else True)
            )
            add(
                "delivery_zip_integrity_and_exact_figure_count",
                zip_ok,
                f"members={len(names)} pdf={len(pdf_names)} png={len(png_names)} blocked={blocked} unsafe={unsafe} qa={qa_in_zip}",
            )
        except Exception as exc:
            add("delivery_zip_integrity_and_exact_figure_count", False, exc)
    else:
        add("delivery_zip_integrity_and_exact_figure_count", False, f"missing {delivery}")
    sidecar = delivery.parent / f"{delivery.name}.sha256"
    sidecar_ok = False
    if delivery.exists() and sidecar.exists():
        fields = sidecar.read_text().strip().split()
        sidecar_ok = len(fields) == 2 and fields[0] == sha256(delivery) and fields[1] == delivery.name
    add("delivery_zip_sha256_sidecar", sidecar_ok, str(sidecar))

    if not args.verify_only:
        write_qa(result / "summary" / "formal_release_qa", checks)
    for row in checks:
        print(f"{row['status']}\t{row['check']}\t{row['detail']}")
    failures = [row for row in checks if row["status"] != "PASS"]
    if failures:
        raise SystemExit(f"QA failed: {len(failures)} checks")
    print(f"[qa] PASS checks={len(checks)} verify_only={args.verify_only}")


if __name__ == "__main__":
    main()
