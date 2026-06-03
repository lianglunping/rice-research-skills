# Plan Section: Chunk 6 — Phase 3, Fix-7 (test_state_machine.py)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0", "jsonschema>=4.0"]
# ///
"""State machine unit tests: 4 test classes covering 9 legal + 5 illegal transitions.

Run:
    uv run --with pyyaml --with jsonschema python3 tests/test_state_machine.py -v
"""
from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent.parent / "scripts"
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"
sys.path.insert(0, str(SCRIPT_DIR))
import status_check  # type: ignore[import-not-found]
from _common import parse_doc  # type: ignore[import-not-found]


def make_doc(status: str, body: str = "") -> Path:
    """Write a temporary provenance.md with the given status and optional body."""
    fd, path_str = tempfile.mkstemp(suffix=".md")
    import os
    os.close(fd)
    p = Path(path_str)
    p.write_text(textwrap.dedent(f"""\
        ---
        template: lite
        status: {status}
        created_at: 2026-04-30
        sealed_at: null
        owner: u
        project: p
        ---
        {body}
    """), encoding="utf-8")
    return p


class TestTransitionTableLoaded(unittest.TestCase):
    """Verify transitions.yaml has expected shape: 9 legal + 5 illegal."""

    def setUp(self) -> None:
        self.transitions = yaml.safe_load(
            (SCHEMA_DIR / "transitions.yaml").read_text(encoding="utf-8")
        )

    def test_metadata_counts_match_actual(self) -> None:
        """`counts` metadata must agree with actual list lengths.

        This single test replaces the older hardcoded `==9` / `==5` asserts:
        the source of truth is `counts` in transitions.yaml, and the lists
        must match it. Prevents silent drift if either side is edited
        without updating the other.
        """
        counts = self.transitions["counts"]
        actual_legal = len(self.transitions["transitions"])
        actual_illegal = len(self.transitions["illegal_examples"])
        actual_states = len(self.transitions["states"])
        self.assertEqual(
            counts["legal_transitions"], actual_legal,
            f"counts.legal_transitions={counts['legal_transitions']} but list has {actual_legal}",
        )
        self.assertEqual(
            counts["illegal_examples"], actual_illegal,
            f"counts.illegal_examples={counts['illegal_examples']} but list has {actual_illegal}",
        )
        self.assertEqual(
            counts["states"], actual_states,
            f"counts.states={counts['states']} but list has {actual_states}",
        )

    def test_spec_minimums(self) -> None:
        """Spec §6.3 minimum requirements: ≥9 legal + ≥5 illegal + 5 states."""
        counts = self.transitions["counts"]
        self.assertGreaterEqual(counts["legal_transitions"], 9)
        self.assertGreaterEqual(counts["illegal_examples"], 5)
        self.assertEqual(counts["states"], 5)


class TestLegalTransitionsAccepted(unittest.TestCase):
    """transition_check() must return [] for every legal from→to pair."""

    def setUp(self) -> None:
        raw = yaml.safe_load(
            (SCHEMA_DIR / "transitions.yaml").read_text(encoding="utf-8")
        )
        self.legal = raw["transitions"]

    def test_status_check_accepts_legal(self) -> None:
        """All 9 legal transitions should produce zero errors from transition_check()."""
        for tr in self.legal:
            with self.subTest(transition=f"{tr['from']}→{tr['to']}"):
                doc_path = make_doc(tr["from"])
                doc = parse_doc(doc_path)
                errs = status_check.transition_check(doc, tr["to"])
                self.assertEqual(
                    len(errs),
                    0,
                    f"{tr['from']}→{tr['to']} should be allowed but got: {errs}",
                )
                doc_path.unlink(missing_ok=True)


class TestIllegalTransitionsRejected(unittest.TestCase):
    """transition_check() must return non-empty errors for every illegal pair."""

    def setUp(self) -> None:
        raw = yaml.safe_load(
            (SCHEMA_DIR / "transitions.yaml").read_text(encoding="utf-8")
        )
        self.illegal = raw["illegal_examples"]

    def test_status_check_rejects_illegal(self) -> None:
        """All 5 illegal transitions should be rejected by transition_check()."""
        for ill in self.illegal:
            with self.subTest(transition=f"{ill['from']}→{ill['to']}"):
                doc_path = make_doc(ill["from"])
                doc = parse_doc(doc_path)
                errs = status_check.transition_check(doc, ill["to"])
                self.assertGreater(
                    len(errs),
                    0,
                    f"{ill['from']}→{ill['to']} should be rejected (reason: {ill.get('reason')})",
                )
                doc_path.unlink(missing_ok=True)


class TestTerminalStateSealed(unittest.TestCase):
    """Verify sealed is terminal: no outbound transitions permitted."""

    def test_sealed_cannot_transition_to_any_non_terminal(self) -> None:
        """sealed → any non-sealed state must all be rejected."""
        non_sealed = ["draft", "numbers-pending", "verification-ready", "verified"]
        doc_path = make_doc("sealed")
        doc = parse_doc(doc_path)
        doc_path.unlink(missing_ok=True)
        for target in non_sealed:
            with self.subTest(target=target):
                errs = status_check.transition_check(doc, target)
                self.assertGreater(
                    len(errs),
                    0,
                    f"sealed→{target} should be rejected as terminal",
                )

    def test_sealed_to_sealed_is_noop_or_allowed(self) -> None:
        """sealed→sealed self-loop: either allowed (0 errors) or rejected is fine,
        but we do NOT require it to be blocked (no spec requirement)."""
        doc_path = make_doc("sealed")
        doc = parse_doc(doc_path)
        doc_path.unlink(missing_ok=True)
        # Just verify no exception is raised — result may be [] or [error]
        errs = status_check.transition_check(doc, "sealed")
        self.assertIsInstance(errs, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
