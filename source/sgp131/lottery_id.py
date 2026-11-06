"""Repair the HGSS persisted Lottery Number high-half destination.

Retail ``Save_VarsFlags_SetLotoId`` writes both halves to variable 0x403C.
The adjacent getter already owns a literal for the intended high variable
0x403D, so one Thumb literal-load halfword can reuse it.  No code is moved and
the save layout is unchanged.
"""
import hashlib
import struct

from sgp12.rom import Arm9


LANGUAGES = ('EN', 'IT')
SETTER = 0x02066CAC
CONTEXT_BYTES = 0x48
PATCH = 0x02066CC0
PREIMAGE = bytes.fromhex(
    '38b50c1c22040649120c051cfff7e0fe220c12040249281c120cfff7d9fe38bd'
    '3c40000038b50649051cfff7e9fe041c0449281cfff7e4fe0004204338bdc046'
    '3c4000003d400000')
POSTIMAGE = bytes.fromhex(
    '38b50c1c22040649120c051cfff7e0fe220c12040b49281c120cfff7d9fe38bd'
    '3c40000038b50649051cfff7e9fe041c0449281cfff7e4fe0004204338bdc046'
    '3c4000003d400000')
PREIMAGE_SHA256 = '2e0543e2c236b0ebc92e6e5d5ef906c706d1a49643cc53b806a41987ac92efd8'
POSTIMAGE_SHA256 = '730e44d0aa7b1f44f3d7c4874ebbeb600da3ac1ce1dba616e47ee4e2f8e693f9'
PATCH_PREIMAGE = bytes.fromhex('0249')
PATCH_POSTIMAGE = bytes.fromhex('0b49')
VAR_LO, VAR_HI = 0x403C, 0x403D
HI_LITERAL = 0x02066CF0
LANGUAGE_ANCHOR_FILE = 137  # a/0/0/8; no current UI/mechanical stage owns it
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Lottery Number: ' + message)


def _language_anchor(data, language):
    try:
        fat, fat_bytes = struct.unpack_from('<II', data, 0x48)
        _need(fat_bytes % 8 == 0 and fat_bytes // 8 > LANGUAGE_ANCHOR_FILE,
              'language anchor FAT')
        entry = fat + LANGUAGE_ANCHOR_FILE * 8
        _need(0 <= fat <= entry and entry + 8 <= len(data), 'language anchor FAT')
        start, end = struct.unpack_from('<II', data, entry)
        _need(0 <= start < end <= len(data), 'language anchor extent')
    except (struct.error, TypeError):
        raise ValueError('Lottery Number: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')
    return start, end


def _literal(arm, address):
    op = arm.u16(address)
    _need(op & 0xF800 == 0x4800 and (op >> 8) & 7 == 1,
          'patched instruction is not ldr r1 literal')
    literal = ((address + 4) & ~3) + (op & 0xFF) * 4
    return literal, arm.u32(literal)


def _preimage(arm):
    context = arm.leggi(SETTER, CONTEXT_BYTES)
    _need(context == PREIMAGE and _sha(context) == PREIMAGE_SHA256,
          'setter/getter preimage differs')
    _need(arm.leggi(PATCH, 2) == PATCH_PREIMAGE,
          'high-half load preimage differs')
    literal, value = _literal(arm, PATCH)
    _need(value == VAR_LO, 'retail second load does not select low variable')
    return context, literal


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    arm = Arm9.from_bytes(data)
    context, old_literal = _preimage(arm)
    arm.scrivi(PATCH, PATCH_POSTIMAGE)
    result = bytes(arm.raw)
    receipt = {
        'schema': 1,
        'stage': 'lottery-id',
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(result),
        'setter_address': SETTER,
        'patch_address': PATCH,
        'preimage_sha256': _sha(context),
        'postimage_sha256': POSTIMAGE_SHA256,
        'old_literal_address': old_literal,
        'high_literal_address': HI_LITERAL,
        'low_variable': VAR_LO,
        'high_variable': VAR_HI,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, result, receipt, unsealed=True)
    return result, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'image geometry')
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    context, old_literal = _preimage(old)
    post = new.leggi(SETTER, CONTEXT_BYTES)
    _need(post == POSTIMAGE and _sha(post) == POSTIMAGE_SHA256,
          'installed setter/getter readback')
    _need(new.leggi(PATCH, 2) == PATCH_POSTIMAGE,
          'installed high-half load readback')
    literal, value = _literal(new, PATCH)
    _need(literal == HI_LITERAL and value == VAR_HI,
          'high-half load does not select high variable')

    restored = bytearray(after)
    at = new.off(PATCH, 2)
    restored[at:at + 2] = PATCH_PREIMAGE
    _need(bytes(restored) == before, 'bytes changed outside declared halfword')

    report = {
        'ok': True,
        'low_half_destination': VAR_LO,
        'high_half_destination': VAR_HI,
        'patch_bytes': 2,
        'changed_bytes': 1,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt_language = receipt.get('language') if isinstance(receipt, dict) else None
    _need(receipt_language in LANGUAGES, 'receipt identity')
    _language_anchor(before, receipt_language)
    required = {
        'schema': 1,
        'stage': 'lottery-id',
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'setter_address': SETTER,
        'patch_address': PATCH,
        'preimage_sha256': PREIMAGE_SHA256,
        'postimage_sha256': POSTIMAGE_SHA256,
        'old_literal_address': old_literal,
        'high_literal_address': HI_LITERAL,
        'low_variable': VAR_LO,
        'high_variable': VAR_HI,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    from . import baseline
    expected_language = baseline.INPUT_HASHES.get(_sha(before))
    allowed = set(required) | {'language'}
    if not unsealed:
        allowed.add('verification')
    _need(isinstance(receipt, dict)
          and set(receipt) == allowed
          and receipt.get('language') in LANGUAGES
          and (expected_language is None or receipt.get('language') == expected_language)
          and (unsealed or receipt.get('verification') == report)
          and all(receipt.get(key) == value for key, value in required.items()),
          'receipt identity')
    return report


def verify(before, after, receipt):
    return _verify(before, after, receipt, unsealed=False)


def spans(data):
    arm = Arm9.from_bytes(bytes(data))
    start = arm.off(PATCH, 2)
    return ((start, start + 2),)
