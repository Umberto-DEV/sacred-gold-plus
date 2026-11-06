"""Close HG-SEC01 decoration writes without constructing a Wonder Card.

The tag-6 check validates all three decoration domains.  The seal check/write
leaves share a resident unsigned 1..80 guard, while the existing fashion and
background bounds become fail-closed instead of asserting and continuing.
Direct ``give`` dispatch still queues the gift as received, matching retail;
it can no longer mutate a decoration object for an invalid ID.
"""
import hashlib
import struct

from sgp12.rom import Arm9


LANGUAGES = ('EN', 'IT')
STAGE = 'wonder-card-decoration-guard'

MG_CHECK = 0x0204C550
MG_CHECK_BYTES = 54
MG_CHECK_PREIMAGE = bytes.fromhex(
    '38b5051cfff71afc44680068012804d002280ad003280ad00be0e868e0f73cfb'
    '211c0122e0f7e2fb38bd012038bd012038bd002038bd')
MG_CHECK_POSTIMAGE = bytes.fromhex(
    '38b5051cfff71afc44680068211c92f3dffa002807d0012807d1e868211c0122'
    'e0f7e4fb38bd002038bd012038bdc046c046c046c046')
MG_CHECK_PRE_SHA256 = 'bd710bd718c640c829ec006bc7f1b3ea769ae5e9f8658f31b4b0c42789753551'
MG_CHECK_POST_SHA256 = 'f1b69f60b8375ed160b608dce87075c17efd50cef8681943ee2f61215f531cd6'

MG_GIVE = 0x0204C588
MG_GIVE_BYTES = 80
MG_GIVE_PREIMAGE = bytes.fromhex(
    '38b5051cfff7fefb44680068012804d002280ad0032812d038bde868e0f720fb'
    '211c0122e0f77efb38bde868dff738fddff712fa211c0122dff7a2fa38bde868'
    'dff72efddff708fa211cdff701fb38bd')
MG_GIVE_POSTIMAGE = bytes.fromhex(
    '38b5051cfff7fefb44680068211c92f3c3fa002819d0012807d1e868e0f720fb'
    '211c0122e0f77efb0fe00090e868dff737fddff711fa211c009b022b03d10122'
    'dff79efa01e0dff703fb38bdc046c046')
MG_GIVE_PRE_SHA256 = '19e3fa0d24e52efba9cd02e0ce6dbef3ebe0193393518b2bd64b94b08f2a062e'
MG_GIVE_POST_SHA256 = '2f37b67ba194802c1eaf18ddacdaf3162e3e14a3a8d4690acea7afb02ee16bb0'

FASHION_ASSERT = 0x0202BB14
FASHION_PREIMAGE = bytes.fromhex('f9f702fd')
FASHION_POSTIMAGE = bytes.fromhex('70bdc046')
BACKGROUND_ASSERT = 0x0202BBE2
BACKGROUND_PREIMAGE = bytes.fromhex('f9f79bfc')
BACKGROUND_POSTIMAGE = bytes.fromhex('38bdc046')

SEAL_GIVE = 0x0202CCAC
SEAL_GIVE_BYTES = 62
SEAL_GIVE_PREIMAGE = bytes.fromhex(
    '70b50d1c691e061c141cfff7e1ff122109017218691e535cc018002c05dae018'
    '01d4505409e0002070bd0019632802dc1819505401e0002070bd012070bd')
SEAL_GIVE_POSTIMAGE = bytes.fromhex(
    '70b54d1e4f2d16d8061c141c291cfff7dfff122109017218535dc018002c03da'
    'e01808d4505504e00019632803dc18195055012070bd002070bdc046c046')
SEAL_GIVE_PRE_SHA256 = 'f4a1a78d0d2003f2038eee08f71cafd51e5422414adace599070d785790630a3'
SEAL_GIVE_POST_SHA256 = 'ff64300fea51e557817f2e7be48e5a0a9c9f6ca3ec546bb1abcd48ca7555167f'

SEAL_CHECK = 0x0202CD3C
SEAL_CHECK_BYTES = 56
SEAL_CHECK_PREIMAGE = bytes.fromhex(
    '70b50d1c691e061c141cfff799ff691e721812210901515c4018002c05da6018'
    '01d4012070bd002070bd0019632801dc012070bd002070bd')
SEAL_CHECK_POSTIMAGE = bytes.fromhex(
    '70b54d1e4f2d13d8061c141c291cfff797ff122109017218515d4018002c02da'
    '601805d402e00019632801dc012070bd002070bdc046c046')
SEAL_CHECK_PRE_SHA256 = 'c5a9ab1d64119b27e45843e603ff893d48e2ef64421983293b70a4297ea7d09c'
SEAL_CHECK_POST_SHA256 = '9ad19796e5d17b039ba19fc383b938d2c8334eb2be9cff43b9d40a9d360d7130'

SLOT = 0x023DEB20
SLOT_BYTES = 32
SLOT_PREIMAGE = bytes(SLOT_BYTES)
SLOT_POSTIMAGE = bytes.fromhex(
    '0138022808d8002800d1013903a2125c914201d2013070470020704750641200')
SLOT_PRE_SHA256 = '66687aadf862bd776c8fc18b8e9f8e20089714856ee233b3902a591d0d5f2925'
SLOT_POST_SHA256 = 'af59b15d230076aeb77856c5d155fae00729ab89ae3949287ba44fd46be9c6e2'

CANARY = 0x023DEB40
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
        raise ValueError('Wonder Card: ' + message)


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
        raise ValueError('Wonder Card: language anchor geometry') from None
    _need(_sha(data[start:end]) == LANGUAGE_ANCHORS.get(language),
          'language anchor mismatch')


def _preimage(arm):
    check = arm.leggi(MG_CHECK, MG_CHECK_BYTES)
    _need(check == MG_CHECK_PREIMAGE and _sha(check) == MG_CHECK_PRE_SHA256,
          'MG check preimage differs')
    give = arm.leggi(MG_GIVE, MG_GIVE_BYTES)
    _need(give == MG_GIVE_PREIMAGE and _sha(give) == MG_GIVE_PRE_SHA256,
          'MG give preimage differs')
    _need(arm.leggi(FASHION_ASSERT, 4) == FASHION_PREIMAGE,
          'fashion leaf preimage differs')
    _need(arm.leggi(BACKGROUND_ASSERT, 4) == BACKGROUND_PREIMAGE,
          'background leaf preimage differs')
    seal_give = arm.leggi(SEAL_GIVE, SEAL_GIVE_BYTES)
    _need(seal_give == SEAL_GIVE_PREIMAGE
          and _sha(seal_give) == SEAL_GIVE_PRE_SHA256,
          'seal-give preimage differs')
    seal_check = arm.leggi(SEAL_CHECK, SEAL_CHECK_BYTES)
    _need(seal_check == SEAL_CHECK_PREIMAGE
          and _sha(seal_check) == SEAL_CHECK_PRE_SHA256,
          'seal-check preimage differs')
    _need(arm.leggi(SLOT, SLOT_BYTES) == SLOT_PREIMAGE,
          'resident slot is not empty')
    _need(arm.leggi(CANARY, len(CANARY_PREIMAGE)) == CANARY_PREIMAGE,
          'following canary differs')


def _postimage(arm):
    check = arm.leggi(MG_CHECK, MG_CHECK_BYTES)
    _need(check == MG_CHECK_POSTIMAGE and _sha(check) == MG_CHECK_POST_SHA256,
          'MG check postimage differs')
    give = arm.leggi(MG_GIVE, MG_GIVE_BYTES)
    _need(give == MG_GIVE_POSTIMAGE and _sha(give) == MG_GIVE_POST_SHA256,
          'MG give postimage differs')
    _need(arm.leggi(FASHION_ASSERT, 4) == FASHION_POSTIMAGE,
          'fashion leaf postimage differs')
    _need(arm.leggi(BACKGROUND_ASSERT, 4) == BACKGROUND_POSTIMAGE,
          'background leaf postimage differs')
    seal_give = arm.leggi(SEAL_GIVE, SEAL_GIVE_BYTES)
    _need(seal_give == SEAL_GIVE_POSTIMAGE
          and _sha(seal_give) == SEAL_GIVE_POST_SHA256,
          'seal-give postimage differs')
    seal_check = arm.leggi(SEAL_CHECK, SEAL_CHECK_BYTES)
    _need(seal_check == SEAL_CHECK_POSTIMAGE
          and _sha(seal_check) == SEAL_CHECK_POST_SHA256,
          'seal-check postimage differs')
    slot = arm.leggi(SLOT, SLOT_BYTES)
    _need(slot == SLOT_POSTIMAGE and _sha(slot) == SLOT_POST_SHA256,
          'resident guard differs')
    _need(arm.leggi(CANARY, len(CANARY_PREIMAGE)) == CANARY_PREIMAGE,
          'following canary changed')


def apply(data, language):
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    _language_anchor(data, language)
    arm = Arm9.from_bytes(data)
    _preimage(arm)
    arm.scrivi(MG_CHECK, MG_CHECK_POSTIMAGE)
    arm.scrivi(MG_GIVE, MG_GIVE_POSTIMAGE)
    arm.scrivi(FASHION_ASSERT, FASHION_POSTIMAGE)
    arm.scrivi(BACKGROUND_ASSERT, BACKGROUND_POSTIMAGE)
    arm.scrivi(SEAL_GIVE, SEAL_GIVE_POSTIMAGE)
    arm.scrivi(SEAL_CHECK, SEAL_CHECK_POSTIMAGE)
    arm.scrivi(SLOT, SLOT_POSTIMAGE)
    out = bytes(arm.raw)
    receipt = {
        'schema': 1, 'stage': STAGE, 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(out),
        'mg_check_address': MG_CHECK,
        'mg_check_preimage_sha256': MG_CHECK_PRE_SHA256,
        'mg_check_postimage_sha256': MG_CHECK_POST_SHA256,
        'mg_give_address': MG_GIVE,
        'mg_give_preimage_sha256': MG_GIVE_PRE_SHA256,
        'mg_give_postimage_sha256': MG_GIVE_POST_SHA256,
        'seal_give_postimage_sha256': SEAL_GIVE_POST_SHA256,
        'seal_check_postimage_sha256': SEAL_CHECK_POST_SHA256,
        'slot_address': SLOT, 'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': SLOT_PRE_SHA256,
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'seal_domain': [1, 80], 'fashion_domain': [0, 99],
        'background_domain': [0, 17],
        'oob_write_closed': True,
        'direct_give_queue_unchanged': True,
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
    patches = ((MG_CHECK, MG_CHECK_PREIMAGE),
               (MG_GIVE, MG_GIVE_PREIMAGE),
               (FASHION_ASSERT, FASHION_PREIMAGE),
               (BACKGROUND_ASSERT, BACKGROUND_PREIMAGE),
               (SEAL_GIVE, SEAL_GIVE_PREIMAGE),
               (SEAL_CHECK, SEAL_CHECK_PREIMAGE),
               (SLOT, SLOT_PREIMAGE))
    for address, preimage in patches:
        at = old.off(address, len(preimage))
        restored[at:at + len(preimage)] = preimage
    _need(bytes(restored) == before, 'bytes changed outside declared patches')
    report = {
        'ok': True,
        'changed_bytes': sum(a != b for a, b in zip(before, after)),
        'oob_write_closed': True,
        'direct_give_queue_unchanged': True,
        'save_layout_unchanged': True,
        'rom_geometry_unchanged': True,
    }
    required = {
        'schema': 1, 'stage': STAGE,
        'input_sha256': _sha(before), 'output_sha256': _sha(after),
        'mg_check_address': MG_CHECK,
        'mg_check_preimage_sha256': MG_CHECK_PRE_SHA256,
        'mg_check_postimage_sha256': MG_CHECK_POST_SHA256,
        'mg_give_address': MG_GIVE,
        'mg_give_preimage_sha256': MG_GIVE_PRE_SHA256,
        'mg_give_postimage_sha256': MG_GIVE_POST_SHA256,
        'seal_give_postimage_sha256': SEAL_GIVE_POST_SHA256,
        'seal_check_postimage_sha256': SEAL_CHECK_POST_SHA256,
        'slot_address': SLOT, 'slot_bytes': SLOT_BYTES,
        'slot_preimage_sha256': SLOT_PRE_SHA256,
        'slot_postimage_sha256': SLOT_POST_SHA256,
        'seal_domain': [1, 80], 'fashion_domain': [0, 99],
        'background_domain': [0, 17],
        'oob_write_closed': True,
        'direct_give_queue_unchanged': True,
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
    rows = ((MG_CHECK, MG_CHECK_BYTES), (MG_GIVE, MG_GIVE_BYTES),
            (FASHION_ASSERT, 4), (BACKGROUND_ASSERT, 4),
            (SEAL_GIVE, SEAL_GIVE_BYTES),
            (SEAL_CHECK, SEAL_CHECK_BYTES), (SLOT, SLOT_BYTES))
    return tuple((arm.off(address, size), arm.off(address, size) + size)
                 for address, size in rows)
