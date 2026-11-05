#!/usr/bin/env python3
"""Apply one staged manifest after source and target CAS checks.

Replacements are individually atomic but not a cross-file filesystem transaction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import time
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inside(root: Path, item: Path) -> bool:
    try:
        item.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_manifest(bundle: Path, manifest: Path, expected_sha256: str = "") -> tuple[list[dict[str, str]], str]:
    """Read and validate a staged manifest without changing any target."""
    raw = manifest.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if expected_sha256 and actual != expected_sha256:
        raise ValueError("staged manifest hash does not match current staged manifest")
    try:
        files = json.loads(raw).get("files", [])
    except Exception as exc:
        raise ValueError(f"invalid manifest: {exc}") from exc
    if not isinstance(files, list) or not files:
        raise ValueError("empty manifest")
    seen: set[Path] = set()
    validated: list[dict[str, str]] = []
    for item in files:
        if not isinstance(item, dict) or set(item) != {"source", "target", "pre_sha256", "source_sha256"}:
            raise ValueError("manifest entry schema")
        if any(not isinstance(item[key], str) or not item[key] for key in item):
            raise ValueError("manifest entry has empty field")
        if any(len(item[key]) != 64 or any(char not in "0123456789abcdef" for char in item[key]) for key in ("pre_sha256", "source_sha256")):
            raise ValueError("invalid manifest hashes")
        source = (bundle / item["source"]).resolve()
        declared_target = Path(item["target"])
        if not declared_target.is_absolute():
            raise ValueError(f"target must be absolute: {declared_target}")
        target = declared_target.resolve()
        if target in seen or not inside(bundle, source) or not source.is_file():
            raise ValueError(f"invalid manifest path: {target}")
        seen.add(target)
        validated.append({"source": str(source), "target": str(target), "pre_sha256": item["pre_sha256"], "source_sha256": item["source_sha256"]})
    return validated, actual


def apply_staged_manifest(bundle: Path, manifest: Path, expected_sha256: str = "") -> None:
    """Apply a manifest with source/target CAS checks; caller owns transaction lock."""
    manifest = manifest.resolve()
    files, initial_manifest_sha = load_manifest(bundle.resolve(), manifest, expected_sha256)
    prepared: list[tuple[Path, Path, Path, str, str]] = []
    try:
        for item in files:
            source, target = Path(item["source"]), Path(item["target"])
            if not target.is_file() or sha(source) != item["source_sha256"] or sha(target) != item["pre_sha256"]:
                raise ValueError(f"manifest CAS failed: {target}")
            fd, raw_temp = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
            os.close(fd)
            temp = Path(raw_temp)
            shutil.copyfile(source, temp)
            if sha(temp) != item["source_sha256"]:
                raise ValueError(f"prepared copy drifted: {target}")
            prepared.append((source, target, temp, item["pre_sha256"], item["source_sha256"]))
        delay = os.environ.get("STAGED_BUNDLE_TEST_DELAY")
        if delay:
            time.sleep(float(delay))
        if sha(manifest) != initial_manifest_sha:
            raise ValueError("staged manifest changed before replace")
        for source, target, temp, pre_sha, source_sha in prepared:
            if sha(source) != source_sha or sha(target) != pre_sha or sha(temp) != source_sha:
                raise ValueError(f"CAS changed before replace: {target}")
        for _, target, temp, _, _ in prepared:
            os.replace(temp, target)
    except Exception:
        for _, _, temp, _, _ in prepared:
            if temp.exists():
                temp.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()
    try:
        apply_staged_manifest(Path(args.bundle), Path(args.manifest))
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    print("PASS\tAPPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
