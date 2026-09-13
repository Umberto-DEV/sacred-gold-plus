#!/usr/bin/env python3
"""Build exact-byte DMA/SPI corrections and optional classic-camera variant.

Restores the matching vanilla USA hardware wait branches in two SDK routines.
Does not remove the frame limiter, replace artwork, or change game/save data.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from ndspy.rom import NintendoDSRom
from build_classic_camera import build as classic_camera
from verify_camera import PLUS_SHA256, USA_SHA256, verify

SITES = (0x020D3FA8, 0x020DE16C)


def correct_waits(plus, reference):
    if hashlib.sha256(plus).hexdigest() != PLUS_SHA256:
        raise ValueError("Plus 1.03 input checksum does not match")
    if hashlib.sha256(reference).hexdigest() != USA_SHA256:
        raise ValueError("HeartGold USA reference checksum does not match")
    arm9_offset = struct.unpack_from("<I", plus, 0x20)[0]
    ref_code = NintendoDSRom(reference).loadArm9().sections[0].data
    result = bytearray(plus)
    for site in SITES:
        off = arm9_offset + site - 0x02000000
        expected = struct.unpack_from("<I", ref_code, site - 0x02000000)[0]
        if struct.unpack_from("<I", plus, off)[0] != 0x0000A0E1 or expected != 0x1AFFFFFC:
            raise ValueError(f"Unexpected code at {site:08X}")
        struct.pack_into("<I", result, off, expected)
    return bytes(result)


def verify_wait_isolation(original, fixed):
    offset = struct.unpack_from("<I", original, 0x20)[0]
    allowed = {offset + s - 0x02000000 + i for s in SITES for i in range(4)}
    changes = {i for i, (a, b) in enumerate(zip(original, fixed)) if a != b}
    if len(original) != len(fixed) or changes != allowed:
        raise ValueError("Change set differs from the eight intended bytes")
    a, b = NintendoDSRom(original), NintendoDSRom(fixed)
    if original[:512] != fixed[:512] or a.arm7 != b.arm7 or a.files != b.files or a.arm9OverlayTable != b.arm9OverlayTable:
        raise ValueError("Changes affect header, ARM7, overlays or NitroFS")
    return {"status": "PASS", "changed_bytes": len(changes), "sha256": hashlib.sha256(fixed).hexdigest()}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plus", type=Path)
    p.add_argument("usa", type=Path)
    p.add_argument("output_dir", type=Path)
    args = p.parse_args()
    names = ["Pokemon - Sacred Gold Plus 1.03 - Fix.nds", "Pokemon - Sacred Gold Plus 1.03 - Fix Camera Classica.nds"]
    paths = [args.output_dir / name for name in names]
    if any(path.exists() for path in paths):
        p.error("Un output esiste già: nessun file viene sovrascritto.")
    plus, reference = args.plus.read_bytes(), args.usa.read_bytes()
    fixed = correct_waits(plus, reference)
    classic = bytearray(classic_camera(plus, reference))
    arm9_offset = struct.unpack_from("<I", plus, 0x20)[0]
    for site in SITES:
        struct.pack_into("<I", classic, arm9_offset + site - 0x02000000, 0x1AFFFFFC)
    variants = [fixed, bytes(classic)]
    evidence = [verify_wait_isolation(plus, fixed), verify(plus, reference, variants[1], wait_fix=True)]
    for path, data, result in zip(paths, variants, evidence):
        with path.open("xb") as f:
            f.write(data)
        result["file"] = str(path.resolve())
    print(json.dumps(evidence, indent=2))
