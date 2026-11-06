"""Reproducer and bounded non-installable design for the Pokégear X culler.

The current overlay-101 function ignores X.  The signed design below is the
smallest verified Thumb-1/caller-ABI replacement found so far.  It has exact
``-7..263`` and ``0..199`` boundaries, but its optimal BLZ stream is four
bytes larger than the immutable overlay slot.  This file deliberately does
not expose an installer until that containment gate can pass.
"""
import hashlib
from pathlib import Path
import struct
import unittest

from sgp12.blz import blz_comprimi_ottimo, blz_decomprimi
from sgp12.rom import Rom, bl_decode
from sgp131 import (fishing, gb_sounds_evolution, lullaby, soul_dew,
                    victory_road_fly, wonder_card)
from sgp131.controls import encode_bl


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136),
}

OVERLAY_ID = 101
OVERLAY_RAM = 0x021E7740
OVERLAY_BYTES = 0x13BC0
COMPRESSED_BYTES = 53576
AUTOCULL = 0x021EC920
DRAW_FLAG = 0x02024830
STOP = 0x023FF000
OBJECT = 0x023FE000
SPRITE = 0x023FE100

PREIMAGE = bytes.fromhex(
    '08b5417800290cd0d82a01dc002a04da006a002137f67cff08bd'
    '006a012137f677ff08bd')

# Exact 36-byte function.  Reverse CMP plus MOVS/ADCS turns the preserved
# carry into a strict Boolean without widening the function.  The final word
# is the unsigned threshold 270 for signed ``x + 7``.
SIGNED_DESIGN = bytearray.fromhex(
    '08b54378002b0ad00731054b8b4200214941c72a00d90021006a'
    '0000000008bd0e010000')
SIGNED_DESIGN[26:30] = encode_bl(AUTOCULL + 26, DRAW_FLAG | 1)
SIGNED_DESIGN = bytes(SIGNED_DESIGN)

# The three private callers must pass signed X in r1 and Y in r2.  The first
# and third use ldrsh for X and ldrh for Y; the middle caller already has both
# signed coordinates and only needs to preserve r1.
CALLER_PATCHES = {
    0x021EC828: bytes.fromhex('0427'),   # movs r7,#4
    0x021EC83C: bytes.fromhex('c288'),   # ldrh r2,[r0,#6]
    0x021EC83E: bytes.fromhex('c15f'),   # ldrsh r1,[r0,r7]
    0x021EC8E4: bytes.fromhex('c046'),   # mov r8,r8
    0x021EC95C: bytes.fromhex('0427'),
    0x021EC964: bytes.fromhex('c15f'),
    0x021EC966: bytes.fromhex('c288'),
}

LOGICAL_PREIMAGE = 'e7fa1b6cc5abac3eda341e2bfa1103665a064b7e28ff20f307e787311c371b72'
LOGICAL_DESIGN = '4319dc18a0f3ee51442c85377745f32e7084561ad8b425a6a0905eadbe67c1b5'
STREAM_DESIGN = '684c9a8fc90ea51a66fdd03366c1f5c70193281447b1d0f236512707da646a20'


def _sha(data):
    return hashlib.sha256(bytes(data)).hexdigest()


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((_sha(data), len(data)), V4[language])
    return data


def _signed(value, bits):
    sign = 1 << (bits - 1)
    return value - (1 << bits) if value & sign else value


class ThumbCullBench:
    """Small Thumb-1 executor for the two exact 36-byte functions."""

    def __init__(self, code, *, base=AUTOCULL, entry=None, extra_segments=()):
        self.segments = ((base, bytes(code)),) + tuple(
            (address, bytes(raw)) for address, raw in extra_segments)
        self.entry = base if entry is None else entry
        self.reg = [0] * 16
        self.frames = []
        self.calls = []
        self.n = self.z = self.c = self.v = False
        self.object = bytearray(0x40)
        struct.pack_into('<I', self.object, 0x20, SPRITE)

    def _read(self, address, size):
        for base, code in self.segments:
            if base <= address < base + len(code):
                at = address - base
                return code[at:at + size].ljust(size, b'\0')
        if OBJECT <= address and address + size <= OBJECT + len(self.object):
            at = address - OBJECT
            return self.object[at:at + size]
        raise AssertionError('read outside culler bench at %#x' % address)

    def _sub_flags(self, left, right):
        left &= 0xFFFFFFFF
        right &= 0xFFFFFFFF
        result = (left - right) & 0xFFFFFFFF
        self.n = bool(result & 0x80000000)
        self.z = result == 0
        self.c = left >= right
        self.v = bool(((left ^ right) & (left ^ result)) & 0x80000000)

    def _add_flags(self, left, right, carry=0):
        total = (left & 0xFFFFFFFF) + (right & 0xFFFFFFFF) + carry
        result = total & 0xFFFFFFFF
        self.n = bool(result & 0x80000000)
        self.z = result == 0
        self.c = total > 0xFFFFFFFF
        self.v = bool((~(left ^ right) & (left ^ result)) & 0x80000000)
        return result

    def _condition(self, condition):
        if condition == 0:   # EQ
            return self.z
        if condition == 8:   # HI
            return self.c and not self.z
        if condition == 9:   # LS
            return not self.c or self.z
        if condition == 10:  # GE
            return self.n == self.v
        if condition == 12:  # GT
            return not self.z and self.n == self.v
        raise AssertionError('unsupported condition %d' % condition)

    def call(self, x, y, auto_cull=1):
        self.reg[:] = [0] * 16
        self.frames.clear()
        self.calls.clear()
        self.object[:] = bytes(len(self.object))
        self.object[1] = auto_cull
        struct.pack_into('<I', self.object, 0x20, SPRITE)
        self.reg[0] = OBJECT
        self.reg[1] = x & 0xFFFFFFFF
        self.reg[2] = y & 0xFFFFFFFF
        self.reg[14] = STOP | 1
        pc = self.entry

        for _step in range(64):
            if pc == STOP:
                return list(self.calls)
            if pc == DRAW_FLAG:
                self.calls.append((self.reg[0], self.reg[1] & 0xFFFFFFFF))
                pc = self.reg[14] & ~1
                continue
            raw = self._read(pc, 4)
            op = int.from_bytes(raw[:2], 'little')
            next_pc = pc + 2

            if op & 0xFE00 == 0xB400:  # push
                regs = [r for r in range(8) if op & (1 << r)]
                if op & 0x100:
                    regs.append(14)
                self.frames.append([self.reg[r] for r in regs])
            elif op & 0xFE00 == 0xBC00:  # pop
                regs = [r for r in range(8) if op & (1 << r)]
                if op & 0x100:
                    regs.append(15)
                values = self.frames.pop()
                for register, value in zip(regs, values):
                    if register == 15:
                        next_pc = value & ~1
                    else:
                        self.reg[register] = value
            elif op & 0xF800 == 0x7800:  # ldrb
                rt, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                self.reg[rt] = self._read(self.reg[rn] + imm, 1)[0]
            elif op & 0xF800 == 0x6800:  # ldr word immediate
                rt, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                address = self.reg[rn] + imm * 4
                self.reg[rt] = int.from_bytes(self._read(address, 4), 'little')
            elif op & 0xF800 == 0x4800:  # ldr literal
                rt, imm = (op >> 8) & 7, op & 0xFF
                address = ((pc + 4) & ~3) + imm * 4
                self.reg[rt] = int.from_bytes(self._read(address, 4), 'little')
            elif op & 0xF800 == 0x2800:  # cmp immediate
                self._sub_flags(self.reg[(op >> 8) & 7], op & 0xFF)
            elif op & 0xFFC0 == 0x4280:  # cmp register
                self._sub_flags(self.reg[op & 7], self.reg[(op >> 3) & 7])
            elif op & 0xF800 == 0x2000:  # movs immediate; C and V preserved
                rd = (op >> 8) & 7
                self.reg[rd] = op & 0xFF
                self.n = False
                self.z = self.reg[rd] == 0
            elif op & 0xF800 == 0x3000:  # adds immediate
                rd = (op >> 8) & 7
                self.reg[rd] = self._add_flags(self.reg[rd], op & 0xFF)
            elif op & 0xFFC0 == 0x4140:  # adcs register
                rd, rm = op & 7, (op >> 3) & 7
                self.reg[rd] = self._add_flags(self.reg[rd], self.reg[rm], self.c)
            elif op & 0xFF87 == 0x4700:  # bx high register
                next_pc = self.reg[(op >> 3) & 0xF] & ~1
            elif op & 0xF000 == 0xD000 and (op >> 8) & 0xF < 0xE:
                condition = (op >> 8) & 0xF
                if self._condition(condition):
                    next_pc = pc + 4 + _signed(op & 0xFF, 8) * 2
            elif op & 0xF800 == 0xF000:  # bl pair
                self.reg[14] = (pc + 4) | 1
                next_pc = bl_decode(pc, raw)
            else:
                raise AssertionError('unsupported Thumb opcode %#06x at %#x'
                                     % (op, pc))
            pc = next_pc
        raise AssertionError('culler did not return')


def _design_image(image):
    out = bytearray(image)
    base = OVERLAY_RAM
    for address, patch in CALLER_PATCHES.items():
        out[address - base:address - base + len(patch)] = patch
    at = AUTOCULL - base
    if out[at:at + len(PREIMAGE)] != PREIMAGE:
        raise AssertionError('AutoCull preimage differs')
    out[at:at + len(SIGNED_DESIGN)] = SIGNED_DESIGN
    return bytes(out)


class PokegearAutoCullRomTests(unittest.TestCase):
    maxDiff = None

    def test_v4_reproduces_missing_x_cull_with_y_and_disable_controls(self):
        for language in V4:
            rom = Rom(candidate(self, language))
            entry, _stream, image = rom.immagine_overlay(OVERLAY_ID)
            self.assertEqual((entry['ram'], len(image)),
                             (OVERLAY_RAM, OVERLAY_BYTES))
            at = AUTOCULL - OVERLAY_RAM
            self.assertEqual(image[at:at + len(PREIMAGE)], PREIMAGE)
            bench = ThumbCullBench(PREIMAGE)
            with self.subTest(language=language):
                self.assertEqual(bench.call(-512, 100), [(SPRITE, 1)])
                self.assertEqual(bench.call(512, 100), [(SPRITE, 1)])
                self.assertEqual(bench.call(0, -1), [(SPRITE, 0)])
                self.assertEqual(bench.call(0, 0), [(SPRITE, 1)])
                self.assertEqual(bench.call(0, 216), [(SPRITE, 1)])
                self.assertEqual(bench.call(0, 217), [(SPRITE, 0)])
                self.assertEqual(bench.call(0, 100, 0), [])

    def test_signed_design_has_exact_x_y_boundaries_and_kills_ldrh_mutant(self):
        bench = ThumbCullBench(SIGNED_DESIGN)
        expected = {
            (-512, 100): 0, (-8, 100): 0, (-7, 100): 1,
            (-1, 100): 1, (0, 0): 1, (263, 199): 1,
            (264, 100): 0, (512, 100): 0, (0, -1): 0,
            (0, 200): 0,
        }
        for (x, y), flag in expected.items():
            with self.subTest(x=x, y=y):
                self.assertEqual(bench.call(x, y), [(SPRITE, flag)])
        self.assertEqual(bench.call(0, 100, 0), [])

        # ldrh would turn the valid partial-left coordinates into large u16s.
        for x in range(-7, 0):
            self.assertGreater((x & 0xFFFF) + 7, 270)
            self.assertEqual(bench.call(x, 100), [(SPRITE, 1)])

    def test_valid_signed_design_is_exactly_four_bytes_over_the_blz_slot(self):
        for language in V4:
            data = candidate(self, language)
            data, _ = lullaby.apply(data, language)
            data, _ = fishing.apply(data, language)
            data, _ = victory_road_fly.apply(data, language)
            entry, stream, image = Rom(data).immagine_overlay(OVERLAY_ID)
            self.assertEqual(_sha(image), LOGICAL_PREIMAGE)
            self.assertEqual(len(stream), COMPRESSED_BYTES)
            designed = _design_image(image)
            encoded = blz_comprimi_ottimo(designed)
            with self.subTest(language=language):
                self.assertEqual(_sha(designed), LOGICAL_DESIGN)
                self.assertEqual((_sha(encoded), len(encoded)),
                                 (STREAM_DESIGN, COMPRESSED_BYTES + 4))
                self.assertEqual(blz_decomprimi(encoded, OVERLAY_BYTES), designed)
                self.assertGreater(len(encoded), COMPRESSED_BYTES)

    def test_resident_thunk_fits_the_existing_overlay_and_preserves_abi(self):
        from sgp131 import pokegear_autocull

        for language in V4:
            data = candidate(self, language)
            for stage in (lullaby, fishing, victory_road_fly, soul_dew,
                          wonder_card, gb_sounds_evolution):
                data, _receipt = stage.apply(data, language)
            after, receipt = pokegear_autocull.apply(data, language)
            self.assertEqual(pokegear_autocull.verify(data, after, receipt),
                             receipt['verification'])

            old_rom, new_rom = Rom(data), Rom(after)
            old_entry, old_stream, old_image = old_rom.immagine_overlay(OVERLAY_ID)
            new_entry, new_stream, new_image = new_rom.immagine_overlay(OVERLAY_ID)
            with self.subTest(language=language, layer='container'):
                self.assertEqual(new_entry, old_entry)
                self.assertEqual(len(new_stream), COMPRESSED_BYTES)
                self.assertEqual(blz_decomprimi(new_stream, OVERLAY_BYTES),
                                 new_image)
                self.assertLessEqual(len(blz_comprimi_ottimo(new_image)),
                                     COMPRESSED_BYTES)

            bench = ThumbCullBench(
                pokegear_autocull.SLOT_POSTIMAGE,
                base=pokegear_autocull.SLOT,
                entry=AUTOCULL,
                extra_segments=((AUTOCULL,
                                 pokegear_autocull.TRAMPOLINE_POSTIMAGE),),
            )
            expected = {
                (-512, 100): 0, (-8, 100): 0, (-7, 100): 1,
                (-1, 100): 1, (0, 0): 1, (263, 199): 1,
                (264, 100): 0, (512, 100): 0, (0, -1): 0,
                (0, 200): 0,
            }
            for (x, y), flag in expected.items():
                with self.subTest(language=language, x=x, y=y):
                    self.assertEqual(bench.call(x, y), [(SPRITE, flag)])
            self.assertEqual(bench.call(0, 100, 0), [])
            self.assertEqual(bench.frames, [])


if __name__ == '__main__':
    unittest.main()
