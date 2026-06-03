#!/usr/bin/env python3
# Plan Section: Chunk 2, Task 1-5 — Lint duplication between provenance.md and siblings
# Plan Version: 2026-04-30-provenance-doc-plan.md
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Lint duplication between provenance.md and sibling YAML/MD docs.

Spec §8.1: ≤40% field overlap allowed. This script extracts "fields"
heuristically:
  - YAML files: top-level keys (recursive dot-path notation)
  - Markdown tables: column headers + first-column values
  - Markdown front-matter: top-level keys

Usage:
    python3 lint_no_duplication.py <provenance.md> [<sibling1> ...]

Exit codes:
    0 - all overlaps within 40%
    1 - some overlap >40%
    2 - misuse
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

OVERLAP_THRESHOLD = 0.40


# ---------------------------------------------------------------------------
# Substep a: helper functions
# ---------------------------------------------------------------------------


def _walk_yaml_keys(obj: Any, prefix: str = "") -> set[str]:
    """Recursively collect dot-path keys from a YAML object.

    Args:
        obj: Parsed YAML object (dict, list, or scalar).
        prefix: Current key path prefix.

    Returns:
        Set of dot-path key strings.
    """
    fields: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            fields.add(key)
            fields.update(_walk_yaml_keys(v, key))
    elif isinstance(obj, list):
        for item in obj:
            fields.update(_walk_yaml_keys(item, prefix))
    return fields


def extract_fields_from_yaml(path: Path) -> set[str]:
    """Extract field identifiers from a YAML file.

    Uses recursive dot-path notation for nested keys.

    Args:
        path: Path to YAML file.

    Returns:
        Set of field strings, empty on parse error.
    """
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if not isinstance(data, dict):
        return set()
    return _walk_yaml_keys(data)


def extract_fields_from_markdown(path: Path) -> set[str]:
    """Extract field identifiers from a Markdown file.

    Sources:
    - YAML front-matter top-level keys
    - Table column headers and non-separator cell values

    Args:
        path: Path to Markdown file.

    Returns:
        Set of field strings.
    """
    text = path.read_text(encoding="utf-8")
    fields: set[str] = set()

    # Front-matter: top-level keys
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1)) or {}
            if isinstance(fm, dict):
                fields.update(str(k) for k in fm.keys())
        except Exception:
            pass

    # Markdown table headers and first-column values
    for line in text.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Skip separator rows (only dashes, colons, spaces)
            cells = [c for c in cells if c and not all(ch in "-: " for ch in c)]
            fields.update(cells)

    return fields


def overlap_ratio(a: set[str], b: set[str]) -> float:
    """Compute overlap ratio as intersection / min(|a|, |b|).

    Args:
        a: First field set.
        b: Second field set.

    Returns:
        Float in [0.0, 1.0].
    """
    if not a or not b:
        return 0.0
    smaller = min(len(a), len(b))
    if smaller == 0:
        return 0.0
    return len(a & b) / smaller


# ---------------------------------------------------------------------------
# Substep b: main() and CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Main entry point for lint_no_duplication CLI.

    Returns:
        0 if all overlaps within threshold, 1 if any exceed 40%, 2 on misuse.
    """
    p = argparse.ArgumentParser(
        description="Check field overlap between provenance.md and sibling docs (spec §8.1)."
    )
    p.add_argument("provenance", type=Path, help="Primary provenance Markdown file.")
    p.add_argument("siblings", nargs="*", type=Path, help="Sibling YAML or Markdown files.")
    args = p.parse_args()

    if not args.provenance.is_file():
        print(f"error: provenance file not found: {args.provenance}", file=sys.stderr)
        return 2

    prov_fields = extract_fields_from_markdown(args.provenance)
    if not prov_fields:
        print(f"warn: no fields extracted from {args.provenance}", file=sys.stderr)
        return 0

    fail = False
    for sib in args.siblings:
        sib_path = Path(sib)
        if sib_path.suffix.lower() in (".yaml", ".yml"):
            sib_fields = extract_fields_from_yaml(sib_path)
        else:
            sib_fields = extract_fields_from_markdown(sib_path)
        ratio = overlap_ratio(prov_fields, sib_fields)
        shared_count = len(prov_fields & sib_fields)
        status = "OK" if ratio <= OVERLAP_THRESHOLD else "FAIL"
        print(f"{status}  {sib}  overlap={ratio:.1%}  ({shared_count} shared)")
        if ratio > OVERLAP_THRESHOLD:
            fail = True

    return 1 if fail else 0


# ---------------------------------------------------------------------------
# Substep c: inline smoke tests
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import tempfile
    import unittest

    class TestExtractFields(unittest.TestCase):
        """Smoke tests for field extraction helpers."""

        def test_yaml_flat_keys(self) -> None:
            """YAML flat dict: top-level keys extracted."""
            with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
                f.write("status: verified\nartifact: x\ntemplate: full\n")
                tmp = Path(f.name)
            fields = extract_fields_from_yaml(tmp)
            tmp.unlink()
            self.assertIn("status", fields)
            self.assertIn("artifact", fields)

        def test_yaml_nested_keys(self) -> None:
            """YAML nested dict: dot-path keys extracted."""
            with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
                f.write("outer:\n  inner: val\n")
                tmp = Path(f.name)
            fields = extract_fields_from_yaml(tmp)
            tmp.unlink()
            self.assertIn("outer", fields)
            self.assertIn("outer.inner", fields)

        def test_markdown_frontmatter(self) -> None:
            """Markdown front-matter keys extracted."""
            with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
                f.write("---\ntemplate: lite\nstatus: verified\n---\nbody\n")
                tmp = Path(f.name)
            fields = extract_fields_from_markdown(tmp)
            tmp.unlink()
            self.assertIn("template", fields)
            self.assertIn("status", fields)

        def test_markdown_table_headers(self) -> None:
            """Markdown table headers extracted as fields."""
            with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
                f.write("---\ntemplate: lite\n---\n| name | path | format |\n|------|------|--------|\n| a | /x | tsv |\n")
                tmp = Path(f.name)
            fields = extract_fields_from_markdown(tmp)
            tmp.unlink()
            self.assertIn("name", fields)
            self.assertIn("path", fields)
            self.assertIn("format", fields)

        def test_overlap_ratio_low(self) -> None:
            """Low overlap: ratio below threshold."""
            a = {"template", "status", "created_at", "owner", "project"}
            b = {"template", "foo", "bar", "baz", "qux"}
            ratio = overlap_ratio(a, b)
            self.assertLessEqual(ratio, OVERLAP_THRESHOLD)

        def test_overlap_ratio_high(self) -> None:
            """High overlap: ratio above threshold."""
            a = {"template", "status", "created_at"}
            b = {"template", "status", "created_at"}
            ratio = overlap_ratio(a, b)
            self.assertGreater(ratio, OVERLAP_THRESHOLD)

        def test_overlap_empty_sets(self) -> None:
            """Empty sets return 0.0 ratio."""
            self.assertEqual(overlap_ratio(set(), {"a"}), 0.0)
            self.assertEqual(overlap_ratio({"a"}, set()), 0.0)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestExtractFields)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(3)

    sys.exit(main())
