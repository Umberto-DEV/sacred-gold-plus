"""Supply accent keys while preserving the shared English game/save identity."""
import struct

ACCENTS = {
    'FR': ('ÀÂÇÉÈÊËÎÏÔÙÛÜ', 'àâçéèêëîïôùûü'),
    'ES': ('ÁÉÍÑÓÚÜ¿¡    ', 'áéíñóúü¿¡    '),
    'DE': ('ÄÖÜß         ', 'äöüß         '),
}
PREIMAGE = struct.pack('<14H', *([0x1DE] * 13 + [0xFFFF]))
EDITS = ((0x02101E2C, 0x02110504), (0x02101F60, 0x02110518))


def rows(locale, encode):
    if locale not in ACCENTS:
        raise ValueError('unsupported accent-row locale')
    result = []
    for text in ACCENTS[locale]:
        words = encode(text)
        if len(words) != 14 or words[-1] != 65535 or any(not 0 < w < 509 for w in words[:-1]):
            raise ValueError('accent-row glyph/geometry contract')
        result.append(struct.pack('<14H', *words))
    return tuple(result)


def apply(data, locate, locale, encode):
    replacements = rows(locale, encode)
    if data[locate(0x020F5670, 1)] != 2:
        raise ValueError('shared game/save identity guard')
    checked = []
    for (address, pointer), replacement in zip(EDITS, replacements):
        at = locate(address, 28)
        if (struct.unpack_from('<I', data, locate(pointer, 4))[0] != address
                or data[at:at + 28] != PREIMAGE):
            raise ValueError('keyboard pointer/preimage guard')
        checked.append((at, replacement))
    output = bytearray(data)
    for at, replacement in checked:
        output[at:at + 28] = replacement
    return bytes(output)
