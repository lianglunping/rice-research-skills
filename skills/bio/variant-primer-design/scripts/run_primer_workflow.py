#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import shlex
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from blast_specificity import (  # noqa: E402
    annotate_specificity,
    ensure_blast_db,
    run_blast_short,
    summarize_primer_hits,
    write_primer_fasta,
)
from export_outputs import export_final_outputs, write_tsv  # noqa: E402
from primer_core import PrimerConstraints, VariantRecord, design_batch  # noqa: E402
from sequence_context import attach_sequence_context, load_table, normalize_variant_table  # noqa: E402


SUPPORTED_ASSAYS = {"indel_pcr", "snp_pcr"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Variant primer workflow with BLAST specificity screening")
    parser.add_argument("--input", required=True, help="Input variant table (xlsx/csv/tsv)")
    parser.add_argument("--reference-fasta", help="Reference FASTA for sequence context and/or BLAST DB creation")
    parser.add_argument("--blast-db-prefix", help="Prebuilt BLAST database prefix")
    parser.add_argument(
        "--assay-mode",
        required=True,
        choices=sorted(SUPPORTED_ASSAYS),
        help="Supported v1 assay mode",
    )
    parser.add_argument("--output-dir", help="Output directory. Defaults to outputs/primer_design_TIMESTAMP")
    parser.add_argument("--flank-size", type=int, default=1000, help="Flank size for building full sequence")
    parser.add_argument(
        "--assume-left-flank",
        type=int,
        default=1000,
        help="Fallback left flank length when full_seq is supplied without left_flank_len",
    )
    parser.add_argument("--threads", type=int, default=4, help="Threads for blastn")
    parser.add_argument("--min-identity", type=float, default=95.0, help="Minimum BLAST percent identity")
    parser.add_argument("--min-coverage", type=float, default=0.95, help="Minimum BLAST query coverage")
    return parser


def default_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path.cwd() / "outputs" / f"primer_design_{timestamp}"


def build_records(df: pd.DataFrame) -> list[VariantRecord]:
    records: list[VariantRecord] = []
    reserved = {
        "name",
        "chrom",
        "pos",
        "ref",
        "alt",
        "full_seq",
        "left_flank_len",
        "variant_type",
        "ref_matches_reference",
    }
    for index, row in enumerate(df.to_dict("records")):
        metadata = {key: value for key, value in row.items() if key not in reserved}
        metadata["input_order"] = index
        records.append(
            VariantRecord(
                name=str(row["name"]),
                chrom=str(row["chrom"]),
                pos=int(row["pos"]),
                ref=str(row["ref"]),
                alt=str(row["alt"]),
                full_seq=str(row["full_seq"]),
                left_flank_len=int(row["left_flank_len"]),
                variant_type=str(row.get("variant_type", "InDel")),
                metadata=metadata,
            )
        )
    return records


def results_to_frame(records: list[VariantRecord], raw_results: list[dict[str, Any]]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for record, result in zip(records, raw_results):
        row = {
            "name": record.name,
            "chrom": record.chrom,
            "pos": record.pos,
            "ref": record.ref,
            "alt": record.alt,
            "variant_type": record.variant_type,
            **record.metadata,
            **result,
        }
        rows.append(row)
    return pd.DataFrame(rows)


def annotate_round(
    round_df: pd.DataFrame,
    round_label: str,
    intermediate_dir: Path,
    db_prefix: Path,
    threads: int,
    min_identity: float,
    min_coverage: float,
) -> pd.DataFrame:
    annotated = round_df.copy()
    success_rows = annotated[annotated["status"] == "SUCCESS"].copy()

    if success_rows.empty:
        annotated["forward_hits"] = 0
        annotated["reverse_hits"] = 0
        annotated["specificity_status"] = "not_designed"
        annotated["specificity_note"] = ""
        write_tsv(annotated, intermediate_dir / f"{round_label}_results.tsv")
        return annotated

    fasta_path = intermediate_dir / f"{round_label}_primers.fa"
    blast_path = intermediate_dir / f"{round_label}_blast.tsv"
    write_primer_fasta(success_rows, fasta_path)
    run_blast_short(fasta_path, db_prefix, blast_path, threads=threads)
    hit_summary = summarize_primer_hits(blast_path, min_identity=min_identity, min_coverage=min_coverage)
    annotated = annotate_specificity(annotated, hit_summary)
    write_tsv(annotated, intermediate_dir / f"{round_label}_results.tsv")
    return annotated


def choose_final_row(round1_row: pd.Series, round2_row: pd.Series | None) -> pd.Series:
    if round2_row is not None and round2_row["status"] == "SUCCESS" and round2_row["specificity_status"] == "specific":
        return round2_row
    if round1_row["status"] == "SUCCESS" and round1_row["specificity_status"] == "specific":
        return round1_row
    if round2_row is not None and round2_row["status"] == "SUCCESS":
        return round2_row
    if round1_row["status"] == "SUCCESS":
        return round1_row
    if round2_row is not None:
        return round2_row
    return round1_row


def merge_rounds(round1_df: pd.DataFrame, round2_df: pd.DataFrame | None) -> pd.DataFrame:
    round1_map = {row["name"]: row for _, row in round1_df.iterrows()}
    round2_map = {}
    if round2_df is not None and not round2_df.empty:
        round2_map = {row["name"]: row for _, row in round2_df.iterrows()}

    final_rows: list[dict[str, Any]] = []
    ordered_names = round1_df.sort_values("input_order")["name"].tolist()

    for name in ordered_names:
        round1_row = round1_map[name]
        round2_row = round2_map.get(name)
        selected = choose_final_row(round1_row, round2_row)
        row_dict = selected.to_dict()
        row_dict["selected_round"] = 2 if round2_row is not None and selected.equals(round2_row) else 1
        row_dict["redesigned"] = "yes" if round2_row is not None else "no"
        final_rows.append(row_dict)

    final_df = pd.DataFrame(final_rows).sort_values("input_order").reset_index(drop=True)
    return final_df


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.reference_fasta and not args.blast_db_prefix:
        parser.error("one of --reference-fasta or --blast-db-prefix is required for BLAST specificity screening")

    output_dir = Path(args.output_dir) if args.output_dir else default_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    intermediate_dir = output_dir / "intermediate"
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    input_df = load_table(args.input)
    normalized_df = normalize_variant_table(input_df)

    has_full_seq = "full_seq" in normalized_df.columns and normalized_df["full_seq"].astype(str).str.strip().ne("").all()
    if not has_full_seq and not args.reference_fasta:
        parser.error("--reference-fasta is required when the input does not already contain full_seq")

    prepared_df = attach_sequence_context(
        normalized_df,
        reference_fasta=args.reference_fasta,
        flank_size=args.flank_size,
        assume_left_flank=args.assume_left_flank,
    )
    records = build_records(prepared_df)

    db_prefix = Path(args.blast_db_prefix) if args.blast_db_prefix else ensure_blast_db(args.reference_fasta, output_dir / "blast_db")

    round1_raw = design_batch(records, PrimerConstraints.strict(), "strict")
    round1_df = results_to_frame(records, round1_raw)
    round1_df = annotate_round(
        round1_df,
        round_label="round1",
        intermediate_dir=intermediate_dir,
        db_prefix=db_prefix,
        threads=args.threads,
        min_identity=args.min_identity,
        min_coverage=args.min_coverage,
    )

    redesign_names = round1_df.loc[
        ~(
            (round1_df["status"] == "SUCCESS")
            & (round1_df["specificity_status"] == "specific")
        ),
        "name",
    ].tolist()

    round2_df: pd.DataFrame | None = None
    if redesign_names:
        redesign_records = [record for record in records if record.name in set(redesign_names)]
        round2_raw = design_batch(redesign_records, PrimerConstraints.relaxed(), "relaxed")
        round2_df = results_to_frame(redesign_records, round2_raw)
        round2_df = annotate_round(
            round2_df,
            round_label="round2",
            intermediate_dir=intermediate_dir,
            db_prefix=db_prefix,
            threads=args.threads,
            min_identity=args.min_identity,
            min_coverage=args.min_coverage,
        )

    final_df = merge_rounds(round1_df, round2_df)

    metadata = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "input_path": str(Path(args.input).resolve()),
        "reference_fasta": str(Path(args.reference_fasta).resolve()) if args.reference_fasta else "",
        "blast_db_prefix": str(db_prefix),
        "assay_mode": args.assay_mode,
        "flank_size": args.flank_size,
        "assume_left_flank": args.assume_left_flank,
        "command": " ".join(shlex.quote(part) for part in ([sys.executable] + sys.argv)),
        "python": platform.python_version(),
        "round1_rows": len(round1_df),
        "round2_rows": 0 if round2_df is None else len(round2_df),
    }

    export_final_outputs(final_df, output_dir, metadata)
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
