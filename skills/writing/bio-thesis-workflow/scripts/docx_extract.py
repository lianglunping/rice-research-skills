#!/usr/bin/env python3
"""Extract a DOCX file into Markdown and JSON.

V1 goals:
- preserve heading structure when detectable
- keep paragraph order stable
- serialize tables into simple pipe-table Markdown when possible
- support section-level extraction by heading text match
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Optional

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


@dataclass
class Block:
    block_id: int
    kind: str
    text: str
    style: str
    level: Optional[int] = None
    rows: Optional[List[List[str]]] = None


def iter_block_items(document: Document) -> Iterable[Paragraph | Table]:
    parent = document.element.body
    for child in parent.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


def heading_level(style_name: str) -> Optional[int]:
    lowered = style_name.lower()
    if lowered.startswith("heading "):
        suffix = lowered.replace("heading ", "", 1).strip()
        if suffix.isdigit():
            return int(suffix)
    return None


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\u00a0", " ").split()).strip()


def table_to_rows(table: Table) -> List[List[str]]:
    rows: List[List[str]] = []
    for row in table.rows:
        rows.append([normalize_text(cell.text) for cell in row.cells])
    return rows


def rows_to_markdown(rows: List[List[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    normalized = [r + [""] * (width - len(r)) for r in rows]
    header = normalized[0]
    separator = ["---"] * width
    body = normalized[1:]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def collect_blocks(document: Document) -> List[Block]:
    blocks: List[Block] = []
    block_id = 1
    for item in iter_block_items(document):
        if isinstance(item, Paragraph):
            text = normalize_text(item.text)
            style = item.style.name if item.style else "Normal"
            level = heading_level(style)
            if not text and level is None:
                continue
            blocks.append(
                Block(
                    block_id=block_id,
                    kind="heading" if level is not None else "paragraph",
                    text=text,
                    style=style,
                    level=level,
                )
            )
        else:
            rows = table_to_rows(item)
            blocks.append(
                Block(
                    block_id=block_id,
                    kind="table",
                    text="",
                    style="Table",
                    rows=rows,
                )
            )
        block_id += 1
    return blocks


def filter_section(blocks: List[Block], section_query: str) -> List[Block]:
    query = section_query.strip().lower()
    if not query:
        return blocks
    match_idx = None
    match_level = None
    for idx, block in enumerate(blocks):
        if block.kind == "heading" and query in block.text.lower():
            match_idx = idx
            match_level = block.level or 1
            break
    if match_idx is None:
        raise ValueError(f"Section not found: {section_query}")
    selected: List[Block] = []
    for idx in range(match_idx, len(blocks)):
        block = blocks[idx]
        if idx > match_idx and block.kind == "heading" and (block.level or 99) <= match_level:
            break
        selected.append(block)
    return selected


def blocks_to_markdown(blocks: List[Block]) -> str:
    lines: List[str] = []
    for block in blocks:
        if block.kind == "heading":
            level = max(1, block.level or 1)
            lines.append("#" * level + f" {block.text}")
        elif block.kind == "paragraph":
            lines.append(block.text)
        elif block.kind == "table":
            lines.append(rows_to_markdown(block.rows or []))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract DOCX to Markdown and JSON")
    parser.add_argument("input_docx", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--section", type=str, default="")
    args = parser.parse_args()

    input_docx = args.input_docx.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    document = Document(str(input_docx))
    blocks = collect_blocks(document)
    selected_blocks = filter_section(blocks, args.section) if args.section else blocks

    markdown = blocks_to_markdown(selected_blocks)
    metadata = {
        "input_docx": str(input_docx),
        "section_filter": args.section or None,
        "block_count": len(selected_blocks),
        "paragraph_count": sum(1 for b in selected_blocks if b.kind == "paragraph"),
        "heading_count": sum(1 for b in selected_blocks if b.kind == "heading"),
        "table_count": sum(1 for b in selected_blocks if b.kind == "table"),
    }

    json_path = output_dir / "document.json"
    md_path = output_dir / "document.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "metadata": metadata,
                "blocks": [asdict(block) for block in selected_blocks],
            },
            fh,
            ensure_ascii=False,
            indent=2,
        )
    md_path.write_text(markdown, encoding="utf-8")

    print(f"input_docx={input_docx}")
    print(f"json_path={json_path}")
    print(f"markdown_path={md_path}")
    print(json.dumps(metadata, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
