# Plan Section: Chunk 5 — Phase 2c, Task 2-6 (Unseal Unsafe)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Unseal a sealed provenance.md (downgrade status to verified, chmod 644).

Spec §6.4. Appends an entry to evolution.md (created if missing).

Usage:
    unseal_unsafe.py --doc <sealed-provenance.md> --reason "..."

Exit codes:
    0 - success
    1 - validation failure (doc not sealed)
    2 - misuse (bad args or doc not found)
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_doc, write_doc  # type: ignore


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def append_evolution(doc_path: Path, reason: str) -> Path:
    """Append an unseal entry to evolution.md (created if missing).

    Args:
        doc_path: Absolute path to the provenance document being unsealed.
        reason: Human-readable reason for unsealing (>=30 chars).

    Returns:
        Path to the evolution.md file that was written.
    """
    evo = doc_path.parent / "evolution.md"
    entry = (
        f"\n## Unseal entry — {dt.datetime.now().isoformat(timespec='seconds')}\n\n"
        f"- File: `{doc_path}`\n"
        f"- Action: unseal_unsafe (sealed → verified)\n"
        f"- Reason: {reason}\n"
    )
    if evo.exists():
        existing_text = evo.read_text(encoding="utf-8")
        evo.write_text(existing_text + entry, encoding="utf-8")
    else:
        evo.write_text("# Evolution Log\n" + entry, encoding="utf-8")
    return evo


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point for unseal_unsafe.py.

    Returns:
        0 on success, 1 on validation failure, 2 on misuse.
    """
    parser = argparse.ArgumentParser(
        description="Unseal a sealed provenance.md (status → verified, chmod 644)."
    )
    parser.add_argument("--doc", type=Path, required=True,
                        help="Path to the sealed provenance.md")
    parser.add_argument("--reason", required=True,
                        help=">=30 chars explaining why the doc is being unsealed")
    args = parser.parse_args()

    if not args.doc.is_file():
        print(f"error: doc not found: {args.doc}", file=sys.stderr)
        return 2

    if len(args.reason) < 30:
        print(
            f"error: --reason must be >=30 chars (got {len(args.reason)})",
            file=sys.stderr,
        )
        return 2

    doc = parse_doc(args.doc)
    if doc.status != "sealed":
        print(
            f"error: doc status is '{doc.status}', not 'sealed' — only sealed docs can be unsealed",
            file=sys.stderr,
        )
        return 1

    # Make writable before writing (file may be chmod 444)
    os.chmod(args.doc, 0o644)

    # Downgrade status and clear sealed_at
    doc.front_matter["status"] = "verified"
    doc.front_matter["sealed_at"] = None
    write_doc(doc)

    evo = append_evolution(args.doc, args.reason)
    print(f"OK: unsealed {args.doc} (status -> verified, chmod 644). Evolution: {evo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
