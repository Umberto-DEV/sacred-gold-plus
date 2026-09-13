"""Focused guards for the new composition, distinct from the reviewed lease."""
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_fixtures


def tearDownModule():
    test_fixtures.cleanup()


class SummaryBuilderTests(unittest.TestCase):
    def builder(self):
        path = HERE / 'build_summary_guide.py'
        self.assertTrue(path.is_file(), 'Native Summary composition is missing')
        spec = importlib.util.spec_from_file_location('guide_builder', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_code_cannot_overlap_text_or_persistent_state(self):
        b = self.builder()
        with self.assertRaisesRegex(ValueError, 'overlap'):
            b.check_budget(bytes(0x1780), b'abc')

    def test_unknown_glyph_is_rejected(self):
        b = self.builder()
        with self.assertRaisesRegex(ValueError, 'glyph'):
            b.encode_line('a☃', {'a': 1})

    def test_main_bl_preimage_is_required_before_mutation(self):
        b = self.builder()
        main = test_fixtures.r5_arm9(self)
        main.sections[0].data[0x88428] ^= 1
        before = [bytes(s.data) for s in main.sections]
        with self.assertRaisesRegex(ValueError, 'Main'):
            b.extend(main, b'\0' * 4, {'eviv_hook': b.CODE + 1, 'guide_exit_hook': b.CODE + 1}, b'\0' * 4)
        self.assertEqual([bytes(s.data) for s in main.sections], before)


if __name__ == '__main__':
    unittest.main()
