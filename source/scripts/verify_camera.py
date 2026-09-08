#!/usr/bin/env python3
"""Verify classic-camera semantics and byte-level isolation on supplied ROMs."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from ndspy.rom import NintendoDSRom

TABLE = 0xF6BE0
COUNT = 540
STRIDE = 24
MASK = 0x3F000
PLUS_SHA256 = "78b198fbad961970ef8563587fb2278ee957e6297589a847dbe78f73d12cc0c1"
USA_SHA256 = "65f02a56842b75aa92d775d56d657a56fe3fa993550b04dc20704ab82d760105"


def verify(original, reference, candidate, wait_fix=False):
    assert hashlib.sha256(original).hexdigest() == PLUS_SHA256, "Wrong Plus input"
    assert hashlib.sha256(reference).hexdigest() == USA_SHA256, "Wrong USA reference"
    assert len(candidate) == len(original), "File size changed"
    r0, ru, rc = (NintendoDSRom(b) for b in (original, reference, candidate))
    a0, au, ac = (r.loadArm9().sections[0].data for r in (r0, ru, rc))
    assert len(a0) == len(au) == len(ac) == 1120352
    arm9_offset = struct.unpack_from("<I", original, 0x20)[0]
    assert original[arm9_offset:arm9_offset + len(a0)] == a0
    allowed = set()
    expected_map_changes = []
    bad_camera = []
    for i in range(COUNT):
        off = TABLE + STRIDE * i + 20
        before, wanted, actual = (struct.unpack_from("<I", a, off)[0] for a in (a0, au, ac))
        if (actual ^ wanted) & MASK:
            bad_camera.append(i)
        assert (before ^ actual) & ~MASK == 0, f"Other map fields changed: {i}"
        if (before ^ wanted) & MASK:
            expected_map_changes.append(i)
        allowed.update(arm9_offset + off + j for j in (1, 2))
    assert not bad_camera, f"Camera mismatch in {len(bad_camera)} maps: {bad_camera[:12]}"
    changed = [i for i, (a, b) in enumerate(zip(original, candidate)) if a != b]
    if wait_fix:
        for address in (0x020D3FA8, 0x020DE16C):
            off = arm9_offset + address - 0x02000000
            assert struct.unpack_from("<I", candidate, off)[0] == 0x1AFFFFFC, "Hardware wait not restored"
            allowed.update(range(off, off + 4))
    assert changed and set(changed) <= allowed, "Changes outside permitted fields"
    assert len(expected_map_changes) == 527
    assert candidate[:512] == original[:512], "Cheat game ID changed"
    assert r0.arm7 == rc.arm7 and r0.arm9OverlayTable == rc.arm9OverlayTable
    assert r0.files == rc.files, "NitroFS or overlay data changed"
    assert [r0.filenames.filenameOf(i) for i in range(len(r0.files))] == [rc.filenames.filenameOf(i) for i in range(len(rc.files))], "NitroFS names changed"
    return {"status": "PASS", "map_count": COUNT, "changed_maps": len(expected_map_changes),
            "changed_bytes": len(changed), "size": len(candidate),
            "sha256": hashlib.sha256(candidate).hexdigest(),
            "limits": "Static isolation and intended camera fields; not a full playthrough or hardware benchmark"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("original", type=Path)
    p.add_argument("reference", type=Path)
    p.add_argument("candidate", type=Path)
    p.add_argument("--wait-fix", action="store_true")
    args = p.parse_args()
    print(json.dumps(verify(args.original.read_bytes(), args.reference.read_bytes(), args.candidate.read_bytes(), args.wait_fix), indent=2))
