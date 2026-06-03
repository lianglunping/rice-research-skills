#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path


CATEGORY_PRIORITY = ["PAIR", "UNPAIRED", "SAMPLE", "FIRST_OF_PAIR", "SECOND_OF_PAIR"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate mapping QC metrics.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate = subparsers.add_parser("evaluate", help="Evaluate one sample.")
    evaluate.add_argument("--sample", required=True)
    evaluate.add_argument("--picard")
    evaluate.add_argument("--flagstat")
    evaluate.add_argument(
        "--metric",
        choices=["auto", "picard_pct_pf_reads_aligned", "flagstat_mapped_pct"],
        default="auto",
    )
    evaluate.add_argument("--warn-below", type=float, required=True)
    evaluate.add_argument("--drop-below", type=float)
    evaluate.add_argument("--output-tsv", required=True)
    evaluate.add_argument("--output-json")

    aggregate = subparsers.add_parser("aggregate", help="Aggregate per-sample summaries.")
    aggregate.add_argument("--inputs", nargs="+", required=True)
    aggregate.add_argument("--action", choices=["mark", "drop"], default="mark")
    aggregate.add_argument("--output-passing", required=True)
    aggregate.add_argument("--output-excluded", required=True)
    aggregate.add_argument("--output-summary", required=True)

    return parser.parse_args()


def read_picard_alignment_summary(path: Path) -> tuple[float, str]:
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    with path.open() as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.startswith("## HISTOGRAM"):
                break
            if not line:
                if header and rows:
                    break
                continue
            if line.startswith("##"):
                continue
            fields = line.split("\t")
            if header is None:
                header = fields
                continue
            if len(fields) == len(header):
                rows.append(dict(zip(header, fields)))

    if not header or "PCT_PF_READS_ALIGNED" not in header or not rows:
        raise ValueError(f"Could not parse Picard alignment metrics from {path}")

    def category_rank(row: dict[str, str]) -> tuple[int, str]:
        category = row.get("CATEGORY", "")
        if category in CATEGORY_PRIORITY:
            return (CATEGORY_PRIORITY.index(category), category)
        return (len(CATEGORY_PRIORITY), category)

    chosen = sorted(rows, key=category_rank)[0]
    return (float(chosen["PCT_PF_READS_ALIGNED"]), chosen.get("CATEGORY", ""))


def _extract_numeric_percent(value: object) -> float | None:
    if isinstance(value, (int, float)):
        value = float(value)
        if value > 1:
            return value / 100.0
        return value
    if isinstance(value, str):
        match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
        if not match:
            return None
        number = float(match.group(1))
        if "%" in value or number > 1:
            return number / 100.0
        return number
    return None


def _search_for_percent(obj: object) -> float | None:
    preferred_keys = {
        "mapped %",
        "mapped_pct",
        "mapped_percent",
        "mapped percentage",
        "mapped_percentage",
    }
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).strip().lower() in preferred_keys:
                found = _extract_numeric_percent(value)
                if found is not None:
                    return found
        for value in obj.values():
            found = _search_for_percent(value)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _search_for_percent(item)
            if found is not None:
                return found
    return None


def read_flagstat(path: Path) -> float:
    text = path.read_text().strip()
    if not text:
        raise ValueError(f"Empty flagstat file: {path}")

    if text[0] in "[{":
        data = json.loads(text)
        found = _search_for_percent(data)
        if found is not None:
            return found

    for line in text.splitlines():
        if " mapped (" not in line:
            continue
        match = re.search(r"\(([0-9]+(?:\.[0-9]+)?)%", line)
        if match:
            return float(match.group(1)) / 100.0

    raise ValueError(f"Could not parse mapped percentage from {path}")


def decide_status(mapping_rate: float, warn_below: float, drop_below: float | None) -> str:
    if drop_below is not None and mapping_rate < drop_below:
        return "DROP"
    if mapping_rate < warn_below:
        return "WARN"
    return "PASS"


def write_single_summary(
    sample: str,
    metric_source: str,
    mapping_rate: float,
    warn_below: float,
    drop_below: float | None,
    status: str,
    output_tsv: Path,
    output_json: Path | None,
) -> None:
    row = {
        "sample": sample,
        "metric_source": metric_source,
        "mapping_rate": f"{mapping_rate:.6f}",
        "warn_below": f"{warn_below:.6f}",
        "drop_below": "" if drop_below is None else f"{drop_below:.6f}",
        "status": status,
        "action": "review" if status == "WARN" else status.lower(),
    }

    output_tsv.parent.mkdir(parents=True, exist_ok=True)
    with output_tsv.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()), delimiter="\t")
        writer.writeheader()
        writer.writerow(row)

    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(row, indent=2) + "\n")


def evaluate(args: argparse.Namespace) -> int:
    picard_path = Path(args.picard) if args.picard else None
    flagstat_path = Path(args.flagstat) if args.flagstat else None

    metric = args.metric
    if metric == "auto":
        if picard_path is not None:
            metric = "picard_pct_pf_reads_aligned"
        elif flagstat_path is not None:
            metric = "flagstat_mapped_pct"
        else:
            raise ValueError("At least one metric source is required for auto mode.")

    if metric == "picard_pct_pf_reads_aligned":
        if picard_path is None:
            raise ValueError("Picard metrics are required for picard_pct_pf_reads_aligned.")
        mapping_rate, category = read_picard_alignment_summary(picard_path)
        metric_source = f"picard_pct_pf_reads_aligned:{category or 'NA'}"
    else:
        if flagstat_path is None:
            raise ValueError("Flagstat output is required for flagstat_mapped_pct.")
        mapping_rate = read_flagstat(flagstat_path)
        metric_source = "flagstat_mapped_pct"

    status = decide_status(mapping_rate, args.warn_below, args.drop_below)
    write_single_summary(
        sample=args.sample,
        metric_source=metric_source,
        mapping_rate=mapping_rate,
        warn_below=args.warn_below,
        drop_below=args.drop_below,
        status=status,
        output_tsv=Path(args.output_tsv),
        output_json=Path(args.output_json) if args.output_json else None,
    )
    return 0


def read_single_summary(path: Path) -> dict[str, str]:
    with path.open() as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        rows = list(reader)
    if len(rows) != 1:
        raise ValueError(f"Expected one row in {path}, found {len(rows)}")
    return rows[0]


def aggregate(args: argparse.Namespace) -> int:
    rows = [read_single_summary(Path(path)) for path in args.inputs]
    rows.sort(key=lambda row: row["sample"])

    for row in rows:
        if args.action == "drop" and row["status"] == "DROP":
            row["pipeline_action"] = "exclude"
        elif row["status"] == "WARN":
            row["pipeline_action"] = "mark"
        else:
            row["pipeline_action"] = "keep"

    summary_path = Path(args.output_summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    passing = [row["sample"] for row in rows if row["pipeline_action"] != "exclude"]
    excluded = [row for row in rows if row["pipeline_action"] == "exclude"]

    passing_path = Path(args.output_passing)
    passing_path.parent.mkdir(parents=True, exist_ok=True)
    with passing_path.open("w") as handle:
        for sample in passing:
            handle.write(f"{sample}\n")

    excluded_path = Path(args.output_excluded)
    excluded_path.parent.mkdir(parents=True, exist_ok=True)
    with excluded_path.open("w", newline="") as handle:
        fieldnames = ["sample", "metric_source", "mapping_rate", "status", "pipeline_action"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in excluded:
            writer.writerow({key: row[key] for key in fieldnames})

    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "evaluate":
            return evaluate(args)
        if args.command == "aggregate":
            return aggregate(args)
        raise ValueError(f"Unsupported command: {args.command}")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
