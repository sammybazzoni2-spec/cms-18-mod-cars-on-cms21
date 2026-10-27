"""Read the header of a Unity bundle (.cms file) using only the standard library.

This needs no UnityPy, so it works anywhere. It reports the signature, Unity
version, sizes and compression, and checks that the recorded total size matches
the file on disk. A mod bundle whose signature is not "UnityFS" is flagged,
because most Unity tools will refuse to open it as-is.

Usage:
    python -m cms_tools.bundle_header FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path
from typing import Any

EXPECTED_SIGNATURE = "UnityFS"
COMPRESSION = {0: "none", 1: "LZMA", 2: "LZ4", 3: "LZ4HC"}


def _cstr(data: bytes, pos: int) -> tuple[str, int]:
    end = data.index(b"\x00", pos)
    return data[pos:end].decode("ascii", "replace"), end + 1


def read_header(path: Path) -> dict[str, Any]:
    size_on_disk = path.stat().st_size
    with path.open("rb") as fh:
        data = fh.read(512)

    signature, pos = _cstr(data, 0)
    (format_version,) = struct.unpack_from(">I", data, pos)
    pos += 4
    player_version, pos = _cstr(data, pos)
    unity_revision, pos = _cstr(data, pos)
    total_size, comp_info, uncomp_info, flags = struct.unpack_from(">QIII", data, pos)

    return {
        "file": path.name,
        "signature": signature,
        "signature_ok": signature == EXPECTED_SIGNATURE,
        "format_version": format_version,
        "player_version": player_version,
        "unity_revision": unity_revision,
        "recorded_total_size": total_size,
        "size_on_disk": size_on_disk,
        "size_matches": total_size == size_on_disk,
        "block_info_compressed": comp_info,
        "block_info_uncompressed": uncomp_info,
        "flags": flags,
        "compression": COMPRESSION.get(flags & 0x3F, f"unknown({flags & 0x3F})"),
        "block_info_at_end": bool(flags & 0x80),
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
            h = read_header(path)
        except (ValueError, struct.error) as exc:
            print(f"{path.name}: could not parse header ({exc})")
            status = 1
            continue
        print(f"== {h['file']}")
        mark = "" if h["signature_ok"] else f"   <-- expected {EXPECTED_SIGNATURE!r}"
        print(f"   signature:        {h['signature']!r}{mark}")
        print(f"   format version:   {h['format_version']}")
        print(f"   player / revision: {h['player_version']} / {h['unity_revision']}")
        print(f"   total size:       recorded {h['recorded_total_size']}, on disk {h['size_on_disk']}"
              f" ({'match' if h['size_matches'] else 'MISMATCH'})")
        print(f"   block info:       {h['block_info_compressed']} -> {h['block_info_uncompressed']} bytes")
        print(f"   compression:      {h['compression']}  (flags=0x{h['flags']:x}, "
              f"block info at end: {h['block_info_at_end']})")
    return status


if __name__ == "__main__":
    raise SystemExit(main())
