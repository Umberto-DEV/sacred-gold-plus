"""Boundary fault tests of the production transaction against native API seams."""
import ctypes as C
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
READ = C.CFUNCTYPE(C.c_uint32, C.c_void_p, C.c_int, C.c_void_p)
WRITE = C.CFUNCTYPE(None, C.c_void_p, C.c_int, C.c_void_p)
RECALC = C.CFUNCTYPE(None, C.c_void_p)
CHARGE = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint32, C.c_uint32)


class API(C.Structure):
    _fields_ = [('read', READ), ('write', WRITE), ('recalculate', RECALC), ('charge', CHARGE)]


class Request(C.Structure):
    _fields_ = [('pid', C.c_uint32), ('ot', C.c_uint32), ('species', C.c_uint16),
                ('kind', C.c_uint8), ('policy', C.c_uint8), ('iv_kind', C.c_uint8),
                ('stat', C.c_uint8), ('value', C.c_uint8), ('reserved', C.c_uint8),
                ('expected', C.c_uint8 * 6), ('target', C.c_uint8 * 6)]


class Transactions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        lib = Path(cls.temp.name) / 'transaction.dylib'
        subprocess.run(['clang', '-shared', '-fPIC', '-std=c99', '-Wall', '-Wextra', '-Werror',
                        str(ROOT / 'transaction.c'),
                        str(ROOT.parent / 'training/sorgenti/core.c'), '-o', str(lib)],
                       check=True, capture_output=True)
        cls.lib = C.CDLL(str(lib))
        cls.lib.sgp_training_transaction.argtypes = [C.POINTER(API), C.c_void_p, C.c_void_p,
                                                       C.POINTER(Request), C.POINTER(C.c_uint32)]
        cls.lib.sgp_training_transaction.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.mon = (C.c_ubyte * 236)()
        for offset, value in ((0, 123), (4, 456), (8, 25), (32, 0), (36, 100)):
            C.c_uint32.from_buffer(self.mon, offset).value = value
        self.mon[20:26] = [12] * 6
        self.mon[40:236] = [(i * 13) & 255 for i in range(196)]
        self.charges = []; self.recalcs = 0
        self.affordable = True; self.fail_set = False; self.corrupt_on_read = False
        offsets = {0: 0, 7: 4, 5: 8, 3: 12, 76: 16, 163: 32, 164: 36}

        def read(ptr, field, dest):
            if self.corrupt_on_read and field == 5:
                C.c_uint32.from_address(ptr + 12).value = 1
            if field in (1, 2):
                return 0
            if 70 <= field <= 75:
                return C.c_ubyte.from_address(ptr + 20 + field - 70).value
            if 13 <= field <= 18:
                return C.c_ubyte.from_address(ptr + 26 + field - 13).value
            return C.c_uint32.from_address(ptr + offsets[field]).value

        def write(ptr, field, value):
            if self.fail_set:
                return
            offset = 20 + field - 70 if field >= 70 else 26 + field - 13
            C.c_ubyte.from_address(ptr + offset).value = C.c_ubyte.from_address(value).value

        def recalc(ptr):
            self.recalcs += 1
            C.c_uint32.from_address(ptr + 36).value = 200

        def charge(context, currency, amount):
            self.charges.append((currency, amount))
            return self.affordable

        self.api = API(READ(read), WRITE(write), RECALC(recalc), CHARGE(charge))
        self.request = Request(123, 456, 25, 0, 1, 1, 2, 31, 0,
                               (C.c_uint8 * 6)(*[12] * 6), (C.c_uint8 * 6)())
        self.paid = C.c_uint32(0xdeadbeef)

    def run_transaction(self):
        return self.lib.sgp_training_transaction(C.byref(self.api), None, self.mon,
                                                 C.byref(self.request), C.byref(self.paid))

    def assert_rejected(self, result):
        before = bytes(self.mon)
        self.assertEqual(self.run_transaction(), result)
        self.assertEqual(bytes(self.mon), before)
        self.assertEqual(self.paid.value, 0xdeadbeef)

    def test_silver_changes_one_iv_preserves_identity_moves_and_fainted_hp(self):
        before = bytes(self.mon)
        self.assertEqual(self.run_transaction(), 0)
        self.assertEqual(list(self.mon[20:26]), [12, 12, 31, 12, 12, 12])
        self.assertEqual(bytes(self.mon[:20]), before[:20])
        self.assertEqual(bytes(self.mon[26:36]), before[26:36])
        self.assertEqual(bytes(self.mon[40:]), before[40:])
        self.assertEqual(self.charges, [(0, 1)])
        self.assertEqual((self.paid.value, self.recalcs), (1, 1))

    def test_gold_and_exact_zero(self):
        self.request.iv_kind = 2
        self.assertEqual(self.run_transaction(), 0)
        self.assertEqual(list(self.mon[20:26]), [31] * 6)
        self.assertEqual(self.charges, [(1, 1)])
        self.request.expected[:] = [31] * 6
        self.request.iv_kind = 0; self.request.stat = 3; self.request.value = 0
        self.assertEqual(self.run_transaction(), 0)
        self.assertEqual(self.mon[23], 0)

    def test_insufficient_payment_cannot_change_mon(self):
        self.affordable = False
        self.assert_rejected(4)
        self.assertEqual(self.charges, [(0, 1)])

    def test_egg_checksum_identity_and_stale_preview_reject_without_charge(self):
        for field, value, result in ((16, 1, 2), (12, 1, 1), (4, 999, 6), (22, 13, 6)):
            with self.subTest(field=field):
                self.setUp()
                if field == 22:
                    self.mon[field] = value
                else:
                    C.c_uint32.from_buffer(self.mon, field).value = value
                self.assert_rejected(result)
                self.assertEqual(self.charges, [])

    def test_checksum_validation_does_not_mark_original_as_bad(self):
        self.corrupt_on_read = True
        self.assert_rejected(1)
        self.assertEqual(self.charges, [])

    def test_noop_and_failed_native_setter_consume_nothing(self):
        self.mon[22] = 31; self.request.expected[2] = 31
        self.assert_rejected(3)
        self.assertEqual(self.charges, [])
        self.setUp(); self.fail_set = True
        self.assert_rejected(1)
        self.assertEqual(self.charges, [])

    def test_ev_increase_cost_and_unlimited_mode(self):
        self.request.kind = 1; self.request.policy = 2
        self.request.expected[:] = [0] * 6; self.request.target[:] = [252] * 6
        self.assertEqual(self.run_transaction(), 0)
        self.assertEqual(list(self.mon[26:32]), [252] * 6)
        self.assertEqual(self.charges, [(2, 151200)])

    def test_ev_reset_is_free_and_classic_overflow_rejected(self):
        self.request.kind = 1; self.request.expected[:] = [0] * 6
        self.request.target[:] = [252] * 6
        self.assert_rejected(1)
        self.assertEqual(self.charges, [])
        self.mon[26:32] = [252] * 6; self.request.expected[:] = [252] * 6
        self.request.target[:] = [0] * 6
        self.assertEqual(self.run_transaction(), 0)
        self.assertEqual(list(self.mon[26:32]), [0] * 6)
        self.assertEqual(self.charges, [])
        self.assertEqual(self.paid.value, 0)


if __name__ == '__main__':
    unittest.main()
