"""Inspect a Unity asset bundle (or a folder of them) and write a JSON report.

The report lists the Unity version, object type counts, meshes, textures,
GameObjects, and the field names of MonoBehaviour / TextAsset data. Run it on a
CMS 2018 mod car and on a CMS 2021 car, then compare the two reports with
``compare_reports.py`` to see what a port would have to change.

Usage:
    python -m cms_tools.inspect_bundle PATH [-o report.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

MAX_LISTED = 500  # cap per category so reports stay readable


def _load_unitypy():
    try:
        import UnityPy  # type: ignore
    except ImportError:
        sys.exit("UnityPy is not installed. Run: pip install -r requirements.txt")
    return UnityPy


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:  # noqa: BLE001 - report generation must never crash on one odd object
        return default


def _typetree_keys(obj) -> list[str] | None:
    tree = _safe(obj.read_typetree)
    if isinstance(tree, dict):
        return sorted(tree.keys())
    return None


def _shader_name(shader) -> str | None:
    return _safe(lambda: shader.m_ParsedForm.m_Name) or _safe(lambda: shader.m_Name) or None


def inspect_file(path: Path) -> dict[str, Any]:
    UnityPy = _load_unitypy()
    env = UnityPy.load(str(path))

    versions = sorted(
        {str(v) for a in env.assets if (v := getattr(a, "unity_version", None))}
    )

    type_counts: Counter[str] = Counter()
    meshes: list[dict[str, Any]] = []
    textures: list[dict[str, Any]] = []
    game_objects: list[str] = []
    behaviours: list[dict[str, Any]] = []
    text_assets: list[dict[str, Any]] = []
    shaders: list[dict[str, Any]] = []
    materials: list[dict[str, Any]] = []
    errors = 0

    for obj in env.objects:
        type_name = obj.type.name
        type_counts[type_name] += 1
        try:
            if type_name == "Mesh":
                data = obj.read()
                meshes.append(
                    {
                        "name": data.m_Name,
                        "vertex_count": getattr(data, "m_VertexCount", None),
                        "submeshes": len(getattr(data, "m_SubMeshes", []) or []),
                    }
                )
            elif type_name == "Texture2D":
                data = obj.read()
                textures.append(
                    {
                        "name": data.m_Name,
                        "width": data.m_Width,
                        "height": data.m_Height,
                        "format": str(getattr(data, "m_TextureFormat", "")),
                    }
                )
            elif type_name == "GameObject":
                game_objects.append(obj.read().m_Name)
            elif type_name == "Shader":
                data = obj.read()
                shaders.append(
                    {
                        "name": _shader_name(data),
                        "platforms": _safe(lambda: [int(p) for p in data.platforms]),
                    }
                )
            elif type_name == "Material":
                data = obj.read()
                ref = getattr(data, "m_Shader", None)
                shader = _safe(lambda: ref.read())
                materials.append(
                    {
                        "name": data.m_Name,
                        "shader": _shader_name(shader) if shader is not None else None,
                        "shader_file_id": _safe(lambda: ref.file_id),
                        "shader_path_id": _safe(lambda: ref.path_id),
                    }
                )
            elif type_name == "MonoBehaviour":
                data = obj.read()
                script = _safe(lambda: data.m_Script.read().m_Name)
                behaviours.append(
                    {
                        "name": _safe(lambda: data.m_Name, ""),
                        "script": script,
                        "fields": _typetree_keys(obj),
                    }
                )
            elif type_name == "TextAsset":
                data = obj.read()
                raw = data.m_Script
                if isinstance(raw, bytes):
                    raw = raw.decode("utf-8", "replace")
                text_assets.append(
                    {
                        "name": data.m_Name,
                        "length": len(raw),
                        "head": raw[:200],
                    }
                )
        except Exception:  # noqa: BLE001
            errors += 1

    return {
        "file": path.name,
        "unity_versions": versions,
        "object_type_counts": dict(type_counts.most_common()),
        "meshes": sorted(meshes, key=lambda m: m["name"] or "")[:MAX_LISTED],
        "textures": sorted(textures, key=lambda t: t["name"] or "")[:MAX_LISTED],
        "game_objects": sorted(game_objects)[:MAX_LISTED],
        "behaviours": behaviours[:MAX_LISTED],
        "text_assets": text_assets[:MAX_LISTED],
        "shaders": shaders[:MAX_LISTED],
        "materials": sorted(materials, key=lambda m: m["name"] or "")[:MAX_LISTED],
        "read_errors": errors,
    }


def inspect_path(path: Path) -> dict[str, Any]:
    if path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
        if not files:
            sys.exit(f"No files found in {path}")
        reports = []
        for f in files:
            try:
                reports.append(inspect_file(f))
            except SystemExit:
                raise
            except Exception as exc:  # noqa: BLE001
                reports.append({"file": f.name, "error": f"{type(exc).__name__}: {exc}"})
        return {"source": str(path), "files": reports}
    if not path.exists():
        sys.exit(f"Path not found: {path}")
    return {"source": str(path), "files": [inspect_file(path)]}


def print_summary(report: dict[str, Any]) -> None:
    for f in report["files"]:
        print(f"== {f['file']}")
        if "error" in f:
            print(f"   could not read: {f['error']}")
            continue
        print(f"   Unity version(s): {', '.join(f['unity_versions']) or 'unknown'}")
        counts = ", ".join(f"{k}={v}" for k, v in list(f["object_type_counts"].items())[:8])
        print(f"   objects: {counts}")
        print(f"   meshes: {len(f['meshes'])}  textures: {len(f['textures'])}  "
              f"gameobjects: {len(f['game_objects'])}  behaviours: {len(f['behaviours'])}  "
              f"text assets: {len(f['text_assets'])}")
        if f["read_errors"]:
            print(f"   objects that could not be read: {f['read_errors']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("path", type=Path, help="bundle file or folder of bundles")
    parser.add_argument("-o", "--output", type=Path, help="write the full JSON report here")
    args = parser.parse_args(argv)

    report = inspect_path(args.path)
    print_summary(report)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"\nFull report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
