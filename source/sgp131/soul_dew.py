"""Repair the HGSS Soul Dew clause when custom rules use ``totalLevel``.

Rule 13 is a flag stored in bit 15 of the same halfword that carries the
custom total-level limit.  Retail returns that whole halfword, while all six
battle consumers compare the result with exactly ``0x8000``.  The confined
successor keeps the getter contract for every other rule and returns only the
Soul Dew bit for rule 13.

The hook and its 32-byte resident slot are inside the existing ARM9 image.
No file geometry, save field, item data or battle consumer is changed.
"""
import hashlib
import struct

from sgp12.rom import Arm9, bl_decode, bl_thumb


LANGUAGES = ('EN', 'IT')
STAGE = 'soul-dew'

GETTER = 0x020290FC
GETTER_BYTES = 0xA8
GETTER_PRE_SHA256 = '97f7a4ea5da6db18d5620b28ce1ab63973fd6da599970d28df6d3d06b97f74ec'
GETTER_POST_SHA256 = 'f2fe42cde1d57b1036c1cb4b51b2bb4660049836c88018ed5dfa4e1fdb9cdca5'
HOOK_PREIMAGE = bytes.fromhex('00220d294bd84918')

SLOT = 0x023DEB00
SLOT_BYTES = 32
SLOT_PREIMAGE = bytes(SLOT_BYTES)
PAYLOAD = bytes.fromhex(
    '0d2903d8'  # cmp rule,13; invalid rules return zero
    '04d00022'  # rule 13 enters the mask path; ordinary rules restore r2
    '49187047'  # ordinary rules restore rule*2 and return to the getter
    '00201847'  # invalid rule: r0=0 and return directly to the caller
    '008bc00b'  # rule 13: load totalLevel and shift away bits 0..14
    'c0031847') # restore bit 15 and return directly to the caller
SLOT_POSTIMAGE = PAYLOAD + bytes(SLOT_BYTES - len(PAYLOAD))
SLOT_POST_SHA256 = '6d3058d72601386741090255c586f2388052a0cf16b77a1cf8adcdc42ee74d5a'

CANARY = 0x023DEB40
CANARY_BYTES = 32
CANARY_PREIMAGE = bytes.fromhex(
    '00005aca01005aca02005aca03005aca04005aca05005aca06005aca07005aca')

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Soul Dew: ' + message)


def _hook_postimage():
    hook = bytes.fromhex('7346') + bl_thumb(GETTER + 2, SLOT) + bytes.fromhex('9e46')
    _need(hook == bytes.fromhex('7346b5f3fffc9e46'), 'hook encoding drift')
    return hook


HOOK_POSTIMAGE = _hook_postimage()


def _language_anchor(data, language):
    try:
        fat, fat_bytes = struct.unpack_from('<II', data, 0x48)
        _need(fat_bytes % 8 == 0 and fat_bytes // 8 > LANGUAGE_ANCHOR_FILE,
              'language anchor FAT')
        entry = fat + LANGUAGE_ANCHOR_FILE * 8
        _need(0 <= fat <= entry and entry + 8 <= len(data),
              'language anchor FAT')
        start, end = struct.unpack_from('<II', data, entry)
        _need(0 <= start < end <= len(data), 'language anchor extent')
    except (struct.error, TypeError):
        raise ValueError('Soul Dew: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')


def _preimage(arm):
    getter = arm.leggi(GETTER, GETTER_BYTES)
    _need(_sha(getter) == GETTER_PRE_SHA256, 'getter preimage differs')
    _need(getter[:len(HOOK_PREIMAGE)] == HOOK_PREIMAGE,
          'hook preimage differs')
    _need(arm.leggi(SLOT, SLOT_BYTES) == SLOT_PREIMAGE,
          'resident slot is not empty')
    _need(arm.leggi(CANARY, CANARY_BYTES) == CANARY_PREIMAGE,
          'following canary differs')


def _postimage(arm):
    getter = arm.leggi(GETTER, GETTER_BYTES)
    _need(_sha(getter) == GETTER_POST_SHA256, 'getter postimage differs')
    _need(getter[:len(HOOK_POSTIMAGE)] == HOOK_POSTIMAGE,
          'hook postimage differs')
    _need(bl_decode(GETTER + 2, HOOK_POSTIMAGE[2:6]) == SLOT,
          'hook target differs')
    slot = arm.leggi(SLOT, SLOT_BYTES)
    _need(slot == SLOT_POSTIMAGE and _sha(slot) == SLOT_POST_SHA256,
          'resident payload differs')
    _need(arm.leggi(CANARY, CANARY_BYTES) == CANARY_PREIMAGE,
          'following canary changed')


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    arm = Arm9.from_bytes(data)
    _preimage(arm)
    arm.scrivi(GETTER, HOOK_POSTIMAGE)
    arm.scrivi(SLOT, SLOT_POSTIMAGE)
    out = bytes(arm.raw)
    receipt = {
        'schema': 1,
        'stage': STAGE,
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(out),
        'getter_address': GETTER,
        'getter_preimage_sha256': GETTER_PRE_SHA256,
        'getter_postimage_sha256': GETTER_POST_SHA256,
        'hook_preimage': HOOK_PREIMAGE.hex(),
        'hook_postimage': HOOK_POSTIMAGE.hex(),
        'slot_address': SLOT,
        'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': _sha(SLOT_PREIMAGE),
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'canary_address': CANARY,
        'canary_sha256': _sha(CANARY_PREIMAGE),
        'rules_0_12_unchanged': True,
        'invalid_rule_unchanged': True,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'ROM geometry')
    _language_anchor(before, receipt.get('language') if isinstance(receipt, dict) else None)
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    _preimage(old)
    _postimage(new)

    restored = bytearray(after)
    hook_at = old.off(GETTER, len(HOOK_PREIMAGE))
    slot_at = old.off(SLOT, SLOT_BYTES)
    restored[hook_at:hook_at + len(HOOK_PREIMAGE)] = HOOK_PREIMAGE
    restored[slot_at:slot_at + SLOT_BYTES] = SLOT_PREIMAGE
    _need(bytes(restored) == before, 'bytes changed outside hook and slot')

    report = {
        'ok': True,
        'rule_13_mask': 'totalLevel & 0x8000',
        'rules_0_12_unchanged': True,
        'invalid_rule_unchanged': True,
        'changed_bytes': sum(a != b for a, b in zip(before, after)),
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1,
        'stage': STAGE,
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'getter_address': GETTER,
        'getter_preimage_sha256': GETTER_PRE_SHA256,
        'getter_postimage_sha256': GETTER_POST_SHA256,
        'hook_preimage': HOOK_PREIMAGE.hex(),
        'hook_postimage': HOOK_POSTIMAGE.hex(),
        'slot_address': SLOT,
        'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': _sha(SLOT_PREIMAGE),
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'canary_address': CANARY,
        'canary_sha256': _sha(CANARY_PREIMAGE),
        'rules_0_12_unchanged': True,
        'invalid_rule_unchanged': True,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    allowed = set(required) | {'language'}
    if not unsealed:
        allowed.add('verification')
    _need(isinstance(receipt, dict) and set(receipt) == allowed
          and receipt.get('language') in LANGUAGES
          and (unsealed or receipt.get('verification') == report)
          and all(receipt.get(key) == value for key, value in required.items()),
          'receipt identity')
    return report


def verify(before, after, receipt):
    return _verify(before, after, receipt, unsealed=False)


def spans(data):
    arm = Arm9.from_bytes(bytes(data))
    hook = arm.off(GETTER, len(HOOK_PREIMAGE))
    slot = arm.off(SLOT, SLOT_BYTES)
    return ((hook, hook + len(HOOK_PREIMAGE)), (slot, slot + SLOT_BYTES))
