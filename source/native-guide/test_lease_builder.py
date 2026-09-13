import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import test_fixtures


def tearDownModule():
    test_fixtures.cleanup()

class LeaseBuilderGuards(unittest.TestCase):
    def builder(self):
        path=HERE/'build_lease_rom.py'
        self.assertTrue(path.exists(),'Bounded lease composer is missing')
        spec=importlib.util.spec_from_file_location('lease_builder',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_unknown_complete_base_rejected_before_creating_output(self):
        b=self.builder()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'unknown.nds';src.write_bytes(b'unknown')
            with self.assertRaisesRegex(ValueError,'Unknown complete Plus base'):
                b.build(src,root/'missing-charmap',root/'out')
            self.assertFalse((root/'out').exists())

    def test_existing_output_refused_before_reading_input(self):
        b=self.builder()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,'Output directory must be new'):
                b.build(Path('/missing'),Path('/missing'),Path(d))

    def test_wrong_r5_hook_preimage_rejected_without_mutation(self):
        b=self.builder();main=self.main()
        main.sections[0].data[0x88b40]^=1
        before=bytes(main.sections[1].data)
        with self.assertRaisesRegex(ValueError,'r5 input hook'):
            b.extend(main,b'\x00\x00',b.PROBE_BASE|1)
        self.assertEqual(bytes(main.sections[1].data),before)

    def test_wrong_itcm_size_rejected(self):
        b=self.builder();main=self.main();main.sections[1].data.extend(b'\0')
        with self.assertRaisesRegex(ValueError,'r5 ITCM extent'):
            b.extend(main,b'\0\0',b.PROBE_BASE|1)

    def test_code_cannot_overlap_owned_markers(self):
        b=self.builder();main=self.main()
        with self.assertRaisesRegex(ValueError,'overlaps marker'):
            b.extend(main,bytes(b.MARKER-b.PROBE_BASE+1),b.PROBE_BASE|1)

    def main(self):
        return test_fixtures.r5_arm9(self)

if __name__=='__main__': unittest.main()
