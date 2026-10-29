"""Add native space without moving any existing runtime address.

The 1.2.5 ARM9 cannot grow in its original ROM slot. Insert space after it and
relocate the original tables/files as opaque bytes, preserving even unindexed
padding. ndspy is used for independent readback, never for cartridge repacking.
No resource, overlay or save format changes in this stage.
"""
import hashlib
import struct

import ndspy.code
import ndspy.fnt
import ndspy.rom
from ndspy import _common


RAM = 0x02000000
OLD_BASE = 0x023D8000
BASE = 0x023D0000  # previous development compartment, public addresses stay fixed
RESERVE_BASE = 0x023C8000
END = 0x023E0000
ARENA = 0x020D2BB0
INPUT_HASHES = {
    'a821961fc1a90e4adaa118c4a09fce5445d25d567130d0c9edb20dfb0520050e': 'EN',
    'bdf50a4f327f8ea0d8a2ef312e1491d78460d34e978d9b15d160eaf140b313d4': 'IT',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def expand_arm9(data):
    code = ndspy.code.MainCodeFile(bytes(data), RAM)
    require(code.codeSettingsOffs == 0xBA0, 'unexpected ARM9 module parameters')
    regions = [s for s in code.sections if s.ramAddress == OLD_BASE]
    require(len(regions) == 1 and len(regions[0].data) == END - OLD_BASE
            and regions[0].bssSize == 0, 'unexpected original reserve')
    region = regions[0]
    for section in code.sections:
        if section is region:
            continue
        start = section.ramAddress
        end = start + len(section.data) + section.bssSize
        require(end <= RESERVE_BASE or start >= END, 'autoload overlap with new reserve')
    static = bytearray(code.sections[0].data)
    require(len(static) >= ARENA - RAM + 4, 'missing arena literal')
    require(struct.unpack_from('<I', static, ARENA - RAM)[0] == OLD_BASE,
            'arena literal preimage mismatch')
    struct.pack_into('<I', static, ARENA - RAM, RESERVE_BASE)
    code.sections[0].data = static
    extra = bytearray(OLD_BASE - RESERVE_BASE)
    legacy = BASE - RESERVE_BASE
    struct.pack_into('<4I', extra, legacy, *range(0xCA5A1700, 0xCA5A1704))
    struct.pack_into('<4I', extra, legacy + 0x10, 0x33475053, 1, BASE, END)
    struct.pack_into('<4I', extra, 0, *range(0xCA5A1900, 0xCA5A1904))
    struct.pack_into('<4I', extra, 0x10, 0x33475053, 2, RESERVE_BASE, END)
    for i in range(64):
        struct.pack_into('<I', extra, 0x7F00 + 4 * i, 0xCA5A1A00 | i)
        struct.pack_into('<I', extra, legacy + 0x7F00 + 4 * i, 0xCA5A1800 | i)
    region.ramAddress = RESERVE_BASE
    region.data = extra + region.data
    return code.save(compress=False)


def expand_rom(data):
    before = ndspy.rom.NintendoDSRom(bytes(data))
    expected_files = tuple(hashlib.sha256(x).digest() for x in before.files)
    require(data[0x12] == 0, 'only ordinary DS cartridge headers are supported')
    require(len(before.arm9OverlayTable) % 32 == 0, 'malformed ARM9 overlay table')
    for offset in range(0, len(before.arm9OverlayTable), 32):
        oid, start, size, bss = struct.unpack_from('<4I', before.arm9OverlayTable, offset)
        end = start + size + bss
        require(end <= RESERVE_BASE or start >= END,
                f'overlay {oid} overlap with new reserve')
    old_arm9 = before.arm9
    before.arm9 = expand_arm9(old_arm9)
    arm9_start = struct.unpack_from('<I', data, 0x20)[0]
    cut = arm9_start + len(old_arm9)
    growth = len(before.arm9) - len(old_arm9)
    require(growth == OLD_BASE - RESERVE_BASE, 'unexpected ARM9 growth')
    output = bytearray(data[:arm9_start]) + before.arm9 + data[cut:]
    struct.pack_into('<I', output, 0x2C, len(before.arm9))
    # Header pointers to ARM7, FNT, FAT, y9/y7, banner and debug ROM data.
    for offset in (0x30, 0x40, 0x48, 0x50, 0x58, 0x68, 0x160):
        pointer = struct.unpack_from('<I', data, offset)[0]
        require(not pointer or pointer >= cut, 'unexpected header region before ARM9 end')
        if pointer:
            struct.pack_into('<I', output, offset, pointer + growth)
    used = struct.unpack_from('<I', data, 0x80)[0]
    require(cut <= used <= len(data), 'invalid used ROM length')
    struct.pack_into('<I', output, 0x80, used + growth)
    while (128 * 1024 << output[0x14]) < len(output):
        output[0x14] += 1
    fat, fat_size = struct.unpack_from('<II', output, 0x48)
    require(fat_size % 8 == 0 and fat + fat_size <= len(output), 'invalid FAT')
    for offset in range(fat, fat + fat_size, 4):
        pointer = struct.unpack_from('<I', output, offset)[0]
        require(pointer >= cut, 'unexpected FAT region before ARM9 end')
        struct.pack_into('<I', output, offset, pointer + growth)
    secure_crc = before.secureAreaChecksum ^ _common.crc16(old_arm9[:0x800]) ^ _common.crc16(before.arm9[:0x800])
    struct.pack_into('<H', output, 0x6C, secure_crc)
    struct.pack_into('<H', output, 0x15E, _common.crc16(output[:0x15E]))
    after = ndspy.rom.NintendoDSRom(output)
    require(tuple(hashlib.sha256(x).digest() for x in after.files) == expected_files,
            'repacking changed a file or its ID')
    for field in ('arm7', 'arm9OverlayTable', 'arm7OverlayTable', 'iconBanner',
                  'arm9EntryAddress', 'arm9RamAddress', 'arm7EntryAddress',
                  'arm7RamAddress', 'arm9PostData'):
        require(getattr(after, field) == getattr(before, field),
                'repacking changed ' + field)
    require(ndspy.fnt.save(after.filenames) == ndspy.fnt.save(before.filenames),
            'repacking changed filenames')
    require(after.arm9 == before.arm9, 'repacking changed expanded ARM9')
    return bytes(output)


def identify(data):
    digest = hashlib.sha256(data).hexdigest()
    require(digest in INPUT_HASHES, 'input must be an exact supported 1.2.5 ROM')
    return INPUT_HASHES[digest]
