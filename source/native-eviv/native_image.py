"""Bounded ARM9/ITCM changes for the identified Community TEST images."""
import struct
from ndspy import _common, rom

PAYLOAD_BASE = 0x01FF8620
ITCM_LIMIT = 0x01FFA000
HOOK_OFFSET = 0x88B40
HOOK_BEFORE = bytes.fromhex('70b56d4a051ca95c')
STATS_OFFSET = 0x8D178
STATS_BEFORE = bytes.fromhex('38b586b000231021')


def require(value, message):
    if not value:
        raise ValueError(message)


def reserve_itcm(main, payload, entry, stats_entry):
    require(len(main.sections) == 3, 'Unexpected autoload sections')
    static, itcm, dtcm = main.sections
    require(static.ramAddress == 0x02000000 and len(static.data) == 0x111860,
            'Unexpected static ARM9 extent')
    require(itcm.ramAddress == 0x01FF8000 and len(itcm.data) == 0x620 and itcm.bssSize == 0,
            'Unexpected ITCM preimage')
    require(dtcm.ramAddress == 0x027E0000 and len(dtcm.data) == 0x60 and dtcm.bssSize == 0x20,
            'Unexpected DTCM preimage')
    require(static.data[HOOK_OFFSET:HOOK_OFFSET + 8] == HOOK_BEFORE, 'Summary hook differs')
    require(static.data[STATS_OFFSET:STATS_OFFSET + 8] == STATS_BEFORE, 'Stats redraw hook differs')
    require(struct.unpack_from('<I', static.data, 0xD2C68)[0] == PAYLOAD_BASE, 'ITCM arena differs')
    end = (PAYLOAD_BASE + len(payload) + 31) & ~31
    require(payload and end <= ITCM_LIMIT, 'Payload exceeds reserved ITCM budget')
    for target in (entry, stats_entry):
        require(target & 1 and PAYLOAD_BASE <= (target & ~1) < PAYLOAD_BASE + len(payload),
                'Thumb entry outside payload')
    # Validate all inputs before modifying the in-memory copy.
    static.data[HOOK_OFFSET:HOOK_OFFSET + 8] = struct.pack('<HHI', 0x4B00, 0x4718, entry)
    static.data[STATS_OFFSET:STATS_OFFSET + 8] = struct.pack('<HHI', 0x4B00, 0x4718, stats_entry)
    struct.pack_into('<I', static.data, 0xD2C68, end)
    itcm.data.extend(payload)
    itcm.data.extend(bytes(end - PAYLOAD_BASE - len(payload)))
    return {'payload_start': PAYLOAD_BASE, 'payload_bytes': len(payload),
            'arena_low_before': PAYLOAD_BASE, 'arena_low_after': end,
            'reserved_bytes': end - PAYLOAD_BASE,
            'hooks': [0x02000000 + HOOK_OFFSET, 0x02000000 + STATS_OFFSET]}


def secure_area_crc(old_area, new_area, old_crc):
    require(len(old_area) == len(new_area) == 0x4000, 'Expected a 16 KiB secure area')
    require(old_area[:0x800] == new_area[:0x800], 'Encrypted secure-area prefix must stay unchanged')
    # The stored CRC covers the encrypted prefix. With an unchanged prefix and
    # equal lengths, XOR of the two CRCs cancels that unknown prefix and seed.
    # Preserve the source relationship without embedding encryption key data.
    return old_crc ^ _common.crc16(old_area) ^ _common.crc16(new_area)


def replace_arm9(source, new_arm9):
    parsed = rom.NintendoDSRom(source)
    start, old_size = struct.unpack_from('<I', source, 0x20)[0], len(parsed.arm9)
    require(start == 0x4000 and len(new_arm9) >= 0x4000, 'Unexpected secure-area placement')
    require(len(new_arm9) <= old_size, 'ARM9 must fit in its original ROM extent')
    crc = secure_area_crc(parsed.arm9[:0x4000], new_arm9[:0x4000], parsed.secureAreaChecksum)
    result = bytearray(source)
    data = bytes(new_arm9) + parsed.arm9PostData
    result[start:start + len(data)] = data
    struct.pack_into('<I', result, 0x2C, len(new_arm9))
    struct.pack_into('<H', result, 0x6C, crc)
    struct.pack_into('<H', result, 0x15E, _common.crc16(result[:0x15E]))
    return bytes(result)
