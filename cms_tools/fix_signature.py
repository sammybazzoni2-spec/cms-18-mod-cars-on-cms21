"""EXPERIMENTAL: write a copy of a CMS 2018 bundle with its signature changed to "UnityFS".

The CMS 2018 car bundle we examined starts with "SnityFS" instead of "UnityFS".
Everything else in its header is consistent, so this is the first thing to try
when testing whether CMS 2021 or UnityPy will open it. It has NOT been tested
in-game; it only changes those first seven bytes, in a copy. The original file
is never modified.

Usage:
    python -m cms_tools.fix_signature SOURCE.cms [OUTPUT.cms]

If OUTPUT is omitted, the copy is written next to the source as NAME_fixed.cms.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

OLD = b"SnityFS"
NEW = b"UnityFS"


def fix_signature(src: Path, dst: Path) -> None:
    if not src.is_file():
        sys.exit(f"Not a file: {src}")
    if dst.exists():
        sys.exit(f"Refusing to overwrite existing file: {dst}")
    if src.resolve() == dst.resolve():
        sys.exit("Output must be a different file from the source")
    with src.open("rb") as fh:
        head = fh.read(len(OLD))
    if head != OLD:
        sys.exit(f"{src.name} does not start with {OLD!r} (found {head!r}); nothing to fix")
    shutil.copyfile(src, dst)
    with dst.open("r+b") as fh:
        fh.write(NEW)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args(argv)

    dst = args.output or args.source.with_name(f"{args.source.stem}_fixed{args.source.suffix}")
    fix_signature(args.source, dst)
    print(f"Wrote {dst} (signature changed to {NEW.decode()}). Original left untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
