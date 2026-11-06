"""HG-F09 Route 43/44 invisible-grass permission repair.

The two exact land members already contain the intended visual models and
collision.  Six permission-grid words incorrectly classify edge-only grass as
tall grass.  This stage changes only those words from ``0x0002`` to ordinary
walkable ground ``0x0400`` inside the existing NARC and ROM allocations.
"""
import hashlib
import struct

import ndspy.narc
import ndspy.rom

from sgp2.formats import LandData


ARCHIVE = "a/0/6/5"
FILE_ID = 194
ARCHIVE_BEFORE_SHA256 = "120594d49680ed216487d40bc68b5af23b11882eac76f5ecafa992c278d4b4ab"
ARCHIVE_AFTER_SHA256 = "a6e5949f73dd5ff04d85a60078e707d1a2ba015ccc0c1b4549026ddcb9a5c5bb"
ARCHIVE_SIZE = 19536658
LANGUAGES = ("EN", "IT")
HEADER_BYTES = 0x200
LANDS = {
    87: {
        "targets": ((11, 16), (12, 16), (13, 16)),
        "visible": ((11, 17), (12, 17), (13, 17)),
        "ordinary": ((8, 17), (9, 17), (10, 17)),
        "water": ((11, 15), (12, 15)),
        "before": "10174f6a0cfdeae637639949cbfbab63c3b77071dbcc2893e1276512d74c6cb2",
        "after": "8635361132fdab31f2e4f1fb49640954c28e30fa8ba370f1bdcd4663732e2fb5",
        "permission_before": "1b5556cccb70bcbff752ae7569600becd48d15a1e5e7207c622bdbef10a652c2",
        "permission_after": "eb1753cfaaec2f36f00093adc0ad128374cee90a5b4f8c4e9c380e2d36c14107",
    },
    102: {
        "targets": ((17, 12), (18, 12), (19, 12)),
        "visible": ((17, 13), (18, 13), (19, 13)),
        "ordinary": (),
        "water": ((18, 11), (19, 11)),
        "before": "b55a1fce3a18a7a226ec851977555dbd1e0dc6872f94f918dd8ee815f4a1b1ec",
        "after": "8d597789c254b19cbe797dd6f1c1107153c258efcf177b399c72b17b55923089",
        "permission_before": "d002ad91ed7c1101a6b757cbb1a12f63efae9597b3ce10521149f09016d60b0b",
        "permission_after": "00934460541798e30b882419c3af82f72182f0f7e6d3b78e82076cec1ed0f842",
    },
}


def _sha256(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError(message)


def _permission(land, x, z):
    return struct.unpack_from("<H", land.permissions, 2 * (z * 32 + x))[0]


def _narc_layout(raw):
    """Return the exact member spans without rebuilding the NARC."""
    raw = bytes(raw)
    _need(len(raw) >= 0x30 and raw[:4] == b"NARC"
          and raw[4:6] in (b"\xfe\xff", b"\xff\xfe"),
          "land archive is not a NARC")
    declared, header_size, blocks = struct.unpack_from("<IHH", raw, 8)
    _need(declared == len(raw) and header_size == 0x10 and blocks == 3,
          "land archive header or length differs")
    magic, btaf_size, count = struct.unpack_from("<4sII", raw, 0x10)
    _need(magic == b"BTAF" and btaf_size == 12 + count * 8
          and 0x10 + btaf_size + 8 <= len(raw),
          "land archive allocation table differs")
    btnf = 0x10 + btaf_size
    _need(raw[btnf:btnf + 4] == b"BTNF", "land archive name table is absent")
    btnf_size = struct.unpack_from("<I", raw, btnf + 4)[0]
    gmif = btnf + btnf_size
    _need(btnf_size >= 8 and gmif + 8 <= len(raw)
          and raw[gmif:gmif + 4] == b"GMIF", "land archive data block is absent")
    gmif_size = struct.unpack_from("<I", raw, gmif + 4)[0]
    _need(gmif_size >= 8 and gmif + gmif_size == len(raw),
          "land archive data length differs")
    data = gmif + 8
    payload = gmif_size - 8
    spans = []
    previous_end = 0
    for index in range(count):
        start, end = struct.unpack_from("<II", raw, 0x1C + 8 * index)
        _need(previous_end <= start <= end <= payload,
              "land archive member %d geometry differs" % index)
        spans.append((data + start, data + end))
        previous_end = end
    return data, tuple(spans)


def _check_land(member, raw, state):
    identity = LANDS[member]
    expected_hash = identity[state]
    _need(_sha256(raw) == expected_hash,
          "land %d %s hash differs" % (member, state))
    land = LandData.parse(bytes(raw))
    expected_permission = identity["permission_" + state]
    _need(_sha256(land.permissions) == expected_permission,
          "land %d %s permission hash differs" % (member, state))
    target = 0x0002 if state == "before" else 0x0400
    _need(tuple(_permission(land, *cell) for cell in identity["targets"])
          == (target, target, target),
          "land %d %s target permissions differ" % (member, state))
    _need(tuple(_permission(land, *cell) for cell in identity["visible"])
          == (0x0002, 0x0002, 0x0002),
          "land %d visible-grass controls differ" % member)
    _need(tuple(_permission(land, *cell) for cell in identity["ordinary"])
          == (0x0400,) * len(identity["ordinary"]),
          "land %d ordinary-ground controls differ" % member)
    _need(tuple(_permission(land, *cell) for cell in identity["water"])
          == (0x0010,) * len(identity["water"]),
          "land %d water controls differ" % member)
    return land


def patch_archive(raw):
    """Change exactly six authenticated permission words in place."""
    raw = bytes(raw)
    digest = _sha256(raw)
    if digest == ARCHIVE_AFTER_SHA256:
        raise ValueError("invisible-grass archive is already patched")
    _need(digest == ARCHIVE_BEFORE_SHA256 and len(raw) == ARCHIVE_SIZE,
          "foreign invisible-grass archive sha256 %s" % digest)
    data_offset, spans = _narc_layout(raw)
    _need(len(spans) > max(LANDS), "land archive member count differs")
    out = bytearray(raw)
    for member, identity in LANDS.items():
        start, end = spans[member]
        land = _check_land(member, raw[start:end], "before")
        for x, z in identity["targets"]:
            land = land.with_permission(x, z, 0x0400)
        encoded = land.encode()
        _need(len(encoded) == end - start, "land %d changed length" % member)
        _check_land(member, encoded, "after")
        out[start:end] = encoded
    out = bytes(out)
    _need(_sha256(out) == ARCHIVE_AFTER_SHA256,
          "invisible-grass archive postimage differs")
    new_data, new_spans = _narc_layout(out)
    _need((new_data, new_spans) == (data_offset, spans),
          "invisible-grass NARC geometry changed")
    return out


def _fat_slot(data, file_id):
    fat_offset, fat_length = struct.unpack_from("<II", data, 0x48)
    _need(type(file_id) is int and 0 <= 8 * file_id <= fat_length - 8,
          "land archive file is outside the FAT")
    start, end = struct.unpack_from("<II", data, fat_offset + 8 * file_id)
    _need(0 <= start < end <= len(data), "land archive FAT slot differs")
    return start, end


def _rom_archive(data):
    data = bytes(data)
    rom = ndspy.rom.NintendoDSRom(data)
    file_id = rom.filenames.idOf(ARCHIVE)
    _need(file_id == FILE_ID, "land archive file id is %d, expected %d" % (file_id, FILE_ID))
    start, end = _fat_slot(data, file_id)
    archive = bytes(rom.files[file_id])
    _need(archive == data[start:end], "parsed land archive differs from its FAT slot")
    return rom, file_id, start, end, archive


def _changed_offsets(before, after, chunk=1 << 20):
    _need(len(before) == len(after), "invisible-grass images differ in length")
    result = []
    for base in range(0, len(before), chunk):
        end = min(base + chunk, len(before))
        if before[base:end] == after[base:end]:
            continue
        result.extend(index for index in range(base, end)
                      if before[index] != after[index])
    return result


def _owned_offsets(archive, rom_start):
    _data, spans = _narc_layout(archive)
    result = []
    for member, identity in LANDS.items():
        member_start = spans[member][0]
        land = LandData.parse(archive[spans[member][0]:spans[member][1]])
        permission_start = member_start + 20 + len(land.bgs)
        for x, z in identity["targets"]:
            archive_offset = permission_start + 2 * (z * 32 + x)
            result.append((member, x, z, archive_offset, rom_start + archive_offset))
    return tuple(result)


def apply(data, language):
    """Apply HG-F09 in memory and return the exact stage receipt."""
    _need(language in LANGUAGES, "unknown invisible-grass language")
    data = bytes(data)
    _rom, file_id, start, end, archive = _rom_archive(data)
    patched = patch_archive(archive)
    _need(len(patched) == end - start, "invisible-grass archive changed size")
    out = data[:start] + patched + data[end:]
    owned = _owned_offsets(archive, start)
    receipt = {
        "schema": 1,
        "stage": "invisible-grass",
        "language": language,
        "input_sha256": _sha256(data),
        "output_sha256": _sha256(out),
        "archive": ARCHIVE,
        "file_id": file_id,
        "rom_slot": [start, end],
        "archive_sha256_before": ARCHIVE_BEFORE_SHA256,
        "archive_sha256_after": ARCHIVE_AFTER_SHA256,
        "edits": [
            {"member": member, "x": x, "z": z, "before": 0x0002, "after": 0x0400,
             "archive_offset": archive_offset, "rom_offset": rom_offset}
            for member, x, z, archive_offset, rom_offset in owned
        ],
    }
    receipt["verification"] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    """Independently re-read the images, members, controls and byte confinement."""
    before, after = bytes(before), bytes(after)
    _need(receipt.get("schema") == 1 and receipt.get("stage") == "invisible-grass",
          "invisible-grass receipt schema or stage differs")
    _need(receipt.get("language") in LANGUAGES,
          "invisible-grass receipt language differs")
    _need(_sha256(before) == receipt.get("input_sha256"),
          "invisible-grass receipt input identity differs")
    _need(_sha256(after) == receipt.get("output_sha256"),
          "invisible-grass receipt output identity differs")
    _need(len(before) == len(after) and before[:HEADER_BYTES] == after[:HEADER_BYTES],
          "invisible-grass changed ROM length or header")

    old_rom, old_id, old_start, old_end, old_archive = _rom_archive(before)
    new_rom, new_id, new_start, new_end, new_archive = _rom_archive(after)
    _need((old_id, old_start, old_end) == (new_id, new_start, new_end),
          "invisible-grass archive FAT identity changed")
    _need(receipt.get("file_id") == old_id
          and receipt.get("rom_slot") == [old_start, old_end],
          "invisible-grass archive FAT identity differs from receipt")
    _need(_sha256(old_archive) == ARCHIVE_BEFORE_SHA256
          and _sha256(new_archive) == ARCHIVE_AFTER_SHA256,
          "invisible-grass archive preimage or postimage differs")
    _need(len(old_rom.files) == len(new_rom.files),
          "invisible-grass NitroFS file count changed")
    for index, (old_file, new_file) in enumerate(zip(old_rom.files, new_rom.files)):
        _need(index == old_id or old_file == new_file,
              "invisible-grass changed unrelated NitroFS file %d" % index)

    old_data, old_spans = _narc_layout(old_archive)
    new_data, new_spans = _narc_layout(new_archive)
    _need((old_data, old_spans) == (new_data, new_spans),
          "invisible-grass NARC geometry changed")
    old_files = ndspy.narc.NARC(old_archive).files
    new_files = ndspy.narc.NARC(new_archive).files
    _need(len(old_files) == len(new_files), "invisible-grass member count changed")
    for index, (old_member, new_member) in enumerate(zip(old_files, new_files)):
        _need(index in LANDS or old_member == new_member,
              "invisible-grass changed unrelated NARC member %d" % index)
    for member in LANDS:
        old_land = _check_land(member, bytes(old_files[member]), "before")
        new_land = _check_land(member, bytes(new_files[member]), "after")
        _need((old_land.bgs, old_land.buildings, old_land.model, old_land.collision)
              == (new_land.bgs, new_land.buildings, new_land.model, new_land.collision),
              "land %d changed non-permission data" % member)
        changed = [index for index, (old, new) in enumerate(
            zip(old_land.permissions, new_land.permissions)) if old != new]
        expected = []
        for x, z in LANDS[member]["targets"]:
            offset = 2 * (z * 32 + x)
            expected.extend((offset, offset + 1))
        _need(changed == expected, "land %d changed permission offsets %r" % (member, changed))

    owned = _owned_offsets(old_archive, old_start)
    expected_rom_offsets = [rom_offset + byte
                            for _member, _x, _z, _archive_offset, rom_offset in owned
                            for byte in (0, 1)]
    _need(_changed_offsets(before, after) == expected_rom_offsets,
          "invisible-grass ROM byte confinement differs")
    expected_edits = [
        {"member": member, "x": x, "z": z, "before": 0x0002, "after": 0x0400,
         "archive_offset": archive_offset, "rom_offset": rom_offset}
        for member, x, z, archive_offset, rom_offset in owned
    ]
    _need(receipt.get("edits") == expected_edits,
          "invisible-grass edit receipt differs")
    _need(receipt.get("archive") == ARCHIVE
          and receipt.get("archive_sha256_before") == ARCHIVE_BEFORE_SHA256
          and receipt.get("archive_sha256_after") == ARCHIVE_AFTER_SHA256,
          "invisible-grass archive receipt differs")
    return {
        "rom_length": len(after),
        "changed_rom_bytes": len(expected_rom_offsets),
        "changed_words": len(owned),
        "changed_members": sorted(LANDS),
        "archive_bytes": len(new_archive),
        "narc_members": len(new_files),
        "nitrofs_files_unchanged": len(old_rom.files) - 1,
        "model_collision_unchanged": True,
    }


def changed_regions(data):
    """Return the two contiguous runs containing the six owned words."""
    data = bytes(data)
    _rom, _file_id, start, _end, archive = _rom_archive(data)
    _need(_sha256(archive) == ARCHIVE_BEFORE_SHA256,
          "invisible-grass regions require the exact archive preimage")
    owned = _owned_offsets(archive, start)
    regions = []
    for member in LANDS:
        offsets = [rom_offset for owned_member, _x, _z, _archive_offset, rom_offset
                   in owned if owned_member == member]
        _need(offsets == list(range(offsets[0], offsets[0] + 2 * len(offsets), 2)),
              "land %d target words are no longer contiguous" % member)
        regions.append((offsets[0], offsets[-1] + 2))
    return tuple(regions)
