#!/usr/bin/env python3
"""Initialize a non-destructive, traceable figure-work directory."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path


FIGURE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SUBDIRS = ("contracts", "data/derived", "scripts", "figures", "qa")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create contract, manifest, QA template, and figure-work directories."
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--figure-id", required=True)
    parser.add_argument("--force", action="store_true", help="Replace this figure's templates")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def copy_template(
    source: Path, target: Path, replacements: dict[str, str], force: bool, dry_run: bool
) -> str:
    if target.exists() and not force:
        return f"[KEEP] {target}"
    if dry_run:
        return f"[PLAN] {source.name} -> {target}"
    target.parent.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8")
    for old, new in replacements.items():
        text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")
    return f"[WRITE] {target}"


def main() -> int:
    args = parse_args()
    if not FIGURE_ID.fullmatch(args.figure_id):
        print(
            "[FAIL] figure-id must be 1-64 characters using letters, digits, dot, underscore, or hyphen",
            file=sys.stderr,
        )
        return 2
    skill_root = Path(__file__).resolve().parent.parent
    assets = skill_root / "assets"
    output = args.output.expanduser().resolve()
    if output.exists() and not output.is_dir():
        print(f"[FAIL] output exists and is not a directory: {output}", file=sys.stderr)
        return 2

    if args.dry_run:
        for subdir in SUBDIRS:
            print(f"[PLAN] mkdir {output / subdir}")
    else:
        for subdir in SUBDIRS:
            (output / subdir).mkdir(parents=True, exist_ok=True)

    replacements = {'figure_id: "fig1_main"': f'figure_id: "{args.figure_id}"'}
    print(
        copy_template(
            assets / "figure_contract.yaml",
            output / "contracts" / f"{args.figure_id}_contract.yaml",
            replacements,
            args.force,
            args.dry_run,
        )
    )
    print(
        copy_template(
            assets / "figure_qa.yaml",
            output / "qa" / f"{args.figure_id}_qa.yaml",
            replacements,
            args.force,
            args.dry_run,
        )
    )

    manifest = output / "figures" / "figure_manifest.tsv"
    if manifest.exists():
        print(f"[KEEP] {manifest}")
    elif args.dry_run:
        print(f"[PLAN] figure_manifest.tsv -> {manifest}")
    else:
        shutil.copyfile(assets / "figure_manifest.tsv", manifest)
        print(f"[WRITE] {manifest}")

    print(f"[OK] figure workspace: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
