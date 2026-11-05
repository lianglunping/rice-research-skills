#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Any


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare exact retained-accession and post-QC SNP lists for the v5 IBS tree.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--source-result", required=True)
    parser.add_argument("--result-dir", required=True)
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    source = Path(args.source_result).resolve()
    result = Path(args.result_dir).resolve()
    config = {row["field"]: row["value"] for row in read_tsv(config_path)}
    gene = config["gene_id"]
    tree_dir = result / "tree"
    tree_dir.mkdir(parents=True, exist_ok=True)

    diplotypes_path = result / "haplotype" / "accession_indel_diplotype.tsv"
    diplotypes = read_tsv(diplotypes_path)
    samples = sorted({row["sample_id"] for row in diplotypes})
    if len(samples) != int(config["tree_expected_tips"]):
        raise SystemExit(f"Expected {config['tree_expected_tips']} retained accessions, observed {len(samples)}")

    variants_path = source / "haplotype" / f"{gene}.superrice_variant_table.tsv"
    variants = read_tsv(variants_path)
    snps = [row for row in variants if row["variant_type"] == "SNP"]
    if len(snps) != int(config["tree_expected_snps"]):
        raise SystemExit(f"Expected {config['tree_expected_snps']} post-QC SNPs, observed {len(snps)}")

    sample_path = tree_dir / "retained_accessions.list"
    sample_path.write_text("\n".join(samples) + "\n")
    region_path = tree_dir / "post_qc_snp_regions.tsv"
    region_path.write_text("".join(f"{config['gene_chr_vcf']}\t{row['POS']}\t{row['POS']}\n" for row in snps))

    tip_fields = [
        "sample_id", "detailed_group", "species_information", "indel_diplotype_class",
        "chromosome1_indel_class", "chromosome2_indel_class", "chromosome1_backbone_id",
        "chromosome2_backbone_id", "backbone_diplotype", "chromosome1_all_haplotype_id",
        "chromosome2_all_haplotype_id", "chromosome1_primary_haplotype_id", "chromosome2_primary_haplotype_id",
    ]
    write_tsv(tree_dir / "sample_tree_tip_metadata.tsv", diplotypes, tip_fields)
    audit = [
        {"metric": "retained_accession_count", "value": len(samples)},
        {"metric": "post_qc_snp_count", "value": len(snps)},
        {"metric": "sample_list_sha256", "value": digest(sample_path)},
        {"metric": "snp_region_list_sha256", "value": digest(region_path)},
        {"metric": "source_variant_table_sha256", "value": digest(variants_path)},
        {"metric": "accession_diplotype_sha256", "value": digest(diplotypes_path)},
    ]
    write_tsv(tree_dir / "sample_tree_input_audit.tsv", audit, ["metric", "value"])
    print(f"[tree-input] accessions={len(samples)} snps={len(snps)}")


if __name__ == "__main__":
    main()
