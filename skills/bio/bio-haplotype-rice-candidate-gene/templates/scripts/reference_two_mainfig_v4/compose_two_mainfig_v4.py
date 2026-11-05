#!/usr/bin/env python3
"""Compose final-size vector Fig1 without shrinking panel typography."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter, Transformation


def read_config(path: Path) -> dict[str, str]:
    with path.open(newline="") as handle:
        return {row["field"]: row["value"] for row in csv.DictReader(handle, delimiter="\t")}


def image_xobject(obj: object) -> bool:
    obj = obj.get_object() if hasattr(obj, "get_object") else obj
    if not hasattr(obj, "get"):
        return False
    if obj.get("/Subtype") == "/Image":
        return True
    resources_ref = obj.get("/Resources")
    if resources_ref is None:
        return False
    resources = resources_ref.get_object() if hasattr(resources_ref, "get_object") else resources_ref
    xobjects_ref = resources.get("/XObject") if hasattr(resources, "get") else None
    if xobjects_ref is None:
        return False
    xobjects = xobjects_ref.get_object() if hasattr(xobjects_ref, "get_object") else xobjects_ref
    return any(image_xobject(value) for value in xobjects.values())


def panel_page(path: Path):
    document = PdfReader(path)
    if len(document.pages) != 1 or image_xobject(document.pages[0]):
        raise SystemExit(f"Panel is not a one-page pure-vector PDF: {path}")
    return document.pages[0]


def compose_pdf(inputs: list[Path], output: Path, width_mm: float, height_mm: float) -> None:
    width_pt = width_mm / 25.4 * 72
    height_pt = height_mm / 25.4 * 72
    margin = 12.0
    gap = 10.0
    inner_width = width_pt - 2 * margin
    pages = [panel_page(path) for path in inputs]
    panel_sizes = [(float(page.mediabox.width), float(page.mediabox.height)) for page in pages]
    top_height = panel_sizes[0][1]
    middle_height = max(panel_sizes[1][1], panel_sizes[3][1])
    bottom_height = panel_sizes[2][1]
    used_height = 2 * margin + 2 * gap + top_height + middle_height + bottom_height
    if abs(used_height - height_pt) > 1.5:
        raise SystemExit(f"Fig1 panel heights do not match declared final height: panels={used_height:.2f} page={height_pt:.2f}")
    for index, (panel_width, _) in enumerate(panel_sizes):
        maximum = inner_width if index in {0, 2} else (inner_width - gap) / 2
        if panel_width > maximum + 0.5:
            raise SystemExit(f"Fig1 panel {inputs[index]} exceeds its final-size cell; shrinking is forbidden")

    bottom_y = margin
    middle_y = bottom_y + bottom_height + gap
    top_y = middle_y + middle_height + gap
    positions = [
        (margin + (inner_width - panel_sizes[0][0]) / 2, top_y),
        (margin, middle_y),
        (margin + (inner_width - panel_sizes[2][0]) / 2, bottom_y),
        (width_pt - margin - panel_sizes[3][0], middle_y),
    ]
    writer = PdfWriter()
    target = writer.add_blank_page(width=width_pt, height=height_pt)
    for page, (x, y) in zip(pages, positions):
        target.merge_transformed_page(page, Transformation().translate(tx=x, ty=y))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as handle:
        writer.write(handle)
    check = PdfReader(output)
    if len(check.pages) != 1 or image_xobject(check.pages[0]):
        raise SystemExit("Fig1 composite failed the pure-vector one-page contract")


def compose_png(inputs: list[Path], output: Path, width_mm: float, height_mm: float, dpi: int) -> None:
    width_px = round(width_mm / 25.4 * dpi)
    height_px = round(height_mm / 25.4 * dpi)
    point_to_px = dpi / 72
    margin = round(12 * point_to_px)
    gap = round(10 * point_to_px)
    images = [Image.open(path).convert("RGB") for path in inputs]
    try:
        top_height = images[0].height
        middle_height = max(images[1].height, images[3].height)
        bottom_height = images[2].height
        used_height = 2 * margin + 2 * gap + top_height + middle_height + bottom_height
        if abs(used_height - height_px) > 4:
            raise SystemExit(f"Fig1 PNG panels do not match declared final height: panels={used_height} page={height_px}")
        inner_width = width_px - 2 * margin
        if images[0].width > inner_width + 2 or images[2].width > inner_width + 2:
            raise SystemExit("Full-width Fig1 PNG panel exceeds its final-size cell")
        if images[1].width + images[3].width + gap > inner_width + 2:
            raise SystemExit("Middle-row Fig1 PNG panels exceed their final-size cells")
        canvas = Image.new("RGB", (width_px, height_px), "white")
        top_y = margin
        middle_y = top_y + top_height + gap
        bottom_y = middle_y + middle_height + gap
        canvas.paste(images[0], ((width_px - images[0].width) // 2, top_y))
        canvas.paste(images[1], (margin, middle_y))
        canvas.paste(images[3], (width_px - margin - images[3].width, middle_y))
        canvas.paste(images[2], ((width_px - images[2].width) // 2, bottom_y))
        output.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(output, dpi=(dpi, dpi))
    finally:
        for image in images:
            image.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--fig1-panels", nargs=4, type=Path, required=True)
    parser.add_argument("--fig1-png-panels", nargs=4, type=Path, required=True)
    parser.add_argument("--fig1-output", type=Path, required=True)
    parser.add_argument("--fig1-png-output", type=Path, required=True)
    args = parser.parse_args()
    config = read_config(Path(args.config).resolve())
    compose_pdf(args.fig1_panels, args.fig1_output, float(config["figure_final_width_mm"]), float(config["fig1_final_height_mm"]))
    compose_png(
        args.fig1_png_panels, args.fig1_png_output,
        float(config["figure_final_width_mm"]), float(config["fig1_final_height_mm"]), int(config["png_dpi"]),
    )


if __name__ == "__main__":
    main()
