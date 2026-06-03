# Plan Section: Chunk 3 — Task 2-1 (Schema + state-machine validator)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.0"]
# ///
"""Schema + state-machine validator for provenance.md.

Spec §5.2 + §6 + §11.

Usage:
    python3 status_check.py <provenance.md> [--target-state STATE]
                                              [--enforce-sealed]

Exit codes:
    0 - all checks pass
    1 - validation failure (any rule)
    2 - misuse / file not found
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # type: ignore[import-not-found]
    ProvenanceDoc,
    SCHEMA_DIR,
    is_safe_relative_path,
    parse_claim_rows,
    parse_doc,
)


# ============ Schema check ============

def load_schema() -> dict[str, Any]:
    """Load and meta-validate the JSON Schema from schema/frontmatter.schema.yaml.

    Returns:
        Parsed schema dict.
    """
    schema = yaml.safe_load(
        (SCHEMA_DIR / "frontmatter.schema.yaml").read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return schema


def load_transitions() -> dict[str, Any]:
    """Load the state-machine transition table from schema/transitions.yaml.

    Returns:
        Parsed transitions dict containing 'transitions' list.
    """
    return yaml.safe_load(
        (SCHEMA_DIR / "transitions.yaml").read_text(encoding="utf-8")
    )


def _coerce_dates(fm: dict[str, Any]) -> dict[str, Any]:
    """Convert date/datetime objects in front_matter to ISO strings.

    yaml.safe_load auto-parses bare YYYY-MM-DD values as datetime.date.
    The JSON Schema expects type: string with format: date, so we must
    coerce them back to strings before validation.

    Args:
        fm: Front-matter dict (not mutated).

    Returns:
        New dict with date/datetime values coerced to ISO format strings.
    """
    import datetime
    out = {}
    for k, v in fm.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def schema_check(doc: ProvenanceDoc) -> list[str]:
    """Validate doc.front_matter against frontmatter.schema.yaml.

    Uses Draft202012Validator with FormatChecker for date format validation.
    YAML auto-parses bare dates to datetime.date; these are coerced back to
    ISO strings before validation so the format checker works correctly.

    Args:
        doc: Parsed provenance document.

    Returns:
        List of error message strings; empty means no errors.
    """
    schema = load_schema()
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    coerced_fm = _coerce_dates(doc.front_matter)
    for err in sorted(
        validator.iter_errors(coerced_fm),
        key=lambda e: list(e.path),
    ):
        errors.append(f"schema: {'.'.join(map(str, err.path))}: {err.message}")
    return errors


def transition_check(doc: ProvenanceDoc, target_state: str) -> list[str]:
    """Validate that the transition current_status -> target_state is legal.

    Args:
        doc: Parsed provenance document (provides current status).
        target_state: The desired next state.

    Returns:
        List of error message strings; empty means transition is legal.
    """
    t = load_transitions()
    legal = [(tr["from"], tr["to"]) for tr in t["transitions"]]
    if (doc.status, target_state) not in legal:
        return [
            f"transition: {doc.status} -> {target_state} is illegal"
            " (see schema/transitions.yaml)"
        ]
    return []


# ============ Extension checks ============

def extension_checks(doc: ProvenanceDoc) -> list[str]:
    """Validate extension_sections entries.

    Checks:
    - No duplicate ids
    - source path is safe (relative, no ..)
    - source file exists and is non-empty when status >= verification-ready
    - waiver_reason >= 10 chars when status=waived

    Args:
        doc: Parsed provenance document.

    Returns:
        List of error message strings; empty means no errors.
    """
    errors = []
    seen_ids: set[str] = set()
    for ext in doc.extensions:
        ext_id = ext.get("id", "")
        if ext_id in seen_ids:
            errors.append(f"extension: duplicate id '{ext_id}'")
        seen_ids.add(ext_id)
        src = ext.get("source", "")
        if not is_safe_relative_path(src):
            errors.append(f"extension {ext_id}: unsafe source path '{src}'")
            continue
        src_path = doc.path.parent / src
        if doc.status in ("verification-ready", "verified", "sealed"):
            if not src_path.is_file():
                errors.append(
                    f"extension {ext_id}: source not found: {src_path}"
                )
            elif src_path.stat().st_size == 0:
                errors.append(
                    f"extension {ext_id}: source is empty (status>=verification-ready)"
                )
        if ext.get("status") == "waived":
            wr = ext.get("waiver_reason", "") or ""
            if len(wr) < 10:
                errors.append(
                    f"extension {ext_id}: waiver_reason too short (<10 chars)"
                )
    return errors


# ============ State-machine guards ============

def _claim_state_guards(doc: ProvenanceDoc) -> dict[str, bool]:
    """Compute boolean guard predicates over claim rows for state checks."""
    rows = parse_claim_rows(doc.body)

    def has_value(r: dict[str, str]) -> bool:
        return bool(r.get("value", "").strip())

    def has_command(r: dict[str, str]) -> bool:
        return bool(r.get("command", "").strip())

    def has_observed(r: dict[str, str]) -> bool:
        return bool(r.get("observed_result", "").strip())

    def valid_status(r: dict[str, str]) -> bool:
        return r.get("status", "") in ("verified", "waived")

    return {
        "any_claim_with_value": any(has_value(r) for r in rows),
        "all_value_have_command": all(
            has_command(r) for r in rows if has_value(r)
        ),
        "no_claim_with_value": not any(has_value(r) for r in rows),
        "no_claims_or_all_complete": not rows
        or all(
            has_value(r) and has_command(r) and has_observed(r) and valid_status(r)
            for r in rows
        ),
        "all_complete_and_extensions_verified": all(
            has_value(r) and has_command(r) and has_observed(r) and valid_status(r)
            for r in rows
        )
        and all(
            e.get("status") in ("verified", "waived") for e in doc.extensions
        ),
        "any_value_without_command": any(
            has_value(r) and not has_command(r) for r in rows
        ),
        "any_value_without_observed_result": any(
            has_value(r) and not has_observed(r) for r in rows
        ),
    }


def _in_archive_path(doc: ProvenanceDoc) -> bool:
    """Return True if doc resides under archive/legacy_results/."""
    return "archive/legacy_results/" in str(doc.path.resolve())


def state_check(doc: ProvenanceDoc) -> list[str]:
    """Verify doc status matches its declared invariants.

    Args:
        doc: Parsed provenance document.

    Returns:
        List of error message strings; empty means no errors.
    """
    errors = []
    guards = _claim_state_guards(doc)
    if doc.status == "numbers-pending" and not guards["any_claim_with_value"]:
        errors.append(
            "state: status=numbers-pending but no claim has value"
        )
    if doc.status == "verification-ready" and not guards["all_value_have_command"]:
        errors.append(
            "state: status=verification-ready but some value lacks command"
        )
    if doc.status == "verified" and not guards["all_complete_and_extensions_verified"]:
        errors.append(
            "state: status=verified but claims/extensions incomplete"
        )
    if doc.status == "sealed":
        if not _in_archive_path(doc):
            errors.append(
                "state: status=sealed but path not under archive/legacy_results/"
            )
        if not doc.front_matter.get("sealed_at"):
            errors.append("state: status=sealed but sealed_at is null")
        if not guards["all_complete_and_extensions_verified"]:
            errors.append(
                "state: status=sealed but claims/extensions incomplete"
            )
    return errors


# ============ Sealed protection ============

def sealed_protection_check(doc: ProvenanceDoc) -> list[str]:
    """Warn if sealed file permissions are not 0o444 (read-only).

    Args:
        doc: Parsed provenance document.

    Returns:
        List of error message strings; empty means no errors.
    """
    if doc.status != "sealed":
        return []
    mode = doc.path.stat().st_mode & 0o777
    if mode != 0o444:
        return [
            f"sealed-protection: {doc.path} mode is {oct(mode)},"
            " expected 0o444 (read-only)"
        ]
    return []


# ============ Main ============

def main() -> int:
    """Entry point for status_check.py.

    Returns:
        Exit code: 0 = OK, 1 = validation failure, 2 = misuse/file not found.
    """
    p = argparse.ArgumentParser(
        description="Validate a provenance.md file against schema and state machine."
    )
    p.add_argument("doc", type=Path, help="Path to provenance.md")
    p.add_argument(
        "--target-state",
        default=None,
        help="Validate transition current_status -> target_state",
    )
    p.add_argument(
        "--enforce-sealed",
        action="store_true",
        help="Fail if sealed file is not chmod 0o444",
    )
    args = p.parse_args()

    if not args.doc.is_file():
        print(f"error: file not found: {args.doc}", file=sys.stderr)
        return 2

    try:
        doc = parse_doc(args.doc)
    except ValueError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    errors: list[str] = []
    errors.extend(schema_check(doc))
    errors.extend(extension_checks(doc))
    errors.extend(state_check(doc))
    if args.target_state:
        errors.extend(transition_check(doc, args.target_state))
    if args.enforce_sealed:
        errors.extend(sealed_protection_check(doc))

    if errors:
        print(f"FAIL: {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"OK: {args.doc} status={doc.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
