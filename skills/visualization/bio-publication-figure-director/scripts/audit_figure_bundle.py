#!/usr/bin/env python3
"""Audit the mechanical floor of a publication-figure delivery bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


@dataclass
class Finding:
    level: str
    check: str
    message: str


def add(findings: list[Finding], level: str, check: str, message: str) -> None:
    findings.append(Finding(level, check, message))


def run_readonly(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    if not shutil.which(command[0]):
        return None
    return subprocess.run(command, check=False, capture_output=True, text=True)


def audit_pdf(
    path: Path,
    findings: list[Finding],
    target_inches: tuple[float, float] | None,
) -> None:
    data = path.read_bytes()
    if not data.startswith(b"%PDF-"):
        add(findings, "FAIL", "pdf-signature", f"{path} is not a valid PDF header")
    elif b"%%EOF" not in data[-4096:]:
        add(findings, "WARN", "pdf-eof", f"{path} has no EOF marker near file end")
    else:
        add(findings, "PASS", "pdf-signature", f"{path.name} has a valid PDF signature")
    info = run_readonly(["pdfinfo", str(path)])
    if info and info.returncode == 0:
        pages_match = re.search(r"^Pages:\s+(\d+)", info.stdout, re.MULTILINE)
        if pages_match and int(pages_match.group(1)) != 1:
            add(
                findings,
                "FAIL",
                "pdf-pages",
                f"{path.name}: expected one page, found {pages_match.group(1)}",
            )
        else:
            add(findings, "PASS", "pdf-pages", f"{path.name}: one-page figure")
        size_match = re.search(
            r"^Page size:\s+([\d.]+)\s+x\s+([\d.]+)\s+pts",
            info.stdout,
            re.MULTILINE,
        )
        if size_match:
            width = float(size_match.group(1)) / 72
            height = float(size_match.group(2)) / 72
            add(
                findings,
                "PASS",
                "pdf-size",
                f"{path.name}: {width:.3f} x {height:.3f} in",
            )
            if target_inches and (
                abs(width - target_inches[0]) > 1 / 72
                or abs(height - target_inches[1]) > 1 / 72
            ):
                add(
                    findings,
                    "WARN",
                    "pdf-target-size",
                    f"{path.name}: differs from target "
                    f"{target_inches[0]:g} x {target_inches[1]:g} in",
                )
    fonts = run_readonly(["pdffonts", str(path)])
    if fonts and fonts.returncode == 0:
        if not fonts.stdout.splitlines()[2:]:
            add(findings, "INFO", "pdf-fonts", f"{path.name}: no fonts reported; inspect paths and raster objects")
        elif "Type 3" in fonts.stdout:
            add(findings, "FAIL", "pdf-fonts", f"{path.name}: contains Type 3 fonts")
        elif re.search(r"\sno\s+(?:yes|no)\s+(?:yes|no)\s+\d+\s+\d+\s*$", fonts.stdout, re.MULTILINE):
            add(findings, "WARN", "pdf-fonts", f"{path.name}: at least one font may be unembedded")
        else:
            add(findings, "PASS", "pdf-fonts", f"{path.name}: reported fonts are embedded and none are Type 3")


def png_metadata(path: Path) -> tuple[int, int, float | None]:
    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n") or len(data) < 33:
        raise ValueError("invalid PNG signature or truncated IHDR")
    width, height = struct.unpack(">II", data[16:24])
    dpi = None
    marker = data.find(b"pHYs")
    if marker >= 0 and marker + 13 <= len(data):
        x_ppm, y_ppm, unit = struct.unpack(">IIB", data[marker + 4 : marker + 13])
        if unit == 1 and x_ppm > 0 and y_ppm > 0:
            dpi = min(x_ppm, y_ppm) * 0.0254
    return width, height, dpi


def audit_png(
    path: Path,
    findings: list[Finding],
    min_dpi: float,
    target_inches: tuple[float, float] | None,
) -> None:
    try:
        width, height, dpi = png_metadata(path)
    except ValueError as exc:
        add(findings, "FAIL", "png-signature", f"{path}: {exc}")
        return
    add(findings, "PASS", "png-size", f"{path.name}: {width} x {height} px")
    if not target_inches and min(width, height) < 600:
        add(
            findings,
            "WARN",
            "png-pixels",
            f"{path.name}: short edge is {min(width, height)} px; inspect at final size",
        )
    if dpi is None:
        add(findings, "WARN", "png-dpi", f"{path.name}: no physical DPI metadata")
    elif dpi + 0.5 < min_dpi:
        add(
            findings,
            "FAIL",
            "png-dpi",
            f"{path.name}: {dpi:.1f} DPI is below required {min_dpi:g}",
        )
    else:
        add(findings, "PASS", "png-dpi", f"{path.name}: {dpi:.1f} DPI")
    if target_inches:
        effective = min(width / target_inches[0], height / target_inches[1])
        if width + 1 < target_inches[0] * min_dpi or height + 1 < target_inches[1] * min_dpi:
            add(
                findings,
                "FAIL",
                "png-effective-dpi",
                f"{path.name}: {effective:.1f} effective DPI at target size",
            )
        else:
            add(
                findings,
                "PASS",
                "png-effective-dpi",
                f"{path.name}: {effective:.1f} effective DPI at target size",
            )


def audit_svg(path: Path, findings: list[Finding]) -> None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        add(findings, "FAIL", "svg-xml", f"{path}: {exc}")
        return
    if not root.tag.lower().endswith("svg"):
        add(findings, "FAIL", "svg-root", f"{path}: root element is not svg")
        return
    add(findings, "PASS", "svg-xml", f"{path.name} is parseable SVG")
    if not (root.get("viewBox") or (root.get("width") and root.get("height"))):
        add(findings, "WARN", "svg-size", f"{path.name}: no viewBox or width/height")


def audit_tiff(path: Path, findings: list[Finding]) -> None:
    header = path.read_bytes()[:4]
    if header not in (b"II*\x00", b"MM\x00*"):
        add(findings, "FAIL", "tiff-signature", f"{path}: invalid TIFF signature")
    else:
        add(findings, "PASS", "tiff-signature", f"{path.name} has a TIFF signature")


def audit_artifact(
    path: Path,
    findings: list[Finding],
    min_dpi: float,
    target_inches: tuple[float, float] | None,
) -> None:
    if not path.exists():
        add(findings, "FAIL", "artifact-exists", f"missing required artifact: {path}")
        return
    if path.stat().st_size < 512:
        add(
            findings,
            "FAIL",
            "artifact-size",
            f"{path} is suspiciously small ({path.stat().st_size} bytes)",
        )
        return
    add(
        findings,
        "PASS",
        "artifact-exists",
        f"{path.name} exists ({path.stat().st_size} bytes)",
    )
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        audit_pdf(path, findings, target_inches)
    elif suffix == ".png":
        audit_png(path, findings, min_dpi, target_inches)
    elif suffix == ".svg":
        audit_svg(path, findings)
    elif suffix in (".tif", ".tiff"):
        audit_tiff(path, findings)


REQUIRED_MANIFEST_COLUMNS = {
    "figure_id",
    "core_claim",
    "claim_status",
    "source_data",
    "generation_script",
    "output_paths",
    "qa_status",
}


def audit_manifest(
    path: Path, figure_id: str, artifacts: list[Path], findings: list[Finding]
) -> dict[str, str] | None:
    if not path.exists():
        add(findings, "FAIL", "manifest-exists", f"missing manifest: {path}")
        return None
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
    except (OSError, UnicodeError, csv.Error) as exc:
        add(findings, "FAIL", "manifest-read", f"{path}: {exc}")
        return None
    if not rows:
        add(findings, "FAIL", "manifest-row", f"{path}: no data rows")
        return None
    columns = set(rows[0])
    missing = REQUIRED_MANIFEST_COLUMNS - columns
    if missing:
        add(
            findings,
            "FAIL",
            "manifest-columns",
            f"{path.name}: missing columns {sorted(missing)}",
        )
        return None
    add(findings, "PASS", "manifest-columns", f"{path.name}: required columns present")
    matches = [row for row in rows if row.get("figure_id", "").strip() == figure_id]
    if not matches:
        add(
            findings,
            "FAIL",
            "manifest-row",
            f"{path.name}: no row with figure_id={figure_id!r}",
        )
        return None
    row = matches[-1]
    for field in ("core_claim", "claim_status", "source_data", "generation_script"):
        if not row.get(field, "").strip():
            add(
                findings,
                "FAIL",
                f"manifest-{field}",
                f"{path.name}: {field} is empty for {figure_id}",
            )
    output_paths = row.get("output_paths", "")
    missing_names = [item.name for item in artifacts if item.name not in output_paths]
    if missing_names:
        add(
            findings,
            "WARN",
            "manifest-outputs",
            f"{path.name}: output_paths does not mention {missing_names}",
        )
    else:
        add(
            findings,
            "PASS",
            "manifest-outputs",
            f"{path.name}: required artifacts are registered",
        )
    qa_status = row.get("qa_status", "").strip().lower()
    if qa_status not in {"pass", "passed", "complete", "accepted"}:
        add(
            findings,
            "WARN",
            "manifest-qa",
            f"{path.name}: qa_status={row.get('qa_status', '')!r}",
        )
    claim_status = row.get("claim_status", "").strip()
    allowed = {
        "observed",
        "conditional_association",
        "hypothesis",
        "future_validation",
    }
    if claim_status not in allowed:
        add(
            findings,
            "FAIL",
            "manifest-claim-status",
            f"{path.name}: unsupported claim_status={claim_status!r}",
        )
    else:
        add(
            findings,
            "PASS",
            "manifest-claim-status",
            f"{path.name}: claim_status={claim_status}",
        )
    return row


def audit_contract(
    path: Path, figure_id: str, findings: list[Finding]
) -> dict[str, Any] | None:
    if not path.exists():
        add(findings, "FAIL", "contract-exists", f"missing contract: {path}")
        return None
    if yaml is None:
        add(findings, "WARN", "contract-yaml", "PyYAML unavailable; contract not parsed")
        return None
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        add(findings, "FAIL", "contract-yaml", f"{path}: {exc}")
        return None
    if not isinstance(contract, dict):
        add(findings, "FAIL", "contract-yaml", f"{path}: root must be a mapping")
        return None
    add(findings, "PASS", "contract-yaml", f"{path.name}: parseable YAML")
    if str(contract.get("figure_id", "")).strip() != figure_id:
        add(
            findings,
            "FAIL",
            "contract-figure-id",
            f"{path.name}: figure_id does not match {figure_id!r}",
        )
    for field in ("core_question", "core_claim", "claim_status"):
        if not str(contract.get(field, "")).strip():
            add(findings, "FAIL", f"contract-{field}", f"{path.name}: {field} is empty")
    status = str(contract.get("claim_status", "")).strip()
    if status and status not in {
        "observed",
        "conditional_association",
        "hypothesis",
        "future_validation",
    }:
        add(
            findings,
            "FAIL",
            "contract-claim-status",
            f"{path.name}: unsupported claim_status={status!r}",
        )
    panels = contract.get("panels")
    if not isinstance(panels, list) or not panels:
        add(findings, "FAIL", "contract-panels", f"{path.name}: panels is empty")
    else:
        empty = [
            str(panel.get("id", "?")) if isinstance(panel, dict) else "?"
            for panel in panels
            if not isinstance(panel, dict) or not str(panel.get("defends", "")).strip()
        ]
        if empty:
            add(
                findings,
                "FAIL",
                "contract-panel-defends",
                f"{path.name}: panels without defends: {empty}",
            )
    return contract


def audit_contract_manifest_consistency(
    contract: dict[str, Any],
    row: dict[str, str],
    findings: list[Finding],
) -> None:
    for field in ("core_claim", "claim_status"):
        contract_value = " ".join(str(contract.get(field, "")).split())
        manifest_value = " ".join(row.get(field, "").split())
        if contract_value != manifest_value:
            add(
                findings,
                "FAIL",
                f"contract-manifest-{field}",
                f"{field} differs between contract and manifest",
            )
        else:
            add(
                findings,
                "PASS",
                f"contract-manifest-{field}",
                f"{field} matches between contract and manifest",
            )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_inputs(
    row: dict[str, str],
    project_root: Path,
    findings: list[Finding],
) -> None:
    raw_sources = [
        item.strip()
        for item in re.split(r"[;,]", row.get("source_data", ""))
        if item.strip()
    ]
    resolved: list[Path] = []
    for item in raw_sources:
        path = Path(item).expanduser()
        if not path.is_absolute():
            path = project_root / path
        if not path.is_file():
            add(findings, "FAIL", "input-exists", f"source_data not found: {path}")
        else:
            resolved.append(path)
            add(findings, "PASS", "input-exists", f"source_data exists: {path}")
    script_text = row.get("generation_script", "").strip()
    if script_text and script_text not in {"not-applicable", "n/a"}:
        script = Path(script_text).expanduser()
        if not script.is_absolute():
            script = project_root / script
        if not script.is_file():
            add(findings, "FAIL", "script-exists", f"generation_script not found: {script}")
        else:
            add(findings, "PASS", "script-exists", f"generation_script exists: {script}")
    expected = row.get("source_checksum", "").strip()
    if expected and len(resolved) == 1:
        expected = expected.removeprefix("sha256:")
        actual = file_sha256(resolved[0])
        if actual.casefold() != expected.casefold():
            add(findings, "FAIL", "input-checksum", f"checksum mismatch: {resolved[0]}")
        else:
            add(findings, "PASS", "input-checksum", f"checksum matches: {resolved[0]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit required figure artifacts and the matching manifest row."
    )
    parser.add_argument(
        "--base",
        required=True,
        type=Path,
        help="Figure basename without extension, e.g. outputs/figures/fig1_main",
    )
    parser.add_argument("--manifest", type=Path, help="TSV figure manifest")
    parser.add_argument("--contract", type=Path, help="YAML Figure Contract")
    parser.add_argument(
        "--figure-id",
        help="Manifest figure_id; defaults to basename",
    )
    parser.add_argument(
        "--require",
        nargs="+",
        default=["pdf", "png"],
        choices=["pdf", "png", "svg", "tif", "tiff"],
        help="Required artifact extensions",
    )
    parser.add_argument("--min-dpi", type=float, default=300.0)
    parser.add_argument(
        "--target-inches",
        nargs=2,
        type=float,
        metavar=("WIDTH", "HEIGHT"),
        help="Expected final figure size for PDF and effective raster DPI checks",
    )
    parser.add_argument(
        "--check-inputs",
        action="store_true",
        help="Resolve source_data and generation_script from the manifest",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Base for relative manifest paths (default: current directory)",
    )
    parser.add_argument("--strict", action="store_true", help="Treat WARN as failure")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = args.base.expanduser()
    figure_id = args.figure_id or base.name
    target_inches = tuple(args.target_inches) if args.target_inches else None
    artifacts = [base.with_suffix(f".{ext}") for ext in args.require]
    findings: list[Finding] = []
    for artifact in artifacts:
        audit_artifact(artifact, findings, args.min_dpi, target_inches)
    manifest_row = None
    if args.manifest:
        manifest_row = audit_manifest(
            args.manifest.expanduser(),
            figure_id,
            artifacts,
            findings,
        )
    else:
        add(findings, "INFO", "manifest", "no optional manifest supplied")
    contract_data = None
    if args.contract:
        contract_data = audit_contract(args.contract.expanduser(), figure_id, findings)
    else:
        add(findings, "INFO", "contract", "no optional Figure Contract supplied")
    if contract_data and manifest_row:
        audit_contract_manifest_consistency(contract_data, manifest_row, findings)
    if args.check_inputs:
        if manifest_row:
            audit_inputs(manifest_row, args.project_root.expanduser().resolve(), findings)
        else:
            add(findings, "FAIL", "inputs", "cannot check inputs without a valid manifest row")

    counts = {
        level: sum(item.level == level for item in findings)
        for level in ("PASS", "WARN", "FAIL")
    }
    if args.json:
        print(
            json.dumps(
                {"summary": counts, "findings": [asdict(item) for item in findings]},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for item in findings:
            print(f"[{item.level}] {item.check}: {item.message}")
        print(
            f"[SUMMARY] PASS={counts['PASS']} WARN={counts['WARN']} FAIL={counts['FAIL']}"
        )
    return int(counts["FAIL"] > 0 or (args.strict and counts["WARN"] > 0))


if __name__ == "__main__":
    sys.exit(main())
