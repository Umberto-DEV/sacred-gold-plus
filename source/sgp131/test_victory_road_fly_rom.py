"""Native EN/IT regression for the Victory Road Fly-marker highlight.

The fly table intentionally keeps two identities for Victory Road: the name
comes from ``MAP_VICTORY_ROAD_1F`` while the warp goes to ``MAP_ROUTE_26``.
The retail selection path feeds the former to the cross-region gate, so the
marker does not animate while the player is still in Johto.  The bounded
Thumb-1 interpreter below executes the exact overlay-100 region classifier
and overlay-101 gate bytes; its expectations are literal and independent of
the producer.
"""
import hashlib
from pathlib import Path
import struct
import unittest

from sgp12.rom import Rom, bl_decode


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90',
           147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156',
           153228136),
}

REGION_GATE = 0x021EA804
FLYPOINT_TABLE = 0x021F79B4
FLYPOINT_BYTES = 14
VICTORY_INDEX = 26
MAP_APP = 0x022C0000
STOP = 0x023FF000

REGION_KANTO = 0
REGION_INDIGO = 1
REGION_JOHTO = 2

# Hand-derived identities and coordinates from gMapFlypointParams.
MAP_INDIGO_PLATEAU = 58
MAP_ROUTE_26 = 30
MAP_VICTORY_ROAD_1F = 124
MAP_BLACKTHORN = 135
MAP_VIRIDIAN = 1


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


def implementation(case):
    try:
        from . import victory_road_fly
    except ImportError as error:
        case.fail('Victory Road Fly producer is not implemented: ' + str(error))
    return victory_road_fly


class ThumbGateBench:
    """Small literal Thumb-1 executor for the two real region-gate functions."""

    def __init__(self, rom):
        parsed = Rom(rom)
        self.images = []
        for overlay_id in (100, 101):
            entry, _stream, image = parsed.immagine_overlay(overlay_id)
            self.images.append((entry['ram'], bytes(image)))
        self.regions = bytearray(0x100)
        self.registers = [0] * 16
        self.frames = []
        self.z = False
        self.c = False

    def read(self, address, size):
        if MAP_APP <= address and address + size <= MAP_APP + len(self.regions):
            at = address - MAP_APP
            return bytes(self.regions[at:at + size])
        for base, image in self.images:
            if base <= address and address + size <= base + len(image):
                at = address - base
                return image[at:at + size]
        raise AssertionError('read outside authenticated gate images at %#x' % address)

    def flypoint(self, index):
        raw = self.read(FLYPOINT_TABLE + index * FLYPOINT_BYTES,
                        FLYPOINT_BYTES)
        name, warp = struct.unpack_from('<HH', raw)
        return name, warp, raw[4], raw[6], raw[7]

    def _cmp(self, left, right):
        left &= 0xFFFFFFFF
        right &= 0xFFFFFFFF
        self.z = left == right
        self.c = left >= right

    def _condition(self, condition):
        if condition == 0:   # EQ
            return self.z
        if condition == 1:   # NE
            return not self.z
        if condition == 2:   # HS
            return self.c
        if condition == 3:   # LO
            return not self.c
        if condition == 8:   # HI
            return self.c and not self.z
        if condition == 9:   # LS
            return not self.c or self.z
        raise AssertionError('unsupported condition %d' % condition)

    @staticmethod
    def _signed(value, bits):
        sign = 1 << (bits - 1)
        return value - (1 << bits) if value & sign else value

    def call(self, map_id, x, y, region):
        self.registers[:] = [0] * 16
        self.frames.clear()
        self.regions[:] = bytes(len(self.regions))
        self.regions[0x0E] = region
        self.registers[:4] = [MAP_APP, map_id, x, y]
        self.registers[14] = STOP | 1
        pc = REGION_GATE

        for _step in range(128):
            if pc == STOP:
                return self.registers[0] & 0xFFFFFFFF
            raw = self.read(pc, 4)
            op = int.from_bytes(raw[:2], 'little')
            next_pc = pc + 2

            if op & 0xFE00 == 0xB400:  # push low registers, optional LR
                regs = [r for r in range(8) if op & (1 << r)]
                if op & 0x100:
                    regs.append(14)
                self.frames.append([self.registers[r] for r in regs])
            elif op & 0xFE00 == 0xBC00:  # pop low registers, optional PC
                regs = [r for r in range(8) if op & (1 << r)]
                if op & 0x100:
                    regs.append(15)
                values = self.frames.pop()
                if len(values) != len(regs):
                    raise AssertionError('unbalanced Thumb push/pop')
                for reg, value in zip(regs, values):
                    if reg == 15:
                        next_pc = value & ~1
                    else:
                        self.registers[reg] = value
            elif op & 0xF800 == 0x2800:  # cmp Rn,#imm8
                self._cmp(self.registers[(op >> 8) & 7], op & 0xFF)
            elif op & 0xFFC0 == 0x4280:  # cmp Rn,Rm
                self._cmp(self.registers[op & 7],
                          self.registers[(op >> 3) & 7])
            elif op & 0xF800 == 0x2000:  # movs Rd,#imm8
                self.registers[(op >> 8) & 7] = op & 0xFF
            elif op & 0xFE00 == 0x1800:  # adds Rd,Rn,Rm
                rd, rn, rm = op & 7, (op >> 3) & 7, (op >> 6) & 7
                self.registers[rd] = (self.registers[rn]
                                      + self.registers[rm]) & 0xFFFFFFFF
            elif op & 0xFE00 == 0x1C00:  # adds Rd,Rn,#imm3
                rd, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 7
                self.registers[rd] = (self.registers[rn] + imm) & 0xFFFFFFFF
            elif op & 0xFE00 == 0x1E00:  # subs Rd,Rn,#imm3
                rd, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 7
                left = self.registers[rn]
                self.registers[rd] = (left - imm) & 0xFFFFFFFF
                self._cmp(left, imm)
            elif op & 0xF800 == 0x7800:  # ldrb Rt,[Rn,#imm5]
                rt, rn, imm = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                self.registers[rt] = self.read(self.registers[rn] + imm, 1)[0]
            elif op & 0xF000 == 0xD000 and (op >> 8) & 0xF < 0xE:
                condition = (op >> 8) & 0xF
                if self._condition(condition):
                    next_pc = pc + 4 + self._signed(op & 0xFF, 8) * 2
            elif op & 0xF800 == 0xE000:  # unconditional branch
                next_pc = pc + 4 + self._signed(op & 0x7FF, 11) * 2
            elif op & 0xF800 == 0xF000:  # BL pair
                self.registers[14] = (pc + 4) | 1
                next_pc = bl_decode(pc, raw)
            elif op == 0x4770:  # bx lr
                next_pc = self.registers[14] & ~1
            elif op == 0x46C0:  # nop
                pass
            else:
                raise AssertionError('unsupported Thumb opcode %#06x at %#x'
                                     % (op, pc))
            pc = next_pc
        raise AssertionError('region gate did not return')


class VictoryRoadFlyRomTests(unittest.TestCase):
    maxDiff = None

    def test_v4_reproduces_the_johto_name_id_failure_with_healthy_controls(self):
        """Catches a false diagnosis that the table, marker or exception is absent."""
        for language in V4:
            bench = ThumbGateBench(candidate(self, language))
            self.assertEqual(bench.flypoint(VICTORY_INDEX),
                             (MAP_VICTORY_ROAD_1F, MAP_ROUTE_26, 33, 28, 7))
            with self.subTest(language=language):
                self.assertEqual(bench.call(MAP_VICTORY_ROAD_1F, 28, 7,
                                            REGION_JOHTO), 0)
                self.assertEqual(bench.call(MAP_ROUTE_26, 28, 7,
                                            REGION_JOHTO), 1)
                self.assertEqual(bench.call(MAP_VICTORY_ROAD_1F, 28, 7,
                                            REGION_KANTO), 1)
                self.assertEqual(bench.call(MAP_VICTORY_ROAD_1F, 28, 7,
                                            REGION_INDIGO), 1)
                self.assertEqual(bench.call(MAP_INDIGO_PLATEAU, 28, 6,
                                            REGION_JOHTO), 1)
                self.assertEqual(bench.call(MAP_BLACKTHORN, 20, 4,
                                            REGION_JOHTO), 1)
                self.assertEqual(bench.call(MAP_VIRIDIAN, 31, 7,
                                            REGION_JOHTO), 0)

    def test_fix_accepts_the_victory_coordinate_without_widening_regions(self):
        """Catches changing the displayed name, y=8, or every Kanto marker."""
        fix = implementation(self)
        for language in V4:
            before = candidate(self, language)
            after, receipt = fix.apply(before, language)
            old = ThumbGateBench(before)
            new = ThumbGateBench(after)
            with self.subTest(language=language):
                self.assertEqual(new.flypoint(VICTORY_INDEX),
                                 (MAP_VICTORY_ROAD_1F, MAP_ROUTE_26, 33, 28, 7))
                self.assertEqual(new.call(MAP_VICTORY_ROAD_1F, 28, 7,
                                          REGION_JOHTO), 1)
                controls = (
                    (MAP_ROUTE_26, 28, 7, REGION_JOHTO),
                    (MAP_VICTORY_ROAD_1F, 28, 7, REGION_KANTO),
                    (MAP_VICTORY_ROAD_1F, 28, 7, REGION_INDIGO),
                    (MAP_INDIGO_PLATEAU, 28, 6, REGION_JOHTO),
                    (MAP_BLACKTHORN, 20, 4, REGION_JOHTO),
                    (MAP_VIRIDIAN, 31, 7, REGION_JOHTO),
                    (MAP_VIRIDIAN, 28, 8, REGION_JOHTO),
                )
                self.assertEqual([new.call(*args) for args in controls],
                                 [old.call(*args) for args in controls])
                self.assertEqual(fix.verify(before, after, receipt),
                                 receipt['verification'])

if __name__ == '__main__':
    unittest.main()
