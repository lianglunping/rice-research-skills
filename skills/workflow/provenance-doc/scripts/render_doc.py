# Plan Section: Chunk 4 — Task 2-4 (Render + inline extension_sections)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Render a provenance.md by inlining extension_sections.

Spec §5 + §11.

Usage:
    render_doc.py --doc <provenance.md> [--out <rendered.md>]
                  [--fail-on-missing-extension]

Default: in-place re-render — preserve original front-matter and §0..§9 body,
append rendered extension block from each ext.source file.

Exit codes:
    0 - success
    1 - missing/empty extension source (when --fail-on-missing-extension)
    2 - misuse / doc not found
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_doc, write_doc, is_safe_relative_path  # type: ignore

# Sentinel header marking the start of the rendered extension block.
# Must not contain any banned terms.
EXTENSION_HEADER = "## 业务统计扩展"


def render_extensions(
    doc_path: Path,
    extensions: list[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Render all extension_sections into a single Markdown block.

    For each extension:
    - If status == 'waived': emit waiver notice; no source file needed.
    - Otherwise: read source file and inline its content.
    - Unsafe or missing source paths accumulate in errors.

    Args:
        doc_path: Absolute path to the provenance doc (used to resolve relative sources).
        extensions: List of extension section dicts from front-matter.

    Returns:
        Tuple of (rendered_block_str, list_of_error_strings).
    """
    parts = [EXTENSION_HEADER, ""]
    errors: list[str] = []

    for ext in extensions:
        eid = ext.get("id", "")
        title = ext.get("title", eid)
        src_str = ext.get("source", "")
        status = ext.get("status", "draft")

        if not is_safe_relative_path(src_str):
            errors.append(f"extension {eid}: unsafe source '{src_str}'")
            parts.append(f"### {title}")
            parts.append(f"> Source: `{src_str}` (status: {status})")
            parts.append("")
            parts.append(f"> _Unsafe extension source path rejected_")
            parts.append("")
            continue

        src_path = doc_path.parent / src_str

        parts.append(f"### {title}")
        parts.append(f"> Source: `{src_str}` (status: {status})")
        parts.append("")

        if status == "waived":
            waiver_reason = ext.get("waiver_reason", "")
            parts.append(f"> **WAIVED**: {waiver_reason}")
            parts.append("")
            continue

        if not src_path.is_file():
            errors.append(f"extension {eid}: source not found: {src_path}")
            parts.append(f"> _Missing extension source: {src_path}_")
            parts.append("")
            continue

        if src_path.stat().st_size == 0:
            errors.append(f"extension {eid}: source is empty: {src_path}")
            parts.append("> _Empty extension source_")
            parts.append("")
            continue

        parts.append(src_path.read_text(encoding="utf-8").rstrip())
        parts.append("")

    return "\n".join(parts), errors


def main() -> int:
    """Entry point for render_doc CLI."""
    p = argparse.ArgumentParser(
        description="Render provenance.md by inlining extension_sections."
    )
    p.add_argument("--doc", type=Path, required=True, help="Path to provenance.md")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output path (default: in-place update of --doc)",
    )
    p.add_argument(
        "--fail-on-missing-extension",
        action="store_true",
        help="Exit 1 if any extension source file is missing or empty",
    )
    args = p.parse_args()

    if not args.doc.is_file():
        print(f"error: doc not found: {args.doc}", file=sys.stderr)
        return 2

    out_path: Path = args.out or args.doc

    # Guard: do not modify sealed (read-only) files in-place.
    if out_path == args.doc and not os.access(args.doc, os.W_OK):
        print(
            f"warning: {args.doc} is not writable (sealed?). Skipping render.",
            file=sys.stderr,
        )
        return 0

    try:
        doc = parse_doc(args.doc)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    extensions = doc.extensions

    # Strip any prior rendered extension section from body before re-rendering.
    body_core = doc.body.split(EXTENSION_HEADER)[0].rstrip() + "\n\n"

    if extensions:
        ext_block, errors = render_extensions(args.doc, extensions)
        body_new = body_core + ext_block
    else:
        errors = []
        body_new = body_core

    if args.fail_on_missing_extension and errors:
        print(f"FAIL: {len(errors)} extension error(s)", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    # Write output.
    doc.body = body_new
    if out_path == args.doc:
        write_doc(doc)
    else:
        fm_yaml = yaml.safe_dump(doc.front_matter, sort_keys=False, allow_unicode=True)
        out_path.write_text(f"---\n{fm_yaml}---\n{body_new}", encoding="utf-8")

    print(
        f"OK: rendered {args.doc} -> {out_path} ({len(extensions)} extension(s))"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
