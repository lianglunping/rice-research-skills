#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from Bio import SeqIO
from Bio.Seq import Seq
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from scipy.stats import fisher_exact


GROUPS = ("XI", "GJ", "Or", "Undefined")
XI_SUBGROUPS = ("XI1", "XI2", "XI3", "XI4", "XI5")
GJ_SUBGROUPS = ("GJ1", "GJ2", "GJ3", "GJ4-1", "GJ4-2", "GJ5")
SUBGROUPS = (*XI_SUBGROUPS, *GJ_SUBGROUPS)
ALLELE_FILLS = {
    "A": "4DAF4A",
    "C": "377EB8",
    "G": "FFB000",
    "T": "E41A1C",
    "DEL": "7F7F7F",
    "INS": "984EA3",
    "REF": "BDBDBD",
    "ALT": "4D4D4D",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build original-style publication-composite tables from a validated superrice run.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--source-result", required=True)
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--site-fst", required=False)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def iter_tsv(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="") as handle:
        yield from csv.DictReader(handle, delimiter="\t")


def read_config(path: Path) -> dict[str, str]:
    return {row["field"]: row["value"] for row in read_tsv(path)}


def write_tsv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_xlsx(path: Path, sheets: list[tuple[str, list[dict[str, Any]], list[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    workbook.remove(workbook.active)
    header_fill = PatternFill("solid", fgColor="1F4E78")
    header_font = Font(name="Arial", size=10, bold=True, color="FFFFFF")
    body_font = Font(name="Arial", size=9)
    thin_gray = Side(style="thin", color="D9E1F2")
    for sheet_name, rows, fields in sheets:
        worksheet = workbook.create_sheet(sheet_name[:31])
        worksheet.append(fields)
        for row in rows:
            worksheet.append([row.get(field, "") for field in fields])
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = Border(bottom=thin_gray)
        for row in worksheet.iter_rows(min_row=2):
            for cell in row:
                cell.font = body_font
                cell.alignment = Alignment(vertical="center", wrap_text=False)
                if str(cell.value) in ALLELE_FILLS:
                    cell.fill = PatternFill("solid", fgColor=ALLELE_FILLS[str(cell.value)])
                    cell.font = Font(name="Arial", size=9, bold=True, color="FFFFFF")
                    cell.alignment = Alignment(horizontal="center", vertical="center")
        for index, field in enumerate(fields, start=1):
            samples = [str(field)] + [str(row.get(field, "")) for row in rows[:100]]
            width = min(42, max(8, max(len(value) for value in samples) + 2))
            worksheet.column_dimensions[get_column_letter(index)].width = width
            lower = field.lower()
            if "frequency" in lower or "rate" in lower or lower.endswith("_ci_low") or lower.endswith("_ci_high"):
                for cell in worksheet[get_column_letter(index)][1:]:
                    if isinstance(cell.value, (int, float)):
                        cell.number_format = "0.000%"
            elif lower in {"fisher_exact_p", "bh_q", "odds_ratio", "site_weir_cockerham_fst"}:
                for cell in worksheet[get_column_letter(index)][1:]:
                    if isinstance(cell.value, (int, float)):
                        cell.number_format = "0.000E+00"
    workbook.save(path)


def write_pair(stem: Path, rows: list[dict[str, Any]], fields: list[str], sheet: str) -> None:
    write_tsv(Path(f"{stem}.tsv"), rows, fields)
    write_xlsx(Path(f"{stem}.xlsx"), [(sheet, rows, fields)])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def as_int(value: Any) -> int:
    return int(float(str(value)))


def as_float(value: Any) -> float:
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return math.nan


def decode_allele(token: str, ref: str, alt: str) -> tuple[str, str, str]:
    alleles = alt.split(",") if alt else []
    if token == ref or token == "0":
        return ref, ref if len(ref) == 1 else "REF", "REF"
    if token == "*":
        return "DEL", "DEL", "Deletion"
    if token.isdigit():
        index = int(token)
        if index == 0:
            return ref, ref, "REF"
        if 1 <= index <= len(alleles):
            value = alleles[index - 1]
            if value == "*" or len(value) < len(ref):
                return value, "DEL", "Deletion"
            if len(value) > len(ref):
                return value, "INS", "Insertion"
            return value, value if len(value) == 1 else "ALT", "ALT"
        return token, f"IDX{index}", "Other"
    if token in alleles:
        if len(token) < len(ref):
            return token, "DEL", "Deletion"
        if len(token) > len(ref):
            return token, "INS", "Insertion"
        return token, token if len(token) == 1 else "ALT", "ALT"
    if len(token) < len(ref):
        return token, "DEL", "Deletion"
    if len(token) > len(ref):
        return token, "INS", "Insertion"
    return token, token if len(token) == 1 else "ALT", "Other"


def hamming(pattern_a: list[str], pattern_b: list[str]) -> int:
    if len(pattern_a) != len(pattern_b):
        raise ValueError("Haplotype patterns have inconsistent lengths")
    return sum(a != b for a, b in zip(pattern_a, pattern_b))


def mst_edges(pairwise: list[dict[str, Any]], ids: list[str]) -> list[dict[str, Any]]:
    parent = {item: item for item in ids}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    selected: list[dict[str, Any]] = []
    for row in sorted(pairwise, key=lambda item: (as_int(item["distance"]), item["hap_a"], item["hap_b"])):
        root_a, root_b = find(row["hap_a"]), find(row["hap_b"])
        if root_a == root_b:
            continue
        parent[root_b] = root_a
        selected.append(row)
        if len(selected) == len(ids) - 1:
            break
    return selected


def parse_gff(path: Path) -> tuple[list[tuple[int, int]], list[tuple[int, int]], list[dict[str, Any]]]:
    exons: list[tuple[int, int]] = []
    cds: list[tuple[int, int]] = []
    cds_rows: list[dict[str, Any]] = []
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 9:
                continue
            start, end = int(fields[3]), int(fields[4])
            if fields[2] == "exon":
                exons.append((start, end))
            elif fields[2] == "CDS":
                cds.append((start, end))
                cds_rows.append({"seqid": fields[0], "start": start, "end": end, "strand": fields[6], "phase": fields[7]})
    return sorted(set(exons)), sorted(set(cds)), cds_rows


def classify_site(pos: int, config: dict[str, str], exons: list[tuple[int, int]], cds: list[tuple[int, int]]) -> str:
    if as_int(config["promoter_start"]) <= pos <= as_int(config["promoter_end"]):
        return "Promoter"
    if not (as_int(config["gene_start"]) <= pos <= as_int(config["gene_end"])):
        return "Outside"
    if any(start <= pos <= end for start, end in cds):
        return "CDS"
    boundaries = [value for interval in exons for value in interval if value not in {as_int(config["gene_start"]), as_int(config["gene_end"])}]
    if any(abs(pos - boundary) <= 2 for boundary in boundaries):
        return "Splice_boundary"
    if any(start <= pos <= end for start, end in exons):
        cds_min = min(start for start, _ in cds)
        cds_max = max(end for _, end in cds)
        if pos < cds_min:
            return "5UTR"
        if pos > cds_max:
            return "3UTR"
        return "Exon_non_CDS"
    return "Intron"


def build_cds_context(config: dict[str, str], cds_rows: list[dict[str, Any]]) -> tuple[str, dict[int, int], dict[str, Any]]:
    genome_path = Path(config["reference_genome_fasta"])
    cds_path = Path(config["reference_cds_fasta"])
    genome = SeqIO.index(str(genome_path), "fasta")
    contig_candidates = [config["gene_chr_gff"], config["gene_chr_gff"].replace("chr", "Chr"), f"Chr{config['gene_chr_vcf']}"]
    contig = next((item for item in contig_candidates if item in genome), None)
    if contig is None:
        raise SystemExit(f"Reference contig not found: {contig_candidates}")
    strand = config["gene_strand"]
    ordered = sorted(cds_rows, key=lambda row: row["start"], reverse=strand == "-")
    transcript_bases: list[str] = []
    genomic_to_cds: dict[int, int] = {}
    for row in ordered:
        positions = range(row["start"], row["end"] + 1) if strand == "+" else range(row["end"], row["start"] - 1, -1)
        for pos in positions:
            base = str(genome[contig].seq[pos - 1 : pos]).upper()
            if strand == "-":
                base = str(Seq(base).complement())
            genomic_to_cds[pos] = len(transcript_bases)
            transcript_bases.append(base)
    cds_sequence = "".join(transcript_bases)
    cds_index = SeqIO.index(str(cds_path), "fasta")
    transcript_id = f"{config['gene_id']}.1"
    expected = str(cds_index[transcript_id].seq).upper() if transcript_id in cds_index else ""
    audit = {
        "reference_genome": str(genome_path),
        "reference_genome_sha256": sha256(genome_path),
        "reference_cds": str(cds_path),
        "reference_cds_sha256": sha256(cds_path),
        "transcript_id": transcript_id,
        "assembled_cds_length": len(cds_sequence),
        "expected_cds_length": len(expected),
        "assembled_matches_reference_cds": "TRUE" if expected and cds_sequence == expected else "FALSE",
    }
    if expected and cds_sequence != expected:
        raise SystemExit(f"Assembled CDS does not match {transcript_id} in {cds_path}")
    return cds_sequence, genomic_to_cds, audit


def consequence_for_site(
    row: dict[str, str], observed_alleles: set[str], cds_sequence: str, genomic_to_cds: dict[int, int], strand: str
) -> tuple[str, str]:
    pos, ref = as_int(row["POS"]), row["REF"].upper()
    feature = row["detailed_feature_class"]
    if feature != "CDS":
        return feature, "FALSE"
    if pos not in genomic_to_cds:
        return "CDS; unmapped", "FALSE"
    offset = genomic_to_cds[pos]
    codon_start = (offset // 3) * 3
    reference_codon = cds_sequence[codon_start : codon_start + 3]
    if len(reference_codon) != 3:
        return "partial CDS codon", "FALSE"
    amino_index = codon_start // 3 + 1
    reference_aa = str(Seq(reference_codon).translate())
    labels: list[str] = []
    protein_altering = False
    for allele in sorted(observed_alleles):
        allele = allele.upper()
        if allele == ref:
            continue
        if allele in {"*", "DEL"}:
            labels.append("spanning-deletion marker")
            continue
        if len(ref) == 1 and len(allele) == 1 and allele in {"A", "C", "G", "T"}:
            transcript_allele = allele if strand == "+" else str(Seq(allele).complement())
            mutable = list(reference_codon)
            mutable[offset % 3] = transcript_allele
            alternate_aa = str(Seq("".join(mutable)).translate())
            if alternate_aa == reference_aa:
                labels.append(f"p.{reference_aa}{amino_index}=")
            else:
                labels.append(f"p.{reference_aa}{amino_index}{alternate_aa}")
                protein_altering = True
            continue
        length_delta = len(allele) - len(ref)
        if length_delta == 0:
            labels.append("coding substitution; protein effect unresolved")
            protein_altering = True
        elif length_delta % 3 == 0:
            labels.append("in-frame InDel")
            protein_altering = True
        else:
            labels.append("frameshift")
            protein_altering = True
    if not labels:
        return "CDS", "FALSE"
    return "/".join(dict.fromkeys(labels)), "TRUE" if protein_altering else "FALSE"


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return math.nan, math.nan
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - radius), min(1.0, centre + radius)


def newcombe_difference_interval(
    successes_a: int, total_a: int, successes_b: int, total_b: int
) -> tuple[float, float]:
    """Newcombe hybrid-score interval for two independent proportions."""
    if total_a == 0 or total_b == 0:
        return math.nan, math.nan
    proportion_a = successes_a / total_a
    proportion_b = successes_b / total_b
    low_a, high_a = wilson_interval(successes_a, total_a)
    low_b, high_b = wilson_interval(successes_b, total_b)
    difference = proportion_a - proportion_b
    lower = difference - math.sqrt((proportion_a - low_a) ** 2 + (high_b - proportion_b) ** 2)
    upper = difference + math.sqrt((high_a - proportion_a) ** 2 + (proportion_b - low_b) ** 2)
    return max(-1.0, lower), min(1.0, upper)


def bh_adjust(p_values: list[float]) -> list[float]:
    count = len(p_values)
    adjusted = [math.nan] * count
    running = 1.0
    for rank, index in reversed(list(enumerate(sorted(range(count), key=lambda i: p_values[i]), start=1))):
        value = min(running, p_values[index] * count / rank)
        adjusted[index] = min(1.0, value)
        running = value
    return adjusted


def parse_site_fst(path: Path | None) -> dict[tuple[str, int], float]:
    if path is None or not path.exists():
        return {}
    rows: dict[tuple[str, int], float] = {}
    with path.open() as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            chrom = row.get("CHROM", "").removeprefix("Chr").removeprefix("chr")
            value = as_float(row.get("WEIR_AND_COCKERHAM_FST", "nan"))
            rows[(chrom, as_int(row["POS"]))] = value
    return rows


def vcf_site_frequencies(config: dict[str, str], source: Path, site_fst: dict[tuple[str, int], float], exons: list[tuple[int, int]], cds: list[tuple[int, int]]) -> list[dict[str, Any]]:
    vcf_path = source / "vcf" / f"{config['gene_id']}.superrice_biallelic_SNP_wide.vcf.gz"
    xi_ids = set((source / "popgen" / "groups" / "XI.list").read_text().split())
    gj_ids = set((source / "popgen" / "groups" / "GJ.list").read_text().split())
    rows: list[dict[str, Any]] = []
    sample_names: list[str] = []
    xi_indexes: list[int] = []
    gj_indexes: list[int] = []
    with gzip.open(vcf_path, "rt") as handle:
        for line in handle:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                sample_names = line.rstrip("\n").split("\t")[9:]
                xi_indexes = [index for index, sample in enumerate(sample_names) if sample in xi_ids]
                gj_indexes = [index for index, sample in enumerate(sample_names) if sample in gj_ids]
                continue
            fields = line.rstrip("\n").split("\t")
            chrom, pos, ref, alt = fields[0], int(fields[1]), fields[3], fields[4]
            if not (as_int(config["analysis_start"]) <= pos <= as_int(config["analysis_end"])):
                continue
            genotypes = fields[9:]

            def counts(indexes: list[int]) -> tuple[int, int, int]:
                ref_n = alt_n = called = 0
                for index in indexes:
                    gt = genotypes[index].split(":", 1)[0].replace("|", "/")
                    alleles = gt.split("/")
                    if len(alleles) != 2 or "." in alleles:
                        continue
                    called += 2
                    ref_n += sum(allele == "0" for allele in alleles)
                    alt_n += sum(allele == "1" for allele in alleles)
                return ref_n, alt_n, called

            xi_ref, xi_alt, xi_called = counts(xi_indexes)
            gj_ref, gj_alt, gj_called = counts(gj_indexes)
            possible = 2 * (len(xi_indexes) + len(gj_indexes))
            combined_call_rate = (xi_called + gj_called) / possible if possible else math.nan
            xi_af = xi_alt / xi_called if xi_called else math.nan
            gj_af = gj_alt / gj_called if gj_called else math.nan
            rows.append({
                "CHROM": chrom,
                "POS": pos,
                "REF": ref,
                "ALT": alt,
                "variant_id": f"Chr{chrom}:{pos}:{ref}>{alt}",
                "feature_class": classify_site(pos, config, exons, cds),
                "XI_ref_alleles": xi_ref,
                "XI_alt_alleles": xi_alt,
                "XI_called_chromosomes": xi_called,
                "XI_alt_frequency": xi_af,
                "GJ_ref_alleles": gj_ref,
                "GJ_alt_alleles": gj_alt,
                "GJ_called_chromosomes": gj_called,
                "GJ_alt_frequency": gj_af,
                "delta_AF_XI_minus_GJ": xi_af - gj_af if math.isfinite(xi_af) and math.isfinite(gj_af) else math.nan,
                "combined_call_rate": combined_call_rate,
                "passes_pairwise_max_missing_0.80": "TRUE" if combined_call_rate >= as_float(config["popgen_max_missing"]) else "FALSE",
                "site_Weir_Cockerham_Fst": site_fst.get((chrom, pos), math.nan),
                "in_analysis_interval": "TRUE" if as_int(config["analysis_start"]) <= pos <= as_int(config["analysis_end"]) else "FALSE",
                "in_filter_scope": "TRUE" if as_int(config["popgen_filter_start"]) <= pos <= as_int(config["popgen_filter_end"]) else "FALSE",
            })
    return rows


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    project_root = Path(args.project_root).resolve()
    source = Path(args.source_result).resolve()
    result = Path(args.result_dir).resolve()
    config = read_config(config_path)
    gene_id = config["gene_id"]
    for name in ("haplotype", "plot_data", "tree", "map", "popgen", "summary", "tables", "logs"):
        (result / name).mkdir(parents=True, exist_ok=True)

    source_hap = source / "haplotype"
    all_counts = read_tsv(source_hap / f"{gene_id}.all_haplotype_counts.tsv")
    all_counts.sort(key=lambda row: (-as_int(row["haplotype_chromosome_count"]), row["all_haplotype_id"]))
    manifest_rows = read_tsv(source_hap / f"{gene_id}.superrice_sample_manifest_detailed.tsv")
    manifest_by_sample = {row["sample_id"]: row for row in manifest_rows}
    assignment_rows: list[dict[str, str]] = []
    carrier_samples: dict[str, set[str]] = defaultdict(set)
    for row in iter_tsv(source_hap / f"{gene_id}.all_haplotype_sample_assignment.tsv"):
        if row["sample_id"] not in manifest_by_sample:
            raise SystemExit(f"Assignment sample missing from manifest: {row['sample_id']}")
        metadata = manifest_by_sample[row["sample_id"]]
        enriched = {
            **row,
            "species_information": metadata["species_information"],
            "detailed_group": metadata["detailed_group"],
            "original_area": metadata["original_area"],
        }
        assignment_rows.append(enriched)
        carrier_samples[row["all_haplotype_id"]].add(row["sample_id"])

    retention = read_tsv(source / "summary" / "sample_retention_by_detailed_group.tsv")
    complete_samples = {row["detailed_group"]: as_int(row["complete_samples"]) for row in retention}
    group_chromosomes = {group: 2 * complete_samples.get(group, 0) for group in GROUPS}
    complete_sample_ids = {row["sample_id"] for row in assignment_rows}
    subgroup_sample_counts: Counter[str] = Counter(
        manifest_by_sample[sample]["species_information"] for sample in complete_sample_ids
    )
    subgroup_chromosomes = {subgroup: 2 * subgroup_sample_counts[subgroup] for subgroup in SUBGROUPS}

    chromosome_by_group: Counter[tuple[str, str]] = Counter()
    chromosome_by_subgroup: Counter[tuple[str, str]] = Counter()
    carrier_by_group: dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in assignment_rows:
        chromosome_by_group[(row["all_haplotype_id"], row["detailed_group"])] += 1
        chromosome_by_subgroup[(row["all_haplotype_id"], row["species_information"])] += 1
        carrier_by_group[(row["all_haplotype_id"], row["detailed_group"])].add(row["sample_id"])

    min_frequency = as_float(config["primary_haplotype_subgroup_chr_frequency_min"])
    min_carriers = as_int(config["primary_haplotype_min_carrier_accessions"])
    selected_all_ids: list[str] = []
    threshold_audit: list[dict[str, Any]] = []
    for count_row in all_counts:
        all_id = count_row["all_haplotype_id"]
        xi_n = chromosome_by_group[(all_id, "XI")]
        gj_n = chromosome_by_group[(all_id, "GJ")]
        xi_frequency = xi_n / group_chromosomes["XI"] if group_chromosomes["XI"] else 0.0
        gj_frequency = gj_n / group_chromosomes["GJ"] if group_chromosomes["GJ"] else 0.0
        carrier_n = len(carrier_samples[all_id])
        selected = carrier_n >= min_carriers and max(xi_frequency, gj_frequency) > min_frequency
        if selected:
            selected_all_ids.append(all_id)
        threshold_audit.append({
            "all_haplotype_id": all_id,
            "haplotype_chromosome_count": as_int(count_row["haplotype_chromosome_count"]),
            "global_chromosome_frequency": as_float(count_row["frequency"]),
            "carrier_accession_count": carrier_n,
            "XI_chromosome_count": xi_n,
            "XI_chromosome_frequency": xi_frequency,
            "GJ_chromosome_count": gj_n,
            "GJ_chromosome_frequency": gj_frequency,
            "max_XI_GJ_chromosome_frequency": max(xi_frequency, gj_frequency),
            "frequency_operator": ">",
            "frequency_threshold": min_frequency,
            "minimum_carrier_accessions": min_carriers,
            "selected_primary": "TRUE" if selected else "FALSE",
        })
    selected_all_ids.sort(key=lambda item: -as_int(next(row["haplotype_chromosome_count"] for row in all_counts if row["all_haplotype_id"] == item)))
    display_lookup = {all_id: f"H{index:03d}" for index, all_id in enumerate(selected_all_ids, start=1)}

    main_assignments = [
        dict(row, primary_haplotype_id=display_lookup[row["all_haplotype_id"]])
        for row in assignment_rows
        if row["all_haplotype_id"] in display_lookup
    ]

    main_summary: list[dict[str, Any]] = []
    tests: list[dict[str, Any]] = []
    for all_id in selected_all_ids:
        display_id = display_lookup[all_id]
        count_row = next(row for row in all_counts if row["all_haplotype_id"] == all_id)
        xi_carriers = len(carrier_by_group[(all_id, "XI")])
        gj_carriers = len(carrier_by_group[(all_id, "GJ")])
        xi_rate = xi_carriers / complete_samples["XI"]
        gj_rate = gj_carriers / complete_samples["GJ"]
        xi_low, xi_high = wilson_interval(xi_carriers, complete_samples["XI"])
        gj_low, gj_high = wilson_interval(gj_carriers, complete_samples["GJ"])
        risk_difference = xi_rate - gj_rate
        risk_low, risk_high = newcombe_difference_interval(
            xi_carriers, complete_samples["XI"], gj_carriers, complete_samples["GJ"]
        )
        table = [[xi_carriers, complete_samples["XI"] - xi_carriers], [gj_carriers, complete_samples["GJ"] - gj_carriers]]
        fisher = fisher_exact(table, alternative="two-sided")
        main_summary.append({
            "primary_haplotype_id": display_id,
            "all_haplotype_id": all_id,
            "carrier_accession_count": len(carrier_samples[all_id]),
            "haplotype_chromosome_count": as_int(count_row["haplotype_chromosome_count"]),
            "global_chromosome_frequency": as_float(count_row["frequency"]),
            "XI_carrier_accessions": xi_carriers,
            "XI_carrier_rate": xi_rate,
            "XI_haplotype_chromosomes": chromosome_by_group[(all_id, "XI")],
            "XI_chromosome_frequency": chromosome_by_group[(all_id, "XI")] / group_chromosomes["XI"],
            "GJ_carrier_accessions": gj_carriers,
            "GJ_carrier_rate": gj_rate,
            "GJ_haplotype_chromosomes": chromosome_by_group[(all_id, "GJ")],
            "GJ_chromosome_frequency": chromosome_by_group[(all_id, "GJ")] / group_chromosomes["GJ"],
            "Or_haplotype_chromosomes": chromosome_by_group[(all_id, "Or")],
            "carrier_rate_difference_XI_minus_GJ": risk_difference,
            "selection_rule": f"carrier_n>={min_carriers} AND max(XI_chr_freq,GJ_chr_freq)>{min_frequency}",
        })
        tests.append({
            "primary_haplotype_id": display_id,
            "all_haplotype_id": all_id,
            "XI_carrier_accessions": xi_carriers,
            "XI_complete_accessions": complete_samples["XI"],
            "XI_carrier_rate": xi_rate,
            "XI_rate_CI_low": xi_low,
            "XI_rate_CI_high": xi_high,
            "GJ_carrier_accessions": gj_carriers,
            "GJ_complete_accessions": complete_samples["GJ"],
            "GJ_carrier_rate": gj_rate,
            "GJ_rate_CI_low": gj_low,
            "GJ_rate_CI_high": gj_high,
            "rate_difference_XI_minus_GJ": risk_difference,
            "rate_difference_CI_low": risk_low,
            "rate_difference_CI_high": risk_high,
            "rate_difference_CI_method": "Newcombe hybrid-score (Wilson)",
            "odds_ratio": float(fisher.statistic),
            "fisher_exact_p": float(fisher.pvalue),
            "fisher_alternative": "two-sided",
            "test_unit": "accession carrier presence/absence",
            "interpretation_scope": "retained_complete_case_cohort",
        })
    adjusted = bh_adjust([as_float(row["fisher_exact_p"]) for row in tests])
    for row, q_value in zip(tests, adjusted):
        row["BH_q"] = q_value

    all_summary: list[dict[str, Any]] = []
    cumulative = 0
    total_chromosomes = sum(as_int(row["haplotype_chromosome_count"]) for row in all_counts)
    for rank, row in enumerate(all_counts, start=1):
        count = as_int(row["haplotype_chromosome_count"])
        cumulative += count
        all_summary.append({
            "rank": rank,
            "all_haplotype_id": row["all_haplotype_id"],
            "primary_haplotype_id": display_lookup.get(row["all_haplotype_id"], ""),
            "carrier_accession_count": len(carrier_samples[row["all_haplotype_id"]]),
            "haplotype_chromosome_count": count,
            "chromosome_frequency": count / total_chromosomes,
            "cumulative_chromosome_frequency": cumulative / total_chromosomes,
            "selected_primary": "TRUE" if row["all_haplotype_id"] in display_lookup else "FALSE",
            "haplotype_pattern": row["haplotype_pattern"],
        })

    subgroup_rows: list[dict[str, Any]] = []
    subgroup_frequency_rows: list[dict[str, Any]] = []
    for summary in main_summary:
        all_id = summary["all_haplotype_id"]
        row: dict[str, Any] = {"primary_haplotype_id": summary["primary_haplotype_id"], "all_haplotype_id": summary["all_haplotype_id"]}
        for subgroup in SUBGROUPS:
            count = chromosome_by_subgroup[(all_id, subgroup)]
            denominator = subgroup_chromosomes[subgroup]
            row[subgroup] = count
            subgroup_frequency_rows.append({
                "primary_haplotype_id": summary["primary_haplotype_id"],
                "all_haplotype_id": all_id,
                "subgroup": subgroup,
                "parent_group": "XI" if subgroup.startswith("XI") else "GJ",
                "haplotype_chromosome_count": count,
                "complete_accession_count": subgroup_sample_counts[subgroup],
                "haplotype_chromosome_denominator": denominator,
                "within_subgroup_chromosome_frequency": count / denominator if denominator else math.nan,
            })
        row.update({
            "XI_total_haplotype_chromosomes": summary["XI_haplotype_chromosomes"],
            "GJ_total_haplotype_chromosomes": summary["GJ_haplotype_chromosomes"],
            "Or_total_haplotype_chromosomes": summary["Or_haplotype_chromosomes"],
            "carrier_accession_count": summary["carrier_accession_count"],
        })
        subgroup_rows.append(row)

    gff_path = project_root / config["annotation_gff3"]
    exons, cds, cds_rows = parse_gff(gff_path)
    cds_sequence, genomic_to_cds, cds_audit = build_cds_context(config, cds_rows)
    variant_rows = read_tsv(source_hap / f"{gene_id}.superrice_variant_table.tsv")
    variant_rows.sort(key=lambda row: as_int(row["variant_index"]))
    count_by_all = {row["all_haplotype_id"]: row for row in all_counts}
    selected_patterns = {
        display_lookup[all_id]: count_by_all[all_id]["haplotype_pattern"].split(",")
        for all_id in selected_all_ids
    }
    main_matrix_all: list[dict[str, Any]] = []
    for all_id in selected_all_ids:
        display_id = display_lookup[all_id]
        tokens = count_by_all[all_id]["haplotype_pattern"].split(",")
        if len(tokens) != len(variant_rows):
            raise SystemExit(f"Pattern length mismatch for {all_id}")
        for variant, token in zip(variant_rows, tokens):
            _raw, display, allele_class = decode_allele(token, variant["REF"], variant["ALT"])
            main_matrix_all.append({
                **variant,
                "all_haplotype_id": all_id,
                "primary_haplotype_id": display_id,
                "haplotype_chromosome_count": as_int(count_by_all[all_id]["haplotype_chromosome_count"]),
                "detailed_feature_class": classify_site(as_int(variant["POS"]), config, exons, cds),
                "allele_token": token,
                "plot_allele": display,
                "allele_class": allele_class,
            })
    alleles_by_site: dict[str, set[str]] = defaultdict(set)
    for row in main_matrix_all:
        alleles_by_site[row["variant_id"]].add(row["plot_allele"])
    variable_site_ids = {variant_id for variant_id, alleles in alleles_by_site.items() if len(alleles) > 1}
    variable_matrix = [row for row in main_matrix_all if row["variant_id"] in variable_site_ids]

    site_meta: dict[str, dict[str, str]] = {}
    for row in main_matrix_all:
        if row["variant_id"] not in site_meta:
            site_meta[row["variant_id"]] = row
    variable_sites: list[dict[str, Any]] = []
    for variant_id in sorted(variable_site_ids, key=lambda item: as_int(site_meta[item]["variant_index"])):
        row = dict(site_meta[variant_id])
        observed_raw = {item["allele_token"] for item in main_matrix_all if item["variant_id"] == variant_id}
        observed_alleles = {decode_allele(token, row["REF"], row["ALT"])[0] for token in observed_raw}
        consequence, protein_altering = consequence_for_site(row, observed_alleles, cds_sequence, genomic_to_cds, config["gene_strand"])
        variable_sites.append({
            "display_site_order": len(variable_sites) + 1,
            "variant_index": row["variant_index"],
            "variant_id": variant_id,
            "CHROM": row.get("CHROM", config["gene_chr_vcf"]),
            "POS": as_int(row["POS"]),
            "REF": row["REF"],
            "ALT": row["ALT"],
            "variant_type": row["variant_type"],
            "feature_class": row["detailed_feature_class"],
            "observed_primary_alleles": ",".join(sorted(observed_alleles)),
            "coding_consequence": consequence,
            "protein_altering": protein_altering,
        })

    for row in variable_matrix:
        consequence = next(item for item in variable_sites if item["variant_id"] == row["variant_id"])
        row["display_site_order"] = consequence["display_site_order"]
        row["coding_consequence"] = consequence["coding_consequence"]
        row["protein_altering"] = consequence["protein_altering"]

    all_matrix_wide: list[dict[str, Any]] = []
    matrix_fields = ["all_haplotype_id", "primary_haplotype_id", "carrier_accession_count", "haplotype_chromosome_count", *[row["variant_id"] for row in variant_rows]]
    for count_row in all_counts:
        tokens = count_row["haplotype_pattern"].split(",")
        if len(tokens) != len(variant_rows):
            raise SystemExit(f"Pattern length mismatch for {count_row['all_haplotype_id']}")
        wide: dict[str, Any] = {
            "all_haplotype_id": count_row["all_haplotype_id"],
            "primary_haplotype_id": display_lookup.get(count_row["all_haplotype_id"], ""),
            "carrier_accession_count": len(carrier_samples[count_row["all_haplotype_id"]]),
            "haplotype_chromosome_count": as_int(count_row["haplotype_chromosome_count"]),
        }
        for variant, token in zip(variant_rows, tokens):
            _raw, display, _class = decode_allele(token, variant["REF"], variant["ALT"])
            wide[variant["variant_id"]] = display
        all_matrix_wide.append(wide)
    main_matrix_wide = [row for row in all_matrix_wide if row["all_haplotype_id"] in display_lookup]
    variable_matrix_fields = ["primary_haplotype_id", "all_haplotype_id", *[row["variant_id"] for row in variable_sites]]
    variable_matrix_wide: list[dict[str, Any]] = []
    for row in main_matrix_wide:
        variable_matrix_wide.append({field: row.get(field, "") for field in variable_matrix_fields})

    site_columns = [f"S{index:02d}" for index in range(1, len(variable_sites) + 1)]
    site_column_by_variant = {
        site["variant_id"]: site_column for site, site_column in zip(variable_sites, site_columns)
    }
    publication_table_fields = [
        "row_type", "row_label", *site_columns, *SUBGROUPS,
        "carrier_accession_count", "haplotype_chromosome_count", "global_chromosome_frequency",
        "XI_carrier_rate", "GJ_carrier_rate", "XI_minus_GJ_carrier_rate",
    ]
    publication_table_rows: list[dict[str, Any]] = []
    for label, key in (
        ("Position", "POS"),
        ("Feature", "feature_class"),
        ("Consequence", "coding_consequence"),
    ):
        annotation_row: dict[str, Any] = {"row_type": "annotation", "row_label": label}
        for site in variable_sites:
            annotation_row[site_column_by_variant[site["variant_id"]]] = site[key]
        publication_table_rows.append(annotation_row)
    matrix_by_primary = {row["primary_haplotype_id"]: row for row in variable_matrix_wide}
    subgroup_by_primary = {row["primary_haplotype_id"]: row for row in subgroup_rows}
    for summary in main_summary:
        primary_id = summary["primary_haplotype_id"]
        table_row: dict[str, Any] = {"row_type": "haplotype", "row_label": primary_id}
        for site in variable_sites:
            table_row[site_column_by_variant[site["variant_id"]]] = matrix_by_primary[primary_id][site["variant_id"]]
        for subgroup in SUBGROUPS:
            table_row[subgroup] = subgroup_by_primary[primary_id][subgroup]
        table_row.update({
            "carrier_accession_count": summary["carrier_accession_count"],
            "haplotype_chromosome_count": summary["haplotype_chromosome_count"],
            "global_chromosome_frequency": summary["global_chromosome_frequency"],
            "XI_carrier_rate": summary["XI_carrier_rate"],
            "GJ_carrier_rate": summary["GJ_carrier_rate"],
            "XI_minus_GJ_carrier_rate": summary["carrier_rate_difference_XI_minus_GJ"],
        })
        publication_table_rows.append(table_row)

    display_ids = list(display_lookup.values())
    pairwise: list[dict[str, Any]] = []
    for index, hap_a in enumerate(display_ids):
        for hap_b in display_ids[index + 1 :]:
            pairwise.append({"hap_a": hap_a, "hap_b": hap_b, "distance": hamming(selected_patterns[hap_a], selected_patterns[hap_b])})
    edges = mst_edges(pairwise, display_ids)
    distance_lookup = {(row["hap_a"], row["hap_b"]): row["distance"] for row in pairwise}
    distance_matrix: list[dict[str, Any]] = []
    for hap_a in display_ids:
        matrix_row: dict[str, Any] = {"primary_haplotype_id": hap_a}
        for hap_b in display_ids:
            if hap_a == hap_b:
                matrix_row[hap_b] = 0
            else:
                key = (hap_a, hap_b) if (hap_a, hap_b) in distance_lookup else (hap_b, hap_a)
                matrix_row[hap_b] = distance_lookup[key]
        distance_matrix.append(matrix_row)
    tree_nodes = []
    for summary in main_summary:
        display_id = summary["primary_haplotype_id"]
        tree_nodes.append({
            **summary,
            "XI": chromosome_by_group[(summary["all_haplotype_id"], "XI")],
            "GJ": chromosome_by_group[(summary["all_haplotype_id"], "GJ")],
            "Or": chromosome_by_group[(summary["all_haplotype_id"], "Or")],
            "Undefined": chromosome_by_group[(summary["all_haplotype_id"], "Undefined")],
            "enrichment_direction": "XI-enriched" if summary["carrier_rate_difference_XI_minus_GJ"] > 0 else "GJ-enriched",
        })

    source_map = read_tsv(source / "map" / "display_haplotype_area_centroid_counts.tsv")
    source_display = read_tsv(source_hap / "display_haplotype_counts_top80.tsv")
    source_display_by_all = {row["all_haplotype_id"]: row["display_haplotype_id"] for row in source_display}
    missing_from_map_source = [all_id for all_id in selected_all_ids if all_id not in source_display_by_all]
    if missing_from_map_source:
        raise SystemExit(f"Primary haplotypes absent from source map display set: {missing_from_map_source}")
    selected_source_to_primary = {
        source_display_by_all[all_id]: display_lookup[all_id] for all_id in selected_all_ids
    }
    map_rows = [dict(row, primary_haplotype_id=selected_source_to_primary[row["display_haplotype_id"]]) for row in source_map if row["display_haplotype_id"] in selected_source_to_primary]

    site_fst = parse_site_fst(Path(args.site_fst) if args.site_fst else None)
    site_differentiation = vcf_site_frequencies(config, source, site_fst, exons, cds)
    gene_features = read_tsv(source / "plot_data" / "gene_feature_segments_detailed.tsv")

    popgen_files = {
        "Pi": source / "popgen" / "pi_tidy.tsv",
        "TajimaD": source / "popgen" / "tajimad_tidy.tsv",
        "Fst": source / "popgen" / "fst_tidy.tsv",
        "Pi_ratio": source / "popgen" / "pi_ratio_tidy.tsv",
    }
    popgen_sheets: list[tuple[str, list[dict[str, Any]], list[str]]] = []
    for name, path in popgen_files.items():
        rows = read_tsv(path)
        shutil.copy2(path, result / "popgen" / path.name)
        popgen_sheets.append((name, rows, list(rows[0])))

    source_files = [
        config_path,
        source_hap / f"{gene_id}.all_haplotype_counts.tsv",
        source_hap / f"{gene_id}.all_haplotype_sample_assignment.tsv",
        source_hap / f"{gene_id}.superrice_sample_manifest_detailed.tsv",
        source_hap / f"{gene_id}.superrice_variant_table.tsv",
        source / "vcf" / f"{gene_id}.superrice_biallelic_SNP_wide.vcf.gz",
        gff_path,
        project_root / config["figure_design_source"],
    ]
    if args.site_fst:
        source_files.append(Path(args.site_fst).resolve())
    provenance = [{"path": str(path), "sha256": sha256(path), "bytes": path.stat().st_size} for path in source_files]
    provenance.extend({"path": key, "sha256": str(value), "bytes": ""} for key, value in cds_audit.items())

    metrics = [
        {"metric": "source_complete_samples", "value": sum(complete_samples.values())},
        {"metric": "source_haplotype_chromosomes", "value": total_chromosomes},
        {"metric": "all_haplotype_count", "value": len(all_summary)},
        {"metric": "primary_haplotype_count", "value": len(main_summary)},
        {"metric": "source_display_haplotype_count", "value": len(read_tsv(source / "haplotype" / "display_haplotype_counts_top80.tsv"))},
        {"metric": "primary_variable_site_count", "value": len(variable_sites)},
        {"metric": "primary_pairwise_distance_count", "value": len(pairwise)},
        {"metric": "primary_mst_edge_count", "value": len(edges)},
        {"metric": "primary_haplotype_chromosome_coverage", "value": sum(row["haplotype_chromosome_count"] for row in main_summary) / total_chromosomes},
        {"metric": "XI_complete_samples", "value": complete_samples["XI"]},
        {"metric": "GJ_complete_samples", "value": complete_samples["GJ"]},
        {"metric": "primary_subgroup_frequency_threshold", "value": min_frequency},
        {"metric": "primary_minimum_carrier_accessions", "value": min_carriers},
        {"metric": "assignment_chromosome_copy_count", "value": len(assignment_rows)},
        {"metric": "analysis_interval_snp_count", "value": sum(row["in_analysis_interval"] == "TRUE" for row in site_differentiation)},
        {"metric": "site_fst_finite_count", "value": sum(math.isfinite(as_float(row["site_Weir_Cockerham_Fst"])) for row in site_differentiation)},
    ]
    subgroup_denominator_rows = [
        {
            "subgroup": subgroup,
            "parent_group": "XI" if subgroup.startswith("XI") else "GJ",
            "complete_accession_count": subgroup_sample_counts[subgroup],
            "haplotype_chromosome_denominator": subgroup_chromosomes[subgroup],
        }
        for subgroup in SUBGROUPS
    ]

    outputs: list[tuple[Path, list[dict[str, Any]], list[str], str]] = [
        (result / "haplotype" / "primary_haplotype_summary", main_summary, list(main_summary[0]), "Primary_Haplotypes"),
        (result / "haplotype" / "all_haplotype_summary", all_summary, list(all_summary[0]), "All_Haplotypes"),
        (result / "haplotype" / "primary_haplotype_assignment", main_assignments, list(main_assignments[0]), "Assignments"),
        (result / "haplotype" / "primary_haplotype_subgroup_counts", subgroup_rows, list(subgroup_rows[0]), "Subgroup_Counts"),
        (result / "haplotype" / "primary_haplotype_subgroup_frequencies", subgroup_frequency_rows, list(subgroup_frequency_rows[0]), "Subgroup_Frequencies"),
        (result / "haplotype" / "subgroup_denominators", subgroup_denominator_rows, list(subgroup_denominator_rows[0]), "Subgroup_Denominators"),
        (result / "haplotype" / "XI_GJ_carrier_tests", tests, list(tests[0]), "XI_GJ_Tests"),
        (result / "haplotype" / "primary_haplotype_threshold_audit", threshold_audit, list(threshold_audit[0]), "Threshold_Audit"),
        (result / "plot_data" / "primary_variable_site_summary", variable_sites, list(variable_sites[0]), "Variable_Sites"),
        (result / "plot_data" / "primary_variable_allele_matrix_long", variable_matrix, list(variable_matrix[0]), "Matrix_Long"),
        (result / "plot_data" / "primary_variable_allele_matrix", variable_matrix_wide, variable_matrix_fields, "Matrix_Wide"),
        (result / "plot_data" / "publication_haplotype_table", publication_table_rows, publication_table_fields, "Publication_Table"),
        (result / "plot_data" / "gene_feature_segments_detailed", gene_features, list(gene_features[0]), "Gene_Features"),
        (result / "plot_data" / "primary_all_site_allele_matrix", main_matrix_wide, matrix_fields, "Primary_All_Sites"),
        (result / "plot_data" / "all_haplotype_all_site_allele_matrix", all_matrix_wide, matrix_fields, "All_All_Sites"),
        (result / "tree" / "primary_haplotype_nodes", tree_nodes, list(tree_nodes[0]), "Nodes"),
        (result / "tree" / "primary_haplotype_pairwise_distance", pairwise, list(pairwise[0]), "Pairwise"),
        (result / "tree" / "primary_haplotype_mst_edges", edges, list(edges[0]), "MST_Edges"),
        (result / "tree" / "primary_haplotype_distance_matrix", distance_matrix, ["primary_haplotype_id", *display_ids], "Distance_Matrix"),
        (result / "map" / "primary_haplotype_area_centroid_counts", map_rows, list(map_rows[0]), "Area_Centroids"),
        (result / "popgen" / "XI_GJ_site_differentiation", site_differentiation, list(site_differentiation[0]), "Site_Differentiation"),
        (result / "summary" / "sample_retention_by_detailed_group", retention, list(retention[0]), "Retention"),
        (result / "summary" / "publication_composite_key_metrics", metrics, ["metric", "value"], "Key_Metrics"),
        (result / "summary" / "source_provenance", provenance, ["path", "sha256", "bytes"], "Provenance"),
    ]
    for stem, rows, fields, sheet in outputs:
        write_pair(stem, rows, fields, sheet)

    write_xlsx(result / "tables" / "Table1_HaplotypeSummary.xlsx", [
        ("Publication_Table", publication_table_rows, publication_table_fields),
        ("Primary_Haplotypes", main_summary, list(main_summary[0])),
        ("Top20_HaplotypeCounts", all_summary[:20], list(all_summary[0])),
        ("All_Haplotypes", all_summary, list(all_summary[0])),
        ("Subgroup_Chr_Counts", subgroup_rows, list(subgroup_rows[0])),
        ("Subgroup_Frequencies", subgroup_frequency_rows, list(subgroup_frequency_rows[0])),
        ("Subgroup_Denominators", subgroup_denominator_rows, list(subgroup_denominator_rows[0])),
        ("Carrier_Assignment", main_assignments, list(main_assignments[0])),
        ("Threshold_Audit", threshold_audit, list(threshold_audit[0])),
    ])
    write_xlsx(result / "tables" / "Table2_XI_GJ_Differentiation.xlsx", [
        ("Carrier_Tests", tests, list(tests[0])),
        ("Site_Differentiation", site_differentiation, list(site_differentiation[0])),
        ("Sample_Retention", retention, list(retention[0])),
    ])
    write_xlsx(result / "tables" / "Table3_VariantMatrix.xlsx", [
        ("Display_Site_Info", variable_sites, list(variable_sites[0])),
        ("Primary_Variable", variable_matrix_wide, variable_matrix_fields),
        ("Primary_All_Sites", main_matrix_wide, matrix_fields),
        ("All_Haplotypes_All_Sites", all_matrix_wide, matrix_fields),
    ])
    write_xlsx(result / "tables" / "TableS1_PopulationGenetics.xlsx", popgen_sheets)
    display_counts = read_tsv(source / "haplotype" / "display_haplotype_counts_top80.tsv")
    display_nodes = read_tsv(source / "tree" / "display_haplotype_node_table.tsv")
    display_edges = read_tsv(source / "tree" / "display_haplotype_mst_edges.tsv")
    display_distance = read_tsv(source / "tree" / "display_haplotype_distance_matrix.tsv")
    display_sites = read_tsv(source / "plot_data" / "display_site_summary_detailed.tsv")
    display_matrix = read_tsv(source / "plot_data" / "display_haplotype_allele_matrix_top80.tsv")
    display_map = read_tsv(source / "map" / "display_haplotype_area_centroid_counts.tsv")
    primary_id_set = set(display_ids)
    primary_map = [row for row in display_map if row["display_haplotype_id"] in primary_id_set]
    figure_decisions = [
        {"legacy_figure": "major_haplotype_counts", "v4_role": "Fig1 panel", "decision": "keep original chart grammar; highlight H001-H009"},
        {"legacy_figure": "haplotype_network", "v4_role": "Fig1 panel", "decision": "keep top80 pie-node MST; label H001-H009"},
        {"legacy_figure": "var_gene", "v4_role": "Fig1 panel", "decision": "keep informative gene-model view"},
        {"legacy_figure": "vat_tab", "v4_role": "Fig1 panel", "decision": "keep matrix grammar; use H001-H009 x 21 variable sites"},
        {"legacy_figure": "hap_map_by_haplotype", "v4_role": "Fig1 panel", "decision": "keep faceted centroid map; use H001-H009"},
        {"legacy_figure": "Pi/TajimaD/Fst all/filter", "v4_role": "Fig2 panels", "decision": "keep original line-chart grammar; arrange broad/local by metric"},
        {"legacy_figure": "local_popgen_profiles", "v4_role": "omitted", "decision": "redundant with Fig2"},
        {"legacy_figure": "all_filter", "v4_role": "omitted", "decision": "superseded by Fig2 composite"},
    ]
    write_pair(result / "summary" / "figure_content_decisions", figure_decisions, list(figure_decisions[0]), "Figure_Decisions")
    write_xlsx(result / "tables" / "Fig1_SourceData.xlsx", [
        ("Primary_Haplotypes", main_summary, list(main_summary[0])),
        ("Top80_Counts", display_counts, list(display_counts[0])),
        ("Threshold_Audit", threshold_audit, list(threshold_audit[0])),
        ("Network_Nodes_Top80", display_nodes, list(display_nodes[0])),
        ("Network_Edges_Top80", display_edges, list(display_edges[0])),
        ("Gene_Sites", display_sites, list(display_sites[0])),
        ("Primary_Variable_Matrix", variable_matrix_wide, variable_matrix_fields),
        ("Primary_Area_Centroids", primary_map, list(primary_map[0])),
        ("Retention", retention, list(retention[0])),
    ])
    write_xlsx(result / "tables" / "Fig2_SourceData.xlsx", popgen_sheets)
    write_xlsx(result / "tables" / "Supplementary_SourceData.xlsx", [
        ("Top80_Distance_Matrix", display_distance, list(display_distance[0])),
        ("Top80_All_Site_Matrix", display_matrix, list(display_matrix[0])),
        ("All_Haplotype_Ranks", all_summary, list(all_summary[0])),
        ("Area_Centroids", display_map, list(display_map[0])),
        ("Primary_Distance_Matrix", distance_matrix, ["primary_haplotype_id", *display_ids]),
    ])
    print(f"[build] primary_haplotypes={len(main_summary)} ids={','.join(display_ids)}")
    print(f"[build] all_haplotypes={len(all_summary)} variable_sites={len(variable_sites)} top80={len(display_counts)}")


if __name__ == "__main__":
    main()
