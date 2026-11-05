#!/usr/bin/env python3
"""Contract QA for the read-only superrice two-main-figure derivative.

This validator intentionally checks table identities, not counts alone: all
retained accessions must be NJ tips, while network and centroid-map IDs must
be exactly the phased-copy major haplotype set.  It never reads raw genotype
matrices or modifies the validated source result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_config(path: Path) -> dict[str, str]:
    return {row["field"]: row["value"] for row in read_tsv(path)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ids(path: Path, field: str) -> set[str]:
    return {row[field] for row in read_tsv(path) if row.get(field, "")}


def parse_rapidnj_tip_names(path: Path) -> list[str]:
    """Read quoted or unquoted RapidNJ leaf labels without recursive tree traversal."""
    newick = path.read_text()
    if not newick.rstrip().endswith(";"):
        raise ValueError("Newick must end with a semicolon")
    tips = []
    for match in re.finditer(r"(?:^|[(,])(?:'((?:''|[^'])*)'|([^'():,;]+)):", newick):
        quoted, unquoted = match.groups()
        tips.append(quoted.replace("''", "'") if quoted is not None else unquoted.strip())
    if not tips:
        raise ValueError("Newick contains no leaf labels")
    return tips


def has_callable_mask_disclosure(wording: str) -> bool:
    lower = wording.lower()
    descriptive = "descriptive" in lower or "描述性" in wording
    return "callable" in lower and "tajima" in lower and "pi" in lower and descriptive


def pdffonts_rows(path: Path) -> list[list[str]]:
    completed = subprocess.run(["pdffonts", str(path)], check=True, capture_output=True, text=True)
    return [line.split() for line in completed.stdout.splitlines()[2:] if line.split()]


def poppler_word_boxes(path: Path) -> list[tuple[str, float, float, float, float]]:
    with tempfile.TemporaryDirectory(prefix="two-mainfig-v4-bbox-") as tmp:
        xml_path = Path(tmp) / "bbox.xml"
        subprocess.run(["pdftotext", "-bbox-layout", str(path), str(xml_path)], check=True, capture_output=True)
        root = ET.parse(xml_path).getroot()
    return [
        (
            (node.text or "").strip(), float(node.attrib["xMin"]), float(node.attrib["yMin"]),
            float(node.attrib["xMax"]), float(node.attrib["yMax"]),
        )
        for node in root.iter()
        if node.tag.endswith("word") and (node.text or "").strip()
    ]


def poppler_words(path: Path) -> list[tuple[str, float]]:
    return [(word, y_max - y_min) for word, _, y_min, _, y_max in poppler_word_boxes(path)]


def effective_pdf_text_runs(path: Path) -> list[tuple[str, float]]:
    """Return extracted nonempty text with its final-page effective point size."""
    from pypdf import PdfReader
    from pypdf._text_extraction import mult

    runs: list[tuple[str, float]] = []

    def visitor(text, cm, tm, font_dict, font_size):
        if not text.strip():
            return
        matrix = mult(tm, cm)
        effective_size = min(
            math.hypot(matrix[0], matrix[1]),
            math.hypot(matrix[2], matrix[3]),
        ) * font_size
        runs.append((text.strip(), effective_size))

    for page in PdfReader(path).pages:
        page.extract_text(visitor_text=visitor)
    return runs


def panel_label_effective_sizes(path: Path, expected: set[str]) -> dict[str, list[float]]:
    """Measure exact panel-label operands after every final-page transform."""
    from pypdf import PdfReader
    from pypdf._text_extraction import mult

    sizes = {label: [] for label in expected}
    identity = [1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
    for page in PdfReader(path).pages:
        ctm = identity.copy()
        stack: list[list[float]] = []
        tm = identity.copy()
        font_size = 1.0
        for operands, operator in page.get_contents().operations:
            if operator == b"q":
                stack.append(ctm.copy())
            elif operator == b"Q":
                ctm = stack.pop() if stack else identity.copy()
            elif operator == b"cm":
                ctm = mult([float(value) for value in operands[:6]], ctm)
            elif operator == b"Tm":
                tm = [float(value) for value in operands[:6]]
            elif operator == b"Tf":
                font_size = float(operands[1])
            elif operator == b"Tj" and str(operands[0]).strip() in expected:
                label = str(operands[0]).strip()
                matrix = mult(tm, ctm)
                sizes[label].append(
                    min(
                        math.hypot(matrix[0], matrix[1]),
                        math.hypot(matrix[2], matrix[3]),
                    ) * font_size
                )
    # Matplotlib can encode a label through a font-specific byte string that
    # pypdf decodes only in its high-level visitor.
    for label in expected:
        if not sizes[label]:
            sizes[label].extend(
                size for text, size in effective_pdf_text_runs(path) if text == label
            )
    return sizes


def fig2_axis_tick_overlaps(
    boxes: list[tuple[str, float, float, float, float]],
) -> list[str]:
    """Detect positive-area collisions between vertical y titles and numeric ticks."""
    numeric = re.compile(r"^[+-]?(?:\\d+(?:\\.\\d*)?|\\.\\d+)(?:e[+-]?\\d+)?$", re.I)
    axis_words = {"Pi", "Tajima's", "D", "Weighted", "Fst", "log2", "ratio"}
    failures: list[str] = []
    for title in (box for box in boxes if box[0] in axis_words):
        for tick in (box for box in boxes if numeric.fullmatch(box[0])):
            _, tx0, ty0, tx1, ty1 = title
            _, nx0, ny0, nx1, ny1 = tick
            x_overlap = min(tx1, nx1) - max(tx0, nx0)
            y_overlap = min(ty1, ny1) - max(ty0, ny0)
            if x_overlap > 0.25 and y_overlap > 0.25:
                failures.append(f"{title[0]}:{tick[0]}")
    return failures


def png_matches_pdf_physical_size(
    image_width: int,
    image_height: int,
    page_width_pt: float,
    page_height_pt: float,
    configured_dpi: int,
    minimum_width: int,
    tolerance_px: int = 4,
) -> bool:
    """Require PNG pixels to match the paired PDF physical size at configured DPI."""
    expected_width = round(page_width_pt / 72 * configured_dpi)
    expected_height = round(page_height_pt / 72 * configured_dpi)
    return (
        image_width >= minimum_width
        and abs(image_width - expected_width) <= tolerance_px
        and abs(image_height - expected_height) <= tolerance_px
    )


def manuscript_contract(manuscript: Path) -> tuple[bool, str]:
    try:
        methods = (manuscript / "材料与方法.md").read_text()
        results = (manuscript / "结果与分析.md").read_text()
        legends = (manuscript / "图注.md").read_text()
        references = (manuscript / "参考文献.md").read_text()
    except OSError as error:
        return False, f"missing manuscript file: {error}"
    required_methods = (
        "数据来源", "万份水稻变异图数据库", "MSU", "分析区间", "质量控制", "相位", "单倍型",
        "RapidNJ", "PLINK", "VCFtools", "Weir", "callable", "图形绘制", "Python", "R 4.5.2",
        "ape::plot.phylo", "ggplot2",
    )
    required_results = (
        "目标区域", "主要单倍型", "群体组成", "样本关系", "地理分布", "核苷酸多样性",
        "Tajima", "Fst", "不能", "描述性", "分母",
    )
    required_legends = (
        "分母", "相位染色体拷贝", "区域质心", "分支长度", "A_vs_B", "Pi_A / Pi_B",
        "callable", "Source Data",
    )
    missing = [f"methods:{term}" for term in required_methods if term not in methods]
    missing += [f"results:{term}" for term in required_results if term not in results]
    missing += [f"legends:{term}" for term in required_legends if term not in legends]
    if re.search(r"(?:/Users/|/home/|[A-Za-z]:\\\\)", methods + "\n" + results + "\n" + legends + "\n" + references):
        missing.append("manuscript:internal absolute path")
    if "ggtree" in methods:
        missing.append("methods:forbidden-unused-ggtree")
    if re.search(r"-\d(?:\.\d+)?--\d", results + "\n" + legends):
        missing.append("numeric-range:ambiguous-double-minus")
    for panel in "abcdefgh":
        if not re.search(rf"(?<![A-Za-z]){panel}(?:、|，|,|\.)", legends):
            missing.append(f"legend-panel:{panel}")
    shape_ok = (
        len(methods) >= 1800 and methods.count("## ") >= 5
        and len(results) >= 1800 and results.count("## ") >= 5
        and len(legends) >= 1400 and "**图1" in legends and "**图2" in legends
        and len(references) >= 500
    )
    return shape_ok and not missing, (
        f"chars={len(methods)}/{len(results)}/{len(legends)}/{len(references)} "
        f"sections={methods.count('## ')}/{results.count('## ')} missing={','.join(missing)}"
    )


def write_report(result_dir: Path, rows: list[tuple[str, bool, str]]) -> None:
    report = result_dir / "summary" / "reference_two_mainfig_v4_qa.tsv"
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=["check", "status", "detail"])
        writer.writeheader()
        writer.writerows({"check": key, "status": "PASS" if ok else "FAIL", "detail": detail} for key, ok, detail in rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate superrice_reference_two_mainfig_v4 evidence.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--result-dir", required=True)
    args = parser.parse_args()
    config = read_config(Path(args.config).resolve())
    project = Path(args.project_root).resolve()
    result = Path(args.result_dir).resolve()
    checks: list[tuple[str, bool, str]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append((name, passed, detail))

    add("formal_mode", config.get("formal_mode") == "superrice_reference_two_mainfig_v4", config.get("formal_mode", "missing"))
    try:
        minimum = int(config["major_haplotype_min_chromosome_count"])
    except (KeyError, ValueError):
        minimum = -1
    add("major_threshold_is_phased_copy_n_ge_30", minimum >= 30, str(minimum))

    immutable = result / "summary/source_allowlist_before.tsv"
    immutable_failures: list[str] = []
    immutable_paths: set[Path] = set()
    if immutable.exists():
        for row in read_tsv(immutable):
            source = Path(row["path"])
            immutable_paths.add(source.resolve())
            expected = row["sha256"]
            if not source.is_file() or sha256(source) != expected or source.stat().st_size != int(row["bytes"]):
                immutable_failures.append(str(source))
    else:
        immutable_failures.append("missing source_allowlist_before.tsv")
    source_root = Path(config.get("source_result_dir", "."));source_root=(source_root if source_root.is_absolute() else project/source_root).resolve()
    declared = [(source_root/item.strip()).resolve() for item in config.get("source_required_relpaths", "").split(",") if item.strip()]
    declared.extend((project/Path(config[key])).resolve() if not Path(config[key]).is_absolute() else Path(config[key]).resolve() for key in config.get("project_required_config_keys", "").split(",") if key)
    declared.extend(Path(config[key]).resolve() for key in config.get("external_required_config_keys", "").split(",") if key)
    declared.append(Path(args.config).resolve())
    for candidate in declared:
        if candidate not in immutable_paths:immutable_failures.append(f"not_fingerprinted:{candidate}")
    add("validated_base_read_only_sha256", not immutable_failures, ",".join(immutable_failures) or "all source fingerprints match")

    major_path = result / "haplotype/primary_haplotype_summary.tsv"
    major: set[str] = set()
    low_major: list[str] = []
    if major_path.exists():
        for row in read_tsv(major_path):
            hap = row.get("primary_haplotype_id", row.get("haplotype_id", ""))
            try:
                copies = int(row.get("haplotype_chromosome_count", row.get("phased_chromosome_copy_count", "")))
            except ValueError:
                copies = -1
            if hap:
                major.add(hap)
                if copies < minimum:
                    low_major.append(hap)
    frozen_ids=set(config.get("frozen_major_haplotype_ids","").split(','))-{''}
    frozen_counts=[int(x) for x in config.get("frozen_major_haplotype_copy_counts","").split(',') if x]
    observed_counts=[int(row.get("haplotype_chromosome_count","-1")) for row in read_tsv(major_path)] if major_path.exists() else []
    add("major_set_from_phased_copy_counts", bool(major) and not low_major and major==frozen_ids and observed_counts==frozen_counts, f"n={len(major)} below={','.join(low_major)} frozen={sorted(frozen_ids)}")

    retained_path = result / "tree/retained_accessions.tsv"
    newick_path = result / "tree/retained_accession_nj.newick"
    retained = ids(retained_path, "sample_id") if retained_path.exists() else set()
    tip_list: list[str] = []
    tree_error = ""
    try:
        tip_list = parse_rapidnj_tip_names(newick_path)
    except Exception as error:  # Biopython returns meaningful parsing errors.
        tree_error = str(error)
    tips = set(tip_list)
    tree_exact = bool(retained) and len(tip_list) == len(retained) == len(tips) and tips == retained
    add("tree_tip_exact_retained_accession_set", tree_exact, f"retained={len(retained)} tips_list={len(tip_list)} unique_tips={len(tips)} parse={tree_error}")

    annotation_path=result/"plot_data/sample_tree_reference_annotation.tsv"
    annotation=read_tsv(annotation_path) if annotation_path.exists() else []
    annotation_ids={row.get("sample_id","") for row in annotation}
    bad_diplotypes=[]
    for row in annotation:
        haps=set(re.findall(r"H\d{3,}",row.get("major_diplotype","")+"/"+row.get("raw_major_diplotype","")))
        if not haps<=major:bad_diplotypes.append(row.get("sample_id",""))
    group_counts={group:sum(row.get("population_group")==group for row in annotation) for group in ("XI","GJ","Or","Undefined")}
    expected_group_counts={group:int(config[f"expected_tree_{group}_accessions"]) for group in group_counts}
    ring_ok=(result/"plot_data/tree_ring_geometry.tsv").is_file() and (result/"plot_data/tree_tip_major_label.tsv").is_file()
    add("tree_annotation_major_diplotype_outer_ring",annotation_ids==retained and not bad_diplotypes and group_counts==expected_group_counts and ring_ok,f"annotation={len(annotation_ids)} bad={len(bad_diplotypes)} groups={group_counts} ring={ring_ok}")

    for label, name in (("network", "network_major_ids.tsv"), ("original_area_centroid_map", "map_major_ids.tsv"), ("allele_matrix", "matrix_major_ids.tsv")):
        candidate = result / "plot_data" / name
        observed = ids(candidate, "haplotype_id") if candidate.exists() else set()
        add(f"{label}_exact_major_set", bool(major) and observed == major, f"major={len(major)} observed={len(observed)}")

    mst_path = result / "tree/major_haplotype_mst_edges.tsv"
    edges = read_tsv(mst_path) if mst_path.exists() else []
    adjacency = {hap: set() for hap in major}
    edge_error = []
    for edge in edges:
        left = edge.get("hap_a", edge.get("from_haplotype_id", ""))
        right = edge.get("hap_b", edge.get("to_haplotype_id", ""))
        if left not in major or right not in major or left == right:
            edge_error.append(f"{left}:{right}")
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)
    visited = set()
    if major:
        stack = [next(iter(major))]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(adjacency[node] - visited)
    mst_ok = bool(major) and len(edges) == len(major) - 1 and not edge_error and visited == major
    add("major_mst_n_minus_1_and_connected", mst_ok, f"nodes={len(major)} edges={len(edges)} visited={len(visited)} bad={','.join(edge_error)}")

    cohort_path=result/"plot_data/cohort_population_counts.tsv";cohort=read_tsv(cohort_path) if cohort_path.exists() else []
    cohort_map={row.get("population_group",""):int(row.get("accession_count","-1")) for row in cohort}
    add("cohort_counts_include_total",cohort_map.get("Total")==int(config.get("expected_complete_accessions","-1")) and all(cohort_map.get(group)==count for group,count in expected_group_counts.items()),str(cohort_map))

    promoter_path=result/"plot_data/promoter_site_audit.tsv";promoter=read_tsv(promoter_path) if promoter_path.exists() else []
    source_variants=read_tsv(source_root/"haplotype"/f"{config['gene_id']}.superrice_variant_table.tsv")
    expected_promoter={row["variant_id"] for row in source_variants if row.get("feature_class","").lower()=="promoter"}
    observed_promoter={row.get("variant_id","") for row in promoter}
    add("all_post_qc_promoter_sites_audited",observed_promoter==expected_promoter,f"expected={len(expected_promoter)} observed={len(observed_promoter)}")

    window_path=result/"plot_data/selection_window_contract.tsv";windows=read_tsv(window_path) if window_path.exists() else []
    expected_windows={(metric,scope) for metric in ("Pi","TajimaD","Fst","Pi_ratio") for scope in ("broad","local")}
    observed_windows={(row.get("metric"),row.get("scope")) for row in windows}
    broad=(config.get("popgen_all_start"),config.get("popgen_all_end"));local=(config.get("popgen_filter_start"),config.get("popgen_filter_end"))
    window_ok=len(windows)==8 and observed_windows==expected_windows and all(int(row.get("window_count","0"))>0 and int(row.get("finite_value_count","0"))>0 and (row.get("start"),row.get("end"))==(broad if row.get("scope")=="broad" else local) and row.get("callable_mask")==config.get("popgen_callable_mask") for row in windows)
    add("selection_broad_local_contract",window_ok,f"rows={len(windows)} pairs={len(observed_windows)} broad={broad} local={local}")

    audit_path=Path(config.get("formal_haplotype_vcf_conversion_audit",""));audit_path=(audit_path if audit_path.is_absolute() else project/audit_path)
    vcf_path=Path(config.get("formal_haplotype_vcf",""));vcf_path=(vcf_path if vcf_path.is_absolute() else project/vcf_path)
    tbi_path=Path(config.get("formal_haplotype_vcf_tbi",""));tbi_path=(tbi_path if tbi_path.is_absolute() else project/tbi_path)
    popgen_vcf=Path(config.get("population_genetics_vcf",""));popgen_vcf=(popgen_vcf if popgen_vcf.is_absolute() else project/popgen_vcf)
    audit_metrics={row["metric"]:row["value"] for row in read_tsv(audit_path)} if audit_path.is_file() else {}
    formal_ok=vcf_path.is_file() and tbi_path.is_file() and audit_path.is_file() and vcf_path.resolve()!=popgen_vcf.resolve() and audit_metrics.get("vcf_sha256")==sha256(vcf_path) and audit_metrics.get("tbi_sha256")==sha256(tbi_path) and audit_metrics.get("samples")==config.get("expected_formal_vcf_samples") and audit_metrics.get("variant_records")==config.get("expected_post_qc_variant_count") and audit_metrics.get("SNP_records")==config.get("expected_post_qc_snp_count") and audit_metrics.get("InDel_records")==config.get("expected_post_qc_indel_site_count") and audit_metrics.get("multiallelic_records")==config.get("expected_formal_vcf_multiallelic_records") and audit_metrics.get("normalized_source_gt_sha256")==audit_metrics.get("normalized_vcf_gt_sha256") and audit_metrics.get("conversion_failures")=="0"
    add("formal_vcf_role_and_conversion_contract",formal_ok,f"formal={vcf_path.name} popgen={popgen_vcf.name} metrics={len(audit_metrics)}")

    manifest_path = result / "summary/figure_manifest.tsv"
    manifest = read_tsv(manifest_path) if manifest_path.exists() else []
    composites = [row for row in manifest if row.get("role") == "main_composite"]
    required_panels = {
        "Fig1_Haplotype/panels/var_gene_vat_tab", "Fig1_Haplotype/panels/major_network",
        "Fig1_Haplotype/panels/all_accession_tree", "Fig1_Haplotype/panels/major_area_map",
        "Fig2_SelectionScan/panels/Pi_broad_local", "Fig2_SelectionScan/panels/TajimaD_broad_local",
        "Fig2_SelectionScan/panels/Fst_broad_local", "Fig2_SelectionScan/panels/Pi_ratio_broad_local",
    }
    stems = {row.get("relative_stem", "") for row in manifest}
    composite_ok = len(composites) == 2 and {row.get("relative_stem") for row in composites} == {
        "Fig1_Haplotype/Fig1_Haplotype", "Fig2_SelectionScan/Fig2_SelectionScan"
    }
    add("exactly_two_nested_main_composites", composite_ok and required_panels <= stems, f"composites={len(composites)} missing_panels={len(required_panels - stems)}")

    review_path = result / "summary/figure_visual_review.tsv"
    reviews = read_tsv(review_path) if review_path.exists() else []
    review_ids = {row.get("relative_stem", "") for row in reviews}
    approved = {"PASS", "PASS_AFTER_FIX"}
    review_ok = bool(manifest) and review_ids == stems and len(reviews) == len(stems) and all(
        row.get("visual_status") in approved and row.get("review_focus", "").strip() and row.get("action_taken", "").strip()
        for row in reviews
    )
    add("manual_visual_review", review_ok, f"manifest={len(stems)} review={len(reviews)}")

    manuscript = result / "manuscript"
    scan_paths = [Path(args.config).resolve(), manifest_path]
    if manuscript.exists():
        scan_paths.extend(manuscript.rglob("*"))
    implementation_root = config.get("implementation_root", "").strip()
    if implementation_root:
        scan_paths.extend(Path(implementation_root).resolve().rglob("*"))
    wording = "\n".join(path.read_text(errors="replace") for path in scan_paths if path.is_file() and path.suffix.lower() in {".md", ".tsv", ".py", ".r", ".sh"})
    unexpected_genes = set(re.findall(r"LOC_Os\d{2}g\d{5}", wording)) - {config.get("gene_id", "")}
    expected_chr = config.get("gene_chr_vcf", "")
    bad_chromosomes = {value for value in re.findall(r"(?:Chromosome|Chr)\s*([0-9]{1,2})", wording) if value != expected_chr}
    add("generic_donor_residue_guard", not unexpected_genes and not bad_chromosomes, f"genes={sorted(unexpected_genes)} chr={sorted(bad_chromosomes)}")
    manuscript_ok, manuscript_detail = manuscript_contract(manuscript)
    add("chinese_manuscript_methods_results_legends", manuscript_ok, manuscript_detail)
    if "popgen_callable_mask" not in config:
        add("callable_mask_descriptive_wording", False, "missing config declaration")
    elif config.get("popgen_callable_mask") == "unavailable":
        wording_ok = has_callable_mask_disclosure(wording)
        add("callable_mask_descriptive_wording", wording_ok, "requires callable, Pi, Tajima, descriptive")
    else:
        add("callable_mask_descriptive_wording", True, "callable mask declared available")

    # Full render checks are only skipped by a synthetic test fixture. Real configs use TRUE.
    if config.get("enforce_pdf_asset_checks", "TRUE").upper() == "TRUE":
        try:
            from pypdf import PdfReader
            def has_image(obj):
                obj = obj.get_object()
                if not hasattr(obj, "get"):
                    return False
                if obj.get("/Subtype") == "/Image":
                    return True
                resource_ref=obj.get("/Resources")
                if resource_ref is None:return False
                resources=resource_ref.get_object();xobjects=resources.get("/XObject")
                if xobjects is None:return False
                return any(has_image(value) for value in xobjects.get_object().values())
            asset_errors: list[str] = []
            configured_dpi = int(config.get("png_dpi", "600"))
            minimum_width = int(config.get("minimum_figure_png_width_px", "1"))
            allowed_font = re.compile(r"(?:Arial|TimesNewRoman|TimesNew-Roman|TimesNew Roman)", re.I)
            word_floor = float(config.get("pdf_min_word_bbox_height_pt", "6.0"))
            text_floor = float(config.get("figure_min_font_pt", "8.5"))
            panel_floor = float(config.get("figure_panel_label_pt", "13"))
            main_size = (
                float(config.get("figure_final_width_mm", "180")) / 25.4 * 72,
                float(config.get("fig1_final_height_mm", "260")) / 25.4 * 72,
            )
            expected_labels = {
                "Fig1_Haplotype/Fig1_Haplotype": set("abcd"),
                "Fig2_SelectionScan/Fig2_SelectionScan": set("abcdefgh"),
            }
            for row in manifest:
                pdf = result / "figures" / f"{row['relative_stem']}.pdf"
                if not pdf.is_file():
                    asset_errors.append(f"missing:{pdf.name}")
                    continue
                document = PdfReader(pdf)
                if len(document.pages) != 1 or has_image(document.pages[0]):
                    asset_errors.append(f"not_vector:{pdf.name}")
                page_width_pt = float(document.pages[0].mediabox.width)
                page_height_pt = float(document.pages[0].mediabox.height)
                if row["relative_stem"] in expected_labels:
                    width = float(document.pages[0].mediabox.width)
                    height = float(document.pages[0].mediabox.height)
                    expected_height = (
                        float(config.get("fig1_final_height_mm", "260")) if row["relative_stem"].startswith("Fig1")
                        else float(config.get("fig2_final_height_mm", "260"))
                    ) / 25.4 * 72
                    if abs(width - main_size[0]) > 0.6 or abs(height - expected_height) > 0.6:
                        asset_errors.append(f"final_size:{pdf.name}:{width:.2f}x{height:.2f}")
                if not "".join(page.extract_text() or "" for page in document.pages):
                    asset_errors.append(f"no_text:{pdf.name}")
                text_layer = "\n".join(page.extract_text() or "" for page in document.pages)
                pdf_bad_genes = set(re.findall(r"LOC_Os\d{2}g\d{5}", text_layer)) - {config.get("gene_id", "")}
                pdf_bad_chromosomes = {value for value in re.findall(r"(?:Chromosome|Chr)\s*([0-9]{1,2})", text_layer) if value != expected_chr}
                if pdf_bad_genes or pdf_bad_chromosomes:
                    asset_errors.append(f"dynamic_label:{pdf.name}")
                if re.search(r"[\u3400-\u9fff]",text_layer):asset_errors.append(f"non_english_text:{pdf.name}")
                if row["relative_stem"].startswith("Fig1_Haplotype/panels/") and any(
                    hap not in major for hap in re.findall(r"\bH\d{3,}\b", text_layer)
                ):
                    asset_errors.append(f"nonmajor_hap_text:{pdf.name}")
                try:
                    fonts = pdffonts_rows(pdf)
                    if not fonts:
                        asset_errors.append(f"no_fonts:{pdf.name}")
                    for fields in fonts:
                        font_name = fields[0]
                        embedded = fields[-5] if len(fields) >= 8 else "no"
                        if not allowed_font.search(font_name) or "Type 3" in " ".join(fields) or embedded != "yes":
                            asset_errors.append(f"font:{pdf.name}:{font_name}:embedded={embedded}")
                    text_runs = effective_pdf_text_runs(pdf)
                    undersized = [(text, size) for text, size in text_runs if size + 0.01 < text_floor]
                    if undersized:
                        detail = ",".join(f"{text[:24]}={size:.2f}" for text, size in undersized[:8])
                        asset_errors.append(f"effective_font_size:{pdf.name}:{detail}")
                    boxes = poppler_word_boxes(pdf)
                    words = [(word, y_max - y_min) for word, _, y_min, _, y_max in boxes]
                    if not words:
                        asset_errors.append(f"no_poppler_words:{pdf.name}")
                    else:
                        heights = sorted(height for _, height in words)
                        percentile = heights[len(heights) // 100]
                        if percentile + 1e-6 < word_floor:
                            asset_errors.append(f"word_bbox:{pdf.name}:{percentile:.2f}")
                        expected = expected_labels.get(row["relative_stem"])
                        if expected:
                            counts = {label: sum(word == label for word, _ in words) for label in expected}
                            if any(count != 1 for count in counts.values()):
                                asset_errors.append(f"panel_labels:{pdf.name}:{counts}")
                            label_sizes = panel_label_effective_sizes(pdf, expected)
                            bad_labels = {
                                label: values for label, values in label_sizes.items()
                                if len(values) != 1 or values[0] + 0.01 < panel_floor
                            }
                            if bad_labels:
                                detail = ",".join(
                                    f"{label}={values[0]:.3f}" if len(values) == 1
                                    else f"{label}:count={len(values)}"
                                    for label, values in sorted(bad_labels.items())
                                )
                                asset_errors.append(f"panel_label_font_size:{pdf.name}:{detail}")
                    if row["relative_stem"].startswith("Fig2_SelectionScan"):
                        overlaps = fig2_axis_tick_overlaps(boxes)
                        if overlaps:
                            asset_errors.append(f"text_overlap:{pdf.name}:{','.join(overlaps[:12])}")
                except (OSError, subprocess.SubprocessError, ET.ParseError, ValueError) as error:
                    asset_errors.append(f"pdf_tooling:{pdf.name}:{error}")
                png = result / "figures" / f"{row['relative_stem']}.png"
                if not png.is_file():
                    asset_errors.append(f"missing:{png.name}")
                else:
                    from PIL import Image
                    with Image.open(png) as image:
                        dpi = image.info.get("dpi", (0, 0))[0]
                        if round(dpi) != configured_dpi or not png_matches_pdf_physical_size(
                            image.width, image.height, page_width_pt, page_height_pt,
                            configured_dpi, minimum_width,
                        ):
                            asset_errors.append(f"png_dpi_or_dimensions:{png.name}")
        except Exception as error:
            asset_errors = [f"pypdf:{error}"]
        add("vector_pdf_no_image_objects_and_text_layer", not asset_errors, ";".join(asset_errors))

    write_report(result, checks)
    for name, passed, detail in checks:
        print(f"{name}\t{'PASS' if passed else 'FAIL'}\t{detail}")
    return 0 if all(passed for _, passed, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
