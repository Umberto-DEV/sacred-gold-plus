"""SG-01b Route 47 final-admin defeat recovery (isolated producer).

The current composed member 260 leaves the field locked when trainer 107
defeats the player: its conditional branch targets map-initialisation code at
0x6c4.  The four preceding partner losses all target the member's unique
``WhiteOut`` at 0x7a4.  This module performs the same-size retarget in memory;
it never opens or writes a ROM or save.
"""
from __future__ import annotations

import hashlib
import struct

import ndspy.narc

from sgp131 import gifts_scripts


SCRIPT_MEMBER = 260
COMMANDS_SHA256 = "fbfbf438104cfc3735c3144730ed711bb882fca370a8de680db5c1d39ffaca5a"
BEFORE_SHA256 = "bcc71c8ce50440b37fc253f04897ef30e765508162d999c057a7bbe6b7ad01b2"
AFTER_SHA256 = "b2570f3e37fd9f3dcbcb2b102f9c2fae2b1db2c1a41a54a755931cf2025cb4d7"
LOSS_BRANCH = 0x61C
DISPLACEMENT_START = 0x61F
BRANCH_END = 0x623
BROKEN_TARGET = 0x6C4
WHITEOUT_TARGET = 0x7A4
PARTNER_LOSS_BRANCHES = (0x217, 0x2F5, 0x43F, 0x545)
SCRIPT_ARCHIVE = "a/0/1/2"
ARCHIVE_BEFORE_SHA256 = "c4d17626516dc22d436fb823b0678b19707c2833d3c22cebcec4570bb419dcf8"
ARCHIVE_AFTER_SHA256 = "7ffe2ae30e8ce42e12fbfc0842c6cb6c1b743ed3692c14dbec249600b64ab813"
ARCHIVE_SIZE = 452480
ARCHIVE_MEMBER_COUNT = 965
ARCHIVE_CHANGED_OFFSETS = (0x3DF77, 0x3DF78)


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _targets(row):
    return [target for _operand, target, kind in row.rami if kind != "movement"]


def _repair_shape(raw, commands):
    _need(type(raw) is bytes and _sha256(raw) == BEFORE_SHA256,
          "Safari defeat member preimage differs")
    _need(getattr(commands, "metadata_sha256", None) == COMMANDS_SHA256,
          "Safari defeat command metadata differs")
    parsed = gifts_scripts.decode(raw, commands, SCRIPT_MEMBER)
    _need(not parsed.errori and parsed.riassembla()[0],
          "Safari defeat member does not decode and round-trip")
    rows = parsed.istruzioni
    _need(rows[LOSS_BRANCH].nome == "GoToIf"
          and rows[LOSS_BRANCH].args == [1, BROKEN_TARGET - BRANCH_END]
          and _targets(rows[LOSS_BRANCH]) == [BROKEN_TARGET],
          "Safari defeat broken branch differs")
    whiteouts = sorted(row.off for row in rows.values()
                       if row.nome == "WhiteOut")
    _need(whiteouts == [WHITEOUT_TARGET],
          "Safari defeat unique WhiteOut differs")
    _need(all(_targets(rows[offset]) == [WHITEOUT_TARGET]
              for offset in PARTNER_LOSS_BRANCHES),
          "Safari defeat partner-loss controls differ")
    return parsed


def _reachable(parsed, start):
    pending = [start]
    seen = set()
    while pending:
        pc = pending.pop()
        if pc in seen:
            continue
        _need(pc in parsed.istruzioni,
              f"Safari defeat CFG edge outside instructions: {pc:#x}")
        seen.add(pc)
        row = parsed.istruzioni[pc]
        if row.nome in ("End", "Return", "WhiteOut"):
            continue
        pending.extend(target for _operand, target, kind in row.rami
                       if kind != "movement")
        if row.nome != "GoTo":
            pending.append(row.fine)
    return seen


def repair_member(before, commands):
    """Retarget the one exact loss edge; return bytes without external writes."""
    _repair_shape(before, commands)
    after = bytearray(before)
    struct.pack_into("<i", after, DISPLACEMENT_START,
                     WHITEOUT_TARGET - BRANCH_END)
    result = bytes(after)
    _need(len(result) == len(before) and _sha256(result) == AFTER_SHA256,
          "Safari defeat repaired identity differs")
    parsed = gifts_scripts.decode(result, commands, SCRIPT_MEMBER)
    _need(not parsed.errori and parsed.riassembla()[0]
          and _targets(parsed.istruzioni[LOSS_BRANCH]) == [WHITEOUT_TARGET]
          and parsed.istruzioni[WHITEOUT_TARGET].nome == "WhiteOut",
          "Safari defeat repaired branch differs")
    verify_repair(before, result, commands)
    return result


def verify_repair(before, after, commands):
    """Independently reconstruct and check the one admitted member delta."""
    before_parsed = _repair_shape(before, commands)
    _need(type(after) is bytes and len(after) == len(before)
          and _sha256(after) == AFTER_SHA256,
          "Safari defeat postimage differs")
    expected = bytearray(before)
    struct.pack_into("<i", expected, DISPLACEMENT_START,
                     WHITEOUT_TARGET - BRANCH_END)
    _need(after == bytes(expected),
          "Safari defeat repair changed bytes outside the displacement")

    changed = [index for index, pair in enumerate(zip(before, after))
               if pair[0] != pair[1]]
    _need(changed == [DISPLACEMENT_START, DISPLACEMENT_START + 1],
          "Safari defeat changed-byte set differs")
    after_parsed = gifts_scripts.decode(after, commands, SCRIPT_MEMBER)
    _need(not after_parsed.errori and after_parsed.riassembla()[0],
          "Safari defeat postimage does not decode and round-trip")
    _need(_targets(after_parsed.istruzioni[LOSS_BRANCH]) == [WHITEOUT_TARGET],
          "Safari defeat repair target differs")

    broken_seen = _reachable(before_parsed, BROKEN_TARGET)
    broken_names = [before_parsed.istruzioni[off].nome
                    for off in sorted(broken_seen)]
    _need("WhiteOut" not in broken_names and "ReleaseAll" not in broken_names,
          "Safari defeat RED unexpectedly recovers")

    tail = []
    cursor = WHITEOUT_TARGET
    for _ in range(3):
        _need(cursor in after_parsed.istruzioni,
              "Safari defeat recovery tail is truncated")
        row = after_parsed.istruzioni[cursor]
        tail.append(row.nome)
        cursor = row.fine
    _need(tail == ["WhiteOut", "ReleaseAll", "End"],
          "Safari defeat recovery tail differs")

    win_seen = _reachable(after_parsed, BRANCH_END)
    _need(0x65D in win_seen and 0x65F in win_seen
          and after_parsed.istruzioni[0x65D].nome == "ReleaseAll"
          and after_parsed.istruzioni[0x65F].nome == "End"
          and not any(after_parsed.istruzioni[off].nome == "WhiteOut"
                      for off in win_seen),
          "Safari defeat win control differs")

    partners_before = [_targets(before_parsed.istruzioni[offset])[0]
                       for offset in PARTNER_LOSS_BRANCHES]
    partners_after = [_targets(after_parsed.istruzioni[offset])[0]
                      for offset in PARTNER_LOSS_BRANCHES]
    _need(partners_before == partners_after == [WHITEOUT_TARGET] * 4,
          "Safari defeat partner controls changed")
    return {
        "member": SCRIPT_MEMBER,
        "before_sha256": BEFORE_SHA256,
        "after_sha256": AFTER_SHA256,
        "bytes": len(after),
        "changed_offsets": changed,
        "admitted_window": [DISPLACEMENT_START, BRANCH_END],
        "red": {
            "target": BROKEN_TARGET,
            "whiteout_reachable": False,
            "release_all_reachable": False,
        },
        "green": {
            "target": WHITEOUT_TARGET,
            "tail": tail,
        },
        "win_control": {
            "start": BRANCH_END,
            "release_all": 0x65D,
            "end": 0x65F,
        },
        "partner_loss_targets": partners_after,
    }


def repair_archive(before, commands):
    """Replace only member 260 in the exact active script archive."""
    _need(type(before) is bytes and len(before) == ARCHIVE_SIZE
          and _sha256(before) == ARCHIVE_BEFORE_SHA256,
          "Safari defeat archive preimage differs")
    archive = ndspy.narc.NARC(before)
    _need(len(archive.files) == ARCHIVE_MEMBER_COUNT,
          "Safari defeat archive member count differs")
    archive.files[SCRIPT_MEMBER] = repair_member(
        bytes(archive.files[SCRIPT_MEMBER]), commands)
    result = archive.save()
    _need(len(result) == len(before) and _sha256(result) == ARCHIVE_AFTER_SHA256,
          "Safari defeat archive repaired identity differs")
    verify_archive(before, result, commands)
    return result


def verify_archive(before, after, commands):
    """Check archive geometry, replay identity and member confinement."""
    _need(type(before) is bytes and len(before) == ARCHIVE_SIZE
          and _sha256(before) == ARCHIVE_BEFORE_SHA256,
          "Safari defeat archive preimage differs")
    _need(type(after) is bytes and len(after) == ARCHIVE_SIZE
          and _sha256(after) == ARCHIVE_AFTER_SHA256,
          "Safari defeat archive postimage differs")
    old = ndspy.narc.NARC(before)
    new = ndspy.narc.NARC(after)
    _need(len(old.files) == len(new.files) == ARCHIVE_MEMBER_COUNT,
          "Safari defeat archive geometry differs")
    changed_members = [index for index, pair in enumerate(zip(old.files, new.files))
                       if bytes(pair[0]) != bytes(pair[1])]
    _need(changed_members == [SCRIPT_MEMBER],
          "Safari defeat archive repair changed another member")
    member_receipt = verify_repair(bytes(old.files[SCRIPT_MEMBER]),
                                   bytes(new.files[SCRIPT_MEMBER]), commands)
    changed_offsets = [index for index, pair in enumerate(zip(before, after))
                       if pair[0] != pair[1]]
    _need(changed_offsets == list(ARCHIVE_CHANGED_OFFSETS),
          "Safari defeat archive changed-byte geometry differs")
    return {
        "archive": SCRIPT_ARCHIVE,
        "before_sha256": ARCHIVE_BEFORE_SHA256,
        "after_sha256": ARCHIVE_AFTER_SHA256,
        "bytes": len(after),
        "members": ARCHIVE_MEMBER_COUNT,
        "changed_members": changed_members,
        "changed_archive_offsets": changed_offsets,
        "member_receipt": member_receipt,
    }
