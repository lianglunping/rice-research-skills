#!/usr/bin/env python3
"""
Extract a gene-region genotype matrix from the superrice wide genotype tables.

Input genotype files are tab-delimited gzip files with:
CHROM POS REF ALT sample1 sample2 ...

The script is intentionally streaming-friendly: it only keeps retained region
rows in memory and writes TSV outputs plus XLSX copies when openpyxl is present.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chrom", required=True, help="Target chromosome, e.g. Chr1, Chr01, 1, or 01")
    p.add_argument("--start", required=True, type=int, help="1-based inclusive start")
    p.add_argument("--end", required=True, type=int, help="1-based inclusive end")
    p.add_argument(
        "--genotype",
        required=True,
        action="append",
        help="Input superrice genotype .gz file. May be repeated for SNP and InDel files.",
    )
    p.add_argument("--metadata-tsv", action="append", default=[], help="Sample metadata TSV. May be repeated.")
    p.add_argument("--metadata-xlsx", action="append", default=[], help="Sample metadata XLSX. May be repeated.")
    p.add_argument("--metadata-sheet", default="Accession Information", help="XLSX sheet name")
    p.add_argument("--out-dir", required=True, help="Output directory")
    p.add_argument("--prefix", required=True, help="Output filename prefix")
    p.add_argument("--wild-regex", default=r"^Or|Or-|rufipogon|nivara", help="Regex for wild rice groups")
    p.add_argument("--cultivar-regex", default=r"^XI|^GJ|^cA|^cB", help="Regex for cultivated rice groups")
    return p.parse_args()


def open_text(path: Path):
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", newline="")
    return open(path, newline="")


def norm_chrom(chrom: str) -> str:
    value = str(chrom).strip()
    value = re.sub(r"^chr", "", value, flags=re.IGNORECASE)
    value = value.lstrip("0")
    return value or "0"


def recode_group(species: str, wild_re: re.Pattern[str], cultivar_re: re.Pattern[str]) -> str:
    value = (species or "").strip()
    if not value:
        return "Undefined"
    if wild_re.search(value):
        return "Wild"
    if cultivar_re.search(value):
        return "Cultivar"
    return "Undefined"


def read_tsv_metadata(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle, delimiter="\t")]


def read_xlsx_metadata(path: Path, sheet_name: str) -> list[dict[str, str]]:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise SystemExit("openpyxl is required for --metadata-xlsx; provide --metadata-tsv instead") from exc

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet_name] if sheet_name in wb.sheetnames else wb[wb.sheetnames[0]]
    rows = ws.iter_rows(values_only=True)
    header = ["" if x is None else str(x).strip() for x in next(rows)]
    out = []
    for row in rows:
        item = {}
        for key, value in zip(header, row):
            item[key] = "" if value is None else str(value).strip()
        out.append(item)
    return out


def metadata_sample_id(row: dict[str, str]) -> str:
    for key in ("sample_id", "Sample ID", "SampleID", "ID", "Accession ID"):
        if row.get(key):
            return str(row[key]).strip()
    return ""


def metadata_species(row: dict[str, str]) -> str:
    for key in ("species_information", "Species Information", "group", "Group", "K5"):
        if row.get(key):
            return str(row[key]).strip()
    return ""


def load_metadata(args: argparse.Namespace) -> dict[str, dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in args.metadata_tsv:
        rows.extend(read_tsv_metadata(Path(path)))
    for path in args.metadata_xlsx:
        rows.extend(read_xlsx_metadata(Path(path), args.metadata_sheet))

    wild_re = re.compile(args.wild_regex, re.IGNORECASE)
    cultivar_re = re.compile(args.cultivar_regex, re.IGNORECASE)
    metadata: dict[str, dict[str, str]] = {}
    for row in rows:
        sample_id = metadata_sample_id(row)
        if not sample_id:
            continue
        species = metadata_species(row)
        metadata[sample_id] = {
            **{str(k).strip().replace(" ", "_").lower(): str(v).strip() for k, v in row.items()},
            "sample_id": sample_id,
            "species_information": species,
            "analysis_group": recode_group(species, wild_re, cultivar_re),
            "metadata_present": "TRUE",
        }
    return metadata


def write_tsv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_xlsx(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    try:
        from openpyxl import Workbook
    except ImportError:
        print(f"[warn] openpyxl not available; skipped {path}", file=sys.stderr)
        return
    wb = Workbook(write_only=True)
    ws = wb.create_sheet("data")
    ws.append(fieldnames)
    for row in rows:
        ws.append([row.get(field, "") for field in fieldnames])
    wb.save(path)


def iter_region_rows(paths: Iterable[Path], target_chrom: str, start: int, end: int):
    header_samples: list[str] | None = None
    out_header: list[str] | None = None
    for path in paths:
        with open_text(path) as handle:
            reader = csv.reader(handle, delimiter="\t")
            header = next(reader)
            if len(header) < 5 or header[:4] != ["CHROM", "POS", "REF", "ALT"]:
                raise SystemExit(f"{path} does not look like a superrice genotype table")
            samples = header[4:]
            if header_samples is None:
                header_samples = samples
                out_header = header
                yield out_header, None
            elif samples != header_samples:
                raise SystemExit(f"Sample columns differ between genotype files; first mismatch: {path}")
            for row in reader:
                if len(row) < 5:
                    continue
                if norm_chrom(row[0]) != target_chrom:
                    continue
                try:
                    pos = int(row[1])
                except ValueError:
                    continue
                if start <= pos <= end:
                    yield None, row


def main() -> None:
    args = parse_args()
    if args.start > args.end:
        raise SystemExit("--start must be <= --end")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    metadata = load_metadata(args)
    target_chrom = norm_chrom(args.chrom)
    genotype_paths = [Path(x) for x in args.genotype]

    out_region = out_dir / f"{args.prefix}.superrice_region_genotype.tsv.gz"
    header: list[str] | None = None
    retained_rows = 0
    with gzip.open(out_region, "wt", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        for maybe_header, row in iter_region_rows(genotype_paths, target_chrom, args.start, args.end):
            if maybe_header is not None:
                header = maybe_header
                writer.writerow(header)
            elif row is not None:
                writer.writerow(row)
                retained_rows += 1

    if header is None:
        raise SystemExit("No genotype header was read")
    samples = header[4:]
    manifest_rows = []
    for sample_id in samples:
        item = metadata.get(sample_id)
        if item is None:
            item = {
                "sample_id": sample_id,
                "species_information": "",
                "analysis_group": "Undefined",
                "metadata_present": "FALSE",
            }
        manifest_rows.append(item)

    group_counts = Counter(row["analysis_group"] for row in manifest_rows)
    group_rows = [
        {"analysis_group": group, "sample_count": count}
        for group, count in sorted(group_counts.items(), key=lambda x: (x[0] != "Cultivar", x[0] != "Wild", x[0]))
    ]
    audit_rows = [
        {"metric": "chrom", "value": args.chrom},
        {"metric": "start", "value": args.start},
        {"metric": "end", "value": args.end},
        {"metric": "genotype_files", "value": ";".join(str(x) for x in genotype_paths)},
        {"metric": "sample_count", "value": len(samples)},
        {"metric": "retained_variant_count", "value": retained_rows},
        {"metric": "wild_regex", "value": args.wild_regex},
        {"metric": "cultivar_regex", "value": args.cultivar_regex},
    ]

    manifest_fields = sorted(set().union(*(row.keys() for row in manifest_rows)))
    for required in ("sample_id", "species_information", "analysis_group", "metadata_present"):
        if required in manifest_fields:
            manifest_fields.remove(required)
    manifest_fields = ["sample_id", "species_information", "analysis_group", "metadata_present"] + manifest_fields

    outputs = [
        (out_dir / f"{args.prefix}.superrice_sample_manifest", manifest_rows, manifest_fields),
        (out_dir / f"{args.prefix}.superrice_group_counts", group_rows, ["analysis_group", "sample_count"]),
        (out_dir / f"{args.prefix}.superrice_extract_audit", audit_rows, ["metric", "value"]),
    ]
    for stem, rows, fields in outputs:
        write_tsv(Path(str(stem) + ".tsv"), rows, fields)
        write_xlsx(Path(str(stem) + ".xlsx"), rows, fields)


if __name__ == "__main__":
    main()
