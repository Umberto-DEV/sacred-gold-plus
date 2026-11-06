"""Synthetic map-resource envelope regressions; no cartridge inputs."""
from dataclasses import FrozenInstanceError, replace
import unittest

from .map_resources import LandData, Matrix

# Little-endian two-cell matrix: headers 0x1234/0xabcd, heights 0/255,
# land indices 0xffff/0x0102. Removing/reordering any section breaks this.
MATRIX = bytes.fromhex('02 01 01 01 02 41 42 34 12 cd ab 00 ff ff ff 02 01')
# BGS must precede the 1024 permission cells, including its nonempty payload.
LAND = (bytes.fromhex('00 08 00 00 03 00 00 00 02 00 00 00 01 00 00 00'
                      '34 12 04 00 aa bb cc dd')
        + b'\x01\x80' * 1024 + b'BLDMD!')


class MatrixTests(unittest.TestCase):
    def test_sections_have_independent_little_endian_meaning(self):
        want = Matrix(2, 1, b'AB', (0x1234, 0xabcd), (0, 255), (65535, 258))
        self.assertEqual(Matrix.parse(MATRIX), want)
        self.assertEqual(want.encode(), MATRIX)

    def test_absent_sections_remain_absent(self):
        raw = bytes.fromhex('01 01 00 00 00 ff ff')
        want = Matrix(1, 1, b'', None, None, (65535,))
        self.assertEqual(Matrix.parse(raw), want)
        self.assertEqual(want.encode(), raw)

    def test_each_optional_section_can_be_present_alone(self):
        for raw, want in (
            (bytes.fromhex('01 01 01 00 00 02 01 04 03'),
             Matrix(1, 1, b'', (258,), None, (772,))),
            (bytes.fromhex('01 01 00 01 00 ff 04 03'),
             Matrix(1, 1, b'', None, (255,), (772,))),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(Matrix.parse(raw), want)
                self.assertEqual(want.encode(), raw)

    def test_native_capacity_and_name_limit_are_usable(self):
        raw = bytes((47, 17, 0, 0, 16)) + b'0123456789abcdef' + b'\xff\xff' * 799
        want = Matrix(47, 17, b'0123456789abcdef', None, None, (65535,) * 799)
        self.assertEqual(Matrix.parse(raw), want)
        self.assertEqual(want.encode(), raw)

    def test_dimensions_cell_capacity_and_name_overflow_are_rejected(self):
        for raw in (b'\0\1\0\0\0', b'\1\0\0\0\0',
                    bytes((40, 20, 0, 0, 0)) + b'\0' * 1600,
                    bytes((1, 1, 0, 0, 17)) + b'x' * 17 + b'\0\0'):
            with self.subTest(raw=raw[:5]), self.assertRaises(ValueError):
                Matrix.parse(raw)

    def test_noncanonical_presence_flags_are_explicitly_unsupported(self):
        for raw in (bytes.fromhex('01 01 02 00 00 01 00 02 00'),
                    bytes.fromhex('01 01 00 ff 00 00 02 00')):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                Matrix.parse(raw)

    def test_every_truncation_and_extra_byte_is_rejected(self):
        for raw in [MATRIX[:i] for i in range(len(MATRIX))] + [MATRIX + b'\0']:
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                Matrix.parse(raw)

    def test_constructed_values_cannot_overflow_or_truncate(self):
        good = Matrix(1, 1, b'', (0,), (0,), (0,))
        for field, bad in (
            ('width', 0), ('height', 256), ('width', True), ('height', 1.0),
            ('name', b'x' * 17), ('name', bytearray(b'A')),
            ('headers', ()), ('headers', (-1,)), ('headers', (65536,)),
            ('altitudes', (256,)), ('altitudes', (False,)),
            ('lands', ()), ('lands', (65536,)), ('lands', (0, 1)),
            ('lands', [0]), ('headers', [0]), ('altitudes', [0]),
        ):
            with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                replace(good, **{field: bad}).encode()

    def test_instances_are_immutable(self):
        matrix = Matrix(1, 1, b'', None, None, (0,))
        with self.assertRaises(FrozenInstanceError):
            matrix.width = 2


class LandDataTests(unittest.TestCase):
    def test_variable_bgs_precedes_permissions_and_opaque_sections(self):
        want = LandData(b'\xaa\xbb\xcc\xdd', b'\x01\x80' * 1024, b'BLD', b'MD', b'!')
        self.assertEqual(LandData.parse(LAND), want)
        self.assertEqual(want.encode(), LAND)

    def test_empty_opaque_sections_are_preserved(self):
        raw = bytes.fromhex('00 08 00 00') + bytes(12) + b'\x34\x12\0\0' + bytes(2048)
        want = LandData(b'', bytes(2048), b'', b'', b'')
        self.assertEqual(LandData.parse(raw), want)
        self.assertEqual(want.encode(), raw)

    def test_permission_edit_uses_x_z_order_and_preserves_every_other_byte(self):
        original = LandData(b'\xaa\xbb\xcc\xdd', b'\x01\x80' * 1024, b'BLD', b'MD', b'!')
        # x=31,z=0 is byte 62; x=0,z=31 is byte 1984, not the same cell.
        for x, z, offset in ((0, 0, 24), (31, 0, 86), (0, 31, 2008), (31, 31, 2070)):
            with self.subTest(x=x, z=z):
                edited = original.with_permission(x, z, 0x1234)
                self.assertIsInstance(edited, LandData)
                expected = LAND[:offset] + b'\x34\x12' + LAND[offset + 2:]
                self.assertEqual(edited.encode(), expected)
                self.assertEqual(original.encode(), LAND)

    def test_invalid_permission_coordinates_and_values_are_rejected(self):
        land = LandData(b'', bytes(2048), b'', b'', b'')
        for x, z, value in ((-1, 0, 0), (32, 0, 0), (0, -1, 0), (0, 32, 0),
                            (0, 0, -1), (0, 0, 65536), (True, 0, 0),
                            (0, 1.0, 0), (0, 0, False)):
            with self.subTest(x=x, z=z, value=value), self.assertRaises(ValueError):
                land.with_permission(x, z, value)

    def test_absent_permissions_are_unsupported_by_fixed_native_readers(self):
        raw = bytes(16) + b'\x34\x12\0\0'
        with self.assertRaises(ValueError):
            LandData.parse(raw)
        with self.assertRaises(ValueError):
            LandData(b'', b'', b'', b'', b'').encode()

    def test_signature_sizes_and_trailing_data_are_checked(self):
        malformed = [LAND[:i] for i in (0, 15, 16, 18, 19, 23, 24, 2071, 2077)]
        malformed += [LAND + b'\0', LAND[:16] + b'\x35\x12' + LAND[18:],
                      LAND[:18] + b'\xff\xff' + LAND[20:],
                      b'\xff\x07\0\0' + LAND[4:],
                      LAND[:4] + b'\xff\xff\xff\xff' + LAND[8:]]
        for raw in malformed:
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                LandData.parse(raw)

    def test_constructed_payloads_must_be_immutable_and_lengths_representable(self):
        good = LandData(b'', bytes(2048), b'', b'', b'')
        for field, bad in (('bgs', b'x' * 65536), ('permissions', bytes(2046)),
                           ('permissions', bytearray(2048)), ('bgs', []),
                           ('buildings', bytearray()), ('model', ''), ('collision', None)):
            with self.subTest(field=field), self.assertRaises(ValueError):
                replace(good, **{field: bad}).encode()

    def test_instances_are_immutable(self):
        land = LandData(b'', bytes(2048), b'', b'', b'')
        with self.assertRaises(FrozenInstanceError):
            land.permissions = b''



if __name__ == "__main__":
    unittest.main()
