"""Compare the sections and keys of two CMS car config.txt files.

It reports which sections and keys exist in one file but not the other. It does
not compare values, because two different cars always differ there. Numbered
groups such as [parts0], [parts1], ... are treated as one group ("parts#").

Usage:
    python -m cms_tools.diff_configs CMS18_config.txt CMS21_config.txt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_config(path: Path) -> dict[str, dict[str, str]]:
    """Parse an INI-style CMS config into {section: {key: value}}."""
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
        elif "=" in line and current is not None:
            key, value = line.split("=", 1)
            sections[current][key.strip()] = value.strip()
    return sections


def group_name(section: str) -> str:
    """[parts12] -> parts#, [carLight1] -> carLight#. Leading numbers (0_main) are kept."""
    return re.sub(r"(?<=[A-Za-z])\d+$", "#", section)


def grouped_keys(sections: dict[str, dict[str, str]]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for name, items in sections.items():
        out.setdefault(group_name(name), set()).update(items)
    return out


def diff(a: dict[str, dict[str, str]], b: dict[str, dict[str, str]], la: str, lb: str) -> str:
    A, B = grouped_keys(a), grouped_keys(b)
    lines: list[str] = []

    only_a, only_b = sorted(set(A) - set(B)), sorted(set(B) - set(A))
    lines.append(f"Sections only in {la}: {', '.join(only_a) or '(none)'}")
    lines.append(f"Sections only in {lb}: {', '.join(only_b) or '(none)'}")

    for sec in sorted(set(A) & set(B)):
        ka, kb = A[sec] - B[sec], B[sec] - A[sec]
        if ka or kb:
            lines.append(f"\n[{sec}]")
            if ka:
                lines.append(f"  only in {la}: {', '.join(sorted(ka))}")
            if kb:
                lines.append(f"  only in {lb}: {', '.join(sorted(kb))}")

    for sec in only_b:
        lines.append(f"\n[{sec}] keys in {lb}: {', '.join(sorted(B[sec]))}")
    for sec in only_a:
        lines.append(f"\n[{sec}] keys in {la}: {', '.join(sorted(A[sec]))}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("config_a", type=Path, help="e.g. a CMS 2018 car's config.txt")
    parser.add_argument("config_b", type=Path, help="e.g. a CMS 2021 car's config.txt")
    args = parser.parse_args(argv)

    for p in (args.config_a, args.config_b):
        if not p.is_file():
            sys.exit(f"Not a file: {p}")
    print(diff(parse_config(args.config_a), parse_config(args.config_b), "A", "B"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
