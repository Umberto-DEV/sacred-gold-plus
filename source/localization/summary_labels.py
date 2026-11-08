"""Guarded German FP/DV labels for the inherited native Summary viewer.

Only eight Thumb glyph instructions and one same-size native String change.
The complete wrapper preimage pins its selector, String guard and native calls.
"""
import hashlib
import struct

WRAPPER_ADDRESS, WRAPPER_BYTES = 0x01FF9348, 96
WRAPPER_SHA256 = '6aa74af161cc1f450a668b57464ee2b43d1ff6dfb226d9bffa5dd6113a9b16a9'
LABELS_ADDRESS = 0x01FF9370
LABELS_PREIMAGE = bytes.fromhex('ff2130310c0011345481b40061181181')

# r6 is 0 for EV and 1 for IV, guarded by the unchanged wrapper. r6 is dead
# after this block and restored by its original push/pop. No call uses flags.
# First = 2*(0x98-r6): F / D. Second = first+10+8*r6: P / V.
#   movs r1,#0x98; subs r1,r1,r6; lsls r1,r1,#1; strh r1,[r2,#8]
#   adds r1,#10; lsls r6,r6,#3; adds r1,r1,r6; strh r1,[r2,#10]
LABELS_REPLACEMENT = struct.pack('<8H', 0x2198, 0x1B89, 0x0049, 0x8111,
                                 0x310A, 0x00F6, 0x1989, 0x8151)

LEGEND_ADDRESS = 0x023D4C30
# Native glyphs from the pinned common font/charmap. Both strings have 22
# visible units and one terminator; retain the original 23/23 String header.
LEGEND_PREIMAGE = struct.pack('<HHI23H', 23, 23, 0xB6F8D2EC,
    0x136, 0x1C4, 0x12F, 0x140, 0x1DE, 0x13D, 0x12F, 0x136, 0x12F,
    0x12D, 0x13E, 0x1C4, 0x13D, 0x158, 0x145, 0x158, 0x1AE, 0x1DE,
    0x13C, 0x1C4, 0x133, 0x140, 0xFFFF)  # L:EV SELECT:Stat. R:IV
LEGEND_REPLACEMENT = struct.pack('<HHI23H', 23, 23, 0xB6F8D2EC,
    0x136, 0x1C4, 0x130, 0x13A, 0x1DE, 0x13D, 0x12F, 0x136, 0x12F,
    0x12D, 0x13E, 0x1C4, 0x141, 0x149, 0x156, 0x158, 0x1AE, 0x1DE,
    0x13C, 0x1C4, 0x12E, 0x140, 0xFFFF)  # L:FP SELECT:Wert. R:DV

OWNED_SPANS = ((LABELS_ADDRESS, len(LABELS_REPLACEMENT)),
               (LEGEND_ADDRESS, len(LEGEND_REPLACEMENT)))


def owned_spans(locale):
    """Return (native address, byte count) pairs for independent readback."""
    if locale not in ('EN', 'IT', 'FR', 'ES', 'DE'):
        raise ValueError('unsupported Summary label locale')
    return OWNED_SPANS if locale == 'DE' else ()


def apply(data: bytes, locate, locale: str) -> bytes:
    if not owned_spans(locale):
        return bytes(data)
    at = locate(WRAPPER_ADDRESS, WRAPPER_BYTES)
    if hashlib.sha256(data[at:at+WRAPPER_BYTES]).hexdigest() != WRAPPER_SHA256:
        raise ValueError('Summary wrapper preimage')
    checked = []
    for address, before, after, name in (
            (LABELS_ADDRESS, LABELS_PREIMAGE, LABELS_REPLACEMENT, 'label'),
            (LEGEND_ADDRESS, LEGEND_PREIMAGE, LEGEND_REPLACEMENT, 'legend')):
        at = locate(address, len(before))
        if data[at:at+len(before)] != before:
            raise ValueError('Summary ' + name + ' preimage')
        checked.append((at, after))
    output = bytearray(data)
    for at, replacement in checked:
        output[at:at+len(replacement)] = replacement
    return bytes(output)
