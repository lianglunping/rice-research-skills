#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import shutil
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from PIL import Image
from scipy.stats import fisher_exact


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comprehensive QA for publication-compact superrice v3.")
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
    worksheet.column_dimensions["A"].width = 44
    worksheet.column_dimensions["B"].width = 12
    worksheet.column_dimensions["C"].width = 110
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
    checks: list[dict[str, str]] = []

    def add(name: str, ok: bool, detail: Any = "") -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "detail": str(detail)})

    required = [
        result / "haplotype" / "primary_haplotype_summary.tsv",
        result / "haplotype" / "all_haplotype_summary.tsv",
        result / "haplotype" / "XI_GJ_carrier_tests.tsv",
        result / "haplotype" / "primary_haplotype_threshold_audit.tsv",
        result / "plot_data" / "primary_variable_site_summary.tsv",
        result / "plot_data" / "all_haplotype_all_site_allele_matrix.tsv",
        result / "popgen" / "XI_GJ_site_differentiation.tsv",
        result / "tree" / "primary_haplotype_mst_edges.tsv",
        result / "tree" / "primary_haplotype_NJ_tree.newick",
        result / "summary" / "source_provenance.tsv",
        result / "summary" / "figure_manifest.tsv",
        result / "summary" / "figure_visual_review.tsv",
        result / "tables" / "Table1_HaplotypeSummary.xlsx",
        result / "tables" / "Table3_VariantMatrix.xlsx",
    ]
    missing = [str(path) for path in required if not path.exists() or path.stat().st_size == 0]
    add("required_files", not missing, f"missing={missing}")

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

    key = metric_dict(result / "summary" / "publication_compact_key_metrics.tsv")
    expected_complete = int(config["expected_complete_accessions"])
    expected_chromosomes = int(config["expected_haplotype_chromosomes"])
    expected_xi = int(config["expected_XI_complete_accessions"])
    expected_gj = int(config["expected_GJ_complete_accessions"])
    expected_primary = int(config["expected_primary_haplotype_count"])
    expected_all = int(config["expected_all_haplotype_count"])
    expected_variants = int(config["expected_post_qc_variant_count"])
    expected_metrics = {
        "all_haplotype_count": config["expected_all_haplotype_count"],
        "primary_haplotype_count": config["expected_primary_haplotype_count"],
        "primary_variable_site_count": config["expected_primary_variable_site_count"],
    }
    metric_mismatch = {name: (key.get(name), expected) for name, expected in expected_metrics.items() if int(float(key.get(name, -1))) != int(expected)}
    add("expected_haplotype_and_site_counts", not metric_mismatch, metric_mismatch)
    add(
        "complete_cohort_contract",
        int(key["source_complete_samples"]) == expected_complete
        and int(key["source_haplotype_chromosomes"]) == expected_chromosomes
        and expected_chromosomes == 2 * expected_complete,
        key,
    )

    source_variants = read_tsv(source / "haplotype" / f"{config['gene_id']}.superrice_variant_table.tsv")
    add("post_qc_variant_count", len(source_variants) == expected_variants, len(source_variants))
    all_summary = read_tsv(result / "haplotype" / "all_haplotype_summary.tsv")
    primary = read_tsv(result / "haplotype" / "primary_haplotype_summary.tsv")
    add(
        "primary_ids",
        [row["primary_haplotype_id"] for row in primary]
        == [f"H{index:03d}" for index in range(1, expected_primary + 1)],
        [row["primary_haplotype_id"] for row in primary],
    )

    threshold = read_tsv(result / "haplotype" / "primary_haplotype_threshold_audit.tsv")
    threshold_failures = []
    minimum_carriers = int(config["primary_haplotype_min_carrier_accessions"])
    minimum_frequency = float(config["primary_haplotype_subgroup_chr_frequency_min"])
    for row in threshold:
        expected = int(row["carrier_accession_count"]) >= minimum_carriers and max(
            float(row["XI_chromosome_frequency"]), float(row["GJ_chromosome_frequency"])
        ) > minimum_frequency
        if (row["selected_primary"] == "TRUE") != expected:
            threshold_failures.append(row["all_haplotype_id"])
    synthetic_rule_ok = (
        not (minimum_carriers >= minimum_carriers and max(minimum_frequency, 0.0) > minimum_frequency)
        and (
            minimum_carriers >= minimum_carriers
            and max(math.nextafter(minimum_frequency, math.inf), 0.0) > minimum_frequency
        )
        and not (minimum_carriers - 1 >= minimum_carriers and max(0.9, 0.0) > minimum_frequency)
    )
    add("strict_primary_threshold_recomputed", not threshold_failures and synthetic_rule_ok, threshold_failures)

    assignment_source = read_tsv(source / "haplotype" / f"{config['gene_id']}.all_haplotype_sample_assignment.tsv")
    manifest = {row["sample_id"]: row for row in read_tsv(source / "haplotype" / f"{config['gene_id']}.superrice_sample_manifest_detailed.tsv")}
    copy_counts: dict[str, int] = defaultdict(int)
    carrier_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in assignment_source:
        copy_counts[row["sample_id"]] += 1
        group = manifest[row["sample_id"]]["detailed_group"]
        carrier_by_group[(row["all_haplotype_id"], group)].add(row["sample_id"])
    add(
        "two_chromosome_copies_per_complete_accession",
        len(copy_counts) == expected_complete and set(copy_counts.values()) == {2},
        {"samples": len(copy_counts), "copy_counts": sorted(set(copy_counts.values()))},
    )

    tests = read_tsv(result / "haplotype" / "XI_GJ_carrier_tests.tsv")
    p_values: list[float] = []
    test_failures = []
    for row in tests:
        all_id = row["all_haplotype_id"]
        xi = len(carrier_by_group[(all_id, "XI")])
        gj = len(carrier_by_group[(all_id, "GJ")])
        table = [[xi, expected_xi - xi], [gj, expected_gj - gj]]
        p_value = float(fisher_exact(table, alternative="two-sided").pvalue)
        p_values.append(p_value)
        low, high = newcombe(xi, expected_xi, gj, expected_gj)
        if xi != int(row["XI_carrier_accessions"]) or gj != int(row["GJ_carrier_accessions"]):
            test_failures.append(f"{row['primary_haplotype_id']}:carrier")
        if not math.isclose(p_value, float(row["fisher_exact_p"]), rel_tol=1e-11, abs_tol=1e-300):
            test_failures.append(f"{row['primary_haplotype_id']}:fisher")
        if not math.isclose(low, float(row["rate_difference_CI_low"]), rel_tol=1e-11) or not math.isclose(high, float(row["rate_difference_CI_high"]), rel_tol=1e-11):
            test_failures.append(f"{row['primary_haplotype_id']}:CI")
    expected_q = bh_adjust(p_values)
    for row, q_value in zip(tests, expected_q):
        if not math.isclose(q_value, float(row["BH_q"]), rel_tol=1e-11, abs_tol=1e-300):
            test_failures.append(f"{row['primary_haplotype_id']}:BH")
    add("accession_fisher_bh_newcombe_recomputed", not test_failures, test_failures)

    variable_sites = read_tsv(result / "plot_data" / "primary_variable_site_summary.tsv")
    annotation_failures = [
        row["variant_id"]
        for row in variable_sites
        if not row["coding_consequence"].strip()
        or len({item for item in row["observed_primary_alleles"].split(",") if item}) < 2
        or row["protein_altering"] not in {"TRUE", "FALSE"}
    ]
    add("variable_site_annotation_contract", not annotation_failures, annotation_failures)
    matrix_rows = read_tsv(result / "plot_data" / "all_haplotype_all_site_allele_matrix.tsv")
    add(
        "full_unfiltered_matrix_shape",
        len(matrix_rows) == expected_all and len(matrix_rows[0]) == 4 + expected_variants,
        f"rows={len(matrix_rows)} columns={len(matrix_rows[0])}",
    )

    edges = read_tsv(result / "tree" / "primary_haplotype_mst_edges.tsv")
    add("mst_edge_count", len(edges) == expected_primary - 1, len(edges))
    try:
        from Bio import Phylo

        tree = Phylo.read(result / "tree" / "primary_haplotype_NJ_tree.newick", "newick")
        tips = {tip.name for tip in tree.get_terminals()}
        add("nj_tip_contract", tips == {row["primary_haplotype_id"] for row in primary}, sorted(tips))
    except Exception as exc:
        add("nj_tip_contract", False, exc)

    site_fst_raw = read_tsv(result / "popgen" / "vcftools_raw" / "XI_vs_GJ.site.weir.fst")
    site_rows = read_tsv(result / "popgen" / "XI_GJ_site_differentiation.tsv")
    finite_fst = [float(row["site_Weir_Cockerham_Fst"]) for row in site_rows if math.isfinite(as_float(row["site_Weir_Cockerham_Fst"]))]
    fst_range_ok = finite_fst and min(finite_fst) >= -1 and max(finite_fst) <= 1
    script_text = (project_root / "scripts" / "publication_compact_v3" / "run_xi_gj_site_fst_v3.sh").read_text()
    fst_range_detail = (
        f"({min(finite_fst):.6g},{max(finite_fst):.6g})" if finite_fst else "unavailable"
    )
    add(
        "vcftools_site_fst_no_maf",
        bool(site_fst_raw) and fst_range_ok and "--weir-fst-pop" in script_text and "--maf" not in script_text,
        f"raw={len(site_fst_raw)} finite={len(finite_fst)} range={fst_range_detail}",
    )

    table1 = load_workbook(result / "tables" / "Table1_HaplotypeSummary.xlsx", read_only=True, data_only=True)
    table3 = load_workbook(result / "tables" / "Table3_VariantMatrix.xlsx", read_only=True, data_only=True)
    required_sheets = {"Publication_Table", "Primary_Haplotypes", "Top20_HaplotypeCounts", "All_Haplotypes", "Subgroup_Frequencies"}
    workbook_ok = required_sheets.issubset(table1.sheetnames) and table1["Top20_HaplotypeCounts"].max_row == min(20, expected_all) + 1
    workbook_ok = workbook_ok and table3["Primary_Variable"].max_row == expected_primary + 1
    workbook_ok = workbook_ok and table3["Primary_Variable"].max_column == int(config["expected_primary_variable_site_count"]) + 2
    workbook_ok = workbook_ok and table3["All_Haplotypes_All_Sites"].max_row == expected_all + 1
    workbook_ok = workbook_ok and table3["All_Haplotypes_All_Sites"].max_column == expected_variants + 4
    add("publication_workbook_contract", workbook_ok, {"Table1": table1.sheetnames, "Table3": table3.sheetnames})
    table1.close()
    table3.close()

    figure_manifest = read_tsv(result / "summary" / "figure_manifest.tsv")
    figure_counts = defaultdict(int)
    for row in figure_manifest:
        figure_counts[row["figure_kind"]] += 1
    expected_figure_counts = {
        "main_panel": int(config["main_panel_figure_count"]),
        "main_composite": int(config["main_composite_figure_count"]),
        "supplementary": int(config["supplementary_figure_count"]),
    }
    pair_contract = (
        len(figure_manifest) == int(config["target_figure_pair_count"])
        and dict(figure_counts) == expected_figure_counts
    )
    add("figure_manifest_contract", pair_contract, dict(figure_counts))

    figure_missing = []
    png_mismatch = []
    text_failures = []
    font_failures = []
    vector_failures = []
    combined_text = ""
    for row in figure_manifest:
        stem = result / "figures" / row["relative_stem"]
        pdf, png = stem.with_suffix(".pdf"), stem.with_suffix(".png")
        if not pdf.exists() or not png.exists():
            figure_missing.append(row["relative_stem"])
            continue
        with Image.open(png) as image:
            expected_width = round(float(row["width_mm"]) / 25.4 * float(config["png_dpi"]))
            expected_height = round(float(row["height_mm"]) / 25.4 * float(config["png_dpi"]))
            if abs(image.width - expected_width) > 2 or abs(image.height - expected_height) > 2:
                png_mismatch.append(f"{row['relative_stem']}:{image.width}x{image.height}!={expected_width}x{expected_height}")
        text_proc = subprocess.run(["pdftotext", str(pdf), "-"], text=True, capture_output=True)
        if text_proc.returncode != 0 or not text_proc.stdout.strip():
            text_failures.append(row["relative_stem"])
        combined_text += "\n" + text_proc.stdout
        font_proc = subprocess.run(["pdffonts", str(pdf)], text=True, capture_output=True)
        font_lines = [line for line in font_proc.stdout.splitlines()[2:] if line.strip()]
        configured_font = config["figure_font_family"].replace(" ", "")
        font_aliases = ["Arial"] if configured_font.lower() == "arial" else [configured_font, "TimesNewRoman", "Times-Roman"]
        if not font_lines or any(
            not any(alias in line.split()[0].replace(" ", "") for alias in font_aliases)
            or " yes " not in f" {line} "
            for line in font_lines
        ):
            font_failures.append(f"{row['relative_stem']}:{font_lines}")
        images_proc = subprocess.run(["pdfimages", "-list", str(pdf)], text=True, capture_output=True)
        embedded = [line for line in images_proc.stdout.splitlines()[2:] if line.strip()]
        if embedded:
            vector_failures.append(f"{row['relative_stem']}:{embedded}")
    add("figure_pdf_png_pairs", not figure_missing, figure_missing)
    add("png_600dpi_dimensions", not png_mismatch, png_mismatch)
    add("pdf_text_layers", not text_failures, text_failures)
    add("pdf_embedded_arial_only", not font_failures, font_failures)
    add("editable_vector_pdf_no_embedded_raster", not vector_failures, vector_failures)
    cjk = re.findall(r"[\u3400-\u9fff]", combined_text)
    add("figure_text_english_only", not cjk, sorted(set(cjk)))
    unexpected_chr = [term for number in range(1, 13) if str(number) != config["gene_chr_vcf"] for term in (f"Chr{number}", f"Chromosome {number}", f"chromosome {number}") if term in combined_text]
    observed_gene_ids = set(re.findall(r"LOC_Os\d{2}g\d{5}", combined_text))
    unexpected_gene_ids = sorted(observed_gene_ids - {config["gene_id"]})
    add(
        "figure_chromosome_and_old_project_guard",
        not unexpected_chr and not unexpected_gene_ids,
        {"chromosome": unexpected_chr, "gene_ids": unexpected_gene_ids},
    )
    italic_targets = [row for row in figure_manifest if row["relative_stem"].endswith(("Fig1_HaplotypeArchitecture_XI_GJ", "Fig1a_HaplotypeMatrix", "Fig2_HaplotypeRelationships_XI_GJ", "Fig2b_SiteDifferentiation"))]
    italic_missing = []
    for row in italic_targets:
        pdf = result / "figures" / f"{row['relative_stem']}.pdf"
        fonts = subprocess.run(["pdffonts", str(pdf)], text=True, capture_output=True).stdout
        italic_aliases = ["Arial-Italic"] if config["figure_font_family"].lower() == "arial" else ["TimesNewRomanPS-Italic", "Times-Italic"]
        if not any(alias in fonts for alias in italic_aliases):
            italic_missing.append(row["relative_stem"])
    add("italic_gene_font_embedded", not italic_missing, italic_missing)

    visual = read_tsv(result / "summary" / "figure_visual_review.tsv")
    visual_ok = len(visual) == len(figure_manifest) and {row["relative_stem"] for row in visual} == {row["relative_stem"] for row in figure_manifest} and all(row["visual_status"] in {"PASS", "PASS_AFTER_FIX"} and row["review_focus"] and row["action_taken"] for row in visual)
    add("manual_publication_visual_review", visual_ok, f"rows={len(visual)}")

    methods_path = release / "manuscript" / "方法描述.md"
    results_path = release / "manuscript" / "Results_Discussion.md"
    if methods_path.exists() and results_path.exists():
        methods_text = methods_path.read_text()
        results_text = results_path.read_text()
        terms = ["retained complete-case cohort", "Newcombe", "Weir-Cockerham", "不能独立证明"]
        evidence_ok = all(term in methods_text for term in terms) and "较低的局部区域 Fst" in results_text and "强分化" in results_text
        add("manuscript_evidence_boundaries", evidence_ok, [term for term in terms if term not in methods_text])
    else:
        add("manuscript_evidence_boundaries", False, "release manuscript missing")

    release_manifest = release / "QA" / "formal_release_file_manifest.tsv"
    if release_manifest.exists():
        manifest_rows = read_tsv(release_manifest)
        mismatches = [row["relative_path"] for row in manifest_rows if not (release / row["relative_path"]).exists() or sha256(release / row["relative_path"]) != row["sha256"]]
        add("release_manifest_sha256", not mismatches, mismatches)
    else:
        add("release_manifest_sha256", False, "release manifest missing")

    if delivery.exists():
        try:
            with zipfile.ZipFile(delivery) as archive:
                bad_member = archive.testzip()
                names = archive.namelist()
            blocked = [name for name in names if Path(name).suffix.lower() in {".py", ".r", ".sh", ".log", ".tsv", ".vcf", ".gz"}]
            pdf_count = sum(name.endswith(".pdf") for name in names)
            png_count = sum(name.endswith(".png") for name in names)
            qa_in_zip = any(name.endswith("formal_release_qa.xlsx") for name in names)
            expected_pairs = int(config["target_figure_pair_count"])
            expected_png = expected_pairs if config.get("delivery_include_png", "FALSE").upper() == "TRUE" else 0
            zip_ok = bad_member is None and not blocked and pdf_count == expected_pairs and png_count == expected_png
            if args.verify_only:
                zip_ok = zip_ok and qa_in_zip
            add("delivery_zip_integrity", zip_ok, f"members={len(names)} pdf={pdf_count} png={png_count} blocked={blocked} qa={qa_in_zip}")
        except Exception as exc:
            add("delivery_zip_integrity", False, exc)
    else:
        add("delivery_zip_integrity", False, f"missing {delivery}")

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
