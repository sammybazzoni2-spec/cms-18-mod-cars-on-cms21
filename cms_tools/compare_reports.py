"""Compare two reports produced by inspect_bundle.py (e.g. CMS 2018 car vs CMS 2021 car).

Usage:
    python -m cms_tools.compare_reports cms18_report.json cms21_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        sys.exit(f"Report not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _merge(report: dict[str, Any]) -> dict[str, Any]:
    """Collapse all files in a report into one view."""
    merged: dict[str, Any] = {
        "versions": set(),
        "types": {},
        "meshes": set(),
        "textures": set(),
        "scripts": {},
    }
    for f in report.get("files", []):
        if "error" in f:
            continue
        merged["versions"].update(f.get("unity_versions", []))
        for k, v in f.get("object_type_counts", {}).items():
            merged["types"][k] = merged["types"].get(k, 0) + v
        merged["meshes"].update(m["name"] for m in f.get("meshes", []))
        merged["textures"].update(t["name"] for t in f.get("textures", []))
        for b in f.get("behaviours", []):
            if b.get("script") and b.get("fields"):
                merged["scripts"].setdefault(b["script"], set()).update(b["fields"])
    return merged


def compare(a: dict[str, Any], b: dict[str, Any], label_a: str, label_b: str) -> str:
    A, B = _merge(a), _merge(b)
    out: list[str] = []

    out.append("Unity versions")
    out.append(f"  {label_a}: {', '.join(sorted(A['versions'])) or 'unknown'}")
    out.append(f"  {label_b}: {', '.join(sorted(B['versions'])) or 'unknown'}")

    out.append("\nObject types (count in A -> count in B)")
    for t in sorted(set(A["types"]) | set(B["types"])):
        ca, cb = A["types"].get(t, 0), B["types"].get(t, 0)
        flag = "" if ca and cb else "   <-- only in one"
        out.append(f"  {t:<22} {ca:>5} -> {cb:<5}{flag}")

    out.append("\nMonoBehaviour scripts / data fields")
    shared = sorted(set(A["scripts"]) & set(B["scripts"]))
    for s in shared:
        only_a = sorted(A["scripts"][s] - B["scripts"][s])
        only_b = sorted(B["scripts"][s] - A["scripts"][s])
        if only_a or only_b:
            out.append(f"  {s}")
            if only_a:
                out.append(f"    only in {label_a}: {', '.join(only_a)}")
            if only_b:
                out.append(f"    only in {label_b}: {', '.join(only_b)}")
    if not shared:
        out.append("  no scripts in common (or none had readable type trees)")
    for s in sorted(set(A["scripts"]) - set(B["scripts"])):
        out.append(f"  only in {label_a}: {s}")
    for s in sorted(set(B["scripts"]) - set(A["scripts"])):
        out.append(f"  only in {label_b}: {s}")

    out.append("\nMesh and texture names")
    out.append(f"  meshes only in {label_a}: {len(A['meshes'] - B['meshes'])}")
    out.append(f"  meshes only in {label_b}: {len(B['meshes'] - A['meshes'])}")
    out.append(f"  textures only in {label_a}: {len(A['textures'] - B['textures'])}")
    out.append(f"  textures only in {label_b}: {len(B['textures'] - A['textures'])}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("report_a", type=Path, help="e.g. CMS 2018 car report")
    parser.add_argument("report_b", type=Path, help="e.g. CMS 2021 car report")
    args = parser.parse_args(argv)
    print(compare(_load(args.report_a), _load(args.report_b), args.report_a.stem, args.report_b.stem))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
