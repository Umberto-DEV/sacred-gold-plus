"""SG-BAG-ALLOC-01: make the expanded-Bag constructor NULL-safe in place.

The historical 1.2.x blob remains immutable.  The 1.3.1 stage replaces only
the existing 28-byte ``sgp_cap_new`` body: a direct Thumb call frees the literal
word needed by the old indirect call, and those bytes hold the allocation-fail
guard without moving any entry point or consuming more resident memory.
"""
import hashlib
import struct

from sgp12.rom import Arm9, bl_decode, bl_thumb


ENTRY = 0x023DC8B0
ALLOC = 0x0201AA8C
CLEAR = 0x023DBFEC
BAG_BYTES = 0x94C
LANGUAGES = ('EN', 'IT')

PREIMAGE = bytes.fromhex(
    '10b50449044a90470400fff797fb200010bdc0464c0900008daa0102')
POSTIMAGE = (bytes.fromhex('10b50549') + bl_thumb(ENTRY + 4, ALLOC)
             + bytes.fromhex('0400002801d0') + bl_thumb(ENTRY + 14, CLEAR)
             + bytes.fromhex('200010bdc046') + struct.pack('<I', BAG_BYTES))
PREIMAGE_SHA256 = 'e66a7873924952340232d7f79af90c65aa1aeef3124c8140c8934856deed2e5d'
POSTIMAGE_SHA256 = 'a7ad1c383609150284ab0b40c3db5560b6aa834ac162504027548efb72b665f6'


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def _need(ok, reason):
    if not ok:
        raise ValueError('Bag allocation: ' + reason)


def _constants():
    _need(len(PREIMAGE) == len(POSTIMAGE) == 28, 'fixed function extent')
    _need(_sha(PREIMAGE) == PREIMAGE_SHA256 and _sha(POSTIMAGE) == POSTIMAGE_SHA256,
          'embedded code identity')
    _need(POSTIMAGE[10:14] == bytes.fromhex('002801d0'), 'NULL comparison and branch')
    _need(bl_decode(ENTRY + 4, POSTIMAGE[4:8]) == ALLOC, 'allocator direct-call target')
    _need(bl_decode(ENTRY + 14, POSTIMAGE[14:18]) == CLEAR, 'clear call target')
    _need(struct.unpack_from('<I', POSTIMAGE, 24)[0] == BAG_BYTES, 'Bag size literal')


def apply(data, language):
    _constants()
    _need(type(data) is bytes and language in LANGUAGES, 'input/language')
    arm = Arm9.from_bytes(data)
    _need(arm.leggi(ENTRY, len(PREIMAGE)) == PREIMAGE,
          'constructor preimage changed or already patched')
    arm.scrivi(ENTRY, POSTIMAGE)
    out = bytes(arm.raw)
    receipt = {
        'stage': 'bag-allocation', 'language': language,
        'input_sha256': _sha(data), 'output_sha256': _sha(out),
        'address': ENTRY, 'bytes': len(POSTIMAGE),
        'preimage_sha256': PREIMAGE_SHA256, 'postimage_sha256': POSTIMAGE_SHA256,
        'allocator': ALLOC, 'clear': CLEAR, 'bag_bytes': BAG_BYTES,
        'entry_points_unchanged': True, 'save_layout_unchanged': True,
    }
    receipt['verification'] = verify(data, out, receipt)
    return out, receipt


def verify(before, after, receipt):
    _constants()
    _need(type(before) is bytes and type(after) is bytes and len(before) == len(after),
          'image geometry')
    old, new = Arm9.from_bytes(before), Arm9.from_bytes(after)
    _need(old.leggi(ENTRY, len(PREIMAGE)) == PREIMAGE, 'constructor preimage')
    _need(new.leggi(ENTRY, len(POSTIMAGE)) == POSTIMAGE, 'constructor postimage')
    at = old.off(ENTRY, len(PREIMAGE))
    _need(at == new.off(ENTRY, len(POSTIMAGE)), 'constructor physical placement')
    restored = bytearray(after)
    restored[at:at + len(PREIMAGE)] = PREIMAGE
    _need(bytes(restored) == before, 'bytes changed outside the constructor')
    _need(type(receipt) is dict and receipt.get('stage') == 'bag-allocation'
          and receipt.get('language') in LANGUAGES
          and receipt.get('input_sha256') == _sha(before)
          and receipt.get('output_sha256') == _sha(after)
          and receipt.get('address') == ENTRY and receipt.get('bytes') == len(POSTIMAGE)
          and receipt.get('preimage_sha256') == PREIMAGE_SHA256
          and receipt.get('postimage_sha256') == POSTIMAGE_SHA256
          and receipt.get('allocator') == ALLOC and receipt.get('clear') == CLEAR
          and receipt.get('bag_bytes') == BAG_BYTES
          and receipt.get('entry_points_unchanged') is True
          and receipt.get('save_layout_unchanged') is True,
          'receipt identity')
    return {'ok': True, 'address': ENTRY, 'bytes': len(POSTIMAGE),
            'postimage_sha256': POSTIMAGE_SHA256, 'null_safe': True,
            'successful_allocation_still_cleared': True,
            'entry_points_unchanged': True, 'save_layout_unchanged': True}


def span(data):
    arm = Arm9.from_bytes(bytes(data))
    at = arm.off(ENTRY, len(POSTIMAGE))
    return at, at + len(POSTIMAGE)
