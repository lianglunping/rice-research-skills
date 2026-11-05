#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

from openpyxl import load_workbook


def workbook_schema(path: Path) -> dict[str, list[str]]:
    workbook = load_workbook(path, read_only=True, data_only=False)
    output: dict[str, list[str]] = {}
    try:
        for sheet in workbook.worksheets:
            rows = [list(row) for row in sheet.iter_rows(values_only=True)]
            header = next((row for row in rows if sum(value is not None for value in row) >= 2), None)
            if header is None:
                raise ValueError(f"No tabular header found: {path}:{sheet.title}")
            output[sheet.title] = [str(value) for value in header if value is not None]
    finally:
        workbook.close()
    return output


def delimited_header(path: Path, delimiter: str) -> list[str]:
    with path.open(newline="") as handle:
        return next(csv.reader(handle, delimiter=delimiter), [])


def dictionary_row_present(text: str, column: str) -> bool:
    escaped = re.escape(column)
    pattern = rf"^\|\s*`?{escaped}`?\s*\|\s*[^|\s][^|]*\|\s*[^|]*\|\s*[^|]*\|\s*$"
    return re.search(pattern, text, flags=re.MULTILINE) is not None


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate recursive table README and schema coverage.")
    parser.add_argument("--table-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    table = Path(args.table_dir).resolve()
    output = Path(args.output).resolve()
    if not table.is_dir():
        raise SystemExit(f"Missing table directory: {table}")

    checks: list[dict[str, str]] = []

    def add(name: str, errors: list[str]) -> None:
        checks.append({"check": name, "status": "PASS" if not errors else "FAIL", "detail": "; ".join(errors)})

    directories = sorted(path for path in [table, *table.rglob("*")] if path.is_dir())
    add("recursive_readme_coverage", [str(path.relative_to(table)) for path in directories if not (path / "README.md").is_file()])

    inventory_errors: list[str] = []
    for directory in directories:
        readme = directory / "README.md"
        if not readme.is_file():
            continue
        text = readme.read_text()
        for child in directory.iterdir():
            if child.name != "README.md" and child.name not in text:
                inventory_errors.append(f"{directory.relative_to(table)}::{child.name}")
    add("immediate_child_inventory", inventory_errors)

    xlsx_errors: list[str] = []
    for path in sorted(table.rglob("*.xlsx")):
        text = (path.parent / "README.md").read_text()
        if path.name not in text:
            xlsx_errors.append(f"file::{path.relative_to(table)}")
        for sheet, columns in workbook_schema(path).items():
            if sheet not in text:
                xlsx_errors.append(f"sheet::{path.relative_to(table)}::{sheet}")
            for column in columns:
                if not dictionary_row_present(text, column):
                    xlsx_errors.append(f"column::{path.relative_to(table)}::{sheet}::{column}")
    add("xlsx_sheet_column_dictionary", xlsx_errors)

    delimited_errors: list[str] = []
    for suffix, delimiter in (("*.tsv", "\t"), ("*.csv", ",")):
        for path in sorted(table.rglob(suffix)):
            text = (path.parent / "README.md").read_text()
            if path.name not in text:
                delimited_errors.append(f"file::{path.relative_to(table)}")
            for column in delimited_header(path, delimiter):
                if not dictionary_row_present(text, column):
                    delimited_errors.append(f"column::{path.relative_to(table)}::{column}")
    add("delimited_table_column_dictionary", delimited_errors)

    vcf_errors: list[str] = []
    for path in sorted(table.rglob("*.vcf.gz")):
        text = (path.parent / "README.md").read_text()
        required = [path.name, "#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT", "GT", ".tbi"]
        vcf_errors.extend(f"{path.relative_to(table)}::{term}" for term in required if term not in text)
    add("vcf_readme_contract", vcf_errors)

    placeholder_errors: list[str] = []
    for path in sorted(table.rglob("README.md")):
        text = path.read_text()
        if any(token in text for token in ("TODO", "TBD", "PLACEHOLDER", "待补充")):
            placeholder_errors.append(str(path.relative_to(table)))
    add("no_placeholders", placeholder_errors)

    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check", "status", "detail"], delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(checks)
    failures = [row for row in checks if row["status"] != "PASS"]
    print(f"[table-readme-qa] checks={len(checks)} pass={len(checks) - len(failures)} fail={len(failures)}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
