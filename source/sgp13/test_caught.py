"""Exact hook boundaries; native rendering is exercised by test_caught_arm."""
import unittest
from sgp13 import caught


class CaughtPatchTests(unittest.TestCase):
    def test_only_trainer_icon_mask_is_removed(self):
        image = bytes(20) + bytes.fromhex('e868d5f7eafe0121084201d044480440') + bytes(30)
        result = caught.patch_image(image, 0x022649F2)
        self.assertEqual(result[34:36], bytes.fromhex('c046'))
        self.assertEqual(result[:34], image[:34])
        self.assertEqual(result[36:], image[36:])

    def test_changed_surrounding_instruction_refused(self):
        image = bytearray(bytes(20) + caught.CONTEXT + bytes(30))
        image[23] ^= 1
        with self.assertRaisesRegex(ValueError, 'preimage'):
            caught.patch_image(image, 0x022649F2)

    def test_wrong_overlay_and_repeat_refused(self):
        with self.assertRaises(ValueError):
            caught.patch_image(bytes(100), 0x02000000)
        image = bytes(20) + caught.CONTEXT + bytes(30)
        result = caught.patch_image(image, 0x022649F2)
        with self.assertRaises(ValueError):
            caught.patch_image(result, 0x022649F2)


if __name__ == '__main__':
    unittest.main()
