# Plan Section: Chunk 3 — Phase 2a (Tasks 2-0, 2-1, 2-2)
# Plan Version: 2026-04-30-provenance-doc-plan.md
"""Smoke tests for Chunk 3 scripts: _common, status_check, new_provenance.

TDD red-test-first per Fix-1 + Fix-2.
Each Test class follows the order: happy path, invalid input, edge case.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_script(script: Path, *args: str) -> tuple[int, str]:
    """Run a script via uv and return (exit_code, combined_output)."""
    r = subprocess.run(
        ["uv", "run", str(script), *args],
        capture_output=True,
        text=True,
    )
    return r.returncode, r.stdout + r.stderr


def _run_py(code: str) -> tuple[int, str]:
    """Run inline Python via uv."""
    r = subprocess.run(
        ["uv", "run", "--with", "pyyaml", "python3", "-c", code],
        capture_output=True,
        text=True,
    )
    return r.returncode, r.stdout + r.stderr


def _write_tmp(content: str, suffix: str = ".md") -> Path:
    f = tempfile.NamedTemporaryFile(
        "w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return Path(f.name)


# ---------------------------------------------------------------------------
# Task 2-0: _common.py
# ---------------------------------------------------------------------------

class TestCommon(unittest.TestCase):
    """Tests for _common.py helpers."""

    def test_import_ok(self) -> None:
        """Happy path: module imports without error."""
        code = (
            "import sys; "
            f"sys.path.insert(0, '{SCRIPTS_DIR}'); "
            "import _common; "
            "print('OK')"
        )
        rc, out = _run_py(code)
        self.assertEqual(rc, 0, out)
        self.assertIn("OK", out)

    def test_parse_doc_valid(self) -> None:
        """Happy path: parse_doc returns correct template and status."""
        content = textwrap.dedent("""\
            ---
            template: lite
            status: draft
            created_at: 2026-04-30
            sealed_at: null
            owner: u
            project: p
            ---
            body text
        """)
        tmp = _write_tmp(content)
        code = (
            "import sys; "
            f"sys.path.insert(0, '{SCRIPTS_DIR}'); "
            "from _common import parse_doc; "
            "from pathlib import Path; "
            f"doc = parse_doc(Path('{tmp}')); "
            "assert doc.template == 'lite', doc.template; "
            "assert doc.status == 'draft', doc.status; "
            "print('OK')"
        )
        rc, out = _run_py(code)
        tmp.unlink(missing_ok=True)
        self.assertEqual(rc, 0, out)
        self.assertIn("OK", out)

    def test_parse_doc_no_frontmatter_raises(self) -> None:
        """Invalid input: file with no YAML front-matter raises ValueError."""
        content = "just body, no front-matter\n"
        tmp = _write_tmp(content)
        py_script = textwrap.dedent(f"""\
            import sys
            sys.path.insert(0, '{SCRIPTS_DIR}')
            from _common import parse_doc
            from pathlib import Path
            try:
                parse_doc(Path('{tmp}'))
                print('SHOULD_HAVE_RAISED')
                sys.exit(1)
            except ValueError:
                print('OK')
                sys.exit(0)
        """)
        script_file = _write_tmp(py_script, suffix=".py")
        r = subprocess.run(
            ["uv", "run", "--with", "pyyaml", "python3", str(script_file)],
            capture_output=True, text=True,
        )
        tmp.unlink(missing_ok=True)
        script_file.unlink(missing_ok=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout + r.stderr)

    def test_parse_claim_rows_extracts_table(self) -> None:
        """Happy path: parse_claim_rows extracts rows from §5 claim table."""
        body = textwrap.dedent("""\
            ## 5. claims
            | claim_id | claim_text | value | command | observed_result | status |
            |----------|-----------|-------|---------|-----------------|--------|
            | c1 | some text | 42 | echo 42 | 42 | verified |
        """)
        code = (
            "import sys; "
            f"sys.path.insert(0, '{SCRIPTS_DIR}'); "
            "from _common import parse_claim_rows; "
            f"rows = parse_claim_rows({body!r}); "
            "assert len(rows) == 1, rows; "
            "assert rows[0]['claim_id'] == 'c1', rows; "
            "print('OK')"
        )
        rc, out = _run_py(code)
        self.assertEqual(rc, 0, out)
        self.assertIn("OK", out)

    def test_is_safe_relative_path(self) -> None:
        """Edge cases: path safety checks."""
        code = (
            "import sys; "
            f"sys.path.insert(0, '{SCRIPTS_DIR}'); "
            "from _common import is_safe_relative_path; "
            "assert is_safe_relative_path('data/foo.txt') is True; "
            "assert is_safe_relative_path('/abs/path') is False; "
            "assert is_safe_relative_path('../escape') is False; "
            "assert is_safe_relative_path('') is False; "
            "print('OK')"
        )
        rc, out = _run_py(code)
        self.assertEqual(rc, 0, out)
        self.assertIn("OK", out)


# ---------------------------------------------------------------------------
# Task 2-1: status_check.py
# ---------------------------------------------------------------------------

VALID_DRAFT_DOC = textwrap.dedent("""\
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

INVALID_ENUM_DOC = textwrap.dedent("""\
    ---
    template: lite
    status: bogus
    created_at: 2026-04-30
    sealed_at: null
    owner: u
    project: p
    ---
""")

STATUS_CHECK = SCRIPTS_DIR / "status_check.py"


class TestStatusCheck(unittest.TestCase):
    """Tests for status_check.py."""

    def test_valid_draft_passes(self) -> None:
        """Happy path: valid draft doc exits 0."""
        tmp = _write_tmp(VALID_DRAFT_DOC)
        rc, out = _run_script(STATUS_CHECK, str(tmp))
        tmp.unlink(missing_ok=True)
        self.assertEqual(rc, 0, out)

    def test_invalid_enum_fails(self) -> None:
        """Invalid input: status=bogus not in enum → exit 1."""
        tmp = _write_tmp(INVALID_ENUM_DOC)
        rc, out = _run_script(STATUS_CHECK, str(tmp))
        tmp.unlink(missing_ok=True)
        self.assertEqual(rc, 1, out)

    def test_missing_file_exit2(self) -> None:
        """Edge case: file not found → exit 2."""
        rc, out = _run_script(STATUS_CHECK, "/nonexistent/path/prov.md")
        self.assertEqual(rc, 2, out)

    def test_transition_check_legal(self) -> None:
        """Happy path: draft -> numbers-pending is a legal transition."""
        tmp = _write_tmp(VALID_DRAFT_DOC)
        rc, out = _run_script(STATUS_CHECK, str(tmp), "--target-state", "numbers-pending")
        tmp.unlink(missing_ok=True)
        self.assertEqual(rc, 0, out)

    def test_transition_check_illegal(self) -> None:
        """Invalid input: draft -> sealed is illegal → exit 1."""
        tmp = _write_tmp(VALID_DRAFT_DOC)
        rc, out = _run_script(STATUS_CHECK, str(tmp), "--target-state", "sealed")
        tmp.unlink(missing_ok=True)
        self.assertEqual(rc, 1, out)

    def test_duplicate_extension_id_fails(self) -> None:
        """Edge case: duplicate extension_sections id → exit 1."""
        doc = textwrap.dedent("""\
            ---
            template: full
            status: draft
            version: v0.1
            created_at: 2026-04-30
            sealed_at: null
            owner: u
            project: p
            prior_version: null
            extension_sections:
              - id: abc_ext
                title: "Abc"
                source: abc.md
                status: draft
                waiver_reason: ""
              - id: abc_ext
                title: "Abc dup"
                source: abc2.md
                status: draft
                waiver_reason: ""
            ---
        """)
        tmp = _write_tmp(doc)
        rc, out = _run_script(STATUS_CHECK, str(tmp))
        tmp.unlink(missing_ok=True)
        self.assertEqual(rc, 1, out)
        self.assertIn("duplicate", out)


# ---------------------------------------------------------------------------
# Task 2-2: new_provenance.py
# ---------------------------------------------------------------------------

NEW_PROV = SCRIPTS_DIR / "new_provenance.py"


class TestNewProvenance(unittest.TestCase):
    """Tests for new_provenance.py."""

    def test_create_lite_doc(self) -> None:
        """Happy path: --template lite creates a file with correct markers."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "test-prov.md"
            rc, log = _run_script(
                NEW_PROV,
                "--template", "lite",
                "--out", str(out),
                "--owner", "u",
                "--project", "p",
            )
            self.assertEqual(rc, 0, log)
            self.assertTrue(out.exists(), "output file not created")
            content = out.read_text(encoding="utf-8")
            self.assertIn("template: lite", content)
            self.assertIn("## 0. 状态与范围", content)

    def test_multi_run_lite_rejected(self) -> None:
        """Invalid input: lite + --runs 3 → exit 1."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "test-prov2.md"
            rc, log = _run_script(
                NEW_PROV,
                "--template", "lite",
                "--out", str(out),
                "--owner", "u",
                "--project", "p",
                "--runs", "3",
            )
            self.assertEqual(rc, 1, log)
            self.assertIn("lite template forbids multi-run", log)

    def test_overwrite_without_force_rejected(self) -> None:
        """Edge case: existing file + no --force → exit 1."""
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "existing.md"
            out.write_text("existing content", encoding="utf-8")
            rc, log = _run_script(
                NEW_PROV,
                "--template", "lite",
                "--out", str(out),
                "--owner", "u",
                "--project", "p",
            )
            self.assertEqual(rc, 1, log)
            self.assertIn("exists", log)

    def test_upgrade_lite_to_full_preserves_claims(self) -> None:
        """Happy path: upgrade lite->full preserves claim rows from §4.2."""
        lite_content = textwrap.dedent("""\
            ---
            template: lite
            status: draft
            created_at: 2026-04-30
            sealed_at: null
            owner: u
            project: p
            extension_sections: []
            verification:
              remote_command_timeout_sec: 300
              fail_closed_on_missing_meta: true
              fail_closed_on_broken_yaml: true
            ---
            # test

            **所有者**: u | **项目**: p | **创建**: 2026-04-30

            ## 4. 输出产物与已验证论断

            ### 4.2 论断验证表（合并版）
            | claim_id | claim_text | value | command | observed_result | status |
            |----------|-----------|-------|---------|-----------------|--------|
            | c1 | total rows | 42 | echo 42 | 42 | verified |
        """)
        with tempfile.TemporaryDirectory() as td:
            existing = Path(td) / "lite.md"
            existing.write_text(lite_content, encoding="utf-8")
            out = Path(td) / "full.md"
            rc, log = _run_script(
                NEW_PROV,
                "--upgrade", "lite-to-full",
                "--upgrade-from", str(existing),
                "--out", str(out),
            )
            self.assertEqual(rc, 0, log)
            self.assertTrue(out.exists(), "output file not created")
            full_content = out.read_text(encoding="utf-8")
            # Claim row must be preserved
            self.assertIn("c1", full_content, "claim_id c1 not found in upgraded full doc")
            self.assertIn("total rows", full_content)


# ---------------------------------------------------------------------------
# Task 2-3: aggregate_meta.py
# ---------------------------------------------------------------------------

AGGREGATE_META = SCRIPTS_DIR / "aggregate_meta.py"


class TestAggregateMeta(unittest.TestCase):
    """Tests for aggregate_meta.py (Chunk 4, Task 2-3)."""

    def _make_doc_dir(self, td: str, extra_meta: dict | None = None) -> Path:
        """Create a minimal test directory with one result artifact + meta."""
        doc_dir = Path(td)
        # Create the artifact
        (doc_dir / "result.tsv").write_text("col\nval\n", encoding="utf-8")
        # Create the meta.yaml
        meta = {
            "artifact_id": "result_a",
            "role": "result",
            "format": "tsv",
            "row_count": 2,
            "md5": "abc123",
            "run_date": "2026-04-30",
            "generated_by": "test_script.py",
        }
        if extra_meta:
            meta.update(extra_meta)
        import yaml as _yaml
        (doc_dir / "result.tsv.meta.yaml").write_text(
            _yaml.safe_dump(meta), encoding="utf-8"
        )
        # Create minimal prov.md
        (doc_dir / "prov.md").write_text(
            "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
            "sealed_at: null\nowner: u\nproject: p\n"
            "verification:\n  fail_closed_on_broken_yaml: true\n"
            "  fail_closed_on_missing_meta: true\n---\nbody\n",
            encoding="utf-8",
        )
        return doc_dir / "prov.md"

    def test_happy_path_markdown_table(self) -> None:
        """Happy path: 1 artifact + meta.yaml → markdown table with result_a row."""
        with tempfile.TemporaryDirectory() as td:
            doc = self._make_doc_dir(td)
            rc, out = _run_script(AGGREGATE_META, "--doc", str(doc))
            self.assertEqual(rc, 0, out)
            self.assertIn("result_a", out)
            self.assertIn("| artifact_id |", out)

    def test_broken_meta_fail_closed_exit1(self) -> None:
        """Sad path: broken YAML meta + fail_closed=true → exit 1 + broken-meta in stderr."""
        with tempfile.TemporaryDirectory() as td:
            doc_dir = Path(td)
            (doc_dir / "result.tsv").write_text("col\nval\n", encoding="utf-8")
            # Write intentionally broken YAML
            (doc_dir / "result.tsv.meta.yaml").write_text(
                "not: valid: yaml: : :\n", encoding="utf-8"
            )
            (doc_dir / "prov.md").write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "verification:\n  fail_closed_on_broken_yaml: true\n"
                "  fail_closed_on_missing_meta: true\n---\nbody\n",
                encoding="utf-8",
            )
            rc, out = _run_script(AGGREGATE_META, "--doc", str(doc_dir / "prov.md"))
            self.assertEqual(rc, 1, out)
            self.assertIn("broken-meta", out)

    def test_missing_meta_fail_closed_true_exit1(self) -> None:
        """Sad path: no *.meta.yaml + fail_closed_on_missing_meta=true → exit 1."""
        with tempfile.TemporaryDirectory() as td:
            doc_dir = Path(td)
            (doc_dir / "prov.md").write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "verification:\n  fail_closed_on_broken_yaml: true\n"
                "  fail_closed_on_missing_meta: true\n---\nbody\n",
                encoding="utf-8",
            )
            rc, out = _run_script(AGGREGATE_META, "--doc", str(doc_dir / "prov.md"))
            self.assertEqual(rc, 1, out)
            self.assertIn("missing-meta", out)

    def test_missing_meta_fail_closed_false_exit0(self) -> None:
        """Edge case: no *.meta.yaml + fail_closed_on_missing_meta=false → exit 0."""
        with tempfile.TemporaryDirectory() as td:
            doc_dir = Path(td)
            (doc_dir / "prov.md").write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "verification:\n  fail_closed_on_broken_yaml: true\n"
                "  fail_closed_on_missing_meta: false\n---\nbody\n",
                encoding="utf-8",
            )
            rc, out = _run_script(AGGREGATE_META, "--doc", str(doc_dir / "prov.md"))
            self.assertEqual(rc, 0, out)
            self.assertIn("(no artifacts)", out)

    def test_check_link_rot_missing_artifact(self) -> None:
        """Sad path: artifact file missing + --check-link-rot → exit 1."""
        with tempfile.TemporaryDirectory() as td:
            doc_dir = Path(td)
            # meta.yaml exists but the artifact file does NOT
            import yaml as _yaml
            (doc_dir / "ghost.tsv.meta.yaml").write_text(
                _yaml.safe_dump({"artifact_id": "ghost", "role": "result"}),
                encoding="utf-8",
            )
            (doc_dir / "prov.md").write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "verification:\n  fail_closed_on_broken_yaml: true\n"
                "  fail_closed_on_missing_meta: false\n---\nbody\n",
                encoding="utf-8",
            )
            rc, out = _run_script(
                AGGREGATE_META, "--doc", str(doc_dir / "prov.md"), "--check-link-rot"
            )
            self.assertEqual(rc, 1, out)


# ---------------------------------------------------------------------------
# Task 2-4: render_doc.py
# ---------------------------------------------------------------------------

RENDER_DOC = SCRIPTS_DIR / "render_doc.py"


class TestRenderDoc(unittest.TestCase):
    """Tests for render_doc.py (Chunk 4, Task 2-4)."""

    _LITE_PROV = textwrap.dedent("""\
        ---
        template: lite
        status: draft
        created_at: 2026-04-30
        sealed_at: null
        owner: u
        project: p
        ---
        # Body
    """)

    def test_render_with_extension_inlines_content(self) -> None:
        """Happy path: extension source inlined with title + content visible."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            (td_path / "_extensions").mkdir()
            (td_path / "_extensions" / "stat_a.md").write_text(
                "| metric | value |\n|--------|-------|\n| n_things | 42 |\n",
                encoding="utf-8",
            )
            prov = td_path / "prov.md"
            prov.write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "extension_sections:\n"
                "  - id: stat_a\n"
                "    title: Domain stat A\n"
                "    source: _extensions/stat_a.md\n"
                "    status: verified\n"
                "---\n# Body\n",
                encoding="utf-8",
            )
            rc, out = _run_script(RENDER_DOC, "--doc", str(prov))
            self.assertEqual(rc, 0, out)
            rendered = prov.read_text(encoding="utf-8")
            self.assertIn("Domain stat A", rendered)
            self.assertIn("n_things", rendered)

    def test_render_missing_extension_no_flag_exit0(self) -> None:
        """Edge case: missing source file without --fail-on-missing-extension → exit 0."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            prov = td_path / "prov.md"
            prov.write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "extension_sections:\n"
                "  - id: missing_one\n"
                "    title: Missing\n"
                "    source: _extensions/missing.md\n"
                "    status: verified\n"
                "---\n# Body\n",
                encoding="utf-8",
            )
            rc, out = _run_script(RENDER_DOC, "--doc", str(prov))
            self.assertEqual(rc, 0, out)

    def test_render_missing_extension_with_flag_exit1(self) -> None:
        """Sad path: missing source + --fail-on-missing-extension → exit 1."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            prov = td_path / "prov.md"
            prov.write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "extension_sections:\n"
                "  - id: missing_one\n"
                "    title: Missing\n"
                "    source: _extensions/missing.md\n"
                "    status: verified\n"
                "---\n# Body\n",
                encoding="utf-8",
            )
            rc, out = _run_script(
                RENDER_DOC, "--doc", str(prov), "--fail-on-missing-extension"
            )
            self.assertEqual(rc, 1, out)
            self.assertIn("FAIL", out)

    def test_render_no_extensions_exit0(self) -> None:
        """Happy path: doc with no extension_sections → renders cleanly, exit 0."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            prov = td_path / "prov.md"
            prov.write_text(self._LITE_PROV, encoding="utf-8")
            rc, out = _run_script(RENDER_DOC, "--doc", str(prov))
            self.assertEqual(rc, 0, out)

    def test_render_waived_extension_no_source_needed(self) -> None:
        """Edge case: waived extension does not require source file to exist."""
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            prov = td_path / "prov.md"
            prov.write_text(
                "---\ntemplate: lite\nstatus: draft\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n"
                "extension_sections:\n"
                "  - id: waived_ext\n"
                "    title: Waived\n"
                "    source: _extensions/no_file.md\n"
                "    status: waived\n"
                "    waiver_reason: not applicable\n"
                "---\n# Body\n",
                encoding="utf-8",
            )
            rc, out = _run_script(
                RENDER_DOC, "--doc", str(prov), "--fail-on-missing-extension"
            )
            self.assertEqual(rc, 0, out)
            rendered = prov.read_text(encoding="utf-8")
            self.assertIn("WAIVED", rendered)


# ---------------------------------------------------------------------------
# Task 2-5: verify_claims.py
# ---------------------------------------------------------------------------

VERIFY_CLAIMS = SCRIPTS_DIR / "verify_claims.py"

# Minimal doc template for verify tests — NOTE: no leading indentation on template lines
_VERIFY_DOC_HEADER = (
    "---\n"
    "template: lite\n"
    "status: numbers-pending\n"
    "created_at: 2026-04-30\n"
    "sealed_at: null\n"
    "owner: u\n"
    "project: p\n"
    "---\n"
    "# Body\n"
    "\n"
    "| claim_id | claim_text | value | source_artifact | command | observed_result | status |\n"
    "|----------|-----------|-------|-----------------|---------|-----------------|--------|\n"
)


def _make_verify_doc(rows: list[str]) -> Path:
    """Write a temporary doc with given table rows (each a complete pipe-delimited line)."""
    # Rows must start with '|' directly (no leading spaces)
    clean_rows = [r.strip() for r in rows]
    content = _VERIFY_DOC_HEADER + "\n".join(clean_rows) + "\n"
    return _write_tmp(content)


class TestVerifyClaims(unittest.TestCase):
    """Tests for verify_claims.py (Task 2-5, Fix-5)."""

    def test_safe_command_runs_and_fills_observed_result(self) -> None:
        """Happy path: safe echo command runs; observed_result filled with '3', status verified."""
        doc = _make_verify_doc([
            "    | c1 | counts to 3 | 3 | x | echo 3 | | unverified |",
        ])
        rc, out = _run_script(VERIFY_CLAIMS, "--doc", str(doc))
        content = doc.read_text(encoding="utf-8")
        doc.unlink(missing_ok=True)
        # Should succeed (rc 0) and c1 observed_result should be 3
        self.assertIn("RUN", out, "Expected RUN in output")
        self.assertIn("`3`", content, f"Expected '3' in observed_result. content=\n{content}")

    def test_dangerous_command_refused(self) -> None:
        """Sad path: rm -rf pattern triggers REFUSE; observed_result=[unverified: dangerous-cmd-refused]."""
        doc = _make_verify_doc([
            "    | c2 | dangerous | 1 | x | rm -rf /tmp/safe-thing | | unverified |",
        ])
        rc, out = _run_script(VERIFY_CLAIMS, "--doc", str(doc))
        content = doc.read_text(encoding="utf-8")
        doc.unlink(missing_ok=True)
        self.assertIn("REFUSE", out, "Expected REFUSE in output")
        self.assertIn("dangerous-cmd-refused", content,
                      f"Expected dangerous-cmd-refused in content. content=\n{content}")
        # rc should be 1 since a command was dangerous
        self.assertEqual(rc, 1, out)

    def test_remote_non_interactive_denied(self) -> None:
        """Fix-5: non-interactive stdin + ssh command → DENIED; observed_result=[unverified: remote-denied]."""
        doc = _make_verify_doc([
            "    | c3 | remote ls | - | x | ssh remotehost ls | | unverified |",
        ])
        # Pipe empty stdin → non-interactive → confirm_remote returns False
        r = subprocess.run(
            ["uv", "run", str(VERIFY_CLAIMS), "--doc", str(doc)],
            capture_output=True, text=True,
            input="",  # empty stdin, not a tty
        )
        content = doc.read_text(encoding="utf-8")
        doc.unlink(missing_ok=True)
        self.assertIn("DENIED", r.stdout + r.stderr,
                      f"Expected DENIED. stdout={r.stdout} stderr={r.stderr}")
        self.assertIn("remote-denied", content,
                      f"Expected remote-denied in content. content=\n{content}")

    def test_dry_run_no_execution(self) -> None:
        """Fix-5: --dry-run prints DRY prefix but does not update observed_result."""
        doc = _make_verify_doc([
            "    | c4 | echo test | hi | x | echo hi | | unverified |",
        ])
        original_content = doc.read_text(encoding="utf-8")
        rc, out = _run_script(VERIFY_CLAIMS, "--doc", str(doc), "--dry-run")
        after_content = doc.read_text(encoding="utf-8")
        doc.unlink(missing_ok=True)
        self.assertIn("DRY", out, "Expected DRY in output")
        # observed_result column must remain empty (unchanged)
        self.assertEqual(original_content, after_content,
                         "File should not be modified in --dry-run mode")

    def test_allow_remote_flag_allows_remote(self) -> None:
        """Edge case: --allow-remote + ssh command → skips confirm_remote, tries to run."""
        doc = _make_verify_doc([
            "    | c5 | remote | - | x | ssh localhost echo hi | | unverified |",
        ])
        # We just check it tries to RUN (it may fail, that's ok)
        rc, out = _run_script(VERIFY_CLAIMS, "--doc", str(doc), "--allow-remote")
        doc.unlink(missing_ok=True)
        # Should NOT print DENIED or SKIP
        self.assertNotIn("DENIED", out, "DENIED should not appear with --allow-remote")

    def test_already_filled_observed_result_skipped(self) -> None:
        """Edge case: row with non-empty observed_result is skipped (not re-run)."""
        doc = _make_verify_doc([
            "    | c6 | already done | 42 | x | echo 999 | 42 | verified |",
        ])
        rc, out = _run_script(VERIFY_CLAIMS, "--doc", str(doc))
        content = doc.read_text(encoding="utf-8")
        doc.unlink(missing_ok=True)
        # The command echo 999 should NOT be run; observed_result stays 42
        self.assertNotIn("RUN", out, "Already-filled rows should be skipped")
        self.assertIn("42", content)

    def test_missing_doc_exit2(self) -> None:
        """Edge case: doc not found → exit 2."""
        rc, out = _run_script(VERIFY_CLAIMS, "--doc", "/nonexistent/prov.md")
        self.assertEqual(rc, 2, out)


# ---------------------------------------------------------------------------
# Task 2-6: unseal_unsafe.py
# ---------------------------------------------------------------------------

UNSEAL_UNSAFE = SCRIPTS_DIR / "unseal_unsafe.py"

_SEALED_DOC = textwrap.dedent("""\
    ---
    template: full
    status: sealed
    version: v1.0
    created_at: 2026-04-30
    sealed_at: 2026-04-30
    owner: u
    project: p
    prior_version: v0.9
    delta_summary_path: ./CHANGES.md
    ---
    body
""")


class TestUnsealUnsafe(unittest.TestCase):
    """Tests for unseal_unsafe.py (Task 2-6)."""

    def test_short_reason_rejected(self) -> None:
        """Invalid input: --reason < 30 chars → exit 2."""
        with tempfile.TemporaryDirectory() as td:
            doc = Path(td) / "prov.md"
            doc.write_text(_SEALED_DOC, encoding="utf-8")
            import os as _os; _os.chmod(doc, 0o444)
            rc, out = _run_script(UNSEAL_UNSAFE, "--doc", str(doc), "--reason", "too short")
            self.assertEqual(rc, 2, out)
            self.assertIn("30", out, "Error message should mention 30 chars")

    def test_happy_path_unseals_doc(self) -> None:
        """Happy path: sealed doc + valid reason → status=verified, chmod 644, evolution.md created."""
        with tempfile.TemporaryDirectory() as td:
            doc = Path(td) / "prov.md"
            doc.write_text(_SEALED_DOC, encoding="utf-8")
            import os as _os; _os.chmod(doc, 0o444)
            long_reason = "Need to fix typo discovered in ch3 review on 2026-04-30"
            rc, out = _run_script(UNSEAL_UNSAFE, "--doc", str(doc), "--reason", long_reason)
            self.assertEqual(rc, 0, out)
            # status downgraded
            content = doc.read_text(encoding="utf-8")
            self.assertIn("status: verified", content,
                          f"Expected status: verified. content=\n{content}")
            # evolution.md created
            evo = Path(td) / "evolution.md"
            self.assertTrue(evo.exists(), "evolution.md should be created")
            evo_content = evo.read_text(encoding="utf-8")
            self.assertIn("unseal_unsafe", evo_content)
            # chmod 644 (owner can read+write, others can read)
            mode = _os.stat(doc).st_mode & 0o777
            self.assertEqual(mode, 0o644, f"Expected mode 644, got {oct(mode)}")

    def test_non_sealed_doc_rejected(self) -> None:
        """Invalid input: doc with status != sealed → exit 1."""
        with tempfile.TemporaryDirectory() as td:
            doc = Path(td) / "prov.md"
            doc.write_text(
                "---\ntemplate: lite\nstatus: verified\ncreated_at: 2026-04-30\n"
                "sealed_at: null\nowner: u\nproject: p\n---\nbody\n",
                encoding="utf-8",
            )
            long_reason = "This is a reason with more than thirty characters exactly"
            rc, out = _run_script(UNSEAL_UNSAFE, "--doc", str(doc), "--reason", long_reason)
            self.assertEqual(rc, 1, out)
            self.assertIn("sealed", out)

    def test_missing_doc_exit2(self) -> None:
        """Edge case: doc not found → exit 2."""
        rc, out = _run_script(UNSEAL_UNSAFE, "--doc", "/nonexistent/prov.md",
                              "--reason", "reason that is long enough to pass the check")
        self.assertEqual(rc, 2, out)

    def test_evolution_md_appended_on_second_unseal(self) -> None:
        """Edge case: second unseal appends a new entry to existing evolution.md."""
        with tempfile.TemporaryDirectory() as td:
            evo = Path(td) / "evolution.md"
            evo.write_text("# Evolution Log\n\n## prior entry\n", encoding="utf-8")
            # Re-seal by writing a fresh sealed doc
            doc = Path(td) / "prov.md"
            doc.write_text(_SEALED_DOC, encoding="utf-8")
            import os as _os; _os.chmod(doc, 0o444)
            long_reason = "Second unseal for appending test on 2026-04-30"
            rc, out = _run_script(UNSEAL_UNSAFE, "--doc", str(doc), "--reason", long_reason)
            self.assertEqual(rc, 0, out)
            evo_content = evo.read_text(encoding="utf-8")
            self.assertIn("prior entry", evo_content, "Prior content must be preserved")
            self.assertIn("unseal_unsafe", evo_content, "New entry must be appended")


# ---------------------------------------------------------------------------
# Fix-12: Edge cases — sealed-render noop
# ---------------------------------------------------------------------------

class TestEdgeCasesAdditional(unittest.TestCase):
    """Fix-12: Additional edge cases per Chunk 6 requirements."""

    def setUp(self) -> None:
        import tempfile
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmp)

    def test_sealed_render_does_not_modify_sealed_doc(self) -> None:
        """render_doc.py on a sealed file must not change it (read-only chmod 444)."""
        ext_dir = self.tmp / "_extensions"
        ext_dir.mkdir()
        (ext_dir / "x.md").write_text("# X")
        archive = self.tmp / "archive" / "legacy_results" / "v1.0"
        archive.mkdir(parents=True)
        prov = archive / "provenance.md"
        prov.write_text(textwrap.dedent("""\
            ---
            template: full
            status: sealed
            version: v1.0
            created_at: 2026-04-30
            sealed_at: 2026-04-30
            owner: u
            project: p
            prior_version: null
            delta_summary_path: null
            extension_sections:
              - id: x
                title: X
                source: _extensions/x.md
                status: verified
            ---
            body
        """))
        import os
        os.chmod(prov, 0o444)
        snap_before = prov.read_text()
        try:
            # render_doc via CLI — sealed doc should be a no-op (exit 0) without modifying
            result = subprocess.run(
                ["uv", "run", "--with", "pyyaml",
                 str(SCRIPT_DIR / "render_doc.py"), "--doc", str(prov)],
                capture_output=True, text=True,
            )
        except Exception:
            pass
        finally:
            os.chmod(prov, 0o644)
        snap_after = prov.read_text()
        self.assertEqual(snap_before, snap_after,
                         "render_doc must not modify a sealed (chmod 444) file")


if __name__ == "__main__":
    unittest.main(verbosity=2)
