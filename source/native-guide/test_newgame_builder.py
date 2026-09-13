"""Composition guards: the Oak wrapper shares the one r5 ITCM allowance."""
import importlib.util
from pathlib import Path
import struct
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


class NewGameBuilderTests(unittest.TestCase):
    def builder(self):
        path = HERE / 'build_combined_guide.py'
        self.assertTrue(path.is_file(), 'Combined New Game composition is missing')
        spec = importlib.util.spec_from_file_location('combined_builder', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_combined_code_and_text_share_one_allowance(self):
        builder = self.builder()
        with self.assertRaisesRegex(ValueError, 'overlap|budget'):
            builder.check_budget(bytes(5000), bytes(1176))

    def test_oak_id_is_validated_before_any_template_mutation(self):
        builder = self.builder()
        image = bytearray(0x106078)
        struct.pack_into('<4I', image, 0x106068,
                         0x021e5901, 0x021e5995, 0x021e5b49, 54)
        before = bytes(image)
        symbols = {name: 0x01ff8881 for name in
                   ['oak_guide_init', 'oak_guide_main', 'oak_guide_exit']}
        with self.assertRaisesRegex(ValueError, 'Oak'):
            builder.patch_oak_template(image, symbols, 4)
        self.assertEqual(bytes(image), before)


if __name__ == '__main__':
    unittest.main()
