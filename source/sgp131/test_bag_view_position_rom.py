"""Real-ROM reproduction for the HGSS ``BagView_SetItem`` position bug.

The immutable EN/IT V4 candidates stay on disk and are only read.  The producer
works in memory; Unicorn, or an independent bounded Thumb-1 interpreter on
hosts where Unicorn SIGILLs, executes the exact installed routines with
canaries around all eight ``BagViewPocket`` entries.  The checks also keep the
adjacent ``sub_020778C8`` flag setter alive after its two-byte relocation.
"""
import hashlib
from functools import lru_cache
from pathlib import Path
import subprocess
import sys
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3)

from sgp12.rom import Arm9, bl_decode
from . import bag_view_position as B


ROOT = Path(__file__).resolve().parents[2]
V4_ROOT = ROOT / 'local/experiments/balance493-2026-10-28'
V4 = {
    'EN': ('179edfb1ca331503f438e98f3afccfb0ab85759bf9ab88fb86c735f5fcefbf90', 147345256),
    'IT': ('2a2f0b437fca524c18b71b20feb01a1f51351e61c7c897ce73d9b3be1ee3a156', 153228136),
}
BASE = 0x02000000
VIEW = 0x02200000
STOP = 0x02201000
VIEW_BYTES = 0x7C
POCKET_BYTES = 12


@lru_cache(maxsize=1)
def unicorn_works():
    probe = subprocess.run(
        [sys.executable, '-c',
         'from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB; '
         'u=Uc(UC_ARCH_ARM,UC_MODE_THUMB); u.mem_map(0x2000000,0x1000); '
         'u.mem_write(0x2000000,bytes.fromhex("01207047")); '
         'u.emu_start(0x2000001,0x2000004,count=1)'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
    return probe.returncode == 0


def candidate(case, language):
    path = V4_ROOT / ('candidate-v4-%s.nds' % language)
    if not path.is_file():
        case.skipTest('immutable V4 candidate unavailable: ' + str(path))
    data = path.read_bytes()
    case.assertEqual((hashlib.sha256(data).hexdigest(), len(data)), V4[language])
    return data


def direct_bl_calls(rom, target):
    arm = Arm9.from_bytes(rom)
    raw = arm.leggi(BASE, 0x111860)
    calls = []
    for offset in range(0, len(raw) - 3, 2):
        hi = int.from_bytes(raw[offset:offset + 2], 'little')
        lo = int.from_bytes(raw[offset + 2:offset + 4], 'little')
        if hi & 0xF800 == 0xF000 and lo & 0xF800 == 0xF800:
            address = BASE + offset
            if bl_decode(address, raw[offset:offset + 4]) == target:
                calls.append(address)
    return calls


class Bench:
    def __init__(self, rom):
        self.mu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.mu.mem_map(BASE, 0x200000)
        self.mu.mem_map(VIEW, 0x2000)
        arm = Arm9.from_bytes(rom)
        for address, offset, size in arm.segmenti:
            if BASE <= address and address + size <= BASE + 0x200000:
                self.mu.mem_write(address, bytes(arm.raw[offset:offset + size]))
        self.mu.mem_write(STOP, b'\x00\xbe')

    def call_setter(self, pocket_id, position, slots):
        self.mu.mem_write(VIEW, bytes([0xA5]) * VIEW_BYTES)
        self.mu.reg_write(UC_ARM_REG_R0, VIEW)
        self.mu.reg_write(UC_ARM_REG_R1, slots)
        self.mu.reg_write(UC_ARM_REG_R2, pocket_id)
        self.mu.reg_write(UC_ARM_REG_R3, position)
        self.mu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(B.SETTER | 1, STOP, count=32)
        return bytes(self.mu.mem_read(VIEW, VIEW_BYTES))

    def call_flag_setter(self, initial):
        self.mu.mem_write(VIEW, bytes(VIEW_BYTES))
        self.mu.mem_write(VIEW + 0x76, initial.to_bytes(2, 'little'))
        self.mu.reg_write(UC_ARM_REG_R0, VIEW)
        self.mu.reg_write(UC_ARM_REG_LR, STOP | 1)
        self.mu.emu_start(B.FLAG_SETTER | 1, STOP, count=32)
        return int.from_bytes(self.mu.mem_read(VIEW + 0x76, 2), 'little')


class MiniThumbBench:
    """Independent Thumb-1 subset for this 26-byte repair, used if Unicorn SIGILLs."""
    def __init__(self, rom):
        self.arm = Arm9.from_bytes(rom)
        self.memory = bytearray(VIEW_BYTES)

    def _run(self, entry, registers):
        pc = entry
        for _ in range(32):
            op = int.from_bytes(self.arm.leggi(pc, 2), 'little')
            pc += 2
            if op == 0x4770:  # bx lr
                self.assert_stop(registers[14])
                return
            if op & 0xF800 == 0x0000:  # lsls Rd,Rs,#imm5
                rd, rs, imm = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                registers[rd] = (registers[rs] << imm) & 0xFFFFFFFF
            elif op & 0xFE00 == 0x1800:  # adds Rd,Rn,Rm
                rd, rn, rm = op & 7, (op >> 3) & 7, (op >> 6) & 7
                registers[rd] = (registers[rn] + registers[rm]) & 0xFFFFFFFF
            elif op & 0xF800 == 0x6000:  # str Rd,[Rb,#imm5*4]
                rd, rb, imm = op & 7, (op >> 3) & 7, ((op >> 6) & 0x1F) * 4
                self._write(registers[rb] + imm, registers[rd].to_bytes(4, 'little'))
            elif op & 0xF800 == 0x7000:  # strb Rd,[Rb,#imm5]
                rd, rb, imm = op & 7, (op >> 3) & 7, (op >> 6) & 0x1F
                self._write(registers[rb] + imm, bytes([registers[rd] & 0xFF]))
            elif op & 0xF800 == 0x2000:  # movs Rd,#imm8
                registers[(op >> 8) & 7] = op & 0xFF
            elif op & 0xF800 == 0x3000:  # adds Rd,#imm8
                rd = (op >> 8) & 7
                registers[rd] = (registers[rd] + (op & 0xFF)) & 0xFFFFFFFF
            elif op & 0xF800 == 0x8800:  # ldrh Rd,[Rb,#imm5*2]
                rd, rb, imm = op & 7, (op >> 3) & 7, ((op >> 6) & 0x1F) * 2
                registers[rd] = int.from_bytes(self._read(registers[rb] + imm, 2), 'little')
            elif op & 0xFFC0 == 0x4300:  # orrs Rdn,Rm
                rdn, rm = op & 7, (op >> 3) & 7
                registers[rdn] |= registers[rm]
            elif op & 0xFFC0 == 0x4340:  # muls Rdn,Rm
                rdn, rm = op & 7, (op >> 3) & 7
                registers[rdn] = (registers[rdn] * registers[rm]) & 0xFFFFFFFF
            elif op & 0xF800 == 0x8000:  # strh Rd,[Rb,#imm5*2]
                rd, rb, imm = op & 7, (op >> 3) & 7, ((op >> 6) & 0x1F) * 2
                self._write(registers[rb] + imm,
                            (registers[rd] & 0xFFFF).to_bytes(2, 'little'))
            else:
                raise AssertionError('unsupported Thumb opcode %#06x at %#x' % (op, pc - 2))
        raise AssertionError('Thumb routine did not return')

    @staticmethod
    def assert_stop(lr):
        if lr != STOP | 1:
            raise AssertionError('unexpected return target %#x' % lr)

    def _range(self, address, size):
        start = address - VIEW
        if not 0 <= start <= start + size <= len(self.memory):
            raise AssertionError('memory access outside canaried BagView')
        return start

    def _read(self, address, size):
        at = self._range(address, size)
        return self.memory[at:at + size]

    def _write(self, address, data):
        at = self._range(address, len(data))
        self.memory[at:at + len(data)] = data

    def call_setter(self, pocket_id, position, slots):
        self.memory[:] = bytes([0xA5]) * VIEW_BYTES
        registers = [0] * 16
        registers[0:4] = [VIEW, slots, pocket_id, position]
        registers[14] = STOP | 1
        self._run(B.SETTER, registers)
        return bytes(self.memory)

    def call_flag_setter(self, initial):
        self.memory[:] = bytes(VIEW_BYTES)
        self._write(VIEW + 0x76, initial.to_bytes(2, 'little'))
        registers = [0] * 16
        registers[0], registers[14] = VIEW, STOP | 1
        self._run(B.FLAG_SETTER, registers)
        return int.from_bytes(self._read(VIEW + 0x76, 2), 'little')


def bench(rom):
    return Bench(rom) if unicorn_works() else MiniThumbBench(rom)


def expected_view(entry, pocket_id, slots):
    expected = bytearray(bytes([0xA5]) * VIEW_BYTES)
    expected[entry * POCKET_BYTES + 4:entry * POCKET_BYTES + 8] = slots.to_bytes(4, 'little')
    expected[entry * POCKET_BYTES + 12] = pocket_id
    return bytes(expected)


class BagViewPositionRomTests(unittest.TestCase):
    def test_retail_and_fixed_twelve_sequence_matrix_en_it(self):
        """Executes the demonstrated retail failure, nine controls and two confutations."""
        sequences = ([(i, i, 'all-pockets-control') for i in range(8)]
                     + [(0, 0, 'single-items-control'),
                        (4, 0, 'single-berries-natural'),
                        (7, 1, 'identity-permutation'),
                        (4, 3, 'identity-permutation')])
        self.assertEqual(len(sequences), 12)
        for language in V4:
            before = candidate(self, language)
            after, _ = B.apply(before, language)
            for pocket_id, position, case in sequences:
                slots = 0x02340000 | pocket_id
                retail = bench(before).call_setter(pocket_id, position, slots)
                fixed = bench(after).call_setter(pocket_id, position, slots)
                with self.subTest(language=language, case=case,
                                  pocket_id=pocket_id, position=position):
                    self.assertEqual(retail, expected_view(pocket_id, pocket_id, slots))
                    self.assertEqual(fixed, expected_view(position, pocket_id, slots))
                    self.assertEqual(retail == fixed, pocket_id == position)

    def test_installed_thumb_uses_position_for_stride_and_retargets_neighbour(self):
        """Catches indexing by pocket ID even when Unicorn is unavailable."""
        before = candidate(self, 'EN')
        after, _ = B.apply(before, 'EN')
        arm = Arm9.from_bytes(after)
        # Hand-derived Thumb-1: r3=position; 4p+8p; identity remains in r2.
        self.assertEqual(arm.leggi(B.SETTER, 14),
                         bytes.fromhex('9b00c0185b00c018416002737047'))
        self.assertEqual(arm.leggi(B.FLAG_SETTER, 12),
                         bytes.fromhex('012176300288114301807047'))
        self.assertEqual(bl_decode(B.FLAG_CALL, arm.leggi(B.FLAG_CALL, 4)),
                         B.FLAG_SETTER)

    def test_single_berry_view_uses_compact_slot_zero_and_preserves_canaries(self):
        """Catches the retail mutation that indexes by pocket ID instead of position."""
        for language in V4:
            before = candidate(self, language)
            after, receipt = B.apply(before, language)
            report = B.verify(before, after, receipt)
            view = bench(after).call_setter(pocket_id=4, position=0, slots=0x02345678)
            with self.subTest(language=language):
                self.assertTrue(report['position_indexed'])
                expected = bytearray(bytes([0xA5]) * VIEW_BYTES)
                expected[4:8] = bytes.fromhex('78563402')
                expected[12] = 4
                self.assertEqual(view, bytes(expected))

    def test_permuted_positions_keep_pocket_identity(self):
        """Catches a tempting but wrong fix that replaces both uses with position."""
        after, _ = B.apply(candidate(self, 'EN'), 'EN')
        for pocket_id, position in ((0, 7), (7, 1), (4, 3)):
            view = bench(after).call_setter(pocket_id, position, 0x02340000 | pocket_id)
            with self.subTest(pocket_id=pocket_id, position=position):
                at = position * POCKET_BYTES
                self.assertEqual(int.from_bytes(view[at + 4:at + 8], 'little'),
                                 0x02340000 | pocket_id)
                self.assertEqual(view[at + 12], pocket_id)

    def test_relocated_flag_setter_and_its_only_callsite_survive(self):
        """Catches overwriting the neighbour without moving its entry and direct BL."""
        for language in V4:
            before = candidate(self, language)
            after, receipt = B.apply(before, language)
            with self.subTest(language=language):
                self.assertEqual(direct_bl_calls(before, B.ORIGINAL_FLAG_SETTER), [B.FLAG_CALL])
                self.assertEqual(direct_bl_calls(after, B.ORIGINAL_FLAG_SETTER), [])
                self.assertEqual(direct_bl_calls(after, B.FLAG_SETTER), [B.FLAG_CALL])
                runner = bench(after)
                self.assertEqual(runner.call_flag_setter(0xA5A4), 0xA5A5)
                self.assertEqual(B.verify(before, after, receipt)['flag_call_target'], B.FLAG_SETTER)

    def test_reader_rejects_foreign_preimage_receipt_and_extra_delta(self):
        before = candidate(self, 'EN')
        after, receipt = B.apply(before, 'EN')
        damaged = bytearray(after)
        damaged[0x300] ^= 1
        with self.assertRaisesRegex(ValueError, 'outside'):
            B.verify(before, bytes(damaged), {**receipt,
                     'output_sha256': hashlib.sha256(damaged).hexdigest()})
        with self.assertRaisesRegex(ValueError, 'receipt'):
            B.verify(before, after, {**receipt, 'stage': 'foreign'})
        with self.assertRaisesRegex(ValueError, 'receipt'):
            B.verify(before, after, {**receipt, 'language': 'IT'})
        with self.assertRaisesRegex(ValueError, 'receipt'):
            B.verify(before, after, {**receipt, 'extra': True})
        damaged = bytearray(before)
        at = Arm9.from_bytes(before).off(B.SETTER, 1)
        damaged[at] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            B.apply(bytes(damaged), 'EN')
        with self.assertRaisesRegex(ValueError, 'preimage'):
            B.apply(after, 'EN')


if __name__ == '__main__':
    unittest.main()
