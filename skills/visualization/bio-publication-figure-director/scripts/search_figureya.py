#!/usr/bin/env python3
"""Search the locally downloaded FigureYa modules without executing them."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


SEARCH_SUFFIXES = {".rmd", ".r", ".md", ".txt"}
HUMAN_BINDING = re.compile(
    r"TxDb\.Hsapiens|org\.Hs\.eg\.db|Homo sapiens|hg19|hg38|TCGA",
    re.IGNORECASE,
)


@dataclass
class Hit:
    module: str
    score: int
    matched_terms: list[str]
    matched_files: list[str]
    human_binding_warning: bool
    path: str


def resolve_root(explicit: Path | None) -> Path:
    if explicit:
        path = explicit.expanduser()
        if path.is_dir() and (path / ".git").exists():
            return path.resolve()
        raise FileNotFoundError(f"explicit FigureYa root is invalid: {path}")
    env_root = os.environ.get("FIGUREYA_ROOT")
    if env_root:
        path = Path(env_root).expanduser()
        if path.is_dir() and (path / ".git").exists():
            return path.resolve()
        raise FileNotFoundError(f"FIGUREYA_ROOT is invalid: {path}")
    raise FileNotFoundError("Pass --root or set FIGUREYA_ROOT to a FigureYa checkout.")


def readable_files(module: Path) -> list[Path]:
    files: list[Path] = []
    for path in module.rglob("*"):
        if (
            path.is_file()
            and path.suffix.casefold() in SEARCH_SUFFIXES
            and path.stat().st_size <= 5 * 1024 * 1024
        ):
            files.append(path)
    return files


def search(root: Path, terms: list[str]) -> list[Hit]:
    normalized = [term.casefold() for term in terms]
    hits: list[Hit] = []
    for module in sorted(root.glob("FigureYa*")):
        if not module.is_dir():
            continue
        module_text = module.name.casefold()
        score = sum(6 for term in normalized if term in module_text)
        matched_terms = {term for term in normalized if term in module_text}
        matched_files: set[str] = set()
        human_binding = False
        for path in readable_files(module):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            lowered = text.casefold()
            file_matches = [term for term in normalized if term in lowered]
            if file_matches:
                score += sum(min(lowered.count(term), 10) for term in file_matches)
                matched_terms.update(file_matches)
                matched_files.add(str(path.relative_to(root)))
            if HUMAN_BINDING.search(text):
                human_binding = True
        if score:
            hits.append(
                Hit(
                    module=module.name,
                    score=score,
                    matched_terms=sorted(matched_terms),
                    matched_files=sorted(matched_files),
                    human_binding_warning=human_binding,
                    path=str(module.resolve()),
                )
            )
    return sorted(hits, key=lambda item: (-item.score, item.module.casefold()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search checked-out FigureYa R/Rmd modules by keyword."
    )
    parser.add_argument("query", nargs="+", help="One or more search terms")
    parser.add_argument("--root", type=Path, help="FigureYa checkout root")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        root = resolve_root(args.root)
    except FileNotFoundError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 2
    hits = search(root, args.query)[: max(args.limit, 0)]
    if args.json:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "query": args.query,
                    "hits": [asdict(item) for item in hits],
                    "license": "CC BY-NC-SA 4.0; inspect and adapt, do not execute automatically.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"[FigureYa] root: {root}")
        print("[License] CC BY-NC-SA 4.0; inspect Rmd before adaptation.")
        if not hits:
            print("[INFO] no checked-out module matched")
            return 1
        for index, hit in enumerate(hits, start=1):
            warning = " [human-bound inputs/packages]" if hit.human_binding_warning else ""
            print(f"{index}. {hit.module} score={hit.score}{warning}")
            print(f"   path: {hit.path}")
            print(f"   terms: {', '.join(hit.matched_terms)}")
            for path in hit.matched_files[:5]:
                print(f"   file: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
