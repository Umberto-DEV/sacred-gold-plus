"""Restore the GB evolution sequence after returning from Pokemon Summary.

HGSS loads the GB counterpart of the evolution music dynamically.  Pokemon
Summary restores sound-heap state 4 and evicts that material, while the
evolution state machine does not start the sequence again on return.  The
confined wrapper preserves the native cleanup helper and reloads sequence 1011
only when the GB Sounds flag is exactly one; the existing dispatcher then maps
it to sequence 1223.

The hook and 32-byte wrapper are inside the existing ARM9 image.  ROM geometry,
save data and sound tables are unchanged.
"""
import hashlib
import struct

from sgp12.rom import Arm9, bl_decode, bl_thumb


LANGUAGES = ('EN', 'IT')
STAGE = 'gb-sounds-evolution'

HOOK = 0x020767BC
HOOK_PREIMAGE = bytes.fromhex('c4f760f8')

SLOT = 0x023D8AA8
SLOT_BYTES = 32
SLOT_PREIMAGE = bytes(SLOT_BYTES)
ORIGINAL_HELPER = 0x0203A880
GB_STATE = 0x02005C18
START_SEQUENCE = 0x02005D10
SEQ_GS_SHINKA = 1011

PRECEDING_CANARY = 0x023D8A98
PRECEDING_CANARY_BYTES = bytes.fromhex(
    '00115aca01115aca02115aca03115aca')
FREE_TAIL = SLOT + SLOT_BYTES
FREE_TAIL_BYTES = 56
NEXT_OWNER = 0x023D8B00
NEXT_OWNER_PREFIX = bytes.fromhex('f0b587b0274a1168491c116001210902')

LANGUAGE_ANCHOR_FILE = 137
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('GB Sounds evolution: ' + message)


def _payload():
    body = (
        bytes.fromhex('08b5')                    # push {r3,lr}; 8-byte SP
        + bl_thumb(SLOT + 2, ORIGINAL_HELPER)     # preserve native cleanup
        + bl_thumb(SLOT + 6, GB_STATE)            # current GB Sounds flag
        + bytes.fromhex('012802d10248')           # cmp 1; bne done; ldr seq
        + bl_thumb(SLOT + 16, START_SEQUENCE)     # reload through dispatcher
        + bytes.fromhex('08bdc046f3030000')       # pop; align; literal 1011
        + bytes(4)
    )
    _need(len(body) == SLOT_BYTES, 'wrapper length')
    _need(bl_decode(SLOT + 2, body[2:6]) == ORIGINAL_HELPER,
          'native-helper branch encoding')
    _need(bl_decode(SLOT + 6, body[6:10]) == GB_STATE,
          'GB-state branch encoding')
    _need(bl_decode(SLOT + 16, body[16:20]) == START_SEQUENCE,
          'StartSequence branch encoding')
    return body


SLOT_POSTIMAGE = _payload()
SLOT_POST_SHA256 = 'c31572585dc8f2c361ebf3dbfe3ed2f7519e229a66ce99e4491ad7cead1c056a'
HOOK_POSTIMAGE = bl_thumb(HOOK, SLOT)


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
        raise ValueError('GB Sounds evolution: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')


def _boundaries(arm):
    _need(arm.leggi(PRECEDING_CANARY, len(PRECEDING_CANARY_BYTES))
          == PRECEDING_CANARY_BYTES, 'preceding camera canary changed')
    _need(arm.leggi(FREE_TAIL, FREE_TAIL_BYTES) == bytes(FREE_TAIL_BYTES),
          'remaining free tail changed')
    _need(arm.leggi(NEXT_OWNER, len(NEXT_OWNER_PREFIX)) == NEXT_OWNER_PREFIX,
          'following owner changed')


def _preimage(arm):
    _need(arm.leggi(HOOK, len(HOOK_PREIMAGE)) == HOOK_PREIMAGE,
          'hook preimage differs')
    _need(arm.leggi(SLOT, SLOT_BYTES) == SLOT_PREIMAGE,
          'resident slot is not empty')
    _boundaries(arm)


def _postimage(arm):
    _need(arm.leggi(HOOK, len(HOOK_POSTIMAGE)) == HOOK_POSTIMAGE,
          'hook postimage differs')
    _need(bl_decode(HOOK, HOOK_POSTIMAGE) == SLOT, 'hook target differs')
    slot = arm.leggi(SLOT, SLOT_BYTES)
    _need(slot == SLOT_POSTIMAGE and _sha(slot) == SLOT_POST_SHA256,
          'resident wrapper differs')
    _boundaries(arm)


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    arm = Arm9.from_bytes(data)
    _preimage(arm)
    arm.scrivi(HOOK, HOOK_POSTIMAGE)
    arm.scrivi(SLOT, SLOT_POSTIMAGE)
    out = bytes(arm.raw)
    receipt = {
        'schema': 1,
        'stage': STAGE,
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(out),
        'hook_address': HOOK,
        'hook_preimage': HOOK_PREIMAGE.hex(),
        'hook_postimage': HOOK_POSTIMAGE.hex(),
        'slot_address': SLOT,
        'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': _sha(SLOT_PREIMAGE),
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'sequence': SEQ_GS_SHINKA,
        'gb_off_unchanged': True,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, out, receipt, unsealed=True)
    return out, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'ROM geometry')
    language = receipt.get('language') if isinstance(receipt, dict) else None
    _language_anchor(before, language)
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    _preimage(old)
    _postimage(new)

    restored = bytearray(after)
    hook_at = old.off(HOOK, len(HOOK_PREIMAGE))
    slot_at = old.off(SLOT, SLOT_BYTES)
    restored[hook_at:hook_at + len(HOOK_PREIMAGE)] = HOOK_PREIMAGE
    restored[slot_at:slot_at + SLOT_BYTES] = SLOT_PREIMAGE
    _need(bytes(restored) == before, 'bytes changed outside hook and slot')

    report = {
        'ok': True,
        'sequence_reloaded_only_with_gb_sounds': SEQ_GS_SHINKA,
        'native_cleanup_preserved': True,
        'changed_bytes': sum(a != b for a, b in zip(before, after)),
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1,
        'stage': STAGE,
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'hook_address': HOOK,
        'hook_preimage': HOOK_PREIMAGE.hex(),
        'hook_postimage': HOOK_POSTIMAGE.hex(),
        'slot_address': SLOT,
        'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': _sha(SLOT_PREIMAGE),
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'sequence': SEQ_GS_SHINKA,
        'gb_off_unchanged': True,
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
    hook = arm.off(HOOK, len(HOOK_PREIMAGE))
    slot = arm.off(SLOT, SLOT_BYTES)
    return ((hook, hook + len(HOOK_PREIMAGE)), (slot, slot + SLOT_BYTES))
