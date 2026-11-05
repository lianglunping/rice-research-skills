#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

from Bio import Phylo


def main() -> None:
    sys.setrecursionlimit(50000)
    parser = argparse.ArgumentParser(description="Audit v5 accession-level RapidNJ tree tips and branch lengths.")
    parser.add_argument("--tree", required=True)
    parser.add_argument("--metadata", required=True)
    parser.add_argument("--expected-snps", required=True, type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with Path(args.metadata).open(newline="") as handle:
        metadata = list(csv.DictReader(handle, delimiter="\t"))
    expected = {row["sample_id"] for row in metadata}
    tree = Phylo.read(args.tree, "newick")
    tips = [tip.name for tip in tree.get_terminals()]
    lengths = [clade.branch_length for clade in tree.find_clades() if clade is not tree.root]
    finite = all(value is not None and math.isfinite(float(value)) and float(value) >= 0 for value in lengths)
    checks = {
        "tree_tip_count": len(tips),
        "tree_unique_tip_count": len(set(tips)),
        "metadata_tip_count": len(expected),
        "tree_tip_set_equals_metadata": str(set(tips) == expected).upper(),
        "nonnegative_finite_branch_lengths": str(finite).upper(),
        "tree_input_snp_count": args.expected_snps,
        "tree_method": f"{args.expected_snps}-site diploid allele-sharing 1-IBS + RapidNJ 2.3.3; PLINK biallelic-site cross-validation recorded separately",
        "tree_scope": "local sample-level IBS/NJ tree; not a genome-wide phylogeny",
    }
    if len(tips) != len(expected) or len(tips) != len(set(tips)) or set(tips) != expected or not finite:
        raise SystemExit(f"Sample tree audit failed: {checks}")
    with Path(args.output).open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=["metric", "value"])
        writer.writeheader()
        writer.writerows({"metric": key, "value": value} for key, value in checks.items())
    print(f"[tree-audit] tips={len(tips)} branches={len(lengths)}")


if __name__ == "__main__":
    main()
