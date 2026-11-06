"""Repair the HGSS compact-position contract of ``BagView_SetItem``.

The retail function ignores its fourth argument and uses ``pocketId`` both as
the display index and as the stored identity.  A single-pocket Berries view
therefore writes entry four although its compact view contains entry zero.

The corrected Thumb-1 setter needs two more bytes.  Its immediately adjacent
bit setter is equivalently encoded in twelve rather than twenty bytes and is
moved from 0x020778C8 to 0x020778CA; its sole direct BL is retargeted.  No
resident reserve, archive, save layout, or ROM geometry changes.
"""
import hashlib

from sgp12.rom import Arm9, bl_decode, bl_thumb


LANGUAGES = ('EN', 'IT')
SETTER = 0x020778BC
BODY_BYTES = 32
ORIGINAL_FLAG_SETTER = 0x020778C8
FLAG_SETTER = 0x020778CA
FLAG_CALL = 0x0203E442
PREIMAGE = bytes.fromhex(
    '0c235343c018416002737047011c76310a88012176308a430121114301807047')
PREIMAGE_SHA256 = '4493fe313b601f01f35c23bbbba5c99682d25ba731bbb753262f66a69ef462c6'
POSTIMAGE = bytes.fromhex(
    '9b00c0185b00c018416002737047'
    '012176300288114301807047'
    'c046c046c046')
POSTIMAGE_SHA256 = 'ef3ce32175d2dd41a97f6eb8ea32fc757c1511e4f273e55556c9998f35073947'
CALL_PREIMAGE = bytes.fromhex('39f041fa')
CALL_POSTIMAGE = bytes.fromhex('39f042fa')


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(condition, message):
    if not condition:
        raise ValueError('BagView position: ' + message)


def _preimage(arm):
    body = arm.leggi(SETTER, BODY_BYTES)
    call = arm.leggi(FLAG_CALL, 4)
    _need(body == PREIMAGE and _sha(body) == PREIMAGE_SHA256,
          'setter/adjacent preimage differs')
    _need(call == CALL_PREIMAGE
          and bl_decode(FLAG_CALL, call) == ORIGINAL_FLAG_SETTER,
          'adjacent flag call preimage differs')
    return body, call


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    arm = Arm9.from_bytes(data)
    before_body, before_call = _preimage(arm)
    _need(bl_thumb(FLAG_CALL, FLAG_SETTER) == CALL_POSTIMAGE,
          'retarget encoding drift')
    arm.scrivi(SETTER, POSTIMAGE)
    arm.scrivi(FLAG_CALL, CALL_POSTIMAGE)
    result = bytes(arm.raw)
    receipt = {
        'schema': 1,
        'stage': 'bag-view-position',
        'language': language,
        'input_sha256': _sha(data),
        'output_sha256': _sha(result),
        'setter_address': SETTER,
        'body_bytes': BODY_BYTES,
        'preimage_sha256': _sha(before_body),
        'postimage_sha256': _sha(POSTIMAGE),
        'flag_call_address': FLAG_CALL,
        'flag_call_preimage': before_call.hex(),
        'flag_call_postimage': CALL_POSTIMAGE.hex(),
        'flag_setter_address': FLAG_SETTER,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt


def verify(before, after, receipt):
    _need(type(before) is bytes and type(after) is bytes
          and len(before) == len(after), 'image geometry')
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    old_body, old_call = _preimage(old)
    post = new.leggi(SETTER, BODY_BYTES)
    call = new.leggi(FLAG_CALL, 4)
    _need(post == POSTIMAGE and _sha(post) == POSTIMAGE_SHA256,
          'installed body readback')
    _need(call == CALL_POSTIMAGE
          and bl_decode(FLAG_CALL, call) == FLAG_SETTER,
          'adjacent flag call readback')

    restored = bytearray(after)
    for address, original in ((SETTER, old_body), (FLAG_CALL, old_call)):
        at = new.off(address, len(original))
        restored[at:at + len(original)] = original
    _need(bytes(restored) == before, 'bytes changed outside declared spans')

    report = {
        'ok': True,
        'position_indexed': True,
        'pocket_identity_preserved': True,
        'flag_call_target': FLAG_SETTER,
        'body_bytes': BODY_BYTES,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1,
        'stage': 'bag-view-position',
        'input_sha256': _sha(before),
        'output_sha256': _sha(after),
        'setter_address': SETTER,
        'body_bytes': BODY_BYTES,
        'preimage_sha256': PREIMAGE_SHA256,
        'postimage_sha256': POSTIMAGE_SHA256,
        'flag_call_address': FLAG_CALL,
        'flag_call_preimage': CALL_PREIMAGE.hex(),
        'flag_call_postimage': CALL_POSTIMAGE.hex(),
        'flag_setter_address': FLAG_SETTER,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    from . import baseline
    expected_language = baseline.INPUT_HASHES.get(_sha(before))
    allowed = set(required) | {'language'}
    if isinstance(receipt, dict) and 'verification' in receipt:
        allowed.add('verification')
    _need(isinstance(receipt, dict)
          and set(receipt) == allowed
          and receipt.get('language') in LANGUAGES
          and (expected_language is None or receipt.get('language') == expected_language)
          and ('verification' not in receipt or receipt['verification'] == report)
          and all(receipt.get(key) == value for key, value in required.items()),
          'receipt identity')
    return report


def spans(data):
    arm = Arm9.from_bytes(bytes(data))
    body = arm.off(SETTER, BODY_BYTES)
    call = arm.off(FLAG_CALL, 4)
    return ((body, body + BODY_BYTES), (call, call + 4))
