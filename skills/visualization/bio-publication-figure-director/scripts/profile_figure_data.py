#!/usr/bin/env python3
"""Profile a tabular dataset for scientific figure planning.

This is a read-only profiler. It reports facts and conservative plotting prompts;
it does not choose a statistical test or claim biological significance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit(
        "profile_figure_data.py requires pandas and numpy in the active project "
        "environment; do not install them globally without approval."
    ) from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_table(path: Path, sheet: str | int | None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    lowered_name = path.name.casefold()
    if suffix == ".csv" or lowered_name.endswith(".csv.gz"):
        return pd.read_csv(path)
    if suffix in {".tsv", ".txt"} or lowered_name.endswith(".tsv.gz"):
        return pd.read_csv(path, sep="\t")
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        selected: str | int = 0 if sheet is None else sheet
        if isinstance(selected, str) and selected.isdigit():
            selected = int(selected)
        return pd.read_excel(path, sheet_name=selected)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(
        f"unsupported input format {suffix!r}; use CSV, TSV/TXT, XLSX/XLSM/XLS, or Parquet"
    )


def finite_number(value: Any) -> float | int | None:
    if value is None or pd.isna(value):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return int(number) if number.is_integer() else number


def classify_column(series: pd.Series, name: str) -> str:
    clean = series.dropna()
    lowered = name.casefold()
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_numeric_dtype(series):
        if lowered in {"start", "end", "pos", "position", "bp", "coordinate"}:
            return "numeric_coordinate"
        unique_ratio = clean.nunique(dropna=True) / max(len(clean), 1)
        id_hint = any(
            token in lowered
            for token in ("id", "sample", "accession", "barcode", "line", "plant")
        )
        if id_hint and unique_ratio > 0.8:
            return "numeric_identifier"
        if clean.nunique(dropna=True) <= min(12, max(2, len(clean) // 10)):
            return "numeric_discrete"
        return "numeric_continuous"
    if isinstance(series.dtype, pd.CategoricalDtype):
        return "categorical"
    unique = clean.nunique(dropna=True)
    unique_ratio = unique / max(len(clean), 1)
    if unique_ratio > 0.9:
        return "identifier_or_text"
    if unique <= 30:
        return "categorical"
    return "text"


def numeric_profile(series: pd.Series) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {}
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        outliers = 0
    else:
        outliers = int(((values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)).sum())
    return {
        "min": finite_number(values.min()),
        "q1": finite_number(q1),
        "median": finite_number(values.median()),
        "mean": finite_number(values.mean()),
        "q3": finite_number(q3),
        "max": finite_number(values.max()),
        "sd": finite_number(values.std(ddof=1)) if len(values) > 1 else None,
        "skew": finite_number(values.skew()) if len(values) > 2 else None,
        "iqr_outliers": outliers,
        "zeros": int((values == 0).sum()),
        "negative": int((values < 0).sum()),
    }


def build_profile(df: pd.DataFrame, source: Path, groups: list[str]) -> dict[str, Any]:
    columns: list[dict[str, Any]] = []
    for name in df.columns:
        series = df[name]
        kind = classify_column(series, str(name))
        clean = series.dropna()
        item: dict[str, Any] = {
            "name": str(name),
            "kind": kind,
            "dtype": str(series.dtype),
            "non_missing": int(series.notna().sum()),
            "missing": int(series.isna().sum()),
            "missing_pct": round(float(series.isna().mean() * 100), 3),
            "unique": int(clean.nunique(dropna=True)),
        }
        if kind.startswith("numeric_"):
            item["summary"] = numeric_profile(series)
        elif kind in {"categorical", "boolean"}:
            counts = clean.astype(str).value_counts(dropna=False).head(20)
            item["top_levels"] = {str(k): int(v) for k, v in counts.items()}
        columns.append(item)

    group_profiles: list[dict[str, Any]] = []
    for group in groups:
        if group not in df.columns:
            group_profiles.append({"column": group, "error": "column not found"})
            continue
        counts = df[group].astype("string").fillna("<NA>").value_counts(dropna=False)
        group_profiles.append(
            {
                "column": group,
                "levels": int(len(counts)),
                "min_n": int(counts.min()) if len(counts) else 0,
                "max_n": int(counts.max()) if len(counts) else 0,
                "counts": {str(k): int(v) for k, v in counts.head(50).items()},
            }
        )

    numeric_names = [
        item["name"]
        for item in columns
        if item["kind"] == "numeric_continuous"
    ]
    correlation: dict[str, dict[str, float | None]] = {}
    if 2 <= len(numeric_names) <= 20:
        matrix = df[numeric_names].corr(method="pearson", min_periods=3)
        correlation = {
            row: {
                col: finite_number(value)
                for col, value in matrix.loc[row].items()
            }
            for row in matrix.index
        }

    prompts = recommend(columns, group_profiles, len(df))
    return {
        "source": str(source.resolve()),
        "sha256": sha256(source),
        "rows": int(len(df)),
        "columns_count": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": columns,
        "groups": group_profiles,
        "pearson_correlation": correlation,
        "plotting_prompts": prompts,
        "boundary": (
            "These are descriptive facts and plotting prompts, not evidence of "
            "significance, causality, validation, or biological mechanism."
        ),
    }


def recommend(
    columns: list[dict[str, Any]], groups: list[dict[str, Any]], rows: int
) -> list[str]:
    prompts: list[str] = []
    numeric = [item for item in columns if item["kind"] == "numeric_continuous"]
    coordinates = [item for item in columns if item["kind"] == "numeric_coordinate"]
    categorical = [item for item in columns if item["kind"] == "categorical"]
    if rows == 0:
        return ["Input table has zero rows; stop before figure design."]
    if any(item["missing_pct"] > 20 for item in columns):
        prompts.append("At least one column has >20% missing values; show or justify missingness.")
    for group in groups:
        if "error" in group:
            prompts.append(f"Requested group {group['column']!r} is absent.")
        elif group["min_n"] < 3:
            prompts.append(
                f"Group {group['column']!r} has a level with n<3; show every point "
                "and avoid box/violin summaries or inferential decoration."
            )
        elif group["min_n"] < 10:
            prompts.append(
                f"Group {group['column']!r} has a level with n<10; show individual "
                "points rather than a mean-only bar."
            )
        if group.get("levels", 0) > 12:
            prompts.append(
                f"Group {group['column']!r} has >12 levels; aggregate, facet, or split the figure."
            )
    coordinate_names = {item["name"].casefold() for item in coordinates}
    if {"start", "end"}.issubset(coordinate_names) or {
        "chr",
        "pos",
    }.issubset({item["name"].casefold() for item in columns}):
        prompts.append(
            "Genomic coordinate columns detected; verify reference assembly, coordinate "
            "basis, contig naming, strand, and interval semantics before choosing a track "
            "or chromosome view."
        )
    if len(numeric) == 1:
        prompts.append("One continuous variable: inspect distribution with points/histogram/ECDF.")
    elif len(numeric) == 2:
        prompts.append(
            "Two continuous variables: consider scatter/hexbin with fit and uncertainty "
            "only if that matches the scientific claim."
        )
    elif len(numeric) > 2:
        prompts.append(
            "Multiple continuous variables: consider a correlation heatmap or selected "
            "pairwise panels; state scaling and clustering choices."
        )
    if categorical and numeric:
        prompts.append(
            "Categorical + continuous variables: choose point/box/violin or model estimates "
            "according to group n and experimental design."
        )
    if any(
        abs(item.get("summary", {}).get("skew") or 0) > 1.5 for item in numeric
    ):
        prompts.append(
            "At least one continuous variable is strongly skewed; inspect raw and transformed "
            "scales and label any log transform explicitly."
        )
    if not prompts:
        prompts.append("No automatic chart warning fired; select the figure from the core claim.")
    return prompts


def markdown_report(profile: dict[str, Any]) -> str:
    lines = [
        "# Figure data profile",
        "",
        f"- Source: `{profile['source']}`",
        f"- SHA256: `{profile['sha256']}`",
        f"- Shape: {profile['rows']} rows x {profile['columns_count']} columns",
        f"- Duplicate rows: {profile['duplicate_rows']}",
        "",
        "## Columns",
        "",
        "| column | kind | non-missing | missing % | unique |",
        "|---|---:|---:|---:|---:|",
    ]
    for item in profile["columns"]:
        lines.append(
            f"| {item['name']} | {item['kind']} | {item['non_missing']} | "
            f"{item['missing_pct']:.3f} | {item['unique']} |"
        )
    if profile["groups"]:
        lines.extend(["", "## Groups", ""])
        for group in profile["groups"]:
            if "error" in group:
                lines.append(f"- `{group['column']}`: {group['error']}")
            else:
                lines.append(
                    f"- `{group['column']}`: {group['levels']} levels, "
                    f"min n={group['min_n']}, max n={group['max_n']}"
                )
    lines.extend(["", "## Plotting prompts", ""])
    lines.extend(f"- {item}" for item in profile["plotting_prompts"])
    lines.extend(["", f"> Boundary: {profile['boundary']}"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only profiling for publication-figure planning."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("--sheet", help="Excel sheet name or zero-based index")
    parser.add_argument("--group", action="append", default=[], help="Grouping column")
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown"
    )
    parser.add_argument("--output", type=Path, help="Optional report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser()
    if not source.is_file():
        print(f"[FAIL] input file not found: {source}", file=sys.stderr)
        return 2
    try:
        frame = load_table(source, args.sheet)
        profile = build_profile(frame, source, args.group)
    except Exception as exc:
        print(f"[FAIL] could not profile {source}: {exc}", file=sys.stderr)
        return 2
    report = (
        json.dumps(profile, ensure_ascii=False, indent=2)
        if args.format == "json"
        else markdown_report(profile)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + ("" if report.endswith("\n") else "\n"), encoding="utf-8")
        print(f"[OK] wrote {args.output}")
    else:
        print(report, end="" if report.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
