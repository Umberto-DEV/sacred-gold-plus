"""German Summary glyphs preserve native String layout and Thumb ownership."""
import hashlib
import struct
import unittest
from unittest import mock

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R6, UC_ARM_REG_R7)

from . import summary_labels as labels


class SummaryLabelsTests(unittest.TestCase):
    def image(self):
        # Synthetic wrapper surroundings, with the actual bounded glyph block.
        wrapper = bytearray(b'\xa5' * labels.WRAPPER_BYTES)
        offset = labels.LABELS_ADDRESS - labels.WRAPPER_ADDRESS
        wrapper[offset:offset+16] = labels.LABELS_PREIMAGE
        legend_at = len(wrapper) + 64
        image = bytes(wrapper) + bytes(64) + labels.LEGEND_PREIMAGE + bytes(32)

        def locate(address, size):
            if labels.WRAPPER_ADDRESS <= address and address+size <= labels.WRAPPER_ADDRESS+len(wrapper):
                return address - labels.WRAPPER_ADDRESS
            if address == labels.LEGEND_ADDRESS and size == len(labels.LEGEND_PREIMAGE):
                return legend_at
            raise AssertionError('unexpected owned address')

        return image, locate, hashlib.sha256(wrapper).hexdigest()

    def test_only_german_owns_any_bytes(self):
        for locale in ('EN', 'IT', 'FR', 'ES'):
            with self.subTest(locale=locale):
                self.assertEqual(labels.owned_spans(locale), ())
                self.assertEqual(labels.apply(b'unchanged', lambda *a: self.fail('no-op lookup'), locale), b'unchanged')
        self.assertEqual(labels.owned_spans('DE'),
                         ((0x01FF9370, 16), (0x023D4C30, 54)))
        with self.assertRaisesRegex(ValueError, 'locale'):
            labels.apply(b'', lambda *a: 0, 'XX')

    def test_legend_uses_the_same_native_units_header_and_padding(self):
        before, after = labels.LEGEND_PREIMAGE, labels.LEGEND_REPLACEMENT
        self.assertEqual(len(before), 54)
        self.assertEqual(len(after), 54)
        self.assertEqual(before[:8], struct.pack('<HHI', 23, 23, 0xB6F8D2EC))
        self.assertEqual(after[:8], before[:8])
        # L:FP SELECT:Wert. R:DV, followed by the sole terminator.
        self.assertEqual(struct.unpack_from('<23H', after, 8),
                         (0x136, 0x1C4, 0x130, 0x13A, 0x1DE, 0x13D, 0x12F,
                          0x136, 0x12F, 0x12D, 0x13E, 0x1C4, 0x141, 0x149,
                          0x156, 0x158, 0x1AE, 0x1DE, 0x13C, 0x1C4, 0x12E,
                          0x140, 0xFFFF))

    def test_synthetic_admitted_image_changes_only_the_declared_spans(self):
        image, locate, digest = self.image()
        with mock.patch.object(labels, 'WRAPPER_SHA256', digest):
            after = labels.apply(image, locate, 'DE')
        spans = [(locate(a, n), locate(a, n)+n) for a, n in labels.owned_spans('DE')]
        self.assertEqual(len(after), len(image))
        self.assertTrue(all(any(a <= i < b for a, b in spans)
                            for i, (x, y) in enumerate(zip(image, after)) if x != y))
        self.assertEqual(after[40:56], labels.LABELS_REPLACEMENT)
        at = locate(labels.LEGEND_ADDRESS, 54)
        self.assertEqual(after[at:at+54], labels.LEGEND_REPLACEMENT)
        self.assertEqual(after[at+54:at+56], image[at+54:at+56])

    def test_foreign_wrapper_or_string_refuses_before_returning_a_patch(self):
        image, locate, digest = self.image()
        with self.assertRaisesRegex(ValueError, 'wrapper preimage'):
            labels.apply(image, locate, 'DE')
        with mock.patch.object(labels, 'WRAPPER_SHA256', digest):
            bad = bytearray(image); bad[0] ^= 1
            with self.assertRaisesRegex(ValueError, 'wrapper preimage'):
                labels.apply(bytes(bad), locate, 'DE')
            for delta in (0, 8, 52):
                bad = bytearray(image)
                bad[locate(labels.LEGEND_ADDRESS, 54)+delta] ^= 1
                with self.assertRaisesRegex(ValueError, 'legend preimage'):
                    labels.apply(bytes(bad), locate, 'DE')

    def test_even_a_matching_wrapper_pin_cannot_admit_another_glyph_block(self):
        image, locate, _ = self.image()
        bad = bytearray(image); bad[40] ^= 1
        digest = hashlib.sha256(bad[:labels.WRAPPER_BYTES]).hexdigest()
        with mock.patch.object(labels, 'WRAPPER_SHA256', digest):
            with self.assertRaisesRegex(ValueError, 'label preimage'):
                labels.apply(bytes(bad), locate, 'DE')

    def test_actual_thumb_instructions_write_fp_or_dv_and_nothing_else(self):
        # Execute the exact replacement instruction bytes, not a Python model.
        for selector, expected in ((0, (0x130, 0x13A)), (1, (0x12E, 0x140))):
            with self.subTest(selector=selector):
                cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
                cpu.mem_map(0x01FF9000, 4096)
                cpu.mem_map(0x02200000, 4096)
                cpu.mem_write(labels.LABELS_ADDRESS, labels.LABELS_REPLACEMENT)
                before = bytes([0xA5])*64
                cpu.mem_write(0x02200000, before)
                initial = {UC_ARM_REG_R0: 0x1234, UC_ARM_REG_R1: 0xFFFF,
                           UC_ARM_REG_R2: 0x02200000, UC_ARM_REG_R3: 0x5678,
                           UC_ARM_REG_R4: 0xB6F8D2EC, UC_ARM_REG_R5: 0x0208C779,
                           UC_ARM_REG_R6: selector, UC_ARM_REG_R7: 0x4321}
                for reg, value in initial.items(): cpu.reg_write(reg, value)
                cpu.emu_start(labels.LABELS_ADDRESS | 1, labels.LABELS_ADDRESS+16, count=8)
                after = bytes(cpu.mem_read(0x02200000, 64))
                self.assertEqual(after, before[:8]+struct.pack('<HH', *expected)+before[12:])
                for reg in (UC_ARM_REG_R0, UC_ARM_REG_R2, UC_ARM_REG_R3,
                            UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R7):
                    self.assertEqual(cpu.reg_read(reg), initial[reg])


if __name__ == '__main__':
    unittest.main()
