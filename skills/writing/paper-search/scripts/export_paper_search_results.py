#!/usr/bin/env python3
"""Normalize paper-search-mcp JSON into TSV, XLSX, and manifest YAML."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import openpyxl
import yaml


COLUMNS = [
    "title",
    "authors",
    "year",
    "source",
    "paper_id",
    "doi",
    "pmid",
    "pmcid",
    "url",
    "pdf_url",
    "abstract",
    "query",
    "sources",
    "retrieved_at",
    "record_hash",
]


def load_results(input_path: Path) -> dict[str, Any]:
    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return {"papers": data, "source_results": {}, "errors": {}, "total": len(data)}
    if not isinstance(data, dict):
        raise ValueError(f"Unsupported JSON root type: {type(data).__name__}")
    papers = data.get("papers")
    if not isinstance(papers, list):
        raise ValueError("Input JSON must contain a 'papers' list")
    return data


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "; ".join(stringify(item) for item in value if stringify(item))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def first_present(record: Mapping[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = stringify(record.get(key))
        if value:
            return value
    return ""


def extract_year(record: Mapping[str, Any]) -> str:
    direct = first_present(record, ["year", "publication_year", "published_year"])
    if direct:
        return direct
    date_value = first_present(record, ["published_date", "publication_date", "date"])
    match = re.match(r"^(\d{4})", date_value)
    return match.group(1) if match else ""


def normalize_record(
    record: Mapping[str, Any],
    query: str,
    sources: str,
    retrieved_at: str,
) -> dict[str, str]:
    row = {
        "title": first_present(record, ["title", "name"]),
        "authors": first_present(record, ["authors", "author", "creators"]),
        "year": extract_year(record),
        "source": first_present(record, ["source", "platform"]),
        "paper_id": first_present(record, ["paper_id", "id", "pmid", "doi"]),
        "doi": first_present(record, ["doi", "DOI"]),
        "pmid": first_present(record, ["pmid", "pubmed_id"]),
        "pmcid": first_present(record, ["pmcid", "pmc_id"]),
        "url": first_present(record, ["url", "paper_url", "landing_page_url"]),
        "pdf_url": first_present(record, ["pdf_url", "pdf", "download_url"]),
        "abstract": first_present(record, ["abstract", "summary"]),
        "query": query,
        "sources": sources,
        "retrieved_at": retrieved_at,
    }
    row["record_hash"] = record_hash(row)
    return row


def record_hash(row: Mapping[str, str]) -> str:
    basis = "|".join(
        [
            row.get("doi", "").lower(),
            row.get("title", "").lower(),
            row.get("year", ""),
            row.get("source", "").lower(),
        ]
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


def dedupe_key(row: Mapping[str, str]) -> str:
    doi = row.get("doi", "").strip().lower()
    if doi:
        return f"doi:{doi}"
    title = row.get("title", "").strip().lower()
    year = row.get("year", "").strip()
    if title:
        return f"title:{title}|year:{year}"
    return f"hash:{row.get('record_hash', '')}"


def deduplicate_records(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    source_sets: dict[str, set[str]] = {}
    for row in rows:
        key = dedupe_key(row)
        if key not in merged:
            merged[key] = dict(row)
            source_sets[key] = set(filter(None, row.get("source", "").split("; ")))
            continue
        source_sets[key].update(filter(None, row.get("source", "").split("; ")))
        for col in COLUMNS:
            if not merged[key].get(col) and row.get(col):
                merged[key][col] = row[col]
    for key, source_set in source_sets.items():
        if source_set:
            merged[key]["source"] = "; ".join(sorted(source_set))
    return list(merged.values())


def write_tsv(rows: list[dict[str, str]], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in COLUMNS})


def write_xlsx(rows: list[dict[str, str]], output_path: Path) -> None:
    workbook = openpyxl.Workbook(write_only=True)
    sheet = workbook.create_sheet("papers")
    sheet.append(COLUMNS)
    for row in rows:
        sheet.append([row.get(column, "") for column in COLUMNS])
    workbook.save(output_path)


def git_commit(repo: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def write_manifest(metadata: dict[str, Any], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(metadata, handle, sort_keys=False, allow_unicode=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Raw paper-search JSON")
    parser.add_argument("--outdir", required=True, type=Path, help="Output directory")
    parser.add_argument("--query", default="", help="Search query")
    parser.add_argument("--sources", default="", help="Comma-separated source list")
    parser.add_argument("--year", default="", help="Year filter, if used")
    parser.add_argument("--command", default="", help="Exact command used for the search")
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("/path/to/paper-search-mcp"),
        help="paper-search-mcp repository path",
    )
    parser.add_argument("--tsv-name", default="papers.tsv")
    parser.add_argument("--xlsx-name", default="papers.xlsx")
    parser.add_argument("--manifest-name", default="manifest.yaml")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = load_results(args.input)
    papers = data["papers"]
    query = args.query or stringify(data.get("query"))
    sources = args.sources or ",".join(data.get("sources_used", []))

    normalized = [
        normalize_record(record, query=query, sources=sources, retrieved_at=retrieved_at)
        for record in papers
    ]
    deduped = deduplicate_records(normalized)

    tsv_path = args.outdir / args.tsv_name
    xlsx_path = args.outdir / args.xlsx_name
    manifest_path = args.outdir / args.manifest_name

    write_tsv(deduped, tsv_path)
    write_xlsx(deduped, xlsx_path)

    manifest = {
        "query": query,
        "sources": sources,
        "year_filter": args.year,
        "retrieved_at": retrieved_at,
        "command": args.command,
        "paper_search_mcp_repo": str(args.repo),
        "paper_search_mcp_commit": git_commit(args.repo),
        "python_version": platform.python_version(),
        "raw_input": str(args.input),
        "tsv_output": str(tsv_path),
        "xlsx_output": str(xlsx_path),
        "total_raw_records": len(papers),
        "total_normalized_records": len(normalized),
        "total_deduplicated_records": len(deduped),
        "source_results": data.get("source_results", {}),
        "errors": data.get("errors", {}),
    }
    write_manifest(manifest, manifest_path)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
