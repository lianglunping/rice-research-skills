#!/usr/bin/env python3
"""Check shipped source syntax and actual local Markdown links without running jobs."""
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]


def main():
    errors = []
    counts = {"python": 0, "shell": 0, "markdown": 0}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or any(part in {".git", "__pycache__", ".pytest_cache"} for part in path.relative_to(ROOT).parts):
            continue
        relative = path.relative_to(ROOT)
        if path.suffix == ".py":
            counts["python"] += 1
            try:
                compile(path.read_text(encoding="utf-8"), str(relative), "exec")
            except SyntaxError as exc:
                errors.append(f"{relative}: {exc}")
        elif path.suffix == ".sh":
            counts["shell"] += 1
            result = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            if result.returncode:
                errors.append(f"{relative}: {result.stderr.strip()}")
        elif path.suffix == ".md":
            counts["markdown"] += 1
            text = path.read_text(encoding="utf-8")
            text = re.sub(r"^(```|~~~).*?^\1.*?$", "", text, flags=re.M | re.S)
            text = re.sub(r"`[^`\n]+`", "", text)
            for link in re.findall(r"\[[^\]]*\]\(([^\s()]+)\)", text):
                if re.match(r"\w+:|/|#", link):
                    continue
                target = unquote(link.split("#", 1)[0])
                if target and not (path.parent / target).exists():
                    errors.append(f"{relative}: missing link target {target}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Source and link validation passed:", counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
