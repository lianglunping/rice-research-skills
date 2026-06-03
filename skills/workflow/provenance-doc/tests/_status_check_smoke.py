# Plan Section: Chunk 3 — Task 2-1 Step 1 (smoke test for status_check.py)
# Plan Version: 2026-04-30-provenance-doc-plan.md
"""Smoke test for status_check.py — to be merged into test_smoke.py later."""
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

SCRIPT = Path(
    str(Path.home()) + "/.codex/skills/provenance-doc/scripts/status_check.py"
)


def run(doc_text: str, *args: str) -> tuple[int, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(doc_text)
        fp = f.name
    r = subprocess.run(
        ["uv", "run", str(SCRIPT), fp, *args],
        capture_output=True,
        text=True,
    )
    return r.returncode, r.stdout + r.stderr


def test_valid_draft() -> None:
    code, out = run(
        textwrap.dedent("""\
        ---
        template: lite
        status: draft
        created_at: 2026-04-30
        sealed_at: null
        owner: u
        project: p
        ---
        body
        """)
    )
    assert code == 0, f"test_valid_draft FAILED (exit={code}):\n{out}"


def test_invalid_enum() -> None:
    code, out = run(
        textwrap.dedent("""\
        ---
        template: lite
        status: bogus
        created_at: 2026-04-30
        sealed_at: null
        owner: u
        project: p
        ---
        """)
    )
    assert code == 1, f"test_invalid_enum FAILED (exit={code}):\n{out}"


if __name__ == "__main__":
    test_valid_draft()
    test_invalid_enum()
    print("OK")
