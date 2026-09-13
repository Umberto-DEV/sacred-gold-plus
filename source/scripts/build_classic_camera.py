#!/usr/bin/env python3
"""Create an optional classic-camera copy of the exact supplied Plus 1.03 ROM.

Requires the user's own matching USA HeartGold ROM as camera reference.
No ROM data is downloaded; files are never overwritten.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom
from verify_camera import TABLE, COUNT, STRIDE, MASK, PLUS_SHA256, USA_SHA256, verify


def build(plus, reference):
    if hashlib.sha256(plus).hexdigest() != PLUS_SHA256:
        raise ValueError("La ROM Plus non corrisponde alla versione 1.03 verificata.")
    if hashlib.sha256(reference).hexdigest() != USA_SHA256:
        raise ValueError("Il riferimento deve essere HeartGold USA verificato, non la versione italiana.")
    vanilla = NintendoDSRom(reference).loadArm9().sections[0].data
    current = NintendoDSRom(plus).loadArm9().sections[0].data
    arm9_offset = struct.unpack_from("<I", plus, 0x20)[0]
    if plus[arm9_offset:arm9_offset + len(current)] != current:
        raise ValueError("Layout ARM9 non supportato: non applicare a un eseguibile compresso.")
    result = bytearray(plus)
    for map_id in range(COUNT):
        offset = TABLE + STRIDE * map_id + 20
        before = struct.unpack_from("<I", current, offset)[0]
        target = struct.unpack_from("<I", vanilla, offset)[0]
        value = (before & ~MASK) | (target & MASK)
        struct.pack_into("<I", result, arm9_offset + offset, value)
    return bytes(result)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("plus", type=Path)
    p.add_argument("usa", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    if args.output.exists():
        p.error("Il file di destinazione esiste già; scelgo di non sovrascriverlo.")
    original, reference = args.plus.read_bytes(), args.usa.read_bytes()
    result = build(original, reference)
    evidence = verify(original, reference, result)
    with args.output.open("xb") as f:
        f.write(result)
    print(json.dumps(evidence, indent=2))
