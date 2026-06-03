#!/usr/bin/env python3
"""Render Markdown to DOCX through pandoc."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Markdown to DOCX with pandoc")
    parser.add_argument("input_markdown", type=Path)
    parser.add_argument("output_docx", type=Path)
    parser.add_argument("--reference-doc", type=Path, default=None)
    args = parser.parse_args()

    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise SystemExit("pandoc not found in PATH")

    input_markdown = args.input_markdown.expanduser().resolve()
    output_docx = args.output_docx.expanduser().resolve()
    output_docx.parent.mkdir(parents=True, exist_ok=True)

    cmd = [pandoc, str(input_markdown), "-f", "markdown", "-o", str(output_docx)]
    if args.reference_doc:
        reference_doc = args.reference_doc.expanduser().resolve()
        cmd.extend(["--reference-doc", str(reference_doc)])

    completed = subprocess.run(cmd, check=False, text=True, capture_output=True)
    print("command=" + " ".join(cmd))
    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip())
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    print(f"output_docx={output_docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
