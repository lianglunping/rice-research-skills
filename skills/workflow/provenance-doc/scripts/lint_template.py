#!/usr/bin/env python3
# Plan Section: Chunk 2, Task 1-4 — Lint banned terms
# Plan Version: 2026-04-30-provenance-doc-plan.md
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Lint banned terms in core templates / references.

Spec §4.3 + §14.5: any banned term appearing in core (templates/*.j2 +
references/*.md) is a hard fail. Domain-specific terms must live in
extension_sections only.

Matching strategy (per banned_terms.txt header guidance + Fix-13):
- Tokens with len(term) <= 2: use word-boundary regex \\bTERM\\b to avoid
  false positives like "M1 cache", "GT model", "filesystem".
- Tokens with len(term) >= 3: use plain substring match (term in line).

Usage:
    python3 lint_template.py [<file_or_dir>...]

Exit codes:
    0 - clean
    1 - banned terms found
    2 - misuse
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DEFAULT_TARGETS = [
    SKILL_DIR / "templates",
    SKILL_DIR / "references",
]
BANNED_FILE = SKILL_DIR / "schema" / "banned_terms.txt"


# ---------------------------------------------------------------------------
# Substep a: helper functions
# ---------------------------------------------------------------------------


def load_banned_terms(path: Path) -> list[str]:
    """Load non-empty, non-comment lines from banned_terms.txt.

    Returns:
        List of banned term strings.

    Raises:
        SystemExit: if the file is not found.
    """
    if not path.exists():
        raise SystemExit(f"error: banned_terms.txt not found: {path}")
    terms: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        terms.append(s)
    return terms


def _term_matches(term: str, line: str) -> bool:
    """Check if a banned term matches within a line.

    Strategy (Fix-13 / banned_terms.txt header):
    - len(term) <= 2  -> word-boundary regex \\bTERM\\b (avoids "M1 cache",
                          "filesystem" false positives for "FS", etc.)
    - len(term) >= 3  -> plain substring match (term in line)

    Args:
        term: The banned term string.
        line: A single line of text to check.

    Returns:
        True if the term is found according to the matching strategy.
    """
    # Word-boundary for ≤2-char tokens (M1, GT, etc.) AND for tokens that have
    # legitimate generic English usage to avoid false positives:
    #   - "transition" / "transversion" appear in state-machine docs
    #     (e.g. "state transition", "schema/transitions.yaml")
    #   - These are still banned as standalone words in claim/stat tables
    WORD_BOUNDARY_TOKENS = {"transition", "transversion"}
    if len(term) <= 2 or term in WORD_BOUNDARY_TOKENS:
        return bool(re.search(r"\b" + re.escape(term) + r"\b", line))
    return term in line


def scan_file(file_path: Path, terms: list[str]) -> list[tuple[int, str, str]]:
    """Scan a single file for banned terms.

    Each hit is reported at most once per line (first matching term wins).

    Args:
        file_path: Path to file to scan.
        terms: List of banned term strings.

    Returns:
        List of (line_no, stripped_line, banned_term) tuples.
    """
    hits: list[tuple[int, str, str]] = []
    if not file_path.is_file():
        return hits
    text = file_path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), 1):
        for term in terms:
            if _term_matches(term, line):
                hits.append((line_no, line.strip(), term))
                break  # report first hit per line only
    return hits


def collect_files(target: Path) -> list[Path]:
    """Collect all scannable files under a target path.

    Args:
        target: A file or directory path.

    Returns:
        Sorted list of .j2, .md, and .markdown files.
    """
    if target.is_file():
        return [target]
    return sorted(
        list(target.rglob("*.j2"))
        + list(target.rglob("*.md"))
        + list(target.rglob("*.markdown"))
    )


# ---------------------------------------------------------------------------
# Substep b: main() and CLI
# ---------------------------------------------------------------------------


def main() -> int:
    """Main entry point for lint_template CLI.

    Returns:
        0 if clean, 1 if banned terms found, 2 on misuse, 3 on self-test fail.
    """
    p = argparse.ArgumentParser(description="Lint banned terms in core templates.")
    p.add_argument(
        "targets",
        nargs="*",
        type=Path,
        help="Files or dirs to scan (default: templates/ + references/)",
    )
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Run inline unit tests for _term_matches and exit (no lint).",
    )
    args = p.parse_args()

    if args.self_test:
        return _run_self_test()

    targets: list[Path] = args.targets or DEFAULT_TARGETS
    terms = load_banned_terms(BANNED_FILE)

    all_hits: list[tuple[Path, int, str, str]] = []
    for target in targets:
        for f in collect_files(Path(target)):
            for line_no, line, term in scan_file(f, terms):
                all_hits.append((f, line_no, line, term))

    if all_hits:
        print(f"FAIL: {len(all_hits)} banned-term hits", file=sys.stderr)
        for f, line_no, line, term in all_hits:
            print(f"  {f}:{line_no}: '{term}' in: {line[:80]}", file=sys.stderr)
        return 1

    print(f"OK: {len(terms)} banned terms checked, 0 hits.")
    return 0


# ---------------------------------------------------------------------------
# Substep c: inline TDD tests (gated behind --self-test to avoid noise on lint runs)
# ---------------------------------------------------------------------------


def _run_self_test() -> int:
    """Run inline unit tests for _term_matches.

    Invoked only via `lint_template.py --self-test`; never on normal lint runs.

    Returns:
        0 if all tests pass, 3 otherwise.
    """
    import unittest

    class TestTermMatches(unittest.TestCase):
        """Unit tests for _term_matches — exercises both word-boundary and substring modes."""

        # ---- Short tokens (len <= 2): word-boundary mode ----

        def test_short_token_standalone_match(self) -> None:
            """'GT' should match when it stands alone."""
            self.assertTrue(_term_matches("GT", "sample GT value"))

        def test_short_token_no_false_positive_filesystem(self) -> None:
            """'FS' should NOT match inside 'filesystem'."""
            self.assertFalse(_term_matches("FS", "filesystem path"))

        def test_short_token_no_false_positive_m1_cache(self) -> None:
            """'M1' as a substring of 'M1cache' should NOT match (no word boundary)."""
            self.assertFalse(_term_matches("M1", "M1cache specs"))

        def test_short_token_matches_with_boundary(self) -> None:
            """'M1' should match when surrounded by spaces."""
            self.assertTrue(_term_matches("M1", "generation M1 plant"))

        def test_single_char_word_boundary(self) -> None:
            """Single-char token on its own word should match."""
            self.assertTrue(_term_matches("A", "column A value"))

        # ---- Long tokens (len >= 3): substring mode ----

        def test_long_token_substring_match(self) -> None:
            """'carrier_family' should match as substring."""
            self.assertTrue(_term_matches("carrier_family", "this contains carrier_family here"))

        def test_long_token_no_match(self) -> None:
            """'carrier_family' should not match unrelated string."""
            self.assertFalse(_term_matches("carrier_family", "no such term here"))

        def test_long_token_embedded_match(self) -> None:
            """Long token embedded in a longer word should still match (substring)."""
            self.assertTrue(_term_matches("ANNOVAR", "run ANNOVAR annotation"))

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestTermMatches)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 3


if __name__ == "__main__":
    sys.exit(main())
