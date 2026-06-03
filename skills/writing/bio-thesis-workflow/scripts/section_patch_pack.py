#!/usr/bin/env python3
"""Build a simple review pack between original and revised Markdown/text."""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path
from typing import List


def split_blocks(text: str) -> List[str]:
    blocks: List[str] = []
    current: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            blocks.append(stripped)
            continue
        if stripped == "":
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line.rstrip())
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block]


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Markdown and JSON patch pack")
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--revised", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    original_path = args.original.expanduser().resolve()
    revised_path = args.revised.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    original_blocks = split_blocks(original_path.read_text(encoding="utf-8"))
    revised_blocks = split_blocks(revised_path.read_text(encoding="utf-8"))

    matcher = difflib.SequenceMatcher(a=original_blocks, b=revised_blocks)
    findings = []
    report_lines = [
        "# Section Patch Pack",
        "",
        f"- original: `{original_path}`",
        f"- revised: `{revised_path}`",
        "",
    ]

    change_id = 1
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        finding = {
            "change_id": change_id,
            "tag": tag,
            "original_index_range": [i1, i2],
            "revised_index_range": [j1, j2],
            "original_blocks": original_blocks[i1:i2],
            "revised_blocks": revised_blocks[j1:j2],
        }
        findings.append(finding)

        report_lines.extend(
            [
                f"## Change {change_id} [{tag}]",
                "",
                "### Original",
                "",
            ]
        )
        if original_blocks[i1:i2]:
            report_lines.extend(original_blocks[i1:i2])
        else:
            report_lines.append("_None_")
        report_lines.extend(["", "### Revised", ""])
        if revised_blocks[j1:j2]:
            report_lines.extend(revised_blocks[j1:j2])
        else:
            report_lines.append("_None_")
        report_lines.extend(["", "---", ""])
        change_id += 1

    json_path = output_dir / "patch_pack.json"
    md_path = output_dir / "patch_pack.md"

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "original": str(original_path),
                "revised": str(revised_path),
                "change_count": len(findings),
                "changes": findings,
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )
    md_path.write_text("\n".join(report_lines).rstrip() + "\n", encoding="utf-8")

    print(f"json_path={json_path}")
    print(f"markdown_path={md_path}")
    print(f"change_count={len(findings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
