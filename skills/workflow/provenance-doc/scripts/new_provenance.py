# Plan Section: Chunk 3 — Task 2-2 (Create provenance.md documents)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jinja2>=3.1"]
# ///
"""Create a new provenance.md from full or lite template.

Spec §4 + §13 Phase 0/1.

Usage:
    new_provenance.py --template (full|lite) --out <path> --owner <user> --project <name>
                      [--version v1.0] [--title "..."]
                      [--extension id:source,id2:source2]
                      [--runs N]
                      [--upgrade lite-to-full --upgrade-from <existing.md>]
                      [--force]

Exit codes:
    0 - success
    1 - error (file exists, validation failure, wrong template)
    2 - misuse (missing required args)
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "templates"


def parse_extensions(spec: str | None) -> list[dict[str, str]]:
    """Parse comma-separated id:source pairs into extension_sections dicts.

    Args:
        spec: String like "ext1:path/a.md,ext2:path/b.md" or None.

    Returns:
        List of extension section dicts with id/title/source/status/waiver_reason.

    Raises:
        SystemExit: When a part is missing the ':' separator.
    """
    if not spec:
        return []
    out = []
    for part in spec.split(","):
        if ":" not in part:
            raise SystemExit(f"error: extension '{part}' missing ':' separator")
        eid, src = part.split(":", 1)
        out.append(
            {
                "id": eid.strip(),
                "title": eid.strip().replace("_", " ").title(),
                "source": src.strip(),
                "status": "draft",
                "waiver_reason": "",
            }
        )
    return out


def render(template_name: str, ctx: dict) -> str:
    """Render a Jinja2 template from the templates/ directory.

    Args:
        template_name: Filename (e.g. 'full.md.j2').
        ctx: Template context dict.

    Returns:
        Rendered string.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
    )
    return env.get_template(template_name).render(**ctx)


def upgrade_lite_to_full(existing: Path, out: Path) -> int:
    """Read a lite doc, carry fields + claims into full template, write to out.

    Preserves §4.2 claim rows from the lite body via parse_claim_rows (Fix-6).
    Sections §0-3 narrative text cannot be auto-migrated; full doc will have
    TODO placeholders that must be filled manually.

    Args:
        existing: Path to the existing lite provenance.md.
        out: Destination path for the upgraded full provenance.md.

    Returns:
        0 on success, 1 on error.
    """
    sys.path.insert(0, str(SCRIPT_DIR))
    from _common import parse_claim_rows, parse_doc  # type: ignore[import-not-found]

    doc = parse_doc(existing)
    if doc.template != "lite":
        print(f"error: {existing} is not template=lite", file=sys.stderr)
        return 1
    fm = doc.front_matter
    # Preserve §4.2 / §5 claims from body (Fix-6)
    claims = parse_claim_rows(doc.body)
    ctx = {
        "title": fm.get("title") or existing.stem,
        "version": fm.get("version") or "v0.1",
        "created_at": fm.get("created_at") or dt.date.today().isoformat(),
        "sealed_at": "null",
        "owner": fm.get("owner") or "unknown",
        "project": fm.get("project") or "unknown",
        "prior_version": "null",
        "delta_summary_path": "null",
        "extension_sections": fm.get("extension_sections") or [],
        "verification_timeout": (fm.get("verification") or {}).get(
            "remote_command_timeout_sec", 300
        ),
        "claims": claims,  # preserved §5 claim rows
        # NOTE: §0-3 narrative sections need manual TODO completion in full template
    }
    out.write_text(render("full.md.j2", ctx), encoding="utf-8")
    print(
        f"OK: upgraded {existing} -> {out} (lite -> full);"
        " review TODO sections in full template",
        file=sys.stderr,
    )
    return 0


def main() -> int:
    """Entry point for new_provenance.py.

    Returns:
        Exit code: 0 = success, 1 = error, 2 = misuse.
    """
    p = argparse.ArgumentParser(
        description="Create a new provenance.md from full or lite template."
    )
    p.add_argument("--template", choices=["full", "lite"])
    p.add_argument("--out", type=Path, required=True, help="Output file path")
    p.add_argument("--owner", default="")
    p.add_argument("--project", default="")
    p.add_argument("--version", default="v0.1")
    p.add_argument("--title", default="")
    p.add_argument(
        "--extension",
        default=None,
        help="Comma-separated id:source pairs for extension_sections",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of upstream runs (lite forbids >1)",
    )
    p.add_argument(
        "--upgrade",
        choices=["lite-to-full"],
        default=None,
        help="Upgrade mode",
    )
    p.add_argument(
        "--upgrade-from",
        type=Path,
        default=None,
        help="Source lite doc for --upgrade lite-to-full",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output file",
    )
    args = p.parse_args()

    # --- Upgrade mode ---
    if args.upgrade == "lite-to-full":
        if not args.upgrade_from:
            print(
                "error: --upgrade lite-to-full requires --upgrade-from",
                file=sys.stderr,
            )
            return 2
        if args.out.exists() and not args.force:
            print(f"error: {args.out} exists; use --force", file=sys.stderr)
            return 1
        return upgrade_lite_to_full(args.upgrade_from, args.out)

    # --- Normal create mode ---
    if not args.template:
        print("error: --template required (unless --upgrade)", file=sys.stderr)
        return 2

    if not args.owner or not args.project:
        print("error: --owner and --project required", file=sys.stderr)
        return 2

    if args.template == "lite" and args.runs > 1:
        print(
            "error: lite template forbids multi-run; use --template full",
            file=sys.stderr,
        )
        return 1

    if args.out.exists() and not args.force:
        print(f"error: {args.out} exists; use --force", file=sys.stderr)
        return 1

    ctx = {
        "title": args.title or args.out.stem,
        "version": args.version,
        "created_at": dt.date.today().isoformat(),
        "sealed_at": "null",
        "owner": args.owner,
        "project": args.project,
        "prior_version": "null",
        "delta_summary_path": "null",
        "extension_sections": parse_extensions(args.extension),
        "verification_timeout": 300,
        "fail_closed_on_missing_meta": True,
    }
    out_dir = args.out.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(f"{args.template}.md.j2", ctx), encoding="utf-8")
    print(f"OK: created {args.out} (template={args.template})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
