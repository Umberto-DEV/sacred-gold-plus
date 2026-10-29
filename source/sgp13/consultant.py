"""Build a dedicated orange Mart consultant from the owner's native texture.

Only transformation rules and preimage hashes are public. Original deliverymen,
all animation frames and every existing archive member retain their bytes.
"""
import hashlib
import struct

SPRITE_ID = 194
MODEL_ARCHIVE = 'a/0/8/1'
SOURCE_MEMBER = 56
SOURCE_SHA = '8553e8c87e65b20cb06b36a4148a76f245a7dd629a5bca10b63fc7d1a31a293f'
TABLE_ADDRESS = 0x022074A8
TABLE_SIZE = 902 * 6
TABLE_SHA = '5b2515a8781ce60c829abd00df88ae1c0ce32ef89287563270c641f21d00276e'
HOOKS = ((0x021F92DC, '08b5074b07491a88', 'training_sprite'),
         (0x021FA248, '08b50d4b0d491a88', 'training_sprite_category'))


def orange_delivery(data):
    """Change two uniform colors in a guarded copy, keeping packed frames exact."""
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA:
        raise ValueError('consultant native Delivery texture preimage')
    out = bytearray(data)
    # The guarded BTX0/TEX0 has one 16-color palette at the end. Hair, skin,
    # parcel, shoes and transparency retain the native palette entries.
    for index, before, after in ((2, 0x2A4C, 27 | (14 << 5) | (3 << 10)),
                                 (4, 0x2947, 16 | (6 << 5) | (2 << 10))):
        offset = len(out) - 32 + index * 2
        if struct.unpack_from('<H', out, offset)[0] != before:
            raise ValueError('consultant uniform palette preimage')
        struct.pack_into('<H', out, offset, after)
    return bytes(out)


def prepare(arm, models, events):
    """Validate native lookup/data ownership before appending one texture."""
    from sgp12.rom import Rom
    v, _, overlay = Rom(arm.raw).immagine_overlay(1)
    table = overlay[TABLE_ADDRESS-v['ram']:TABLE_ADDRESS-v['ram']+TABLE_SIZE]
    if hashlib.sha256(table).hexdigest() != TABLE_SHA:
        raise ValueError('consultant native sprite table preimage')
    records = list(struct.iter_unpack('<3H', table))
    if records[-1][0] != 65535 or any(r[0] == SPRITE_ID for r in records):
        raise ValueError('consultant sprite ID already registered')
    for address, expected, _ in HOOKS:
        if overlay[address-v['ram']:address-v['ram']+8] != bytes.fromhex(expected):
            raise ValueError('consultant native lookup preimage')
    object_count = 0
    for member in events.files:
        if len(member) < 4:
            raise ValueError('consultant event header bounds')
        off = 4 + 20 * struct.unpack_from('<I', member)[0]
        if off+4 > len(member):
            raise ValueError('consultant event object bounds')
        count = struct.unpack_from('<I', member, off)[0]
        if off+4+32*count > len(member):
            raise ValueError('consultant event object count bounds')
        object_count += count
        for i in range(count):
            if struct.unpack_from('<H', member, off+4+32*i+2)[0] == SPRITE_ID:
                raise ValueError('consultant sprite ID already used in an event')
    if len(models.files) != 863:
        raise ValueError('consultant model archive preimage count')
    member_id = len(models.files)
    models.files.append(orange_delivery(models.files[SOURCE_MEMBER]))
    return dict(sprite=SPRITE_ID, member=member_id, source_member=SOURCE_MEMBER,
                native_sprite_records=len(records)-1, checked_event_objects=object_count,
                texture_bytes=len(models.files[-1]), palette_entries_changed=[2, 4])


def patch_overlay(raw, symbols):
    from sgp12.rom import Rom
    from sgp12.blz import blz_comprimi_ottimo
    from sgp13.resources import append_file
    from sgp13.training import entry_hook
    v, _, before = Rom(raw).immagine_overlay(1)
    after = bytearray(before)
    for address, expected, name in HOOKS:
        off = address-v['ram']
        if after[off:off+8] != bytes.fromhex(expected):
            raise ValueError('consultant lookup patch preimage')
        after[off:off+8] = entry_hook(address, symbols[name])
    compressed = blz_comprimi_ottimo(bytes(after))
    if isinstance(compressed, tuple):
        compressed = compressed[0]
    result = bytearray(append_file(raw, v['file_id'], compressed))
    struct.pack_into('<I', result, v['offset_voce']+28,
                     (v['parola_comp'] & 0xff000000) | len(compressed))
    if Rom(result).immagine_overlay(1)[2] != after:
        raise ValueError('consultant lookup readback')
    return result
