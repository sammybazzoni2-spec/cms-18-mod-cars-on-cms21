"""Peek inside a Unity bundle (.cms file) with only the standard library.

It decompresses the bundle's LZ4 / LZ4HC data blocks in pure Python, lists the
files stored inside, finds the Unity version recorded in the serialized data,
and scans for shader names. This does not need UnityPy and never leaves your
machine, so it is suitable for game files you should not upload.

It is a quick look, not a full parser: shader names come from a text scan of
the decompressed bytes, so treat counts as rough. Bundles using LZMA
compression are not supported.

Usage:
    python -m cms_tools.bundle_peek FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path
from typing import Any

SHADER_PATTERNS = [
    rb"HDRP/[A-Za-z0-9_ /]{2,40}",
    rb"Universal Render Pipeline/[A-Za-z0-9_ /]{2,40}",
    rb"Shader Graphs/[A-Za-z0-9_ /]{2,40}",
    rb"Legacy Shaders/[A-Za-z0-9_ /]{2,40}",
    rb"Hidden/[A-Za-z0-9_ /.\-]{2,60}",
    rb"Custom/[A-Za-z0-9_ /]{2,40}",
    rb"(?<![A-Za-z0-9_/])Standard(?: \((?:Specular setup|Roughness setup)\))?(?![A-Za-z0-9_])",
]
VERSION_RE = re.compile(rb"\d{4}\.\d+\.\d+[abfp]\d+")


def lz4_block_decompress(src: bytes) -> bytes:
    """Decompress one raw LZ4 block."""
    dst = bytearray()
    i, n = 0, len(src)
    while i < n:
        token = src[i]
        i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        dst += src[i : i + lit]
        i += lit
        if i >= n:
            break
        offset = src[i] | (src[i + 1] << 8)
        i += 2
        mlen = token & 15
        if mlen == 15:
            while True:
                b = src[i]
                i += 1
                mlen += b
                if b != 255:
                    break
        mlen += 4
        start = len(dst) - offset
        if offset >= mlen:
            dst += dst[start : start + mlen]
        else:
            chunk = bytes(dst[start:])
            dst += (chunk * (mlen // offset + 1))[:mlen]
    return bytes(dst)


def _decompress(data: bytes, mode: int, label: str) -> bytes:
    if mode == 0:
        return data
    if mode in (2, 3):
        return lz4_block_decompress(data)
    raise ValueError(f"{label}: unsupported compression type {mode} (only none, LZ4 and LZ4HC)")


def _cstr(data: bytes, pos: int) -> tuple[str, int]:
    end = data.index(b"\x00", pos)
    return data[pos:end].decode("ascii", "replace"), end + 1


def peek(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    signature, pos = _cstr(data, 0)
    (version,) = struct.unpack_from(">I", data, pos)
    pos += 4
    _player, pos = _cstr(data, pos)
    revision, pos = _cstr(data, pos)
    _total, comp_info, uncomp_info, flags = struct.unpack_from(">QIII", data, pos)
    pos += 20
    if version >= 7:
        pos = (pos + 15) & ~15

    if flags & 0x80:
        info_raw = data[len(data) - comp_info :]
    else:
        info_raw = data[pos : pos + comp_info]
        pos += comp_info
    if flags & 0x200:
        pos = (pos + 15) & ~15

    info = _decompress(info_raw, flags & 0x3F, "block info")
    if len(info) != uncomp_info:
        raise ValueError(f"block info size mismatch: got {len(info)}, expected {uncomp_info}")

    p = 16  # skip hash
    (block_count,) = struct.unpack_from(">i", info, p)
    p += 4
    blocks = []
    for _ in range(block_count):
        usize, csize, bflags = struct.unpack_from(">IIH", info, p)
        p += 10
        blocks.append((usize, csize, bflags))
    (node_count,) = struct.unpack_from(">i", info, p)
    p += 4
    nodes = []
    for _ in range(node_count):
        offset, size, nflags = struct.unpack_from(">qqI", info, p)
        p += 20
        name, p = _cstr(info, p)
        nodes.append({"path": name, "offset": offset, "size": size, "flags": nflags})

    out = bytearray()
    for usize, csize, bflags in blocks:
        chunk = _decompress(data[pos : pos + csize], bflags & 0x3F, "data block")
        if len(chunk) != usize:
            raise ValueError(f"data block size mismatch: got {len(chunk)}, expected {usize}")
        out += chunk
        pos += csize
    payload = bytes(out)

    versions: dict[str, str] = {}
    for node in nodes:
        head = payload[node["offset"] : node["offset"] + min(node["size"], 4096)]
        m = VERSION_RE.search(head)
        if m:
            versions[node["path"]] = m.group().decode()

    shaders: dict[str, int] = {}
    for pattern in SHADER_PATTERNS:
        for m in re.finditer(pattern, payload):
            name = m.group().decode("ascii", "replace").rstrip()
            shaders[name] = shaders.get(name, 0) + 1

    return {
        "file": path.name,
        "signature": signature,
        "format_version": version,
        "revision": revision,
        "blocks": block_count,
        "decompressed_bytes": len(payload),
        "nodes": [(n["path"], n["size"]) for n in nodes],
        "serialized_unity_versions": versions,
        "shader_names": dict(sorted(shaders.items(), key=lambda kv: -kv[1])),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)

    status = 0
    for path in args.files:
        if not path.is_file():
            print(f"{path}: not a file", file=sys.stderr)
            status = 1
            continue
        try:
            r = peek(path)
        except (ValueError, struct.error, IndexError) as exc:
            print(f"== {path.name}\n   could not read: {exc}")
            status = 1
            continue
        print(f"== {r['file']}")
        print(f"   signature {r['signature']!r}, format {r['format_version']}, revision {r['revision']}")
        print(f"   {r['blocks']} data blocks, {r['decompressed_bytes']} bytes decompressed")
        for name, size in r["nodes"]:
            print(f"   stored file: {name} ({size} bytes)")
        for name, ver in r["serialized_unity_versions"].items():
            print(f"   Unity version recorded in {name}: {ver}")
        shown = list(r["shader_names"].items())[:12]
        print("   shader-like names (count): " + (", ".join(f"{n} ({c})" for n, c in shown) or "none found"))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
