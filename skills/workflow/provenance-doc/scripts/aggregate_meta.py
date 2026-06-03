# Plan Section: Chunk 4 — Task 2-3 (Aggregate artifact metadata)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Aggregate artifact metadata from sibling *.meta.yaml or runs_manifest.yaml.

Spec §7.1 + §11. Outputs a Markdown table for §4 of provenance.md.

Usage:
    aggregate_meta.py --doc <provenance.md>
                      [--manifest <runs_manifest.yaml>]
                      [--check-link-rot]
                      [--output (markdown|tsv)]

Exit codes:
    0 - all artifacts found / no errors
    1 - broken/missing meta (fail_closed=True) OR link-rot detected
    2 - misuse / doc not found
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_doc  # type: ignore


def md5_of_file(path: Path, chunk_size: int = 1 << 20) -> str:
    """Compute MD5 checksum of a file using stdlib hashlib.

    Args:
        path: Path to the file.
        chunk_size: Read chunk size in bytes.

    Returns:
        Hex digest string.
    """
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def line_count(path: Path) -> int:
    """Count lines for text-like files; return -1 for binary formats.

    Args:
        path: Path to the artifact file.

    Returns:
        Line count for text files, -1 for binary.
    """
    if path.suffix in (".tsv", ".csv", ".txt", ".md", ".vcf"):
        with path.open("r", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    return -1  # binary; skip


def collect_from_sibling_meta(
    doc_dir: Path,
    fail_closed_broken: bool,
    fail_closed_missing: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Collect artifact records from sibling *.meta.yaml files.

    Implements Fix-4 fail-closed behavior: when fail_closed_broken=True,
    broken YAML files accumulate an error instead of silently skipping.
    When fail_closed_missing=True, absence of any *.meta.yaml is also an error.

    Args:
        doc_dir: Directory containing the provenance doc.
        fail_closed_broken: If True, broken YAML files produce an error entry.
        fail_closed_missing: If True, absence of any *.meta.yaml is an error.

    Returns:
        Tuple of (artifacts, errors). Callers must check errors when fail_closed_*=True.
    """
    artifacts: list[dict[str, Any]] = []
    errors: list[str] = []

    metas = sorted(doc_dir.glob("*.meta.yaml"))

    if not metas and fail_closed_missing:
        errors.append(f"missing-meta: no *.meta.yaml in {doc_dir}")
        return artifacts, errors

    for meta in metas:
        try:
            data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            msg = f"broken-meta: {meta}: {e}"
            errors.append(msg)
            continue  # do not include broken artifact in output

        artifact_path = doc_dir / (meta.name[: -len(".meta.yaml")])
        exists = artifact_path.exists()
        artifacts.append(
            {
                "artifact_id": data.get("artifact_id", artifact_path.stem),
                "role": data.get("role", "result"),
                "path": str(artifact_path),
                "format": data.get("format", artifact_path.suffix.lstrip(".")),
                "size": artifact_path.stat().st_size if exists else "MISSING",
                "record_count": data.get(
                    "row_count",
                    line_count(artifact_path) if exists else "MISSING",
                ),
                "checksum": data.get("md5")
                or (md5_of_file(artifact_path) if exists else "MISSING"),
                "created_at": data.get("run_date", ""),
                "producer": data.get("generated_by", ""),
                "meta_yaml": str(meta.relative_to(doc_dir)),
            }
        )
    return artifacts, errors


def collect_from_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    """Collect artifact records from a runs_manifest.yaml file.

    Args:
        manifest_path: Path to runs_manifest.yaml.

    Returns:
        List of artifact dicts.
    """
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    artifacts: list[dict[str, Any]] = []
    for run in data.get("runs", []):
        for art in run.get("artifacts", []):
            p = Path(art).expanduser()
            artifacts.append(
                {
                    "artifact_id": p.stem,
                    "role": "result",
                    "path": str(p),
                    "format": p.suffix.lstrip("."),
                    "size": p.stat().st_size if p.exists() else "MISSING",
                    "record_count": line_count(p) if p.exists() else "MISSING",
                    "checksum": md5_of_file(p) if p.exists() else "MISSING",
                    "created_at": "",
                    "producer": run.get("id", ""),
                    "meta_yaml": "(remote/manifest)",
                }
            )
        for remote in run.get("artifacts_remote", []):
            artifacts.append(
                {
                    "artifact_id": Path(remote.split(":")[-1]).stem,
                    "role": "result-remote",
                    "path": remote,
                    "format": Path(remote).suffix.lstrip("."),
                    "size": "[unverified: remote-only]",
                    "record_count": "[unverified: remote-only]",
                    "checksum": "[unverified: remote-only]",
                    "created_at": "",
                    "producer": run.get("id", ""),
                    "meta_yaml": "(remote/manifest)",
                }
            )
    return artifacts


def render_markdown(rows: list[dict[str, Any]]) -> str:
    """Render artifact list as a Markdown pipe table.

    Args:
        rows: List of artifact dicts.

    Returns:
        Markdown table string (or '(no artifacts)' sentinel when empty).
    """
    if not rows:
        return "(no artifacts)\n"
    headers = [
        "artifact_id",
        "role",
        "path",
        "format",
        "size",
        "record_count",
        "checksum",
        "created_at",
        "producer",
        "meta_yaml",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(h, "")) for h in headers) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    """Entry point for aggregate_meta CLI."""
    p = argparse.ArgumentParser(
        description="Aggregate artifact metadata for provenance.md §4."
    )
    p.add_argument("--doc", type=Path, required=True, help="Path to provenance.md")
    p.add_argument(
        "--manifest", type=Path, default=None, help="Path to runs_manifest.yaml"
    )
    p.add_argument(
        "--check-link-rot",
        action="store_true",
        help="Exit 1 if any artifact file is missing",
    )
    p.add_argument(
        "--output",
        choices=["markdown", "tsv"],
        default="markdown",
        help="Output format",
    )
    args = p.parse_args()

    if not args.doc.is_file():
        print(f"error: doc not found: {args.doc}", file=sys.stderr)
        return 2

    # Read fail-closed flags from doc front-matter.
    # fail_closed_on_broken_yaml: spec §5.1 — NON-OVERRIDABLE invariant, always True.
    # fail_closed_on_missing_meta: lite may set to false.
    try:
        doc = parse_doc(args.doc)
        verification = doc.front_matter.get("verification") or {}
        # Spec §5.1 explicit `const: true`. Ignore any front-matter override.
        fail_closed_broken: bool = True
        fail_closed_missing: bool = bool(
            verification.get("fail_closed_on_missing_meta", True)
        )
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    artifacts: list[dict[str, Any]] = []
    errors: list[str] = []

    if args.manifest:
        if not args.manifest.is_file():
            print(f"error: manifest not found: {args.manifest}", file=sys.stderr)
            return 2
        artifacts.extend(collect_from_manifest(args.manifest))
    else:
        arts, errs = collect_from_sibling_meta(
            args.doc.parent, fail_closed_broken, fail_closed_missing
        )
        artifacts.extend(arts)
        errors.extend(errs)

    # Fail-closed: any errors with fail_closed flags active → exit 1
    if errors and (fail_closed_broken or fail_closed_missing):
        print(
            f"FAIL: {len(errors)} meta error(s)", file=sys.stderr
        )
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    if args.check_link_rot:
        rotted = [a for a in artifacts if a["size"] == "MISSING"]
        if rotted:
            print(f"FAIL: {len(rotted)} link-rot artifact(s)", file=sys.stderr)
            for a in rotted:
                print(f"  - {a['path']}", file=sys.stderr)
            return 1

    if args.output == "tsv":
        for a in artifacts:
            print(
                "\t".join(
                    str(a.get(k, ""))
                    for k in [
                        "artifact_id",
                        "role",
                        "path",
                        "size",
                        "record_count",
                        "checksum",
                    ]
                )
            )
    else:
        print(render_markdown(artifacts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
