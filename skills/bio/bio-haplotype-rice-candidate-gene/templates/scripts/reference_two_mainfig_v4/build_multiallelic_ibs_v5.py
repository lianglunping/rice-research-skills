#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from build_publication_tables_v5 import decode_allele_event


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def ibs_distance(encoded: np.ndarray) -> np.ndarray:
    count, site_count, _ = encoded.shape
    similarity = np.zeros((count, count), dtype=np.float32)
    for site in range(site_count):
        left = encoded[:, site, :]
        direct = (left[:, None, 0] == left[None, :, 0]).astype(np.int8) + (left[:, None, 1] == left[None, :, 1]).astype(np.int8)
        swapped = (left[:, None, 0] == left[None, :, 1]).astype(np.int8) + (left[:, None, 1] == left[None, :, 0]).astype(np.int8)
        similarity += np.maximum(direct, swapped) * 0.5
    distance = 1.0 - similarity / site_count
    np.fill_diagonal(distance, 0.0)
    return distance


def encode_signatures(signatures: list[tuple[tuple[str, str], ...]]) -> np.ndarray:
    site_count = len(signatures[0])
    encoded = np.empty((len(signatures), site_count, 2), dtype=np.int16)
    for site in range(site_count):
        allele_ids = {allele: index for index, allele in enumerate(sorted({value for signature in signatures for pair in [signature[site]] for value in pair}))}
        for index, signature in enumerate(signatures):
            encoded[index, site, 0] = allele_ids[signature[site][0]]
            encoded[index, site, 1] = allele_ids[signature[site][1]]
    return encoded


def write_matrix(path: Path, matrix: np.ndarray, ids: list[str], phylip: bool) -> None:
    with path.open("w") as handle:
        if phylip:
            handle.write(f"{len(ids)}\n")
        for sample_id, row in zip(ids, matrix):
            prefix = sample_id + " " if phylip else ""
            handle.write(prefix + " ".join(f"{float(value):.8g}" for value in row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute configured-site diploid allele-sharing 1-IBS distances and validate the biallelic subset against PLINK.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--source-result", required=True)
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--plink-mdist", required=True)
    parser.add_argument("--plink-ids", required=True)
    args = parser.parse_args()

    config = {row["field"]: row["value"] for row in read_tsv(Path(args.config))}
    source = Path(args.source_result)
    result = Path(args.result_dir)
    tree_dir = result / "tree"
    gene = config["gene_id"]
    variants = read_tsv(source / "haplotype" / f"{gene}.superrice_variant_table.tsv")
    snp_indices = [index for index, row in enumerate(variants) if row["variant_type"] == "SNP"]
    if len(snp_indices) != int(config["tree_expected_snps"]):
        raise SystemExit(f"Expected {config['tree_expected_snps']} SNP-tagged sites, observed {len(snp_indices)}")

    assignments = read_tsv(source / "haplotype" / f"{gene}.all_haplotype_sample_assignment.tsv")
    by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in assignments:
        by_sample[row["sample_id"]].append(row)
    ids = sorted(by_sample)
    if len(ids) != int(config["tree_expected_tips"]):
        raise SystemExit(f"Expected {config['tree_expected_tips']} complete accessions, observed {len(ids)}")

    sample_signatures: list[tuple[tuple[str, str], ...]] = []
    for sample_id in ids:
        copies = sorted(by_sample[sample_id], key=lambda row: int(row["chromosome_copy"]))
        if len(copies) != 2:
            raise SystemExit(f"Expected two chromosome copies for {sample_id}")
        patterns = [row["haplotype_pattern"].split(",") for row in copies]
        genotype: list[tuple[str, str]] = []
        for index in snp_indices:
            variant = variants[index]
            alleles = sorted(
                decode_allele_event(pattern[index], variant["REF"], variant["ALT"]).resolved_allele
                for pattern in patterns
            )
            genotype.append((alleles[0], alleles[1]))
        sample_signatures.append(tuple(genotype))

    unique_lookup: dict[tuple[tuple[str, str], ...], int] = {}
    unique_signatures: list[tuple[tuple[str, str], ...]] = []
    sample_to_unique: list[int] = []
    for signature in sample_signatures:
        if signature not in unique_lookup:
            unique_lookup[signature] = len(unique_signatures)
            unique_signatures.append(signature)
        sample_to_unique.append(unique_lookup[signature])
    encoded_unique = encode_signatures(unique_signatures)
    unique_distance = ibs_distance(encoded_unique)
    sample_index = np.asarray(sample_to_unique, dtype=np.int32)
    distance = unique_distance[np.ix_(sample_index, sample_index)]

    plink_ids = [line.split()[-1] for line in Path(args.plink_ids).read_text().splitlines() if line.strip()]
    if plink_ids != ids:
        raise SystemExit("PLINK sample order differs from deterministic retained-accession order")
    plink_distance = np.loadtxt(args.plink_mdist, dtype=np.float32)

    biallelic_indices = [
        offset for offset, source_index in enumerate(snp_indices)
        if len(variants[source_index]["REF"]) == 1
        and len(variants[source_index]["ALT"].split(",")) == 1
        and variants[source_index]["ALT"] != "*"
        and len(variants[source_index]["ALT"]) == 1
    ]
    if len(biallelic_indices) != int(config["tree_plink_biallelic_validation_snps"]):
        raise SystemExit(f"Expected {config['tree_plink_biallelic_validation_snps']} canonical biallelic SNPs, observed {len(biallelic_indices)}")
    validation_signatures = [tuple(signature[index] for index in biallelic_indices) for signature in unique_signatures]
    validation_unique = ibs_distance(encode_signatures(validation_signatures))
    validation_distance = validation_unique[np.ix_(sample_index, sample_index)]
    plink_max_abs_difference = float(np.abs(validation_distance - plink_distance).max())
    if plink_max_abs_difference > 1e-6:
        raise SystemExit(f"Biallelic 1-IBS extension disagrees with PLINK: max abs difference={plink_max_abs_difference}")

    basename = config["tree_basename"]
    mdist_path = tree_dir / f"{basename}_multiallelic_1ibs.mdist"
    ids_path = tree_dir / f"{basename}_multiallelic_1ibs.mdist.id"
    phylip_path = tree_dir / f"{basename}_multiallelic_1ibs.phylip"
    ids_path.write_text("".join(f"{sample_id}\t{sample_id}\n" for sample_id in ids))
    write_matrix(mdist_path, distance, ids, phylip=False)
    write_matrix(phylip_path, distance, ids, phylip=True)
    rows: list[dict[str, Any]] = [
        {"metric": "distance_sample_count", "value": len(ids)},
        {"metric": "post_qc_snp_count", "value": len(snp_indices)},
        {"metric": "unique_diploid_genotype_count", "value": len(unique_signatures)},
        {"metric": "canonical_biallelic_validation_snp_count", "value": len(biallelic_indices)},
        {"metric": "plink_validation_max_absolute_difference", "value": plink_max_abs_difference},
        {"metric": "distance_min", "value": float(distance.min())},
        {"metric": "distance_max", "value": float(distance.max())},
        {"metric": "distance_symmetry_absolute_max", "value": float(np.abs(distance - distance.T).max())},
        {"metric": "distance_diagonal_absolute_max", "value": float(np.abs(np.diag(distance)).max())},
        {"metric": "distance_definition", "value": f"mean over {config['tree_expected_snps']} loci of 1 - maximum unordered diploid allele matches/2"},
    ]
    with (tree_dir / "sample_tree_distance_audit.tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[tree-distance] samples={len(ids)} unique_genotypes={len(unique_signatures)} SNPs={len(snp_indices)} PLINK_delta={plink_max_abs_difference:.3g}")


if __name__ == "__main__":
    main()
