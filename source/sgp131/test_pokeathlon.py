"""HG-P01: the friendship-room summary must retain the full medal count."""
import hashlib
import unittest

from . import pokeathlon as p


BASE, SIZE = 0x021E5900, 0x4D00
WRITER = (0x021E6FD0, 0x021E7060)
ACCESSOR = (0x021E7078, 0x021E7088)
SITES = (
    (0x021E703A, bytes.fromhex('a075'), bytes.fromhex('6083')),
    (0x021E7082, bytes.fromhex('a07d'), bytes.fromhex('608b')),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def synthetic():
    image = bytearray((index * 19 + 7) & 0xFF for index in range(SIZE))
    for address, before, _ in SITES:
        image[address - BASE:address - BASE + len(before)] = before
    return bytes(image)


def pin(image, span):
    return digest(image[span[0] - BASE:span[1] - BASE])


class PokeathlonPatchTests(unittest.TestCase):
    def test_exact_two_halfwords_move_the_count_to_u16_padding(self):
        before = synthetic()
        after, report = p.patch_overlay(
            before, writer_sha256=pin(before, WRITER),
            accessor_sha256=pin(before, ACCESSOR))
        expected = bytearray(before)
        for address, _, replacement in SITES:
            expected[address - BASE:address - BASE + 2] = replacement
        self.assertEqual(after, bytes(expected))
        self.assertEqual(p.PATCHES, SITES)
        self.assertEqual(report['summary_offset_before'], 0x16)
        self.assertEqual(report['summary_offset_after'], 0x1A)
        self.assertEqual(report['summary_width_before'], 1)
        self.assertEqual(report['summary_width_after'], 2)
        self.assertEqual(report['changed_offsets'], [
            address - BASE + index
            for address, old, new in SITES
            for index, (left, right) in enumerate(zip(old, new)) if left != right])
        self.assertEqual(p.verify_images(before, after)['changed_bytes'], 4)

    def test_context_function_size_and_repeat_fail_closed(self):
        before = synthetic()
        writer_pin, accessor_pin = pin(before, WRITER), pin(before, ACCESSOR)
        for address, _, _ in SITES:
            damaged = bytearray(before)
            damaged[address - BASE] ^= 1
            with self.assertRaisesRegex(ValueError, 'preimage'):
                p.patch_overlay(
                    bytes(damaged),
                    writer_sha256=pin(bytes(damaged), WRITER),
                    accessor_sha256=pin(bytes(damaged), ACCESSOR))
        damaged = bytearray(before)
        damaged[WRITER[0] - BASE] ^= 1
        with self.assertRaisesRegex(ValueError, 'writer'):
            p.patch_overlay(bytes(damaged), writer_sha256=writer_pin,
                            accessor_sha256=accessor_pin)
        damaged = bytearray(before)
        damaged[ACCESSOR[1] - BASE - 1] ^= 1
        with self.assertRaisesRegex(ValueError, 'accessor'):
            p.patch_overlay(bytes(damaged), writer_sha256=writer_pin,
                            accessor_sha256=accessor_pin)
        after, _ = p.patch_overlay(before, writer_sha256=writer_pin,
                                   accessor_sha256=accessor_pin)
        with self.assertRaises(ValueError):
            p.patch_overlay(after, writer_sha256=pin(after, WRITER),
                            accessor_sha256=pin(after, ACCESSOR))
        with self.assertRaisesRegex(ValueError, 'size'):
            p.patch_overlay(before[:-1], writer_sha256=writer_pin,
                            accessor_sha256=accessor_pin)

    def test_verifier_rejects_extra_or_missing_bytes(self):
        before = synthetic()
        after, _ = p.patch_overlay(before, writer_sha256=pin(before, WRITER),
                                   accessor_sha256=pin(before, ACCESSOR))
        damaged = bytearray(after)
        damaged[0] ^= 1
        with self.assertRaises(ValueError):
            p.verify_images(before, bytes(damaged))
        for address, old, _ in SITES:
            damaged = bytearray(after)
            damaged[address - BASE:address - BASE + 2] = old
            with self.assertRaises(ValueError):
                p.verify_images(before, bytes(damaged))


if __name__ == '__main__':
    unittest.main()
