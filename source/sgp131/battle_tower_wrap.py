"""Preserve the full Battle Tower round when selecting Frontier opponents.

HGSS stores completed rounds as ``u16`` but narrows them to ``u8`` in both
branches of ``FrontierFieldSystem_SetRandomFrontierTrainers``.  At round 256
(1792 wins) this selects bracket zero again.  The downstream selector already
handles every value >= 7 correctly, so the repair removes only the two caller
narrowings.  Save data, trainer tables and the RNG routine stay unchanged;
the corrected trainer pool may legitimately consume a different number of RNG
draws than the wrapped pool.
"""
import hashlib

from sgp12.rom import Arm9


LANGUAGES = ('EN', 'IT')
CALLER_START, CALLER_END = 0x0204ABC8, 0x0204AC76
CALLER_PREIMAGE_SHA256 = '1e2022313e2fcebeaadb8b5566e70bfec6c44a712beb4be8e2574dca445fbc97'
CALLER_POSTIMAGE_SHA256 = 'd33e21da6f263e5904edb56b2c3a59c2981988d0d5e4fd7e674034d97285bc3a'
SELECTOR_START, SELECTOR_END = 0x0204B73C, 0x0204B7B8
SELECTOR_SHA256 = '116f286bdcd855a0a341b3e88f879c76cd56b115f696e004c2b70c8e6d8501c6'

MULTI_TRUNCATE = 0x0204ABF6
MULTI_PREIMAGE = bytes.fromhex('1006000e')       # lsls r0,r2,#24; lsrs r0,r0,#24
MULTI_POSTIMAGE = bytes.fromhex('101cc046')      # adds r0,r2,#0; nop
SINGLE_SPAN = 0x0204AC4A
SINGLE_PREIMAGE = bytes.fromhex('0906281c090e')  # narrow r1 around an unrelated mov
SINGLE_POSTIMAGE = bytes.fromhex('c046281cc046') # preserve full ldrh value

PATCHES = (
    (MULTI_TRUNCATE, MULTI_PREIMAGE, MULTI_POSTIMAGE),
    (SINGLE_SPAN, SINGLE_PREIMAGE[:2], SINGLE_POSTIMAGE[:2]),
    (SINGLE_SPAN + 4, SINGLE_PREIMAGE[4:], SINGLE_POSTIMAGE[4:]),
)

LANGUAGE_ANCHOR_FILE = 137  # a/0/0/8, unchanged by current mechanics stages
LANGUAGE_ANCHORS = {
    'EN': '60e81902afb23e1949199b582040a69874144e6f29a69e69bbd912e34f0fef82',
    'IT': 'edcfc7fe353c3eaa5405a038365127f500e98c3f0e2c137a08d588d6c901f233',
}


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('Battle Tower wrap: ' + message)


def _language_anchor(data, language):
    import struct
    try:
        fat, fat_bytes = struct.unpack_from('<II', data, 0x48)
        _need(fat_bytes % 8 == 0 and fat_bytes // 8 > LANGUAGE_ANCHOR_FILE,
              'language anchor FAT')
        entry = fat + LANGUAGE_ANCHOR_FILE * 8
        _need(0 <= fat <= entry and entry + 8 <= len(data), 'language anchor FAT')
        start, end = struct.unpack_from('<II', data, entry)
        _need(0 <= start < end <= len(data), 'language anchor extent')
    except (struct.error, TypeError):
        raise ValueError('Battle Tower wrap: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')
    return start, end


def _preimage(arm):
    caller = arm.leggi(CALLER_START, CALLER_END - CALLER_START)
    selector = arm.leggi(SELECTOR_START, SELECTOR_END - SELECTOR_START)
    _need(_sha(caller) == CALLER_PREIMAGE_SHA256, 'caller preimage differs')
    _need(_sha(selector) == SELECTOR_SHA256, 'selector preimage differs')
    for address, preimage, _postimage in PATCHES:
        _need(arm.leggi(address, len(preimage)) == preimage,
              'narrowing preimage differs at %#x' % address)
    return caller


def _patch_receipt():
    return [
        {'address': address, 'before': preimage.hex(), 'after': postimage.hex()}
        for address, preimage, postimage in PATCHES
    ]


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    arm = Arm9.from_bytes(data)
    _preimage(arm)
    for address, _preimage_bytes, postimage in PATCHES:
        arm.scrivi(address, postimage)
    result = bytes(arm.raw)
    receipt = {
        'schema': 1,
        'stage': 'battle-tower-wrap',
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(result),
        'caller_address': CALLER_START,
        'caller_preimage_sha256': CALLER_PREIMAGE_SHA256,
        'caller_postimage_sha256': CALLER_POSTIMAGE_SHA256,
        'selector_sha256': SELECTOR_SHA256,
        'patches': _patch_receipt(),
        'changed_halfwords': 4,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = _verify(data, result, receipt, unsealed=True)
    return result, receipt


def _verify(before, after, receipt, *, unsealed):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'image geometry')
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    _preimage(old)
    _need(_sha(new.leggi(CALLER_START, CALLER_END - CALLER_START))
          == CALLER_POSTIMAGE_SHA256, 'installed caller readback')
    _need(_sha(new.leggi(SELECTOR_START, SELECTOR_END - SELECTOR_START))
          == SELECTOR_SHA256, 'selector changed')
    for address, preimage, postimage in PATCHES:
        _need(old.leggi(address, len(preimage)) == preimage, 'old seam readback')
        _need(new.leggi(address, len(postimage)) == postimage,
              'installed seam readback at %#x' % address)

    restored = bytearray(after)
    changed_bytes = 0
    for address, preimage, postimage in PATCHES:
        at = new.off(address, len(postimage))
        changed_bytes += sum(left != right for left, right in zip(preimage, postimage))
        restored[at:at + len(preimage)] = preimage
    _need(bytes(restored) == before, 'bytes changed outside declared seams')

    report = {
        'ok': True,
        'round_width_bits': 16,
        'patch_spans': len(PATCHES),
        'changed_halfwords': 4,
        'changed_bytes': changed_bytes,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1,
        'stage': 'battle-tower-wrap',
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'caller_address': CALLER_START,
        'caller_preimage_sha256': CALLER_PREIMAGE_SHA256,
        'caller_postimage_sha256': CALLER_POSTIMAGE_SHA256,
        'selector_sha256': SELECTOR_SHA256,
        'patches': _patch_receipt(),
        'changed_halfwords': 4,
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
    _language_anchor(before, receipt.get('language'))
    return report


def verify(before, after, receipt):
    return _verify(before, after, receipt, unsealed=False)


def spans(data):
    arm = Arm9.from_bytes(bytes(data))
    return tuple((arm.off(address, len(postimage)),
                  arm.off(address, len(postimage)) + len(postimage))
                 for address, _preimage, postimage in PATCHES)
