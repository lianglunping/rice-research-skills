# Plan Section: Chunk 6 — Phase 3, Task 3-2 Step 2 (check_v132_mapping.py)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Check v132 section mapping fixture covers >= 90% of source file.

Pass condition (§14.1): covered lines >= 485 (>= 90% of 539).

Run:
    uv run --with pyyaml python3 tests/check_v132_mapping.py

Exit codes:
    0 - coverage >= 90%
    1 - coverage < 90%
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

FIX = Path(__file__).resolve().parent / "fixtures" / "v132_section_mapping.yaml"


def main() -> int:
    """Check mapping coverage and return exit code."""
    if not FIX.exists():
        print(f"ERROR: fixture not found: {FIX}")
        return 1

    m = yaml.safe_load(FIX.read_text(encoding="utf-8"))
    src = Path(m["source_file"])
    declared: int = m["total_lines"]

    if not src.exists():
        print(f"WARN: source file not found locally: {src}")
        print("Falling back to declared total_lines for coverage calculation.")
    else:
        actual_lines = sum(1 for _ in src.open(encoding="utf-8", errors="replace"))
        if actual_lines != declared:
            print(f"WARN: declared total_lines={declared} but actual={actual_lines}")

    # Sum up all mapped line ranges; supports "N" (single line) and "N-M" (range)
    covered: int = 0
    for entry in m["mapping"]:
        raw = str(entry["source_lines"]).strip()
        if "-" in raw:
            parts = raw.split("-")
            a, b = int(parts[0]), int(parts[1])
        else:
            a = b = int(raw)
        covered += b - a + 1

    ratio = covered / declared
    print(f"covered={covered}/{declared} = {ratio * 100:.1f}%")

    if ratio < 0.90:
        print("FAIL: coverage <90%")
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
