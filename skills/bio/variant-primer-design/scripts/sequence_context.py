#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

try:
    from pyfaidx import Fasta
except ImportError:  # pragma: no cover - exercised in runtime checks
    Fasta = None


CANONICAL_ALIASES = {
    "name": {"name", "marker", "locus", "site", "名称"},
    "chrom": {"chrom", "chr", "chrm", "染色体"},
    "pos": {"pos", "position", "位置"},
    "ref": {"ref"},
    "alt": {"alt"},
    "full_seq": {"fullseq", "fullsequence", "sequence", "全长"},
    "upstream_seq": {"upstreamseq", "upstream1kb"},
    "downstream_seq": {"downstreamseq", "downstream1kb"},
    "left_flank_len": {"leftflanklen", "upstreamlen"},
}

REQUIRED_FIELDS = ("name", "chrom", "pos", "ref", "alt")


def _normalize_header(value: Any) -> str:
    text = str(value).strip().lower()
    for token in (" ", "_", "-", "."):
        text = text.replace(token, "")
    return text


def load_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".tsv", ".txt"}:
        return pd.read_csv(path, sep="\t")
    raise ValueError(f"unsupported input format: {path}")


def normalize_variant_table(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    used_canonicals: set[str] = set()

    for column in df.columns:
        normalized = _normalize_header(column)
        for canonical, aliases in CANONICAL_ALIASES.items():
            if canonical in used_canonicals:
                continue
            if normalized in aliases:
                rename_map[column] = canonical
                used_canonicals.add(canonical)
                break

    result = df.rename(columns=rename_map).copy()
    missing = [field for field in REQUIRED_FIELDS if field not in result.columns]
    if missing:
        raise ValueError(f"missing required input columns: {missing}")

    for column in ("name", "chrom", "ref", "alt", "full_seq", "upstream_seq", "downstream_seq"):
        if column in result.columns:
            result[column] = result[column].astype(str).str.strip()

    result["pos"] = pd.to_numeric(result["pos"], errors="raise").astype(int)

    if "left_flank_len" in result.columns:
        result["left_flank_len"] = pd.to_numeric(result["left_flank_len"], errors="coerce").astype("Int64")

    if "variant_type" not in result.columns:
        result["variant_type"] = result.apply(
            lambda row: infer_variant_type(str(row["ref"]), str(row["alt"])),
            axis=1,
        )

    return result


def infer_variant_type(ref: str, alt: str) -> str:
    if len(ref) == 1 and len(alt) == 1:
        return "SNP"
    if len(ref) != len(alt):
        return "InDel"
    return "MNV"


def _require_pyfaidx() -> None:
    if Fasta is None:
        raise ImportError("pyfaidx is required. Run scripts/bootstrap_env.sh first.")


def open_reference(reference_fasta: str | Path):
    _require_pyfaidx()
    return Fasta(str(reference_fasta), as_raw=True, sequence_always_upper=True, rebuild=True)


def resolve_chrom_name(reference, chrom: str) -> str:
    if chrom in reference:
        return chrom
    lowercase = {name.lower(): name for name in reference.keys()}
    try:
        return lowercase[chrom.lower()]
    except KeyError as exc:
        raise KeyError(f"chromosome not found in reference FASTA: {chrom}") from exc


def validate_ref_allele(reference_fasta: str | Path, chrom: str, pos: int, ref: str) -> tuple[bool, str]:
    reference = open_reference(reference_fasta)
    chrom_name = resolve_chrom_name(reference, chrom)
    observed = reference[chrom_name][pos - 1 : pos - 1 + len(ref)].upper()
    return observed == ref.upper(), observed


def fetch_flanks(
    reference_fasta: str | Path,
    chrom: str,
    pos: int,
    ref: str,
    flank_size: int = 1000,
) -> dict[str, Any]:
    reference = open_reference(reference_fasta)
    chrom_name = resolve_chrom_name(reference, chrom)
    seq = reference[chrom_name]

    ref_ok, observed = validate_ref_allele(reference_fasta, chrom, pos, ref)
    if not ref_ok:
        raise ValueError(
            f"reference allele mismatch at {chrom}:{pos}. expected={ref.upper()} observed={observed}"
        )

    left_start = max(0, pos - 1 - flank_size)
    left_end = pos - 1
    right_start = pos - 1 + len(ref)
    right_end = min(len(seq), right_start + flank_size)

    left_flank = seq[left_start:left_end].upper()
    right_flank = seq[right_start:right_end].upper()
    return {
        "chrom_name": chrom_name,
        "left_flank": left_flank,
        "right_flank": right_flank,
        "left_flank_len": len(left_flank),
    }


def build_full_sequence(left_flank: str, ref: str, right_flank: str) -> str:
    return f"{left_flank.upper()}{ref.upper()}{right_flank.upper()}"


def attach_sequence_context(
    df: pd.DataFrame,
    reference_fasta: str | Path | None = None,
    flank_size: int = 1000,
    assume_left_flank: int = 1000,
) -> pd.DataFrame:
    result = df.copy()
    full_sequences: list[str] = []
    left_lengths: list[int] = []
    ref_valid_flags: list[bool | None] = []

    for row in result.to_dict("records"):
        ref = str(row["ref"]).upper()
        alt = str(row["alt"]).upper()

        existing_full_seq = str(row.get("full_seq", "")).strip()
        upstream_seq = str(row.get("upstream_seq", "")).strip()
        downstream_seq = str(row.get("downstream_seq", "")).strip()
        left_flank_len = row.get("left_flank_len")

        if existing_full_seq and existing_full_seq.lower() != "nan":
            full_seq = existing_full_seq.upper()
            if left_flank_len is None or pd.isna(left_flank_len):
                if upstream_seq and upstream_seq.lower() != "nan":
                    left_len = len(upstream_seq)
                else:
                    left_len = int(assume_left_flank)
            else:
                left_len = int(left_flank_len)

            if reference_fasta:
                ref_ok, observed = validate_ref_allele(reference_fasta, str(row["chrom"]), int(row["pos"]), ref)
                if not ref_ok:
                    raise ValueError(
                        f"reference allele mismatch at {row['chrom']}:{row['pos']}. "
                        f"expected={ref} observed={observed}"
                    )
                ref_valid_flags.append(True)
            else:
                ref_valid_flags.append(None)
        elif upstream_seq and upstream_seq.lower() != "nan" and downstream_seq and downstream_seq.lower() != "nan":
            full_seq = build_full_sequence(upstream_seq, ref, downstream_seq)
            left_len = len(upstream_seq)
            if reference_fasta:
                ref_ok, observed = validate_ref_allele(reference_fasta, str(row["chrom"]), int(row["pos"]), ref)
                if not ref_ok:
                    raise ValueError(
                        f"reference allele mismatch at {row['chrom']}:{row['pos']}. "
                        f"expected={ref} observed={observed}"
                    )
                ref_valid_flags.append(True)
            else:
                ref_valid_flags.append(None)
        else:
            if not reference_fasta:
                raise ValueError(
                    "reference FASTA is required when full_seq and flank sequences are not already present"
                )
            fetched = fetch_flanks(reference_fasta, str(row["chrom"]), int(row["pos"]), ref, flank_size)
            full_seq = build_full_sequence(fetched["left_flank"], ref, fetched["right_flank"])
            left_len = int(fetched["left_flank_len"])
            ref_valid_flags.append(True)

        full_sequences.append(full_seq)
        left_lengths.append(left_len)

        if "variant_type" not in result.columns or not str(row.get("variant_type", "")).strip():
            row["variant_type"] = infer_variant_type(ref, alt)

    result["full_seq"] = full_sequences
    result["left_flank_len"] = left_lengths
    if ref_valid_flags:
        result["ref_matches_reference"] = ref_valid_flags
    result["variant_type"] = result.apply(
        lambda row: infer_variant_type(str(row["ref"]), str(row["alt"])),
        axis=1,
    )
    return result
