"""HG-F13: stop field-overlay reloads reapplying a frozen follower jump.

The follower height helper already owns the current rendered ``facingVector``.
When the X menu pauses movement, that vector is the frozen pose and must be
reused as-is if a child page tears down and recreates the field renderer.
Retail instead asks the phase table for the same jump height again and adds it
to the retained vector on every return.

This stage adds one early ``MapObject_CheckMovementPaused`` guard to the exact
height helper.  Unpaused movement, the existing follower-mode guard, phase
lookup, frame bounds check and height table remain byte-for-byte equivalent.
Only compressed overlay 1 is rewritten; ROM geometry and save data do not
change.
"""
from __future__ import annotations

import hashlib
import struct

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Arm9, Rom, bl_decode


LANGUAGES = ("EN", "IT")
STAGE = "follower-menu-jump"

OVERLAY_ID = 1
OVERLAY_RAM = 0x021E5900
OVERLAY_BYTES = 148064
OVERLAY_BSS_BYTES = 245792
COMPRESSED_BYTES = 109652
STATIC_INIT_RANGE = (0x02209810, 0x02209814)

FUNCTION = 0x022054E0
FUNCTION_BYTES = 92
PAUSE_CHECK = 0x0205F714
FOLLOWER_MODE_CHECK = 0x02205584
PHASE_GETTER = 0x020659A8
FRAME_GETTER = 0x0206599C
ASSERT_FAIL = 0x0202551C
PHASE_TABLE = 0x02209750
MODEL_OBJECT = 0x0227BEEF

FUNCTION_PREIMAGE = bytes.fromhex(
    "38b5b0b0144d041c00ab182203cd03c3521efbd1201c00f045f8002802d030b0"
    "002038bd201c60f64ffa0006050e02d130b0002038bd201c60f640fa041c102c"
    "01db1ff6fbff681e0006820c00a8a1008018085830b038bd50972002"
)
FUNCTION_POSTIMAGE = bytes.fromhex(
    "38b5b0b0041c5af615f9002807d1201c00f048f8002805d0c046c046c04630b0"
    "002038bd201c60f64ffa0006050e02d130b0002038bd201c60f640fa041c102c"
    "01db1ff6fbff681e0006820c0248a1008018085830b038bd50972002"
)
FUNCTION_PRE_SHA256 = "e56508e5bf456f99bfd2b0e7b5050588e0c821c7d7fc674043162c4484be209f"
FUNCTION_POST_SHA256 = "a46c985929aaf0562315698e7ccaceacef79da2e4ff7e7f632e44b2a81467b52"

# The second profile is the exact output of HG-F02.  Supporting both keeps this
# module independently testable while making the eventual order explicit:
# Waterfall facing first, follower/menu jump second.
PROFILES = {
    "06e85ab93f575bb98578bbed46376847300d71eed7b20f9396aa4d5a2737af7e": {
        "name": "active-v4",
        "stream_pre": "c1a4aba1743cd3de24808eb1a507f4f53390ef5a9cdc473e529944cb6ba3b41c",
        "logical_post": "f355bf34ea5ab06938441455e702c0f8a6b7dded0e67f59b43be62eddd2b9499",
        "stream_post": "e36245361c1d3b61451a8329e88bc8e75a48c7f06392c0aea8ed93af40bd21a3",
    },
    "f1936d462da76d057b2db1e5c787a3d0079211e2f818cfb907d61736cd19eb77": {
        "name": "after-waterfall-facing",
        "stream_pre": "3dd306b0e2f8c8e0e1fdd216ed331f65c55a8feff2ec1321497fb96479ed74f5",
        "logical_post": "c5ed85217408f3bceea034b1f60bb78c6ec711840a136ddc6fa88339d0682f3b",
        "stream_post": "7e75a92ec2266cadce002c4603b6a860ad9efb3bc0131e6d3eaf0c2087b510da",
    },
}

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    "EN": "60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82",
    "IT": "edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233",
}

PAUSE_CHECK_SHA256 = "975f0afc9495dc18fd74aea26aa961b2ce3171f3c30d026d4852438b30814400"
FOLLOWER_MODE_CHECK_SHA256 = "251bd612a0227ccbafcda6f13b9ad131d575c15f1765cb2ee99dabbdd5b3d463"
PHASE_GETTERS_SHA256 = "921b03d3bbfd590073eaaec53321a93857a48e7f3308af700e1a11a3c6e02500"
PHASE_TABLE_SHA256 = "929630c594a8f6c8f6d370f022085113bb6bbfe36dc75259657ef5515fe8b5b0"


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError("Follower menu jump: " + message)


def _signed(value, bits=32):
    value &= (1 << bits) - 1
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


def evaluate_height_helper(code, *, paused, mode_guard, phase, frame, table,
                           initial_sp=0x03000000):
    """Execute the helper's small Thumb subset as a semantic/ABI oracle.

    This intentionally decodes control flow, calls, stack changes and the
    phase-table load instead of accepting a hash as proof of behavior.  It is
    bounded to this helper's instruction vocabulary, so an unknown or mutated
    instruction is rejected rather than guessed.
    """
    code, table = bytes(code), bytes(table)
    _need(len(code) == FUNCTION_BYTES, "semantic helper geometry")
    _need(len(table) == 192, "semantic phase-table geometry")
    registers = [0] * 8
    registers[0] = MODEL_OBJECT
    sp = initial_sp
    pc = FUNCTION
    flags = {"z": False, "n": False, "v": False}
    calls = []
    outputs = {
        PAUSE_CHECK: paused,
        FOLLOWER_MODE_CHECK: mode_guard,
        PHASE_GETTER: phase,
        FRAME_GETTER: frame,
    }

    def halfword(address):
        offset = address - FUNCTION
        _need(0 <= offset <= len(code) - 2 and offset % 2 == 0,
              "semantic PC escaped helper")
        return struct.unpack_from("<H", code, offset)[0]

    def set_sub_flags(left, right, result):
        nonlocal flags
        left &= 0xFFFFFFFF
        right &= 0xFFFFFFFF
        result &= 0xFFFFFFFF
        flags = {
            "z": result == 0,
            "n": bool(result & 0x80000000),
            "v": bool(((left ^ right) & (left ^ result)) & 0x80000000),
        }

    for _step in range(96):
        insn = halfword(pc)

        if insn & 0xF800 == 0xF000:
            second = halfword(pc + 2)
            _need(second & 0xF800 == 0xF800, "semantic malformed BL")
            target = bl_decode(pc, code[pc - FUNCTION:pc - FUNCTION + 4])
            _need(target in outputs or target == ASSERT_FAIL,
                  "semantic unexpected call target")
            calls.append({"target": target, "r0": registers[0], "sp": sp})
            if target in outputs:
                registers[0] = int(outputs[target]) & 0xFFFFFFFF
            pc += 4
            continue

        if insn & 0xFE00 == 0xB400:  # push low registers and optional LR
            count = (insn & 0xFF).bit_count() + ((insn >> 8) & 1)
            sp -= count * 4
            pc += 2
            continue
        if insn & 0xFE00 == 0xBC00:  # pop low registers and optional PC
            count = (insn & 0xFF).bit_count() + ((insn >> 8) & 1)
            sp += count * 4
            _need(insn & 0x100, "semantic pop does not return")
            return {
                "result": _signed(registers[0]),
                "calls": calls,
                "returned_sp": sp,
            }
        if insn & 0xFF00 == 0xB000:  # add/sub SP, immediate * 4
            amount = (insn & 0x7F) * 4
            sp += -amount if insn & 0x80 else amount
            pc += 2
            continue
        if insn == 0x46C0:  # nop
            pc += 2
            continue
        if insn & 0xFE00 == 0x1C00:  # adds Rd,Rn,#imm3
            immediate = (insn >> 6) & 7
            source = (insn >> 3) & 7
            destination = insn & 7
            registers[destination] = (registers[source] + immediate) & 0xFFFFFFFF
            pc += 2
            continue
        if insn & 0xFE00 == 0x1E00:  # subs Rd,Rn,#imm3
            immediate = (insn >> 6) & 7
            source = (insn >> 3) & 7
            destination = insn & 7
            value = (registers[source] - immediate) & 0xFFFFFFFF
            registers[destination] = value
            set_sub_flags(registers[source], immediate, value)
            pc += 2
            continue
        if insn & 0xF800 == 0x2000:  # movs Rd,#imm8
            destination = (insn >> 8) & 7
            registers[destination] = insn & 0xFF
            flags["z"] = registers[destination] == 0
            flags["n"] = False
            pc += 2
            continue
        if insn & 0xF800 == 0x2800:  # cmp Rn,#imm8
            source = (insn >> 8) & 7
            immediate = insn & 0xFF
            value = (registers[source] - immediate) & 0xFFFFFFFF
            set_sub_flags(registers[source], immediate, value)
            pc += 2
            continue
        if insn & 0xF800 == 0x0000:  # lsls Rd,Rs,#imm5
            amount = (insn >> 6) & 0x1F
            source = (insn >> 3) & 7
            destination = insn & 7
            registers[destination] = (registers[source] << amount) & 0xFFFFFFFF
            flags["z"] = registers[destination] == 0
            flags["n"] = bool(registers[destination] & 0x80000000)
            pc += 2
            continue
        if insn & 0xF800 == 0x0800:  # lsrs Rd,Rs,#imm5
            amount = (insn >> 6) & 0x1F
            source = (insn >> 3) & 7
            destination = insn & 7
            registers[destination] = (registers[source] & 0xFFFFFFFF) >> amount
            flags["z"] = registers[destination] == 0
            flags["n"] = False
            pc += 2
            continue
        if insn & 0xF000 == 0xD000 and insn & 0x0F00 != 0x0F00:
            condition = (insn >> 8) & 0xF
            take = {0: flags["z"], 1: not flags["z"],
                    11: flags["n"] != flags["v"]}.get(condition)
            _need(take is not None, "semantic unsupported conditional branch")
            displacement = _signed(insn & 0xFF, 8) * 2
            pc = pc + 4 + displacement if take else pc + 2
            continue
        if insn & 0xF800 == 0x4800:  # ldr Rd,[PC,#imm8*4]
            destination = (insn >> 8) & 7
            address = ((pc + 4) & ~3) + (insn & 0xFF) * 4
            offset = address - FUNCTION
            _need(0 <= offset <= len(code) - 4,
                  "semantic literal escaped helper")
            registers[destination] = struct.unpack_from("<I", code, offset)[0]
            pc += 2
            continue
        if insn & 0xFE00 == 0x1800:  # adds Rd,Rn,Rm
            source_m = (insn >> 6) & 7
            source_n = (insn >> 3) & 7
            destination = insn & 7
            registers[destination] = (
                registers[source_n] + registers[source_m]) & 0xFFFFFFFF
            pc += 2
            continue
        if insn & 0xF800 == 0x0000:
            raise AssertionError("unreachable shift decoder")
        if insn & 0xF800 == 0x5800:  # ldr Rd,[Rn,Rm]
            source_m = (insn >> 6) & 7
            source_n = (insn >> 3) & 7
            destination = insn & 7
            address = (registers[source_n] + registers[source_m]) & 0xFFFFFFFF
            offset = address - PHASE_TABLE
            _need(0 <= offset <= len(table) - 4 and offset % 4 == 0,
                  "semantic phase-table read escaped")
            registers[destination] = struct.unpack_from("<I", table, offset)[0]
            pc += 2
            continue
        _need(False, "semantic unsupported instruction %04x" % insn)
    raise ValueError("Follower menu jump: semantic helper did not return")


def check_height_helper(code, table):
    """Check the decoded pause/mode/phase/frame/table contract and Thumb ABI."""
    initial_sp = 0x03000000
    cases = (
        (1, 0, 3, 15, 0, (PAUSE_CHECK,)),
        (0, 1, 3, 15, 0, (PAUSE_CHECK, FOLLOWER_MODE_CHECK)),
        (0, 0, 0, 15, 0,
         (PAUSE_CHECK, FOLLOWER_MODE_CHECK, PHASE_GETTER)),
        (0, 0, 1, 0, struct.unpack_from("<i", table, 0)[0],
         (PAUSE_CHECK, FOLLOWER_MODE_CHECK, PHASE_GETTER, FRAME_GETTER)),
        (0, 0, 2, 7, struct.unpack_from("<i", table, (16 + 7) * 4)[0],
         (PAUSE_CHECK, FOLLOWER_MODE_CHECK, PHASE_GETTER, FRAME_GETTER)),
        (0, 0, 3, 15, struct.unpack_from("<i", table, 47 * 4)[0],
         (PAUSE_CHECK, FOLLOWER_MODE_CHECK, PHASE_GETTER, FRAME_GETTER)),
    )
    try:
        for paused, mode, phase, frame, result, targets in cases:
            observed = evaluate_height_helper(
                code, paused=paused, mode_guard=mode, phase=phase,
                frame=frame, table=table, initial_sp=initial_sp)
            if (observed["result"] != result
                    or tuple(call["target"] for call in observed["calls"]) != targets
                    or any(call["r0"] != MODEL_OBJECT for call in observed["calls"])
                    or any(call["sp"] % 8 for call in observed["calls"])
                    or observed["returned_sp"] != initial_sp):
                return False
    except (ValueError, struct.error, TypeError):
        return False
    return True


def _language_anchor(data, language):
    try:
        fat, fat_bytes = struct.unpack_from("<II", data, 0x48)
        entry = fat + LANGUAGE_ANCHOR_FILE * 8
        _need(fat_bytes % 8 == 0 and entry + 8 <= fat + fat_bytes,
              "language anchor FAT")
        start, end = struct.unpack_from("<II", data, entry)
        _need(0 <= start < end <= len(data), "language anchor extent")
    except (struct.error, TypeError):
        raise ValueError("Follower menu jump: language anchor geometry") from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          "language anchor mismatch")


def _read_overlay(data):
    try:
        rom = Rom(data)
        entry, stream, image = rom.immagine_overlay(OVERLAY_ID)
        fat = rom.voce_fat(entry["file_id"])
    except (ValueError, struct.error, IndexError) as error:
        raise ValueError("Follower menu jump: overlay geometry") from error
    _need(entry["id"] == OVERLAY_ID and entry["file_id"] == OVERLAY_ID,
          "overlay identity")
    _need((entry["ram"], entry["ram_size"], entry["bss_size"])
          == (OVERLAY_RAM, OVERLAY_BYTES, OVERLAY_BSS_BYTES),
          "overlay RAM geometry")
    _need(entry["compresso"] and entry["dim_compressa"] == COMPRESSED_BYTES,
          "overlay compression geometry")
    _need((entry["static_init_start"], entry["static_init_end"])
          == STATIC_INIT_RANGE, "overlay static initializer range")
    _need(fat["bytes"] == COMPRESSED_BYTES and len(stream) == COMPRESSED_BYTES,
          "overlay FAT extent")
    return rom, entry, fat, bytes(stream), bytes(image)


def _function(image, post=False):
    _need(type(image) is bytes and len(image) == OVERLAY_BYTES,
          "overlay logical geometry")
    at = FUNCTION - OVERLAY_RAM
    actual = image[at:at + FUNCTION_BYTES]
    expected = FUNCTION_POSTIMAGE if post else FUNCTION_PREIMAGE
    digest = FUNCTION_POST_SHA256 if post else FUNCTION_PRE_SHA256
    _need(actual == expected and _sha(actual) == digest,
          "height helper %simage differs" % ("post" if post else "pre"))
    return actual


def _contract(data, image):
    arm = Arm9.from_bytes(data)
    pause = arm.leggi(PAUSE_CHECK, 40)
    mode = image[FOLLOWER_MODE_CHECK - OVERLAY_RAM:
                 FOLLOWER_MODE_CHECK - OVERLAY_RAM + 44]
    getters = arm.leggi(0x0206599C, 28)
    table = image[PHASE_TABLE - OVERLAY_RAM:PHASE_TABLE - OVERLAY_RAM + 192]
    _need(_sha(pause) == PAUSE_CHECK_SHA256,
          "movement-pause predicate differs")
    _need(_sha(mode) == FOLLOWER_MODE_CHECK_SHA256,
          "existing follower-mode predicate differs")
    _need(_sha(getters) == PHASE_GETTERS_SHA256,
          "follower phase getters differ")
    _need(_sha(table) == PHASE_TABLE_SHA256,
          "follower height table differs")
    helper = image[FUNCTION - OVERLAY_RAM:FUNCTION - OVERLAY_RAM + FUNCTION_BYTES]
    if helper == FUNCTION_POSTIMAGE:
        _need(check_height_helper(helper, table),
              "height helper semantic/ABI contract differs")
    return {
        "pause_check_sha256": PAUSE_CHECK_SHA256,
        "follower_mode_check_sha256": FOLLOWER_MODE_CHECK_SHA256,
        "phase_getters_sha256": PHASE_GETTERS_SHA256,
        "phase_table_sha256": PHASE_TABLE_SHA256,
        "paused_returns_zero_before_phase_path": True,
        "unpaused_mode_phase_frame_table_path_preserved": True,
        "call_sp_aligned_and_returned_sp_restored": True,
    }


def _preimage(data):
    rom, entry, fat, stream, image = _read_overlay(data)
    profile = PROFILES.get(_sha(image))
    _need(profile is not None, "overlay preimage differs")
    _need(_sha(stream) == profile["stream_pre"],
          "compressed overlay preimage differs")
    _function(image)
    contract = _contract(data, image)
    return rom, entry, fat, stream, image, profile, contract


def _patch_image(image, profile):
    _function(image)
    out = bytearray(image)
    at = FUNCTION - OVERLAY_RAM
    out[at:at + FUNCTION_BYTES] = FUNCTION_POSTIMAGE
    out = bytes(out)
    _need(_sha(out) == profile["logical_post"],
          "overlay postimage differs")
    _function(out, post=True)
    return out


def apply(data, language):
    """Apply HG-F13 in memory and return a sealed byte-confinement receipt."""
    data = bytes(data)
    _need(language in LANGUAGES, "input/language")
    _language_anchor(data, language)
    _rom, entry, fat, stream, image, profile, contract = _preimage(data)
    patched = _patch_image(image, profile)
    encoded = blz_comprimi_ottimo(patched, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES
          and _sha(encoded) == profile["stream_post"],
          "compressed overlay postimage differs")
    _need(blz_decomprimi(encoded, OVERLAY_BYTES) == patched,
          "compressed overlay does not round-trip")

    out = bytearray(data)
    out[fat["inizio"]:fat["fine"]] = encoded
    out = bytes(out)
    receipt = {
        "schema": 1,
        "stage": STAGE,
        "language": language,
        "profile": profile["name"],
        "input_sha256": _sha(data),
        "output_sha256": _sha(out),
        "overlay_id": OVERLAY_ID,
        "file_id": entry["file_id"],
        "rom_slot": [fat["inizio"], fat["fine"]],
        "function_address": FUNCTION,
        "function_bytes": FUNCTION_BYTES,
        "function_preimage_sha256": FUNCTION_PRE_SHA256,
        "function_postimage_sha256": FUNCTION_POST_SHA256,
        "overlay_preimage_sha256": _sha(image),
        "overlay_postimage_sha256": profile["logical_post"],
        "compressed_preimage_sha256": _sha(stream),
        "compressed_postimage_sha256": profile["stream_post"],
        "contract": contract,
        "save_layout_unchanged": True,
        "rom_geometry_unchanged": True,
    }
    receipt["verification"] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    before, after = bytes(before), bytes(after)
    _need(len(before) == len(after) and before[:0x200] == after[:0x200],
          "ROM geometry/header")
    (_old_rom, old_entry, old_fat, old_stream, old_image,
     profile, contract) = _preimage(before)
    _new_rom, new_entry, new_fat, new_stream, new_image = _read_overlay(after)
    _need(old_entry == new_entry and old_fat == new_fat,
          "FAT/y9 overlay identity changed")
    _need(_sha(new_stream) == profile["stream_post"]
          and _sha(new_image) == profile["logical_post"],
          "installed overlay postimage differs")
    _function(new_image, post=True)
    _contract(after, new_image)
    _need(blz_decomprimi(new_stream, OVERLAY_BYTES) == new_image,
          "installed compressed overlay does not round-trip")

    restored_image = bytearray(new_image)
    at = FUNCTION - OVERLAY_RAM
    restored_image[at:at + FUNCTION_BYTES] = FUNCTION_PREIMAGE
    _need(bytes(restored_image) == old_image,
          "logical bytes changed outside the height helper")
    restored_rom = bytearray(after)
    restored_rom[old_fat["inizio"]:old_fat["fine"]] = old_stream
    _need(bytes(restored_rom) == before,
          "ROM bytes changed outside compressed overlay 1")

    first_call = FUNCTION + 6
    second_call = FUNCTION + 16
    _need(bl_decode(first_call, new_image[first_call - OVERLAY_RAM:
                                          first_call - OVERLAY_RAM + 4])
          == PAUSE_CHECK,
          "pause guard call target differs")
    _need(bl_decode(second_call, new_image[second_call - OVERLAY_RAM:
                                           second_call - OVERLAY_RAM + 4])
          == FOLLOWER_MODE_CHECK,
          "existing mode guard call target differs")
    logical_changes = [index for index, (old, new) in enumerate(
        zip(old_image, new_image)) if old != new]
    _need(logical_changes and min(logical_changes) >= at
          and max(logical_changes) < at + FUNCTION_BYTES,
          "logical change confinement differs")

    report = {
        "ok": True,
        "profile": profile["name"],
        "changed_logical_bytes": len(logical_changes),
        "changed_rom_bytes": sum(a != b for a, b in zip(old_stream, new_stream)),
        "paused_height_delta": 0,
        "unpaused_phase_path_preserved": True,
        "existing_mode_guard_preserved": True,
        "phase_table_preserved": True,
        "save_layout_unchanged": True,
        "rom_geometry_unchanged": True,
    }
    required = {
        "schema": 1,
        "stage": STAGE,
        "profile": profile["name"],
        "input_sha256": _sha(before),
        "output_sha256": _sha(after),
        "overlay_id": OVERLAY_ID,
        "file_id": old_entry["file_id"],
        "rom_slot": [old_fat["inizio"], old_fat["fine"]],
        "function_address": FUNCTION,
        "function_bytes": FUNCTION_BYTES,
        "function_preimage_sha256": FUNCTION_PRE_SHA256,
        "function_postimage_sha256": FUNCTION_POST_SHA256,
        "overlay_preimage_sha256": _sha(old_image),
        "overlay_postimage_sha256": profile["logical_post"],
        "compressed_preimage_sha256": _sha(old_stream),
        "compressed_postimage_sha256": profile["stream_post"],
        "contract": contract,
        "save_layout_unchanged": True,
        "rom_geometry_unchanged": True,
    }
    allowed = set(required) | {"language"}
    if not unsealed:
        allowed.add("verification")
    _need(isinstance(receipt, dict) and set(receipt) == allowed
          and receipt.get("language") in LANGUAGES
          and (unsealed or receipt.get("verification") == report)
          and all(receipt.get(key) == value for key, value in required.items()),
          "receipt identity")
    _language_anchor(before, receipt.get("language"))
    return report


def verify(before, after, receipt):
    """Re-read both complete images and enforce semantic/physical confinement."""
    return _verify(before, after, receipt, unsealed=False)


def peel(after):
    """Remove HG-F13 while preserving the preceding HG-F02 overlay-1 edit."""
    after = bytes(after)
    _rom, _entry, fat, stream, image = _read_overlay(after)
    profile = next(row for row in PROFILES.values()
                   if row["name"] == "after-waterfall-facing")
    _need(_sha(stream) == profile["stream_post"]
          and _sha(image) == profile["logical_post"],
          "peel postimage is not the HG-F02/HG-F13 composition")
    _function(image, post=True)
    _contract(after, image)
    out_image = bytearray(image)
    at = FUNCTION - OVERLAY_RAM
    out_image[at:at + FUNCTION_BYTES] = FUNCTION_PREIMAGE
    out_image = bytes(out_image)
    pre_hash = next(digest for digest, row in PROFILES.items()
                    if row is profile)
    _need(_sha(out_image) == pre_hash, "peeled overlay preimage differs")
    encoded = blz_comprimi_ottimo(out_image, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES
          and _sha(encoded) == profile["stream_pre"],
          "peeled compressed overlay differs")
    out = bytearray(after)
    out[fat["inizio"]:fat["fine"]] = encoded
    return bytes(out)


def spans(data):
    """Return the labeled physical owner for later shared-stage integration."""
    _rom, _entry, fat, _stream, _image, _profile, _contract = _preimage(bytes(data))
    return ((fat["inizio"], fat["fine"],
             "overlay 1 follower/menu height helper"),)


def changed_regions(data):
    """Return the one physical owner without labels."""
    return tuple((start, end) for start, end, _label in spans(data))
