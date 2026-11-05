#!/usr/bin/env python3
"""Create deterministic grayscale and severe colour-vision review renders."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


MATRICES = {
    "protan": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "deutan": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "tritan": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


def write_variant(source: Path, destination: Path, mode: str) -> None:
    image = Image.open(source).convert("RGB")
    try:
        pixels = np.asarray(image, dtype=np.float32) / 255.0
        if mode == "grayscale":
            luminance = np.dot(pixels[..., :3], [0.2126, 0.7152, 0.0722])
            transformed = np.repeat(luminance[..., None], 3, axis=2)
        else:
            transformed = pixels @ MATRICES[mode].T
        Image.fromarray(np.clip(transformed * 255.0, 0, 255).astype(np.uint8)).save(
            destination, dpi=image.info.get("dpi", (600, 600))
        )
    finally:
        image.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-dir", required=True, type=Path)
    args = parser.parse_args()
    result = args.result_dir
    targets = [
        result / "figures/Fig1_Haplotype/Fig1_Haplotype.png",
        result / "figures/Fig1_Haplotype/panels/var_gene_vat_tab.png",
        result / "figures/Fig1_Haplotype/panels/major_network.png",
        result / "figures/Fig1_Haplotype/panels/all_accession_tree.png",
        result / "figures/Fig1_Haplotype/panels/major_area_map.png",
        result / "figures/Fig2_SelectionScan/Fig2_SelectionScan.png",
        result / "figures/Fig2_SelectionScan/panels/Pi_broad_local.png",
        result / "figures/Fig2_SelectionScan/panels/TajimaD_broad_local.png",
        result / "figures/Fig2_SelectionScan/panels/Fst_broad_local.png",
        result / "figures/Fig2_SelectionScan/panels/Pi_ratio_broad_local.png",
    ]
    out = result / "summary/visual_review_renders"
    out.mkdir(parents=True, exist_ok=True)
    for source in targets:
        if not source.is_file():
            raise SystemExit(f"missing review PNG: {source}")
        for mode in ("grayscale", "protan", "deutan", "tritan"):
            write_variant(source, out / f"{source.stem}_{mode}.png", mode)
    print(f"PASS\tvisual-review renders={len(targets) * 4}")


if __name__ == "__main__":
    main()
