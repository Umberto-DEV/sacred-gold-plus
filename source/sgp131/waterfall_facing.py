"""HG-F02: face South before a successful automatic Waterfall descent.

The retail field-input gate already admits only direction South and only then
calls ``ov01_021F28EC`` to start the descent task.  Its task moves South but
never updates ``PlayerAvatar.currentFacing``.  Replace that one BL with a
20-byte resident wrapper which sets current facing South, then calls the
original task with the original field-system argument.  Failure paths and the
script/menu ascent path do not pass through this seam.
"""
import hashlib
import struct

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Arm9, Rom, bl_decode, bl_thumb


LANGUAGES = ("EN", "IT")
STAGE = "waterfall-facing"
SOUTH, WEST, EAST = 1, 2, 3

OVERLAY_ID = 1
OVERLAY_RAM = 0x021E5900
OVERLAY_BYTES = 148064
OVERLAY_BSS_BYTES = 245792
COMPRESSED_BYTES = 109652
STATIC_INIT_RANGE = (0x02209810, 0x02209814)
HOOK = 0x021F252E
ORIGINAL_TASK = 0x021F28EC
SET_FACING = 0x0205C660
SLOT = 0x023D8AEC
SLOT_BYTES = 20
SLOT_PREIMAGE = bytes(SLOT_BYTES)
NEXT_OWNER = 0x023D8B00
NEXT_OWNER_PREFIX = bytes.fromhex("f0b587b0274a1168491c116001210902")

HOOK_PREIMAGE = bl_thumb(HOOK, ORIGINAL_TASK)
HOOK_POSTIMAGE = bl_thumb(HOOK, SLOT)
OVERLAY_PRE_SHA256 = "06e85ab93f575bb98578bbed46376847300d71eed7b20f9396aa4d5a2737af7e"
STREAM_PRE_SHA256 = "c1a4aba1743cd3de24808eb1a507f4f53390ef5a9cdc473e529944cb6ba3b41c"
OVERLAY_POST_SHA256 = "f1936d462da76d057b2db1e5c787a3d0079211e2f818cfb907d61736cd19eb77"
STREAM_POST_SHA256 = "3dd306b0e2f8c8e0e1fdd216ed331f65c55a8feff2ec1321497fb96479ed74f5"

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    "EN": "60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82",
    "IT": "edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233",
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError("Waterfall facing: " + message)


def _payload():
    # Keep SP 8-byte aligned at both calls: push {r0,r1,r2,lr}; load avatar;
    # set South; reload the saved field system; start task; restore and return.
    out = bytearray.fromhex("07b5006c012100000000009801210000000007bd")
    out[6:10] = bl_thumb(SLOT + 6, SET_FACING)
    out[14:18] = bl_thumb(SLOT + 14, ORIGINAL_TASK)
    return bytes(out)


SLOT_POSTIMAGE = _payload()
SLOT_POST_SHA256 = "9f5db195a0490f28e83ae2dc20c6c503007c541fa06116fc127a686a402f6417"


def decode_payload_calls(payload):
    """Return the ordered external calls from an authenticated wrapper."""
    payload = bytes(payload)
    _need(len(payload) == SLOT_BYTES, "resident payload length")
    return (("set-facing", bl_decode(SLOT + 6, payload[6:10])),
            ("start-task", bl_decode(SLOT + 14, payload[14:18])))


def check_payload(payload):
    """Strict ABI/order predicate used by source tests and mutant checks."""
    payload = bytes(payload)
    if payload != SLOT_POSTIMAGE or _sha(payload) != SLOT_POST_SHA256:
        return False
    if payload[:6] != bytes.fromhex("07b5006c0121"):
        return False
    if payload[10:14] != bytes.fromhex("00980121") or payload[18:] != bytes.fromhex("07bd"):
        return False
    return decode_payload_calls(payload) == (("set-facing", SET_FACING),
                                              ("start-task", ORIGINAL_TASK))


def payload_call_sp(payload, entry_sp=0x03000000):
    """Interpret stack-affecting instructions and report SP at each BL."""
    payload = bytes(payload)
    _need(len(payload) == SLOT_BYTES, "resident payload length")
    sp = entry_sp
    _need(payload[:2] == bytes.fromhex("07b5"), "resident push ABI")
    sp -= 16
    calls = ((bl_decode(SLOT + 6, payload[6:10]), sp),
             (bl_decode(SLOT + 14, payload[14:18]), sp))
    _need(payload[18:] == bytes.fromhex("07bd"), "resident pop ABI")
    sp += 16
    return calls, sp


def _language_anchor(data, language):
    try:
        fat, fat_bytes = struct.unpack_from("<II", data, 0x48)
        entry = fat + LANGUAGE_ANCHOR_FILE * 8
        _need(fat_bytes % 8 == 0 and entry + 8 <= fat + fat_bytes,
              "language anchor FAT")
        start, end = struct.unpack_from("<II", data, entry)
        _need(0 <= start < end <= len(data), "language anchor extent")
    except (struct.error, TypeError):
        raise ValueError("Waterfall facing: language anchor geometry") from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          "language anchor mismatch")


def _read_overlay(data):
    try:
        rom = Rom(data)
        entry, stream, image = rom.immagine_overlay(OVERLAY_ID)
        fat = rom.voce_fat(entry["file_id"])
    except (ValueError, struct.error, IndexError) as error:
        raise ValueError("Waterfall facing: overlay geometry") from error
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


def _guard_overlay(image, post=False):
    _need(type(image) is bytes and len(image) == OVERLAY_BYTES,
          "overlay logical geometry")
    _need(_sha(image) == (OVERLAY_POST_SHA256 if post else OVERLAY_PRE_SHA256),
          "overlay %simage differs" % ("post" if post else "pre"))
    at = HOOK - OVERLAY_RAM
    call = image[at:at + 4]
    expected = HOOK_POSTIMAGE if post else HOOK_PREIMAGE
    target = SLOT if post else ORIGINAL_TASK
    _need(call == expected and bl_decode(HOOK, call) == target,
          "successful descent call differs")


def _guard_resident(arm, post=False):
    from . import pokegear_autocull
    _need(arm.leggi(pokegear_autocull.SLOT, pokegear_autocull.SLOT_BYTES)
          == pokegear_autocull.SLOT_POSTIMAGE,
          "preceding Pokégear owner differs")
    payload = arm.leggi(SLOT, SLOT_BYTES)
    _need(payload == (SLOT_POSTIMAGE if post else SLOT_PREIMAGE),
          "resident %simage differs" % ("post" if post else "pre"))
    _need(not post or check_payload(payload), "resident ABI/order differs")
    _need(arm.leggi(NEXT_OWNER, len(NEXT_OWNER_PREFIX)) == NEXT_OWNER_PREFIX,
          "following owner differs")


def _preimage(data):
    rom, entry, fat, stream, image = _read_overlay(data)
    _need(_sha(stream) == STREAM_PRE_SHA256, "compressed overlay preimage differs")
    _guard_overlay(image)
    arm = Arm9.from_bytes(data)
    _guard_resident(arm)
    return rom, entry, fat, stream, image, arm


def apply(data, language):
    data = bytes(data)
    _need(language in LANGUAGES, "input/language")
    _language_anchor(data, language)
    _rom, entry, fat, stream, image, arm = _preimage(data)
    patched = bytearray(image)
    at = HOOK - OVERLAY_RAM
    patched[at:at + 4] = HOOK_POSTIMAGE
    patched = bytes(patched)
    _guard_overlay(patched, post=True)
    encoded = blz_comprimi_ottimo(patched, bersaglio=COMPRESSED_BYTES)
    _need(len(encoded) == COMPRESSED_BYTES and _sha(encoded) == STREAM_POST_SHA256,
          "compressed overlay postimage differs")
    _need(blz_decomprimi(encoded, OVERLAY_BYTES) == patched,
          "compressed overlay does not round-trip")

    out = bytearray(data)
    out[fat["inizio"]:fat["fine"]] = encoded
    resident = Arm9.from_bytes(bytes(out))
    _guard_resident(resident)
    resident.scrivi(SLOT, SLOT_POSTIMAGE)
    out = bytes(resident.raw)
    receipt = {
        "schema": 1, "stage": STAGE, "language": language,
        "input_sha256": _sha(data), "output_sha256": _sha(out),
        "overlay_id": OVERLAY_ID, "file_id": entry["file_id"],
        "rom_slot": [fat["inizio"], fat["fine"]],
        "hook_address": HOOK,
        "hook_before": HOOK_PREIMAGE.hex(), "hook_after": HOOK_POSTIMAGE.hex(),
        "overlay_preimage_sha256": OVERLAY_PRE_SHA256,
        "overlay_postimage_sha256": OVERLAY_POST_SHA256,
        "compressed_preimage_sha256": _sha(stream),
        "compressed_postimage_sha256": STREAM_POST_SHA256,
        "slot_address": SLOT, "slot_bytes": SLOT_BYTES,
        "slot_preimage_sha256": _sha(SLOT_PREIMAGE),
        "slot_postimage_sha256": SLOT_POST_SHA256,
        "save_layout_unchanged": True, "rom_geometry_unchanged": True,
    }
    receipt["verification"] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    before, after = bytes(before), bytes(after)
    _need(len(before) == len(after) and before[:0x200] == after[:0x200],
          "ROM geometry/header")
    _old_rom, old_entry, old_fat, old_stream, old_image, old_arm = _preimage(before)
    _new_rom, new_entry, new_fat, new_stream, new_image = _read_overlay(after)
    _need(old_entry == new_entry and old_fat == new_fat,
          "FAT/y9 overlay identity changed")
    _need(_sha(new_stream) == STREAM_POST_SHA256, "installed stream differs")
    _guard_overlay(new_image, post=True)
    new_arm = Arm9.from_bytes(after)
    _guard_resident(new_arm, post=True)

    restored_image = bytearray(new_image)
    at = HOOK - OVERLAY_RAM
    restored_image[at:at + 4] = HOOK_PREIMAGE
    _need(bytes(restored_image) == old_image,
          "logical bytes changed outside successful descent call")
    restored = bytearray(after)
    restored[old_fat["inizio"]:old_fat["fine"]] = old_stream
    slot_at = old_arm.off(SLOT, SLOT_BYTES)
    restored[slot_at:slot_at + SLOT_BYTES] = SLOT_PREIMAGE
    _need(bytes(restored) == before,
          "ROM bytes changed outside overlay and resident slot")

    report = {
        "ok": True, "facing_before_task": True, "direction": SOUTH,
        "failed_branches_unchanged": True, "ascent_menu_unchanged": True,
        "callee_saved_registers_preserved": True, "stack_alignment": 8,
        "save_layout_unchanged": True, "rom_geometry_unchanged": True,
    }
    required = {
        "schema": 1, "stage": STAGE,
        "input_sha256": _sha(before), "output_sha256": _sha(after),
        "overlay_id": OVERLAY_ID, "file_id": old_entry["file_id"],
        "rom_slot": [old_fat["inizio"], old_fat["fine"]],
        "hook_address": HOOK,
        "hook_before": HOOK_PREIMAGE.hex(), "hook_after": HOOK_POSTIMAGE.hex(),
        "overlay_preimage_sha256": OVERLAY_PRE_SHA256,
        "overlay_postimage_sha256": OVERLAY_POST_SHA256,
        "compressed_preimage_sha256": _sha(old_stream),
        "compressed_postimage_sha256": STREAM_POST_SHA256,
        "slot_address": SLOT, "slot_bytes": SLOT_BYTES,
        "slot_preimage_sha256": _sha(SLOT_PREIMAGE),
        "slot_postimage_sha256": SLOT_POST_SHA256,
        "save_layout_unchanged": True, "rom_geometry_unchanged": True,
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
    return _verify(before, after, receipt, unsealed=False)


def spans(data):
    _rom, _entry, fat, _stream, _image = _read_overlay(bytes(data))
    arm = Arm9.from_bytes(bytes(data))
    slot = arm.off(SLOT, SLOT_BYTES)
    return ((fat["inizio"], fat["fine"], "overlay 1 Waterfall seam"),
            (slot, slot + SLOT_BYTES, "Waterfall South-facing wrapper"))


def changed_regions(data):
    return [(start, end) for start, end, _label in spans(data)]
