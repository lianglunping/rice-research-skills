#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd


BLAST_COLUMNS = [
    "qseqid",
    "sseqid",
    "pident",
    "length",
    "qlen",
    "qstart",
    "qend",
    "mismatch",
    "gaps",
    "evalue",
    "bitscore",
]


def ensure_blast_db(reference_fasta: str | Path, db_dir: str | Path) -> Path:
    reference_fasta = Path(reference_fasta)
    db_dir = Path(db_dir)
    db_dir.mkdir(parents=True, exist_ok=True)
    db_prefix = db_dir / reference_fasta.stem

    existing_suffixes = [".nhr", ".00.nhr", ".ndb"]
    if not any((db_prefix.with_suffix(suffix)).exists() for suffix in existing_suffixes):
        cmd = [
            "makeblastdb",
            "-in",
            str(reference_fasta),
            "-dbtype",
            "nucl",
            "-out",
            str(db_prefix),
        ]
        subprocess.run(cmd, check=True)
    return db_prefix


def write_primer_fasta(results_df: pd.DataFrame, fasta_path: str | Path) -> Path:
    fasta_path = Path(fasta_path)
    fasta_path.parent.mkdir(parents=True, exist_ok=True)

    with fasta_path.open("w", encoding="utf-8") as handle:
        for row in results_df.to_dict("records"):
            if row.get("status") != "SUCCESS":
                continue
            handle.write(f">{row['forward_name']}\n{row['forward_seq']}\n")
            handle.write(f">{row['reverse_name']}\n{row['reverse_seq']}\n")

    return fasta_path


def run_blast_short(
    query_fasta: str | Path,
    db_prefix: str | Path,
    out_tsv: str | Path,
    threads: int = 4,
) -> Path:
    out_tsv = Path(out_tsv)
    out_tsv.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "blastn",
        "-task",
        "blastn-short",
        "-query",
        str(query_fasta),
        "-db",
        str(db_prefix),
        "-out",
        str(out_tsv),
        "-dust",
        "no",
        "-soft_masking",
        "false",
        "-evalue",
        "1000",
        "-word_size",
        "7",
        "-num_threads",
        str(threads),
        "-outfmt",
        "6 qseqid sseqid pident length qlen qstart qend mismatch gaps evalue bitscore",
    ]
    subprocess.run(cmd, check=True)
    return out_tsv


def load_blast_results(blast_tsv: str | Path) -> pd.DataFrame:
    blast_tsv = Path(blast_tsv)
    if not blast_tsv.exists() or blast_tsv.stat().st_size == 0:
        return pd.DataFrame(columns=BLAST_COLUMNS)
    return pd.read_csv(blast_tsv, sep="\t", names=BLAST_COLUMNS)


def summarize_primer_hits(
    blast_tsv: str | Path,
    min_identity: float = 95.0,
    min_coverage: float = 0.95,
) -> pd.DataFrame:
    blast_df = load_blast_results(blast_tsv)
    if blast_df.empty:
        return pd.DataFrame(columns=["qseqid", "hit_count"])

    blast_df["coverage"] = blast_df["length"] / blast_df["qlen"]
    filtered = blast_df[
        (blast_df["pident"] >= min_identity) & (blast_df["coverage"] >= min_coverage)
    ].copy()

    if filtered.empty:
        return pd.DataFrame(columns=["qseqid", "hit_count"])

    summary = (
        filtered.groupby("qseqid", as_index=False)
        .size()
        .rename(columns={"size": "hit_count"})
        .sort_values("qseqid")
    )
    return summary


def annotate_specificity(results_df: pd.DataFrame, hit_summary: pd.DataFrame) -> pd.DataFrame:
    hit_map = {}
    if not hit_summary.empty:
        hit_map = hit_summary.set_index("qseqid")["hit_count"].to_dict()

    annotated = results_df.copy()
    annotated["forward_hits"] = annotated["forward_name"].map(hit_map).fillna(0).astype(int)
    annotated["reverse_hits"] = annotated["reverse_name"].map(hit_map).fillna(0).astype(int)

    specificity_status: list[str] = []
    specificity_note: list[str] = []
    for row in annotated.to_dict("records"):
        if row.get("status") != "SUCCESS":
            specificity_status.append("not_designed")
            specificity_note.append("")
            continue
        note = f"F:{int(row['forward_hits'])}, R:{int(row['reverse_hits'])}"
        specificity_note.append(note)
        if int(row["forward_hits"]) == 1 and int(row["reverse_hits"]) == 1:
            specificity_status.append("specific")
        else:
            specificity_status.append("non_specific")

    annotated["specificity_status"] = specificity_status
    annotated["specificity_note"] = specificity_note
    return annotated
