#!/usr/bin/env python3
"""Validate the CNS empirical-writing overlay without third-party packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


REQUIRED_FILES = (
    "SKILL.md",
    "references/module-router.md",
    "references/deai-bio-zh-en.md",
    "references/results-to-prose.md",
    "references/literature-review-workflow.md",
    "agents/openai.yaml",
    "references/cns-empirical-writing.md",
    "references/cns-style-evidence.md",
    "examples/cns-style-example.md",
    "tests/cns-style-cases.json",
)
EXPECTED_SECTIONS = "abstract;introduction;results;discussion-or-closing"
EXPECTED_CASE_IDS = {"abstract_en", "results_en", "discussion_zh"}


def fail(messages: list[str], message: str) -> None:
    messages.append(message)


def readable(path: Path, messages: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        fail(messages, f"unreadable: {path}: {exc}")
        return None


def validate_files(root: Path, messages: list[str]) -> dict[str, str]:
    content: dict[str, str] = {}
    for relative in REQUIRED_FILES:
        text = readable(root / relative, messages)
        if text is not None:
            content[relative] = text
    return content


def validate_skill(content: dict[str, str], messages: list[str]) -> None:
    skill = content.get("SKILL.md", "")
    frontmatter = re.search(r"^---\n(.*?)\n---", skill, re.DOTALL)
    if not frontmatter:
        fail(messages, "SKILL.md missing frontmatter")
    else:
        description = re.search(r"^description:\s*(.*)$", frontmatter.group(1), re.MULTILINE)
        if not description or not description.group(1).startswith("Use when"):
            fail(messages, "SKILL.md description must start with 'Use when'")
        if not description or not all(token in description.group(1) for token in ("Cell", "Nature", "Science")):
            fail(messages, "SKILL.md description lacks explicit CNS journal triggers")
    required_links = (
        "references/cns-empirical-writing.md",
        "references/cns-style-evidence.md",
        "examples/cns-style-example.md",
        "tests/cns-style-cases.json",
        "scripts/validate_cns_style_contract.py",
    )
    for link in required_links:
        if link not in skill:
            fail(messages, f"SKILL.md resource map missing {link}")
    for rule in ("style-induced claim escalation", "cargo-cult wording", "identifiers, numbers"):
        if rule not in skill:
            fail(messages, f"SKILL.md hard rule missing: {rule}")


def validate_routing(content: dict[str, str], messages: list[str]) -> None:
    router = content.get("references/module-router.md", "")
    for term in ("primary_module", "style_profile", "journal_target", "cns_empirical", "Exactly one", "at most one overlay"):
        if term not in router:
            fail(messages, f"module router missing routing term: {term}")
    overlay = content.get("references/cns-empirical-writing.md", "")
    for heading in ("## Activation", "## Non-Imitation Boundary", "## Shared Section Contracts", "## Conditional Journal Modifiers", "## Claim Calibration", "## English and Chinese Guidance", "## Final Checklist"):
        if heading not in overlay:
            fail(messages, f"CNS reference missing heading: {heading}")
    for term in ("allele-specific perturbation", "regulatory relationship", "Unvalidated breeding", "Cell", "Nature", "Science"):
        if term not in overlay:
            fail(messages, f"CNS reference missing claim boundary: {term}")
    if "superficial imitation" not in content.get("references/deai-bio-zh-en.md", ""):
        fail(messages, "de-AI reference lacks superficial-imitation boundary")
    result = content.get("references/results-to-prose.md", "")
    for function in ("discovery", "validation", "mechanism", "resource", "application"):
        if function not in result:
            fail(messages, f"results reference lacks paragraph function: {function}")
    literature = content.get("references/literature-review-workflow.md", "")
    if "CNS Introduction Compression" not in literature:
        fail(messages, "literature reference lacks optional CNS introduction route")


def validate_openai(content: dict[str, str], messages: list[str]) -> None:
    text = content.get("agents/openai.yaml", "")
    match = re.search(r'^\s*short_description:\s*"([^"]+)"\s*$', text, re.MULTILINE)
    if not match or not 25 <= len(match.group(1)) <= 64:
        fail(messages, "openai.yaml short_description must be quoted and 25-64 characters")
    prompt = re.search(r'^\s*default_prompt:\s*"([^"]+)"\s*$', text, re.MULTILINE)
    if not prompt or "$bio-thesis-workflow" not in prompt.group(1):
        fail(messages, "openai.yaml default_prompt must contain $bio-thesis-workflow")


def validate_cases(path: Path, messages: list[str]) -> None:
    text = readable(path, messages)
    if text is None:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(messages, f"invalid cases JSON: {exc}")
        return
    cases = data.get("cases") if isinstance(data, dict) else None
    if not isinstance(cases, list) or len(cases) != 3:
        fail(messages, "cases must contain exactly three records")
        return
    ids = set()
    required_fields = {"id", "prompt", "source_facts", "required_literals", "forbidden_claims", "expected_structure", "hard_fail_conditions"}
    for case in cases:
        if not isinstance(case, dict) or not required_fields.issubset(case):
            fail(messages, "each case must include all contract fields")
            continue
        ids.add(case["id"])
        if not all(isinstance(case[field], list) and case[field] for field in required_fields - {"id", "prompt"}):
            fail(messages, f"case {case.get('id')} has empty or invalid evidence fields")
    if ids != EXPECTED_CASE_IDS:
        fail(messages, f"case IDs must be {sorted(EXPECTED_CASE_IDS)}")


def validate_improved_abstract(example_path: Path, cases_path: Path, messages: list[str]) -> None:
    example = readable(example_path, messages)
    cases_text = readable(cases_path, messages)
    if example is None or cases_text is None:
        return
    try:
        cases = json.loads(cases_text)["cases"]
        abstract_case = next(case for case in cases if case["id"] == "abstract_en")
    except (json.JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
        fail(messages, f"cannot load abstract_en case for example validation: {exc}")
        return
    match = re.search(
        r"^## Improved Abstract Decision\n(.*?)(?=^## |\Z)", example, re.DOTALL | re.MULTILINE
    )
    if not match:
        fail(messages, "example missing Improved Abstract Decision")
        return
    decision = re.split(r"^Why this works:", match.group(1), maxsplit=1, flags=re.MULTILINE)[0]
    for literal in abstract_case["required_literals"]:
        if literal not in decision:
            fail(messages, f"Improved Abstract Decision missing required literal: {literal}")
    for claim in abstract_case["forbidden_claims"]:
        if claim in decision:
            fail(messages, f"Improved Abstract Decision contains forbidden claim: {claim}")


def validate_evidence(path: Path, messages: list[str]) -> None:
    text = readable(path, messages)
    if text is None:
        return
    if re.search(r"^\|[^\n]*\b(excerpt|excerpts|quoted text)\b", text, re.IGNORECASE | re.MULTILINE):
        fail(messages, "evidence registry must not contain a source excerpts field")
    lines = [line for line in text.splitlines() if line.startswith("| ")]
    if not lines or "| journal | parent_key | attachment_key | year | DOI | title | fulltext_chars | inspected_sections |" not in lines[0]:
        fail(messages, "evidence table header is missing or invalid")
        return
    rows = []
    for line in lines[1:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) == 8:
            rows.append(cells)
    if len(rows) != 30:
        fail(messages, f"evidence table must contain exactly 30 records, found {len(rows)}")
        return
    journals = Counter(row[0] for row in rows)
    if journals != Counter({"Cell": 10, "Nature": 10, "Science": 10}):
        fail(messages, f"journal counts must be Cell/Nature/Science = 10/10/10, found {dict(journals)}")
    for column, label in ((1, "parent"), (2, "attachment"), (4, "DOI")):
        values = [row[column] for row in rows]
        if len(values) != len(set(values)):
            fail(messages, f"evidence {label} values must be unique")
    for journal, parent, attachment, year, doi, title, chars, sections in rows:
        prefix = "10.1016/j.cell." if journal == "Cell" else "10.1038/" if journal == "Nature" else "10.1126/science."
        if not doi.startswith(prefix):
            fail(messages, f"DOI prefix mismatch for {parent}")
        try:
            if int(year) <= 0 or int(chars) <= 0:
                raise ValueError
        except ValueError:
            fail(messages, f"year/fulltext_chars must be positive for {parent}")
        if sections != EXPECTED_SECTIONS:
            fail(messages, f"inspected_sections mismatch for {parent}")
        if not title:
            fail(messages, f"title missing for {parent}")


def validate_no_markers(root: Path, messages: list[str]) -> None:
    for relative in REQUIRED_FILES:
        text = readable(root / relative, messages)
        if text is not None and re.search(r"\b(TODO|TBD|FIXME)\b|<[^>\n]+>", text):
            fail(messages, f"unresolved marker in {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    if not args.skill_root.is_dir() or not args.cases.is_file() or not args.evidence.is_file():
        print("FAIL input: missing/unreadable skill root, cases, or evidence")
        return 2
    messages: list[str] = []
    content = validate_files(args.skill_root, messages)
    validate_skill(content, messages)
    validate_routing(content, messages)
    validate_openai(content, messages)
    validate_cases(args.cases, messages)
    validate_improved_abstract(args.skill_root / "examples/cns-style-example.md", args.cases, messages)
    validate_evidence(args.evidence, messages)
    validate_no_markers(args.skill_root, messages)
    if messages:
        for message in messages:
            print(f"FAIL {message}")
        return 1
    print("PASS CNS style contract: files, routing, claims, evidence registry, and cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
