#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create contact sheets for manual publication review.")
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    args = parse_args()
    result_dir = Path(args.result_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_tsv(result_dir / "summary" / "figure_manifest.tsv")
    font_path = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
    font = ImageFont.truetype(str(font_path), 28) if font_path.exists() else ImageFont.load_default()
    cells_per_sheet = 4
    cell_width, cell_height = 1600, 1250
    for sheet_index in range(math.ceil(len(manifest) / cells_per_sheet)):
        rows = manifest[sheet_index * cells_per_sheet : (sheet_index + 1) * cells_per_sheet]
        canvas = Image.new("RGB", (cell_width * 2, cell_height * 2), "white")
        draw = ImageDraw.Draw(canvas)
        for index, row in enumerate(rows):
            png = result_dir / "figures" / f"{row['relative_stem']}.png"
            with Image.open(png) as source:
                image = source.convert("RGB")
                image.thumbnail((cell_width - 40, cell_height - 100), Image.Resampling.LANCZOS)
            left = (index % 2) * cell_width + (cell_width - image.width) // 2
            top = (index // 2) * cell_height + 70 + (cell_height - 100 - image.height) // 2
            canvas.paste(image, (left, top))
            draw.text(((index % 2) * cell_width + 20, (index // 2) * cell_height + 20), row["relative_stem"], fill="black", font=font)
        output = output_dir / f"figure_contact_sheet_{sheet_index + 1:02d}.png"
        canvas.save(output, dpi=(200, 200))
    print(f"[contact-sheets] figures={len(manifest)} sheets={math.ceil(len(manifest) / cells_per_sheet)}")


if __name__ == "__main__":
    main()
