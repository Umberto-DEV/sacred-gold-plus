"""Class A contracts for HG-B08 transformed level-up stat preservation."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                               UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
                               UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                               UC_ARM_REG_R7, UC_ARM_REG_SP)

from . import transform_reload as T


CTX = 0x02380000
BSYS = 0x02370000
MON = 0x02360000
STACK = 0x023F0000
STOP = 0x023FF000
BATMON = 0x2D40
TRANSFORM = 1 << 21
CANARY = 0xA5A5A5A5


def synthetic_overlay():
    image = bytearray(T.OVERLAY_SIZE)
    at = T.RELOAD_ADDRESS - T.OVERLAY_BASE
    image[at:at + T.RELOAD_BYTES] = T.RELOAD_PREIMAGE
    at = T.LITERAL_ADDRESS - T.OVERLAY_BASE
    image[at:at + len(T.LITERAL_PREIMAGE)] = T.LITERAL_PREIMAGE
    return bytes(image)


class ReloadBench:
    def __init__(self, code):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(0x02000000, 0x400000)
        self.uc.mem_write(T.RELOAD_ADDRESS, code)
        self.calls = []
        self.fields = {
            165: 101, 166: 102, 167: 103, 168: 104, 169: 105,
            161: 50, 9: 101, 163: 83, 164: 166, 8: 654321,
            **{54 + i: 501 + i for i in range(4)},
            **{58 + i: 21 + i for i in range(4)},
            **{62 + i: (i + 3) % 4 for i in range(4)},
        }
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    def _return(self, value):
        self.uc.reg_write(UC_ARM_REG_R0, value)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def _hook(self, uc, address, size, unused):
        if address == T.GET_PARTY_MON:
            self.calls.append(('party', uc.reg_read(UC_ARM_REG_R1),
                               uc.reg_read(UC_ARM_REG_R2)))
            self._return(MON)
        elif address == T.GET_MON_DATA:
            field = uc.reg_read(UC_ARM_REG_R1)
            self.calls.append(('data', field))
            self._return(self.fields[field])

    def run(self, transformed, mimic=0):
        uc = self.uc
        uc.mem_write(CTX, bytes(0x4000))
        self.calls = []
        base = CTX + BATMON
        for i, value in enumerate((301, 302, 303, 304, 305)):
            uc.mem_write(base + 2 + i * 2, value.to_bytes(2, 'little'))
        for i, value in enumerate((401, 402, 403, 404)):
            uc.mem_write(base + 12 + i * 2, value.to_bytes(2, 'little'))
            uc.mem_write(base + 44 + i, bytes((11 + i,)))
            uc.mem_write(base + 48 + i, bytes((i,)))
        uc.mem_write(base + 52, bytes((49, 100)))
        uc.mem_write(base + 76, (77).to_bytes(4, 'little'))
        uc.mem_write(base + 80, (155).to_bytes(4, 'little'))
        uc.mem_write(base + 100, (123456).to_bytes(4, 'little'))
        uc.mem_write(base + 112, (TRANSFORM if transformed else 0).to_bytes(4, 'little'))
        uc.mem_write(base + 140, (mimic << 2).to_bytes(4, 'little'))
        for reg, value in ((UC_ARM_REG_R0, BSYS), (UC_ARM_REG_R1, CTX),
                           (UC_ARM_REG_R2, 0), (UC_ARM_REG_R3, 5),
                           (UC_ARM_REG_SP, STACK), (UC_ARM_REG_LR, STOP | 1)):
            uc.reg_write(reg, value)
        for reg in (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7):
            uc.reg_write(reg, CANARY)
        uc.emu_start(T.RELOAD_ADDRESS | 1, STOP, count=20_000)
        self.assert_abi()
        return {
            'stats': tuple(int.from_bytes(uc.mem_read(base + 2 + i * 2, 2), 'little')
                           for i in range(5)),
            'moves': tuple(int.from_bytes(uc.mem_read(base + 12 + i * 2, 2), 'little')
                           for i in range(4)),
            'pp': tuple(uc.mem_read(base + 44 + i, 1)[0] for i in range(4)),
            'ppups': tuple(uc.mem_read(base + 48 + i, 1)[0] for i in range(4)),
            'level_friendship': tuple(uc.mem_read(base + 52, 2)),
            'hp_max': (int.from_bytes(uc.mem_read(base + 76, 4), 'little'),
                       int.from_bytes(uc.mem_read(base + 80, 4), 'little')),
            'exp': int.from_bytes(uc.mem_read(base + 100, 4), 'little'),
            'fields': [row[1] for row in self.calls if row[0] == 'data'],
        }

    def assert_abi(self):
        if self.uc.reg_read(UC_ARM_REG_PC) & ~1 != STOP:
            raise AssertionError('candidate did not return')
        if self.uc.reg_read(UC_ARM_REG_SP) != STACK:
            raise AssertionError('candidate changed caller SP')
        if any(self.uc.reg_read(reg) != CANARY for reg in
               (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7)):
            raise AssertionError('candidate changed a callee-saved register')


class TransformReloadCompiler(unittest.TestCase):
    def test_exact_function_replacement(self):
        with tempfile.TemporaryDirectory() as work:
            payload, receipt = T.compile_native(Path(work))
        self.assertEqual(len(payload), T.RELOAD_BYTES)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), T.PAYLOAD_SHA256)
        self.assertEqual(receipt['entry'], T.RELOAD_ADDRESS | 1)
        self.assertEqual(receipt['party_target'], T.GET_PARTY_MON | 1)
        self.assertEqual(receipt['data_target'], T.GET_MON_DATA | 1)


class TransformReloadOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='transform-reload-test-')
        cls.payload, cls.compiled = T.compile_native(Path(cls.work.name))

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def test_exact_owned_span_and_mutants(self):
        before = synthetic_overlay()
        after, receipt = T.patch_overlay(before, self.payload)
        self.assertTrue(T.verify_overlay(before, after, self.payload, receipt)['ok'])
        at = T.RELOAD_ADDRESS - T.OVERLAY_BASE
        self.assertEqual(after[at:at + T.RELOAD_BYTES], self.payload)
        self.assertEqual(after[T.LITERAL_ADDRESS - T.OVERLAY_BASE:
                               T.LITERAL_ADDRESS - T.OVERLAY_BASE + len(T.LITERAL_PREIMAGE)],
                         T.LITERAL_PREIMAGE)
        mutant = bytearray(after); mutant[0] ^= 1
        with self.assertRaises(ValueError):
            T.verify_overlay(before, bytes(mutant), self.payload, receipt)
        bad = bytearray(before); bad[at + 10] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            T.patch_overlay(bytes(bad), self.payload)

    def test_transform_preserves_only_copied_stats(self):
        row = ReloadBench(self.payload).run(True)
        self.assertEqual(row['stats'], (301, 302, 303, 304, 305))
        self.assertEqual(row['moves'], (401, 402, 403, 404))
        self.assertEqual(row['pp'], (11, 12, 13, 14))
        self.assertEqual(row['ppups'], (0, 1, 2, 3))
        self.assertEqual(row['level_friendship'], (50, 101))
        self.assertEqual(row['hp_max'], (83, 166))
        self.assertEqual(row['exp'], 123456)
        self.assertEqual(row['fields'], [161, 9, 163, 164])

    def test_ordinary_reload_and_mimic_control(self):
        row = ReloadBench(self.payload).run(False, mimic=1 << 2)
        self.assertEqual(row['stats'], (101, 102, 103, 104, 105))
        self.assertEqual(row['moves'], (501, 502, 403, 504))
        self.assertEqual(row['pp'], (21, 22, 13, 24))
        self.assertEqual(row['ppups'], (3, 0, 2, 2))
        self.assertEqual(row['exp'], 654321)
        self.assertNotIn(56, row['fields'])
        self.assertNotIn(60, row['fields'])
        self.assertNotIn(64, row['fields'])


if __name__ == '__main__':
    unittest.main()
