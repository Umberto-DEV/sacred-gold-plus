#!/usr/bin/env python3
"""Build bounded level-150 growth members without modifying a ROM."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from typing import Iterable, Sequence


ARCHIVE = "a/0/0/3"
CAP = 150
OLD_LEVELS = 101
NEW_LEVELS = 151
MEMBER_PINS = (
    "a33f5a043396120d4d42a807a240d87d144ca800c4b41cfdd848951c662909b6",
    "98781feea113d8d2e3e3f578d98d0a7f76bd0d008e79dd3942cb0ed490ebd7ee",
    "f3a821d7e60596706c3194766b2f9e87795d45450712432a8a8399b41c5ee1e7",
    "ce0722560af1b3f820abbc165685ca922edcf99c4e808815f17d05fc20956590",
    "d57547b2a55109f3b92e6c4214dc79c8f92688205f7460e7fe868c3c363012af",
    "bfd0fd42601e0c68de3ed54272ae341e207bea9a89c2d8c57efe1ac8a22799f5",
    "a33f5a043396120d4d42a807a240d87d144ca800c4b41cfdd848951c662909b6",
    "a33f5a043396120d4d42a807a240d87d144ca800c4b41cfdd848951c662909b6",
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validated_members(members: Iterable[bytes]) -> tuple[bytes, ...]:
    result = tuple(bytes(member) for member in members)
    if len(result) != len(MEMBER_PINS):
        raise ValueError("growth archive must contain exactly eight members")
    for index, (member, pin) in enumerate(zip(result, MEMBER_PINS)):
        if len(member) != OLD_LEVELS * 4:
            raise ValueError(f"growth member {index} is not 404 bytes")
        if _sha256(member) != pin:
            raise ValueError(f"growth member {index} does not match the pinned candidate")
        values = struct.unpack("<101I", member)
        if values[:2] != (0, 0) or any(values[level] <= values[level - 1]
                                        for level in range(2, OLD_LEVELS)):
            raise ValueError(f"growth member {index} is not strictly monotonic")
    return result


def extend_members(members: Iterable[bytes]) -> tuple[bytes, ...]:
    """Return eight 604-byte members; the original 404 bytes stay identical."""
    original = _validated_members(members)
    extended = []
    for member in original:
        values = list(struct.unpack("<101I", member))
        at_100 = values[100]
        for level in range(101, NEW_LEVELS):
            # Python integers make the required u64 intermediate explicit.
            values.append(at_100 * level * level * level // 1_000_000)
        if any(values[level] <= values[level - 1] for level in range(2, NEW_LEVELS)):
            raise ValueError("extended growth member is not strictly monotonic")
        packed = struct.pack("<151I", *values)
        if packed[:len(member)] != member:
            raise AssertionError("extension changed an original growth byte")
        extended.append(packed)
    return tuple(extended)


def level_from_exp(table: Sequence[int], experience: int, cap: int = CAP) -> int:
    """Invert a threshold table without ever reading beyond the selected cap."""
    values = tuple(table)
    if type(cap) is not int or not 1 <= cap <= CAP:
        raise ValueError("cap outside 1..150")
    if type(experience) is not int or not 0 <= experience <= 0xFFFFFFFF:
        raise ValueError("experience outside u32")
    if len(values) < cap + 1 or values[0] != 0:
        raise ValueError("incomplete threshold table")
    if cap >= 1 and values[1] != 0:
        raise ValueError("level-one threshold must be zero")
    if any(values[level] <= values[level - 1] for level in range(2, cap + 1)):
        raise ValueError("threshold table is not strictly monotonic")
    low, high = 1, cap
    while low < high:
        middle = (low + high + 1) // 2
        if values[middle] <= experience:
            low = middle
        else:
            high = middle - 1
    return low


def extract_growth_members(rom_path: Path) -> tuple[bytes, ...]:
    """Read the pinned growth archive from a supplied candidate, read-only."""
    from ndspy.narc import NARC
    from ndspy.rom import NintendoDSRom

    path = Path(rom_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    rom = NintendoDSRom.fromFile(str(path))
    return tuple(bytes(member) for member in NARC(rom.getFileByName(ARCHIVE)).files)


def write_bundle(members: Iterable[bytes], output: Path) -> dict:
    """Write only eight bounded members and their deterministic manifest."""
    original = _validated_members(members)
    extended = extend_members(original)
    destination = Path(output)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"output directory is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (before, after) in enumerate(zip(original, extended)):
        name = f"{index}.bin"
        (destination / name).write_bytes(after)
        values = struct.unpack("<151I", after)
        rows.append({
            "index": index,
            "file": name,
            "bytes": len(after),
            "input_sha256": _sha256(before),
            "output_sha256": _sha256(after),
            "exp_100": values[100],
            "exp_150": values[150],
        })
    manifest = {"schema": 1, "archive": ARCHIVE, "cap": CAP, "members": rows}
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="read-only candidate ROM")
    parser.add_argument("--out", required=True, type=Path, help="new or empty output directory")
    args = parser.parse_args(argv)
    write_bundle(extract_growth_members(args.rom), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
