#!/usr/bin/env python3
"""Stamp PNG physical-resolution metadata without changing decoded pixels."""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from PIL import Image


def stamp(path: Path, dpi: int) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    with Image.open(path) as image:
        image.load()
        mode = image.mode
        size = image.size
        pixels = image.tobytes()
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".png", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            image.save(temporary, format="PNG", dpi=(dpi, dpi))
            with Image.open(temporary) as checked:
                checked.load()
                if checked.mode != mode or checked.size != size or checked.tobytes() != pixels:
                    raise ValueError(f"decoded pixels changed while stamping {path}")
                if round(checked.info.get("dpi", (0, 0))[0]) != dpi:
                    raise ValueError(f"DPI metadata was not written for {path}")
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Write PNG DPI metadata and verify decoded-pixel invariance.")
    parser.add_argument("--dpi", type=int, required=True)
    parser.add_argument("png", nargs="+")
    args = parser.parse_args()
    if args.dpi <= 0:
        raise SystemExit("--dpi must be positive")
    for item in args.png:
        stamp(Path(item), args.dpi)


if __name__ == "__main__":
    main()
