# Plan Section: Chunk 3 — Task 2-0 (Shared helpers)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
"""Common helpers for provenance-doc scripts."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
SCHEMA_DIR = SKILL_DIR / "schema"


@dataclass
class ProvenanceDoc:
    path: Path
    front_matter: dict[str, Any]
    body: str

    @property
    def template(self) -> str:
        return self.front_matter.get("template", "")

    @property
    def status(self) -> str:
        return self.front_matter.get("status", "")

    @property
    def extensions(self) -> list[dict[str, Any]]:
        return self.front_matter.get("extension_sections") or []


FRONT_MATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)", re.DOTALL)


def parse_doc(path: Path) -> ProvenanceDoc:
    """Parse a provenance.md file with YAML front-matter.

    Args:
        path: Absolute path to the provenance document.

    Returns:
        ProvenanceDoc instance with parsed front_matter and body.

    Raises:
        ValueError: When front-matter is missing or malformed.
    """
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path}: no YAML front-matter found")
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"{path}: front-matter YAML parse error: {e}")
    if not isinstance(fm, dict):
        raise ValueError(f"{path}: front-matter is not a mapping")
    body = m.group(2)
    return ProvenanceDoc(path=path, front_matter=fm, body=body)


def write_doc(doc: ProvenanceDoc) -> None:
    """Write back a doc with updated front-matter.

    Args:
        doc: ProvenanceDoc whose path will be overwritten.
    """
    fm_yaml = yaml.safe_dump(doc.front_matter, sort_keys=False, allow_unicode=True)
    text = f"---\n{fm_yaml}---\n{doc.body}"
    doc.path.write_text(text, encoding="utf-8")


def is_safe_relative_path(path_str: str) -> bool:
    """Return True if path_str is a safe relative path (no absolute, no '..' segments).

    Args:
        path_str: String to check.

    Returns:
        True when path is non-empty, relative, and contains no '..' parts.
    """
    if not path_str:
        return False
    p = Path(path_str)
    if p.is_absolute():
        return False
    if ".." in p.parts:
        return False
    return True


# === Claim table parsing (very lightweight) ===
CLAIM_TABLE_HEADER_RE = re.compile(
    r"^\|\s*claim_id\s*\|.*\|\s*status\s*\|", re.IGNORECASE | re.MULTILINE
)


def parse_claim_rows(body: str) -> list[dict[str, str]]:
    """Extract rows of the claim table from document body.

    Supports both §4.2 (lite) and §5 (full) claim table headers.
    Returns list of dicts keyed by header column names.

    Args:
        body: Document body text (everything after the YAML front-matter).

    Returns:
        List of row dicts, one per data row. Empty list if no table found.
    """
    lines = body.splitlines()
    rows: list[dict[str, str]] = []
    in_table = False
    headers: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not in_table:
            if CLAIM_TABLE_HEADER_RE.search(line):
                headers = [c.strip() for c in stripped.strip("|").split("|")]
                in_table = True
            continue
        if not stripped.startswith("|"):
            in_table = False
            continue
        cells = [c.strip().strip("`") for c in stripped.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # separator row
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows
