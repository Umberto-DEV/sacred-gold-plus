"""HG-T09: retain 999:00:00..999:59:58 before the native maximum.

Only change BLO to BLS after the 999-hour comparison; save layout, callers,
Training's independent played counter and the original 999:59:59 cap stay intact.
"""
import hashlib
import struct

ENTRY, END, SITE = 0x0202CDBC, 0x0202CE24, 0x0202CE0E
FUNCTION_SHA256 = '276a47f980a794aee10600dec8d3a2736ae37263a6dc1cea5c8bb992792cff02'


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def patch_native(image):
    image = bytes(image)
    _need(len(image) == END-ENTRY, 'IGT native function size')
    _need(hashlib.sha256(image).hexdigest() == FUNCTION_SHA256,
          'IGT native function preimage changed or already patched')
    at = SITE-ENTRY
    _need(image[at:at+2] == b'\x02\xd3', 'IGT native comparison branch')
    return image[:at] + b'\x02\xd9' + image[at+2:]


def apply(data, language):
    _need(language in ('EN','IT'), 'IGT language')
    data = bytes(data)
    _need(len(data) >= 0x40, 'IGT cartridge header')
    offset, _, base, size = struct.unpack_from('<4I', data, 0x20)
    _need(base == 0x02000000 and ENTRY >= base and END <= base+size
          and offset+size <= len(data), 'IGT ARM9 bounds')
    at = offset+ENTRY-base
    result = data[:at] + patch_native(data[at:at+END-ENTRY]) + data[at+END-ENTRY:]
    receipt = {'stage':'legacy-igt', 'language':language,
               'input_sha256':hashlib.sha256(data).hexdigest(),
               'output_sha256':hashlib.sha256(result).hexdigest()}
    # Integration target is sgp131; the private test imports these copies as
    # top-level modules without modifying the canonical package.
    if __package__:
        from .igt_verify import verify
    else:
        from igt_verify import verify
    receipt['verification'] = verify(data, result, receipt)
    return result, receipt
