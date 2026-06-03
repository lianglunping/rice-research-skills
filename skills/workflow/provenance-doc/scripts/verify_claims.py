# Plan Section: Chunk 5 — Phase 2c, Task 2-5 (Verify Claims)
# Plan Version: 2026-04-30-provenance-doc-plan.md
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Run verification commands listed in §5 論断验证册 and fill observed_result.

Spec §6.5 + §11.

Usage:
    verify_claims.py --doc <provenance.md>
                     [--dry-run]
                     [--allow-remote]
                     [--timeout 300]

Behaviour:
    - Reads §5 table rows
    - For each row with non-empty `command` and empty `observed_result`:
        - If --dry-run: print command, do NOT execute
        - If command contains 'ssh '/'scp '/'rsync ' and not --allow-remote:
            prompt user via stdin [y/N]; non-interactive default-deny
        - Else: subprocess.run with timeout
    - Updates §5 table in place

Exit codes:
    0 - success (all requested commands ran or were skipped)
    1 - some command failed or was refused
    2 - misuse
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import parse_doc, parse_claim_rows, write_doc  # type: ignore

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r">\s*/dev/",
    r"\bmkfs\b",
    r"\bdd\s+if=",
    r":\s*\(\)\s*\{",  # fork bomb
]
REMOTE_PATTERNS = [r"\bssh\s+", r"\bscp\s+", r"\brsync\s+", r"mcp__ssh-session__"]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def is_dangerous(cmd: str) -> bool:
    """Return True if cmd matches any dangerous pattern.

    Args:
        cmd: Shell command string to check.

    Returns:
        True when at least one dangerous pattern matches.
    """
    return any(re.search(p, cmd) for p in DANGEROUS_PATTERNS)


def is_remote(cmd: str) -> bool:
    """Return True if cmd is a remote command (ssh/scp/rsync).

    Args:
        cmd: Shell command string to check.

    Returns:
        True when at least one remote pattern matches.
    """
    return any(re.search(p, cmd) for p in REMOTE_PATTERNS)


def confirm_remote(cmd: str) -> bool:
    """Ask user via stdin [y/N]. Default=N. Non-interactive (no TTY) → False.

    Args:
        cmd: The remote command to confirm.

    Returns:
        True only if user explicitly types 'y'.
    """
    if not sys.stdin.isatty():
        return False  # non-interactive: default deny
    print(f"\n[REMOTE COMMAND]\n  {cmd}\nProceed? [y/N]: ", end="", flush=True)
    try:
        ans = input().strip().lower()
    except EOFError:
        return False
    return ans == "y"


def run_command(cmd: str, timeout: int) -> tuple[str, str]:
    """Execute cmd in a subprocess and return (observed_result, status).

    Args:
        cmd: Shell command to execute.
        timeout: Maximum seconds to wait.

    Returns:
        Tuple of (observed_result_string, status_string).
        status is 'verified' on rc=0, 'unverified' otherwise.
    """
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out_lines = (r.stdout or "").strip().splitlines()
        first_line = out_lines[0] if out_lines else ""
        if r.returncode != 0:
            stderr_snippet = (r.stderr or "").strip()[:80]
            return f"[error rc={r.returncode}: {stderr_snippet}]", "unverified"
        return first_line[:120], "verified"
    except subprocess.TimeoutExpired:
        return "[unverified: timeout]", "unverified"
    except Exception as exc:
        return f"[unverified: exception {exc.__class__.__name__}]", "unverified"


def update_table_in_body(body: str, updates: list[tuple[str, str, str]]) -> str:
    """Update observed_result + status in §5 claim table only.

    Only modifies the table that starts with a `claim_id` header row.
    Other tables in the document are left intact.

    Args:
        body: Full document body text.
        updates: List of (claim_id, observed_result, status) tuples.

    Returns:
        Updated body text.
    """
    updates_dict = {cid: (obs, st) for cid, obs, st in updates}
    lines = body.splitlines()
    in_claim_table = False
    headers: list[str] = []
    out: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Detect start of claim table (must have claim_id header)
        if not in_claim_table and re.search(r"^\|\s*claim_id\s*\|", line, re.IGNORECASE):
            headers = [c.strip() for c in stripped.strip("|").split("|")]
            in_claim_table = True
            out.append(line)
            continue

        if in_claim_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # Separator row (e.g. |---|---|)
            if all(set(c) <= set("-: ") for c in cells):
                out.append(line)
                continue
            # Malformed row (wrong column count)
            if len(cells) != len(headers):
                out.append(line)
                continue
            row = dict(zip(headers, cells))
            cid = row.get("claim_id", "").strip("`").strip()
            if cid in updates_dict:
                obs, st = updates_dict[cid]
                idx_obs = headers.index("observed_result") if "observed_result" in headers else None
                idx_st = headers.index("status") if "status" in headers else None
                if idx_obs is not None:
                    cells[idx_obs] = f"`{obs}`"
                if idx_st is not None:
                    cells[idx_st] = st
                out.append("| " + " | ".join(cells) + " |")
                continue
            out.append(line)
            continue

        # End of claim table block
        if in_claim_table and not stripped.startswith("|"):
            in_claim_table = False

        out.append(line)

    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    """Entry point for verify_claims.py.

    Returns:
        0 on success, 1 if any command failed/refused, 2 on misuse.
    """
    parser = argparse.ArgumentParser(
        description="Run §5 verification commands and fill observed_result."
    )
    parser.add_argument("--doc", type=Path, required=True,
                        help="Path to provenance.md")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without executing")
    parser.add_argument("--allow-remote", action="store_true",
                        help="Skip stdin confirmation for remote commands")
    parser.add_argument("--timeout", type=int, default=None,
                        help="Override remote_command_timeout_sec from front-matter")
    args = parser.parse_args()

    if not args.doc.is_file():
        print(f"error: doc not found: {args.doc}", file=sys.stderr)
        return 2

    doc = parse_doc(args.doc)
    verification_cfg = doc.front_matter.get("verification") or {}
    timeout = args.timeout or verification_cfg.get("remote_command_timeout_sec", 300)

    rows = parse_claim_rows(doc.body)
    updates: list[tuple[str, str, str]] = []
    any_fail = False

    for row in rows:
        cid = row.get("claim_id", "").strip()
        cmd = row.get("command", "").strip()
        obs = row.get("observed_result", "").strip()

        # Skip rows with no claim_id, no command, or already-filled observed_result
        if not cid or not cmd or obs:
            continue

        # Block dangerous commands unconditionally
        if is_dangerous(cmd):
            print(f"REFUSE {cid}: dangerous pattern in command", file=sys.stderr)
            updates.append((cid, "[unverified: dangerous-cmd-refused]", "unverified"))
            any_fail = True
            continue

        # Handle remote commands: prompt unless --allow-remote
        if is_remote(cmd) and not args.allow_remote:
            if not confirm_remote(cmd):
                print(f"DENIED {cid}: remote command rejected", file=sys.stderr)
                updates.append((cid, "[unverified: remote-denied]", "unverified"))
                any_fail = True
                continue
            # If user confirmed, fall through to execution

        # Dry-run: print and skip
        if args.dry_run:
            print(f"DRY    {cid}: {cmd}")
            continue

        # Execute command
        print(f"RUN    {cid}: {cmd[:80]}")
        observed, status = run_command(cmd, timeout)
        updates.append((cid, observed, status))
        if status != "verified":
            any_fail = True

    # Write updates back to doc (only if not dry-run and there are updates)
    if not args.dry_run and updates:
        doc.body = update_table_in_body(doc.body, updates)
        write_doc(doc)
        print(f"OK: updated {len(updates)} claim row(s) in {args.doc}")

    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
