#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill


FIELDS = ["relative_stem", "review_focus", "visual_status", "action_taken"]
PASS_STATUSES = {"PASS", "PASS_AFTER_FIX"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and record a completed manual figure review.")
    parser.add_argument("--result-dir", required=True)
    parser.add_argument("--review-input", required=True)
    parser.add_argument("--out-stem", required=True)
    return parser.parse_args()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    args = parse_args()
    result_dir = Path(args.result_dir).resolve()
    review_path = Path(args.review_input).resolve()
    out_stem = Path(args.out_stem).resolve()
    manifest = read_tsv(result_dir / "summary" / "figure_manifest.tsv")
    reviews = read_tsv(review_path)
    if list(reviews[0]) != FIELDS:
        raise SystemExit(f"Review columns must be exactly: {FIELDS}")
    expected = {row["relative_stem"] for row in manifest}
    observed = {row["relative_stem"] for row in reviews}
    if expected != observed or len(reviews) != len(expected):
        raise SystemExit(f"Review/manifest mismatch: missing={sorted(expected - observed)} extra={sorted(observed - expected)}")
    review_time = datetime.now().astimezone().isoformat(timespec="seconds")
    rows: list[dict[str, str]] = []
    for row in reviews:
        if row["visual_status"] not in PASS_STATUSES:
            raise SystemExit(f"Non-passing review status for {row['relative_stem']}: {row['visual_status']}")
        if not row["review_focus"].strip() or not row["action_taken"].strip():
            raise SystemExit(f"Incomplete review evidence: {row['relative_stem']}")
        pdf = result_dir / "figures" / f"{row['relative_stem']}.pdf"
        png = result_dir / "figures" / f"{row['relative_stem']}.png"
        if not pdf.exists() or not png.exists():
            raise SystemExit(f"Reviewed figure pair is missing: {row['relative_stem']}")
        rows.append({
            **row,
            "reviewer": "Codex manual publication audit",
            "review_time": review_time,
            "evidence_png": str(png),
        })
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with out_stem.with_suffix(".tsv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, delimiter="\t", lineterminator="\n", fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "visual_review"
    worksheet.append(fields)
    for cell in worksheet[1]:
        cell.font = Font(name="Arial", bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for row in rows:
        worksheet.append([row[field] for field in fields])
    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    for column, width in zip("ABCDEFG", (58, 58, 18, 70, 34, 28, 90)):
        worksheet.column_dimensions[column].width = width
    workbook.save(out_stem.with_suffix(".xlsx"))
    print(f"[visual-review] PASS rows={len(rows)} output={out_stem}")


if __name__ == "__main__":
    main()
