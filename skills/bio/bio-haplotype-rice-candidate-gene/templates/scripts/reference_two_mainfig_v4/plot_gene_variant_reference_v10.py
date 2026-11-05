#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/reference-split-v10-matplotlib")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrow, Rectangle


PRIMARY_IDS: list[str] = []
GENE_ID = ""
GROUPS = ["XI", "GJ", "Or", "Total"]
FONT_FAMILY = "Arial"
MIN_FONT = 8.5
BASE_FONT = 9.5
PANEL_FONT = 13.0


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def config(path: Path) -> dict[str, str]:
    return {row["field"]: row["value"] for row in read_tsv(path)}


def save_pair(fig: plt.Figure, output: Path, stem: str, width: float, height: float, dpi: int) -> None:
    fig.set_size_inches(width, height)
    fig.savefig(output / f"{stem}.pdf", format="pdf", facecolor="white", bbox_inches=None)
    fig.savefig(output / f"{stem}.png", format="png", dpi=dpi, facecolor="white", bbox_inches=None)
    plt.close(fig)


def layout_geometry(site_count: int) -> dict[str, float]:
    label_width = 2.30
    site_width = 0.70
    group_width = 1.12
    site_start = label_width
    site_end = site_start + site_count * site_width
    total_width = site_end + len(GROUPS) * group_width
    return {
        "label_width": label_width,
        "site_width": site_width,
        "group_width": group_width,
        "site_start": site_start,
        "site_end": site_end,
        "total_width": total_width,
    }


def gene_model_bounds(geometry: dict[str, float], align_to_table: bool) -> tuple[float, float]:
    if align_to_table:
        return 0.35, max(geometry["site_end"] - 0.10, 3.55)
    return 0.55, geometry["total_width"] - 0.55


def add_gene_title(fig: plt.Figure, y: float, suffix: str, fontsize: float | None = None) -> None:
    fontsize = 10.5 if fontsize is None else fontsize
    fig.text(0.5, y, GENE_ID, ha="right", va="center", family=FONT_FAMILY, style="italic", fontsize=fontsize)
    fig.text(0.5, y, suffix, ha="left", va="center", family=FONT_FAMILY, fontsize=fontsize)


def draw_gene_model(
    ax: plt.Axes,
    cfg: dict[str, str],
    sites: list[dict[str, str]],
    promoter: list[dict[str, str]],
    segments: list[dict[str, str]],
    geometry: dict[str, float],
    label_positions: bool,
    align_to_table: bool,
) -> None:
    gene_start, gene_end = int(cfg["gene_start"]), int(cfg["gene_end"])
    analysis_start, analysis_end = int(cfg["analysis_start"]), int(cfg["analysis_end"])
    x0, x1 = gene_model_bounds(geometry, align_to_table)
    span = analysis_end - analysis_start

    def gx(position: int) -> float:
        return x0 + (position - analysis_start) / span * (x1 - x0)

    y_gene = 0.69
    ax.plot([gx(int(cfg["promoter_start"])), gx(int(cfg["promoter_end"]))], [y_gene, y_gene], color="#8A8A8A", linewidth=1.2, linestyle=(0, (3, 2)))
    ax.plot([gx(gene_start), gx(gene_end)], [y_gene, y_gene], color="black", linewidth=1.5)
    for row in promoter:
        x = gx(int(row["POS"]))
        ax.plot([x, x], [y_gene - 0.055, y_gene + 0.055], color="#A8A8A8", linewidth=0.55, zorder=2)

    for segment in segments:
        feature = segment["feature_class"]
        if feature not in {"CDS", "5UTR", "3UTR"}:
            continue
        start, end = int(segment["start"]), int(segment["end"])
        left, right = gx(start), gx(end)
        if feature == "CDS":
            face, height = "black", 0.16
        else:
            face, height = "white", 0.13
        ax.add_patch(Rectangle((left, y_gene - height / 2), max(right - left, 0.015), height, facecolor=face, edgecolor="black", linewidth=1.0, zorder=3))
    if cfg["gene_strand"] == "+":
        ax.add_patch(FancyArrow(gx(gene_end) - 0.18, y_gene, 0.18, 0, width=0.012, head_width=0.095, head_length=0.13, length_includes_head=True, color="black", zorder=4))
    else:
        ax.add_patch(FancyArrow(gx(gene_start) + 0.18, y_gene, -0.18, 0, width=0.012, head_width=0.095, head_length=0.13, length_includes_head=True, color="black", zorder=4))

    centers = (
        [geometry["site_start"] + (index + 0.5) * geometry["site_width"] for index in range(len(sites))]
        if align_to_table
        else [x0 + (index + 1) / (len(sites) + 1) * (x1 - x0) for index in range(len(sites))]
    )
    for center, site in zip(centers, sites):
        x = gx(int(site["POS"]))
        color = "#009E60" if site["highlight_protein_altering"] == "True" else "#222222"
        ax.plot([x, center], [y_gene - 0.02, 0.15], color="#555555", linewidth=0.55, zorder=1)
        ax.scatter([x], [y_gene], s=14, facecolor=color, edgecolor="black", linewidth=0.35, zorder=5)
        if label_positions:
            ax.text(center, 0.115, site["POS"], rotation=90, ha="center", va="top", family=FONT_FAMILY, fontsize=MIN_FONT)

    promoter_diff = sum(row.get("differentiates_primary_haplotypes", "False") == "True" for row in promoter)
    primary_label = f"{PRIMARY_IDS[0]}-{PRIMARY_IDS[-1]}" if len(PRIMARY_IDS) > 1 else PRIMARY_IDS[0]
    promoter_note = f"Promoter: {len(promoter)} post-QC; {promoter_diff} variable in {primary_label}"
    if cfg["gene_strand"] == "+":
        ax.text(x0, 0.97, promoter_note, ha="left", va="center", family=FONT_FAMILY, fontsize=MIN_FONT, color="#555555")
        ax.text(x1, 0.82, "Primary transcript, 5' to 3'", ha="right", va="center", family=FONT_FAMILY, fontsize=MIN_FONT)
    else:
        ax.text(x1, 0.97, promoter_note, ha="right", va="center", family=FONT_FAMILY, fontsize=MIN_FONT, color="#555555")
        ax.text(x0, 0.82, "Primary transcript, 5' to 3'", ha="left", va="center", family=FONT_FAMILY, fontsize=MIN_FONT)
    ax.text(gx(gene_start), y_gene - 0.13, f"{gene_start:,}", ha="center", va="top", family=FONT_FAMILY, fontsize=MIN_FONT)
    ax.text(gx(gene_end), y_gene - 0.13, f"{gene_end:,}", ha="right", va="top", family=FONT_FAMILY, fontsize=MIN_FONT)
    if analysis_start != gene_start:
        ax.text(gx(analysis_start), y_gene - 0.13, f"{analysis_start:,}", ha="left", va="top", family=FONT_FAMILY, fontsize=MIN_FONT, color="#555555")
    if analysis_end != gene_end:
        ax.text(gx(analysis_end), y_gene - 0.13, f"{analysis_end:,}", ha="right", va="top", family=FONT_FAMILY, fontsize=MIN_FONT, color="#555555")
    legend = [
        Rectangle((0, 0), 1, 1, facecolor="black", edgecolor="black", label="CDS"),
        Rectangle((0, 0), 1, 1, facecolor="white", edgecolor="black", label="UTR"),
        Line2D([0], [0], color="#A8A8A8", linewidth=1.2, label="Screened promoter site"),
    ]
    if any(site["highlight_protein_altering"] == "True" for site in sites):
        legend.append(Line2D([0], [0], marker="o", color="none", markerfacecolor="#009E60", markeredgecolor="black", markersize=5, label="Protein-altering site"))
    ax.legend(handles=legend, loc="upper right", ncol=2, frameon=False, prop={"family": FONT_FAMILY, "size": MIN_FONT}, handlelength=1.0, columnspacing=0.8)
    ax.set_xlim(0, geometry["total_width"])
    ax.set_ylim(0, 1)
    ax.axis("off")


def draw_cell(ax: plt.Axes, x: float, y: float, width: float, height: float, face: str = "white", linewidth: float = 0.55) -> None:
    ax.add_patch(Rectangle((x, y), width, height, facecolor=face, edgecolor="#333333", linewidth=linewidth))


def draw_haplotype_table(
    ax: plt.Axes,
    sites: list[dict[str, str]],
    matrix: list[dict[str, str]],
    carrier: list[dict[str, str]],
    cohort: list[dict[str, str]],
    geometry: dict[str, float],
) -> None:
    position_h, effect_h, hap_h, cohort_h = 2.60, 2.40, 0.50, 0.50
    total_h = position_h + effect_h + len(PRIMARY_IDS) * hap_h + cohort_h
    top = total_h
    label_w, site_w, group_w = geometry["label_width"], geometry["site_width"], geometry["group_width"]
    site_start, site_end = geometry["site_start"], geometry["site_end"]

    y_position = top - position_h
    draw_cell(ax, 0, y_position, label_w, position_h)
    ax.text(label_w / 2, y_position + position_h / 2, "Physical\nposition", ha="center", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)
    for index, site in enumerate(sites):
        x = site_start + index * site_w
        face = "#00A651" if site["highlight_protein_altering"] == "True" else "white"
        draw_cell(ax, x, y_position, site_w, position_h, face=face)
        ax.text(x + site_w / 2, y_position + position_h / 2, site["POS"], rotation=90, ha="center", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)

    y_effect = y_position - effect_h
    draw_cell(ax, 0, y_effect, label_w, effect_h, face="#F2F2F2")
    ax.text(label_w / 2, y_effect + effect_h / 2, "Variant\neffect", ha="center", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)
    for index, site in enumerate(sites):
        x = site_start + index * site_w
        draw_cell(ax, x, y_effect, site_w, effect_h, face="#F2F2F2")
        ax.text(x + site_w / 2, y_effect + effect_h / 2, site["functional_label"], rotation=90, ha="center", va="center", family=FONT_FAMILY, fontsize=MIN_FONT, style="italic" if str(site["functional_label"]).startswith("p.") else "normal")

    group_x = site_end
    for index, group in enumerate(GROUPS):
        x = group_x + index * group_w
        draw_cell(ax, x, y_effect, group_w, position_h + effect_h, face="#F7F7F7")
        ax.text(x + group_w / 2, y_effect + (position_h + effect_h) / 2 + 0.12, group, ha="center", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)
        ax.text(x + group_w / 2, y_effect + 0.36, "carrier n", ha="center", va="center", family=FONT_FAMILY, fontsize=MIN_FONT, style="italic")

    matrix_by_hap = {row["primary_haplotype_id"]: row for row in matrix}
    carrier_by_hap = {row["primary_haplotype_id"]: row for row in carrier}
    y = y_effect
    for hap_index, hap in enumerate(PRIMARY_IDS):
        y -= hap_h
        face = "#EDEDED" if hap_index % 2 == 0 else "#F7F7F7"
        draw_cell(ax, 0, y, label_w, hap_h, face=face)
        ax.text(label_w * 0.80, y + hap_h / 2, hap, ha="right", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)
        row = matrix_by_hap[hap]
        for site_index, site in enumerate(sites):
            x = site_start + site_index * site_w
            draw_cell(ax, x, y, site_w, hap_h, face=face)
            ax.text(x + site_w / 2, y + hap_h / 2, row[site["site_label"]], ha="center", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)
        counts = carrier_by_hap[hap]
        for group_index, group in enumerate(GROUPS):
            x = group_x + group_index * group_w
            draw_cell(ax, x, y, group_w, hap_h, face=face)
            value = int(counts[group])
            ax.text(x + group_w / 2, y + hap_h / 2, f"{value:,}", ha="center", va="center", family=FONT_FAMILY, fontsize=MIN_FONT)

    cohort_by_group = {row["population_group"]: int(row["accession_count"]) for row in cohort}
    y -= cohort_h
    draw_cell(ax, 0, y, label_w, cohort_h, face="white")
    ax.text(label_w * 0.90, y + cohort_h / 2, "Cohort n", ha="right", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)
    draw_cell(ax, site_start, y, site_end - site_start, cohort_h, face="white")
    for group_index, group in enumerate(GROUPS):
        x = group_x + group_index * group_w
        draw_cell(ax, x, y, group_w, cohort_h, face="white")
        ax.text(x + group_w / 2, y + cohort_h / 2, f"{cohort_by_group[group]:,}", ha="center", va="center", family=FONT_FAMILY, weight="bold", fontsize=MIN_FONT)

    ax.set_xlim(0, geometry["total_width"])
    ax.set_ylim(0, total_h)
    ax.axis("off")


def main() -> None:
    parser = argparse.ArgumentParser(description="Draw reference-style gene structure and haplotype tables for v10.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--figure-dir", required=True)
    args = parser.parse_args()

    cfg = config(Path(args.config).resolve())
    global PRIMARY_IDS, GENE_ID, FONT_FAMILY, MIN_FONT, BASE_FONT, PANEL_FONT
    # The v4 major set is data-defined (phased chromosome copies >= configured
    # threshold); configs intentionally do not carry a stale comma-list.
    PRIMARY_IDS = [row["primary_haplotype_id"] for row in read_tsv(Path(args.result_dir) / "haplotype" / "primary_haplotype_summary.tsv")]
    GENE_ID = cfg["gene_id"]
    FONT_FAMILY = cfg["figure_font_family"]
    MIN_FONT = float(cfg["figure_min_font_pt"])
    BASE_FONT = float(cfg["figure_base_font_pt"])
    PANEL_FONT = float(cfg["figure_panel_label_pt"])
    result = Path(args.result_dir).resolve()
    output = Path(args.figure_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    sites = read_tsv(result / "plot_data" / "major_haplotype_display_sites.tsv")
    promoter = read_tsv(result / "plot_data" / "promoter_site_audit.tsv")
    segments = read_tsv(result / "plot_data" / "gene_feature_segments.tsv")
    matrix = read_tsv(result / "plot_data" / "major_haplotype_allele_matrix.tsv")
    carrier = read_tsv(result / "plot_data" / "haplotype_carrier_counts_by_population.tsv")
    cohort = read_tsv(result / "plot_data" / "cohort_population_counts.tsv")
    geometry = layout_geometry(len(sites))
    dpi = int(cfg["png_dpi"])

    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.unicode_minus": False,
    })

    fig_gene = plt.figure(figsize=(6.75, 1.5), facecolor="white")
    add_gene_title(fig_gene, 0.94, " promoter and gene-region variants")
    ax_gene = fig_gene.add_axes([0.025, 0.07, 0.95, 0.82])
    draw_gene_model(ax_gene, cfg, sites, promoter, segments, geometry, label_positions=True, align_to_table=False)
    save_pair(fig_gene, output, "var_gene", 6.75, 1.5, dpi)

    fig_table = plt.figure(figsize=(6.75, 2.4), facecolor="white")
    add_gene_title(fig_table, 0.965, " major-haplotype table")
    ax_table = fig_table.add_axes([0.025, 0.03, 0.95, 0.89])
    draw_haplotype_table(ax_table, sites, matrix, carrier, cohort, geometry)
    save_pair(fig_table, output, "vat_tab", 6.75, 2.4, dpi)

    fig_combined = plt.figure(figsize=(6.75, 2.83), facecolor="white")
    fig_combined.text(0.012, 0.982, "a", ha="left", va="top", family=FONT_FAMILY, weight="bold", fontsize=PANEL_FONT)
    add_gene_title(fig_combined, 0.975, " major-haplotype variation")
    ax_gene_c = fig_combined.add_axes([0.025, 0.66, 0.95, 0.25])
    draw_gene_model(ax_gene_c, cfg, sites, promoter, segments, geometry, label_positions=False, align_to_table=True)
    ax_table_c = fig_combined.add_axes([0.025, 0.035, 0.95, 0.62])
    draw_haplotype_table(ax_table_c, sites, matrix, carrier, cohort, geometry)
    save_pair(fig_combined, output, "var_gene_vat_tab", 6.75, 2.83, dpi)

    (result / "logs" / "matplotlib_plot_gene_variant_v10.txt").write_text(
        f"matplotlib={matplotlib.__version__}\nfont={FONT_FAMILY}\nmin_font_pt={MIN_FONT}\npanel_font_pt={PANEL_FONT}\npdf_fonttype=42\npng_dpi={dpi}\n"
    )
    promoter_diff = sum(row.get("differentiates_primary_haplotypes", "False") == "True" for row in promoter)
    print(f"[figure-v10] promoter={len(promoter)} promoter_diff={promoter_diff} sites={len(sites)} haps={len(matrix)}")


if __name__ == "__main__":
    main()
