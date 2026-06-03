#!/usr/bin/env python3
from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

import pandas as pd


FINAL_COLUMNS = [
    "name",
    "status",
    "reason",
    "chrom",
    "pos",
    "ref",
    "alt",
    "variant_type",
    "indel_size",
    "forward_name",
    "forward_seq",
    "forward_len",
    "forward_tm",
    "forward_gc",
    "reverse_name",
    "reverse_seq",
    "reverse_len",
    "reverse_tm",
    "reverse_gc",
    "product_wt",
    "product_mt",
    "tm_diff",
    "avg_tm",
    "avg_gc",
    "var_dist_f",
    "var_dist_r",
    "center_ratio",
    "score",
    "design_params",
    "selected_round",
    "redesigned",
    "specificity_status",
    "specificity_note",
    "forward_hits",
    "reverse_hits",
]


def _ensure_parent(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_tsv(df: pd.DataFrame, path: str | Path) -> Path:
    path = _ensure_parent(path)
    df.to_csv(path, sep="\t", index=False)
    return path


def write_xlsx(df: pd.DataFrame, path: str | Path, sheet_name: str = "Sheet1") -> Path:
    path = _ensure_parent(path)
    with pd.ExcelWriter(path) as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    return path


def build_order_table(final_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    columns = [
        "name",
        "primer_name",
        "direction",
        "sequence",
        "length",
        "design_params",
        "specificity_status",
    ]
    for row in final_df.to_dict("records"):
        if row.get("status") != "SUCCESS":
            continue
        rows.append(
            {
                "name": row["name"],
                "primer_name": row["forward_name"],
                "direction": "F",
                "sequence": row["forward_seq"],
                "length": row["forward_len"],
                "design_params": row["design_params"],
                "specificity_status": row["specificity_status"],
            }
        )
        rows.append(
            {
                "name": row["name"],
                "primer_name": row["reverse_name"],
                "direction": "R",
                "sequence": row["reverse_seq"],
                "length": row["reverse_len"],
                "design_params": row["design_params"],
                "specificity_status": row["specificity_status"],
            }
        )
    return pd.DataFrame(rows, columns=columns)


def build_specificity_table(final_df: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "name",
        "forward_name",
        "forward_hits",
        "reverse_name",
        "reverse_hits",
        "specificity_status",
        "specificity_note",
    ]
    existing = [column for column in columns if column in final_df.columns]
    return final_df[existing].copy()


def reorder_final_columns(final_df: pd.DataFrame) -> pd.DataFrame:
    ordered = [column for column in FINAL_COLUMNS if column in final_df.columns]
    extras = [column for column in final_df.columns if column not in ordered]
    return final_df[ordered + extras].copy()


def generate_report(final_df: pd.DataFrame, metadata: dict[str, Any], report_path: str | Path) -> Path:
    report_path = _ensure_parent(report_path)

    success_mask = final_df["status"].eq("SUCCESS")
    specific_mask = final_df.get("specificity_status", pd.Series(dtype=object)).eq("specific")
    non_specific_mask = final_df.get("specificity_status", pd.Series(dtype=object)).eq("non_specific")
    failure_counts = (
        final_df.loc[final_df["status"] != "SUCCESS", "reason"]
        .fillna("")
        .replace("", "unknown")
        .value_counts()
        .to_dict()
    )

    lines = [
        "=" * 72,
        "Primer Design Report",
        "=" * 72,
        "",
        "Run Metadata",
        "-" * 72,
        f"Timestamp: {metadata.get('timestamp', '')}",
        f"Input table: {metadata.get('input_path', '')}",
        f"Reference FASTA: {metadata.get('reference_fasta', '')}",
        f"BLAST DB prefix: {metadata.get('blast_db_prefix', '')}",
        f"Assay mode: {metadata.get('assay_mode', '')}",
        f"Flank size: {metadata.get('flank_size', '')}",
        f"Assumed left flank: {metadata.get('assume_left_flank', '')}",
        f"Python: {platform.python_version()}",
        f"Command: {metadata.get('command', '')}",
        "",
        "Summary",
        "-" * 72,
        f"Total loci: {len(final_df)}",
        f"Successful designs: {int(success_mask.sum())}",
        f"Specific primer pairs: {int((success_mask & specific_mask).sum())}",
        f"Non-specific primer pairs: {int((success_mask & non_specific_mask).sum())}",
        f"Failed loci: {int((~success_mask).sum())}",
        "",
        "Failure Reasons",
        "-" * 72,
    ]

    if failure_counts:
        for reason, count in failure_counts.items():
            lines.append(f"{reason}: {count}")
    else:
        lines.append("none")

    lines.extend(
        [
            "",
            "Round Summary",
            "-" * 72,
            f"Round 1 rows: {metadata.get('round1_rows', 0)}",
            f"Round 2 rows: {metadata.get('round2_rows', 0)}",
            "=" * 72,
            "",
        ]
    )

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def export_final_outputs(final_df: pd.DataFrame, output_dir: str | Path, metadata: dict[str, Any]) -> dict[str, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_df = final_df.drop(columns=["input_order"], errors="ignore")
    final_df = reorder_final_columns(final_df)
    specificity_df = build_specificity_table(final_df)
    order_df = build_order_table(final_df)

    paths = {
        "final_tsv": write_tsv(final_df, output_dir / "final_primers.tsv"),
        "final_xlsx": write_xlsx(final_df, output_dir / "final_primers.xlsx", sheet_name="final_primers"),
        "specificity_tsv": write_tsv(specificity_df, output_dir / "primer_specificity.tsv"),
        "specificity_xlsx": write_xlsx(
            specificity_df,
            output_dir / "primer_specificity.xlsx",
            sheet_name="primer_specificity",
        ),
        "order_tsv": write_tsv(order_df, output_dir / "primer_order.tsv"),
        "order_xlsx": write_xlsx(order_df, output_dir / "primer_order.xlsx", sheet_name="primer_order"),
        "report": generate_report(final_df, metadata, output_dir / "design_report.txt"),
    }
    return paths
