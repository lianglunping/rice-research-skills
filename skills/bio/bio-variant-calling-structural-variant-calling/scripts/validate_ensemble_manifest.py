#!/usr/bin/env python3
"""Validate a short-read SV ensemble manifest without modifying callsets.

The script checks representation provenance, caller-panel completeness, algorithm
family diversity, coordinate-reference consistency, callset indexes, and VCF/BCF
parsing. It writes auditable TSV/XLSX/JSON reports under an explicit prefix.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


REQUIRED_COLUMNS = {
    "sample_id",
    "caller",
    "caller_version",
    "callset",
    "algorithm_family",
    "alignment_mode",
    "coordinate_reference",
}
VALID_ALIGNMENT_MODES = {"linear", "graph_surjected"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SUPPORTED_SUFFIXES = (".vcf.gz", ".vcf.bgz", ".bcf")


@dataclass
class Check:
    check_id: str
    scope: str
    subject: str
    status: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="UTF-8 TSV ensemble manifest")
    parser.add_argument(
        "--output-prefix",
        required=True,
        type=Path,
        help="Write <prefix>.tsv, <prefix>.xlsx, and <prefix>.json",
    )
    parser.add_argument("--bcftools", default="bcftools", help="bcftools executable or command name")
    parser.add_argument("--timeout", type=int, default=60, help="Per-call bcftools timeout in seconds")
    parser.add_argument(
        "--allow-missing-callsets",
        action="store_true",
        help="Planning-only mode: report missing callsets as WARN instead of ERROR",
    )
    parser.add_argument(
        "--skip-vcf-parse",
        action="store_true",
        help="Skip bcftools header parsing and record a reproducibility warning",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite only the three report files")
    return parser.parse_args()


def add(
    checks: list[Check],
    check_id: str,
    scope: str,
    subject: object,
    status: str,
    message: str,
) -> None:
    checks.append(Check(check_id, scope, str(subject), status, message))


def absolute(path: Path, base: Path | None = None) -> Path:
    expanded = path.expanduser()
    if not expanded.is_absolute() and base is not None:
        expanded = base / expanded
    return expanded.resolve(strict=False)


def resolve_executable(value: str) -> str | None:
    candidate = Path(value).expanduser()
    if candidate.parent != Path(".") or os.sep in value:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate.resolve())
        return None
    return shutil.which(value)


def run_command(command: list[str], timeout: int) -> tuple[int, str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 127, str(exc)
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return result.returncode, output


def first_nonempty_line(text: str) -> str:
    return next((line.strip() for line in text.splitlines() if line.strip()), "unknown")


def read_manifest(path: Path, checks: list[Check]) -> list[dict[str, str]]:
    if not path.is_file():
        add(checks, "MANIFEST_EXISTS", "manifest", path, "ERROR", "file does not exist")
        return []
    add(checks, "MANIFEST_EXISTS", "manifest", path, "PASS", "file exists")
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            fields = reader.fieldnames or []
            missing = sorted(REQUIRED_COLUMNS - set(fields))
            if missing:
                add(
                    checks,
                    "MANIFEST_HEADER",
                    "manifest",
                    path,
                    "ERROR",
                    "missing required columns: " + ",".join(missing),
                )
                return []
            rows = [{key: (value or "").strip() for key, value in row.items()} for row in reader]
    except (OSError, csv.Error) as exc:
        add(checks, "MANIFEST_READ", "manifest", path, "ERROR", str(exc))
        return []
    if rows:
        add(checks, "MANIFEST_ROWS", "manifest", path, "PASS", f"{len(rows)} rows")
    else:
        add(checks, "MANIFEST_ROWS", "manifest", path, "ERROR", "no data rows")
    return rows


def callset_index_candidates(path: Path) -> list[Path]:
    return [Path(f"{path}.tbi"), Path(f"{path}.csi")]


def normalize_rows(
    rows: list[dict[str, str]],
    manifest_dir: Path,
    checks: list[Check],
) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    keys_seen: Counter[tuple[str, str, str]] = Counter()

    for line_number, row in enumerate(rows, 2):
        subject = f"line {line_number}"
        empty = sorted(column for column in REQUIRED_COLUMNS if not row.get(column, ""))
        if empty:
            add(checks, "REQUIRED_VALUE", "manifest", subject, "ERROR", "empty fields: " + ",".join(empty))
            continue

        sample_id = row["sample_id"]
        caller = row["caller"].lower()
        family = row["algorithm_family"].lower()
        mode = row["alignment_mode"].lower()
        if not SAFE_ID.fullmatch(sample_id):
            add(checks, "SAMPLE_ID_FORMAT", "manifest", subject, "ERROR", f"unsafe sample_id: {sample_id!r}")
        if not SAFE_ID.fullmatch(caller):
            add(checks, "CALLER_ID_FORMAT", "manifest", subject, "ERROR", f"unsafe caller: {caller!r}")
        if not SAFE_ID.fullmatch(family):
            add(checks, "FAMILY_ID_FORMAT", "manifest", subject, "ERROR", f"unsafe algorithm_family: {family!r}")
        if mode not in VALID_ALIGNMENT_MODES:
            add(
                checks,
                "ALIGNMENT_MODE",
                "manifest",
                subject,
                "ERROR",
                f"expected one of {sorted(VALID_ALIGNMENT_MODES)}, found {mode!r}",
            )

        original_path = Path(row["callset"]).expanduser()
        if not original_path.is_absolute():
            add(
                checks,
                "CALLSET_ABSOLUTE_PATH",
                "manifest",
                subject,
                "WARN",
                "relative path resolved against manifest directory",
            )
        callset = absolute(original_path, manifest_dir)
        if not str(callset).endswith(SUPPORTED_SUFFIXES):
            add(
                checks,
                "CALLSET_SUFFIX",
                "callset",
                callset,
                "ERROR",
                "expected .vcf.gz, .vcf.bgz, or .bcf",
            )

        if "sha256:" not in row["coordinate_reference"].lower() and "md5:" not in row["coordinate_reference"].lower():
            add(
                checks,
                "REFERENCE_IMMUTABLE_ID",
                "reference",
                row["coordinate_reference"],
                "WARN",
                "coordinate reference has no sha256/md5 identifier",
            )

        key = (sample_id, caller, mode)
        keys_seen[key] += 1
        item = dict(row)
        item.update(
            {
                "caller": caller,
                "algorithm_family": family,
                "alignment_mode": mode,
                "callset": str(callset),
                "manifest_line": str(line_number),
            }
        )
        normalized.append(item)

    duplicates = [key for key, count in keys_seen.items() if count > 1]
    if duplicates:
        for sample_id, caller, mode in sorted(duplicates):
            add(
                checks,
                "ROW_UNIQUE",
                "manifest",
                f"{sample_id}/{caller}/{mode}",
                "ERROR",
                "duplicate sample/caller/alignment-mode rows",
            )
    elif normalized:
        add(checks, "ROW_UNIQUE", "manifest", "all rows", "PASS", f"{len(normalized)} unique rows")
    return normalized


def check_callsets(
    rows: list[dict[str, str]],
    args: argparse.Namespace,
    checks: list[Check],
) -> dict[str, str]:
    versions: dict[str, str] = {}
    bcftools: str | None = None
    if args.skip_vcf_parse:
        add(
            checks,
            "VCF_PARSE",
            "tool",
            "bcftools",
            "WARN",
            "header parsing explicitly skipped; production acceptance not met",
        )
    else:
        bcftools = resolve_executable(args.bcftools)
        if bcftools is None:
            add(checks, "BCFTOOLS_AVAILABLE", "tool", args.bcftools, "ERROR", "executable not found")
        else:
            code, output = run_command([bcftools, "--version"], args.timeout)
            if code != 0:
                add(checks, "BCFTOOLS_VERSION", "tool", bcftools, "ERROR", first_nonempty_line(output))
            else:
                versions["bcftools"] = first_nonempty_line(output)
                add(checks, "BCFTOOLS_VERSION", "tool", bcftools, "PASS", versions["bcftools"])

    for row in rows:
        callset = Path(row["callset"])
        subject = f"{row['sample_id']}/{row['caller']}/{row['alignment_mode']}"
        if not callset.is_file():
            status = "WARN" if args.allow_missing_callsets else "ERROR"
            message = "missing callset (planning-only allowance)" if args.allow_missing_callsets else "file does not exist"
            add(checks, "CALLSET_EXISTS", "callset", subject, status, f"{message}: {callset}")
            continue
        add(checks, "CALLSET_EXISTS", "callset", subject, "PASS", str(callset))
        index = next((candidate for candidate in callset_index_candidates(callset) if candidate.is_file()), None)
        if index is None:
            add(
                checks,
                "CALLSET_INDEX",
                "callset",
                subject,
                "ERROR",
                "missing .tbi/.csi index",
            )
        else:
            add(checks, "CALLSET_INDEX", "callset", subject, "PASS", str(index))

        if bcftools is not None and not args.skip_vcf_parse:
            code, output = run_command([bcftools, "view", "-h", str(callset)], args.timeout)
            if code != 0:
                add(checks, "VCF_PARSE", "callset", subject, "ERROR", first_nonempty_line(output))
            elif "#CHROM" not in output:
                add(checks, "VCF_HEADER", "callset", subject, "ERROR", "bcftools output lacks #CHROM header")
            else:
                add(checks, "VCF_PARSE", "callset", subject, "PASS", "bcftools header parse passed")
    return versions


def check_design(rows: list[dict[str, str]], checks: list[Check]) -> dict[str, object]:
    by_sample: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_sample[row["sample_id"]].append(row)

    all_panel_entries = {(row["caller"], row["alignment_mode"]) for row in rows}
    sample_summaries: dict[str, object] = {}
    for sample_id, sample_rows in sorted(by_sample.items()):
        coordinate_refs = {row["coordinate_reference"] for row in sample_rows}
        if len(coordinate_refs) != 1:
            add(
                checks,
                "COORDINATE_REFERENCE",
                "sample",
                sample_id,
                "ERROR",
                "multiple coordinate references: " + ",".join(sorted(coordinate_refs)),
            )
        else:
            add(
                checks,
                "COORDINATE_REFERENCE",
                "sample",
                sample_id,
                "PASS",
                next(iter(coordinate_refs)),
            )

        panel = {(row["caller"], row["alignment_mode"]) for row in sample_rows}
        missing_panel = sorted(all_panel_entries - panel)
        if missing_panel:
            missing_text = ",".join(f"{caller}:{mode}" for caller, mode in missing_panel)
            add(checks, "PANEL_COMPLETENESS", "sample", sample_id, "WARN", "missing panel rows: " + missing_text)
        else:
            add(checks, "PANEL_COMPLETENESS", "sample", sample_id, "PASS", f"{len(panel)} panel rows")

        modes = sorted({row["alignment_mode"] for row in sample_rows})
        for mode in modes:
            mode_rows = [row for row in sample_rows if row["alignment_mode"] == mode]
            callers = {row["caller"] for row in mode_rows}
            families = {row["algorithm_family"] for row in mode_rows}
            if len(callers) < 2:
                add(
                    checks,
                    "ENSEMBLE_SIZE",
                    "sample_mode",
                    f"{sample_id}/{mode}",
                    "WARN",
                    "fewer than two callers; treat as a single-caller lane",
                )
            else:
                add(
                    checks,
                    "ENSEMBLE_SIZE",
                    "sample_mode",
                    f"{sample_id}/{mode}",
                    "PASS",
                    f"{len(callers)} callers",
                )
            if len(families) < 2 and len(callers) >= 2:
                add(
                    checks,
                    "ALGORITHM_DIVERSITY",
                    "sample_mode",
                    f"{sample_id}/{mode}",
                    "WARN",
                    "multiple tools but only one declared algorithm family",
                )
            elif len(families) >= 2:
                add(
                    checks,
                    "ALGORITHM_DIVERSITY",
                    "sample_mode",
                    f"{sample_id}/{mode}",
                    "PASS",
                    f"{len(families)} declared families",
                )

            family_by_caller = {row["caller"]: row["algorithm_family"] for row in mode_rows}
            if {"lumpy", "smoove"}.issubset(family_by_caller):
                if family_by_caller["lumpy"] != family_by_caller["smoove"]:
                    add(
                        checks,
                        "LUMPY_SMOOVE_FAMILY",
                        "sample_mode",
                        f"{sample_id}/{mode}",
                        "ERROR",
                        "LUMPY and Smoove must share one algorithm_family",
                    )
                else:
                    add(
                        checks,
                        "LUMPY_SMOOVE_FAMILY",
                        "sample_mode",
                        f"{sample_id}/{mode}",
                        "PASS",
                        "shared family; do not count as independent votes",
                    )

        graph_callers = {row["caller"] for row in sample_rows if row["alignment_mode"] == "graph_surjected"}
        linear_callers = {row["caller"] for row in sample_rows if row["alignment_mode"] == "linear"}
        missing_linear = sorted(graph_callers - linear_callers)
        if missing_linear:
            add(
                checks,
                "GRAPH_LINEAR_BASELINE",
                "sample",
                sample_id,
                "WARN",
                "graph-surjected callers lack matched linear baseline: " + ",".join(missing_linear),
            )
        elif graph_callers:
            add(
                checks,
                "GRAPH_LINEAR_BASELINE",
                "sample",
                sample_id,
                "PASS",
                f"{len(graph_callers)} graph callers have matched linear rows",
            )

        sample_summaries[sample_id] = {
            "rows": len(sample_rows),
            "callers": sorted({row["caller"] for row in sample_rows}),
            "algorithm_families": sorted({row["algorithm_family"] for row in sample_rows}),
            "alignment_modes": modes,
            "coordinate_references": sorted(coordinate_refs),
        }

    return {"samples": sample_summaries, "panel": sorted(f"{caller}:{mode}" for caller, mode in all_panel_entries)}


def xlsx_column(index: int) -> str:
    letters = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def write_checks_xlsx(path: Path, checks: list[Check]) -> None:
    headers = ["check_id", "scope", "subject", "status", "message"]
    values = [headers, *[[item.check_id, item.scope, item.subject, item.status, item.message] for item in checks]]
    rows: list[str] = []
    for row_number, row in enumerate(values, 1):
        cells: list[str] = []
        for column_number, value in enumerate(row, 1):
            reference = f"{xlsx_column(column_number)}{row_number}"
            cells.append(
                f'<c r="{reference}" t="inlineStr"><is><t xml:space="preserve">'
                f"{escape(str(value))}</t></is></c>"
            )
        rows.append(f'<row r="{row_number}">' + "".join(cells) + "</row>")

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
    package_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="ensemble_checks" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""
    worksheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<dimension ref="A1:E{len(values)}"/><sheetData>{"".join(rows)}</sheetData>'
        '<autoFilter ref="A1:E1"/></worksheet>'
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet)


def write_reports(
    prefix: Path,
    checks: list[Check],
    payload: dict[str, object],
    force: bool,
) -> tuple[Path, Path, Path]:
    tsv_path = Path(f"{prefix}.tsv")
    xlsx_path = Path(f"{prefix}.xlsx")
    json_path = Path(f"{prefix}.json")
    existing = [path for path in (tsv_path, xlsx_path, json_path) if path.exists()]
    if existing and not force:
        raise FileExistsError("report exists; use --force to replace only: " + ", ".join(map(str, existing)))
    prefix.parent.mkdir(parents=True, exist_ok=True)
    with tsv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            delimiter="\t",
            fieldnames=["check_id", "scope", "subject", "status", "message"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(asdict(item) for item in checks)
    write_checks_xlsx(xlsx_path, checks)
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return tsv_path, xlsx_path, json_path


def main() -> int:
    args = parse_args()
    if args.timeout <= 0:
        raise SystemExit("--timeout must be positive")

    checks: list[Check] = []
    manifest = absolute(args.manifest)
    output_prefix = absolute(args.output_prefix)
    rows = read_manifest(manifest, checks)
    normalized = normalize_rows(rows, manifest.parent, checks)
    versions = check_callsets(normalized, args, checks)
    design = check_design(normalized, checks)

    counts = {status: sum(item.status == status for item in checks) for status in ("PASS", "WARN", "ERROR")}
    overall = "ERROR" if counts["ERROR"] else ("WARN" if counts["WARN"] else "PASS")
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "overall_status": overall,
        "counts": counts,
        "inputs": {"manifest": str(manifest)},
        "options": {
            "allow_missing_callsets": args.allow_missing_callsets,
            "skip_vcf_parse": args.skip_vcf_parse,
        },
        "versions": versions,
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "random_seed": "not_applicable",
        },
        "design": design,
        "manifest_rows": normalized,
        "checks": [asdict(item) for item in checks],
    }
    try:
        tsv_path, xlsx_path, json_path = write_reports(output_prefix, checks, payload, args.force)
    except FileExistsError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"overall_status={overall}")
    print(f"errors={counts['ERROR']} warnings={counts['WARN']} passes={counts['PASS']}")
    print(f"tsv={tsv_path}")
    print(f"xlsx={xlsx_path}")
    print(f"json={json_path}")
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
