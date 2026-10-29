import ctypes as C
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def fnv(data):
    value = 2166136261
    for byte in data:
        value = ((value ^ byte) * 16777619) & 0xffffffff
    return value


class StrategyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        target = Path(cls.temp.name) / 'strategy.dylib'
        subprocess.run(['clang', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        str(ROOT / 'strategy.c'), '-o', str(target)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(target))
        cls.lib.strategy_apply.argtypes = [C.c_void_p, C.c_uint32, C.c_uint32, C.c_uint32, C.c_void_p]
        cls.lib.strategy_apply.restype = C.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def fixture(self, bad_offset=False):
        original = bytearray(range(108))
        struct.pack_into('<HH', original, 98, 21, 397)
        updated = bytearray(original)
        struct.pack_into('<HH', updated, 98, 89, 360)
        config = (struct.pack('<IHH', 0x31544753, 1, 2) +
                  struct.pack('<HHIIBBBB', 33, 0, fnv(original), fnv(updated), 3, 6, 108, 2) +
                  struct.pack('<4H', 98, 21, 89, 0) +
                  struct.pack('<4H', 110 if bad_offset else 100, 397, 360, 0))
        return bytes(original), bytes(updated), C.create_string_buffer(config)

    def test_plus_changes_only_reviewed_moves_once(self):
        original, updated, config = self.fixture()
        buffer = C.create_string_buffer(original)
        self.assertEqual(self.lib.strategy_apply(buffer, 33, 0x603, 1, config), 2)
        self.assertEqual(buffer.raw[:108], updated)
        self.assertEqual(self.lib.strategy_apply(buffer, 33, 0x603, 1, config), 0)
        self.assertEqual(buffer.raw[:108], updated)

    def test_classic_unknown_team_and_bad_record_preserve_every_byte(self):
        original, _, config = self.fixture()
        for trainer, kind, plus in ((33, 0x603, 0), (999, 0x603, 1), (33, 0x601, 1)):
            buffer = C.create_string_buffer(original)
            self.assertEqual(self.lib.strategy_apply(buffer, trainer, kind, plus, config), 0)
            self.assertEqual(buffer.raw[:108], original)
        modified = bytearray(original); modified[0] ^= 1
        buffer = C.create_string_buffer(bytes(modified))
        self.assertEqual(self.lib.strategy_apply(buffer, 33, 0x603, 1, config), 0)
        self.assertEqual(buffer.raw[:108], modified)

    def test_all_changes_validated_before_first_mutation(self):
        original, _, config = self.fixture(bad_offset=True)
        buffer = C.create_string_buffer(original)
        self.assertEqual(self.lib.strategy_apply(buffer, 33, 0x603, 1, config), 0)
        self.assertEqual(buffer.raw[:108], original)


if __name__ == '__main__':
    unittest.main()
