"""Owned static-address counterexamples; no ROM, optional packages or CPU."""
from pathlib import Path
import importlib.util
import struct
import unittest


class OrdinaryReadbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).parents[1]/'tools/rileggi_shellbell_ordinary.py'
        spec=importlib.util.spec_from_file_location('owned_ordinary_readback',path)
        cls.T=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.T)

    def test_window_rejects_negative_wrapped_and_boolean_geometry(self):
        self.assertEqual(self.T.window(b'01234567',0x1000,0x1002,2),b'23')
        for base,address,size in [(0x1000,0xfff,2),(0x1000,0x1006,4),(True,1,1),(0x1000,0x1000,True),(0xfffffffC,0xfffffffc,8)]:
            with self.assertRaises(ValueError):self.T.window(b'01234567',base,address,size)

    def own_switch(self):
        blob=bytearray(64);struct.pack_into('<hh',blob,24,-8,20)
        return bytes(blob)

    def test_switch_sign_extension_and_actual_add_pc_base(self):
        self.assertEqual(self.T.switch_targets(self.own_switch(),0x1000,0x1018,0x100c,2,{0x1008,0x1024}),[0x1008,0x1024])

    def test_switch_rejects_data_or_second_halfword_targets(self):
        for starts in ({0x100a,0x1024},{0x1008,0x1026}):
            with self.assertRaises(ValueError):self.T.switch_targets(self.own_switch(),0x1000,0x1018,0x100c,2,starts)

    def test_switch_checks_table_extent_count_and_typed_starts(self):
        for table,count,starts in [(0x103e,2,{0x1008,0x1024}),(0x1018,True,{0x1008,0x1024}),(0x1018,2,{True,0x1024}),(0x1018,0,{0x1008,0x1024})]:
            with self.assertRaises(ValueError):self.T.switch_targets(self.own_switch(),0x1000,table,0x100c,count,starts)

    def test_literal_uses_aligned_pc_plus_four_and_destination_register(self):
        blob=bytearray(32);struct.pack_into('<H',blob,2,0x4b02);struct.pack_into('<I',blob,12,0x12345678)
        self.assertEqual(self.T.literal_word(bytes(blob),0x1000,0x1002),dict(register=3,address=0x100c,value=0x12345678))

    def test_literal_rejects_non_ldr_truncated_and_odd_site(self):
        for blob,pc in [(bytes(32),0x1000),(bytes.fromhex('ff48'),0x1000),(bytes(32),0x1001)]:
            with self.assertRaises(ValueError):self.T.literal_word(blob,0x1000,pc)

    def test_output_creation_preserves_existing_file_and_symlink(self):
        import tempfile
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);p=root/'result.json';p.write_text('owned')
            with self.assertRaises(FileExistsError):self.T.save_new(p,{'a':1})
            link=root/'link.json';link.symlink_to(p)
            with self.assertRaises(FileExistsError):self.T.save_new(link,{'a':1})
            self.assertEqual(p.read_text(),'owned')

    def test_reports_are_refused_inside_source_including_parent_symlink(self):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory()as directory:
            root=Path(directory);public=root/'source';public.mkdir();link=root/'indirect';link.symlink_to(public,target_is_directory=True)
            with patch.object(self.T,'SOURCE',public):
                for output in(public/'report.json',link/'report.json'):
                    with self.assertRaises(ValueError):self.T.save_new(output,{'private':True})
                self.assertFalse((public/'report.json').exists())

    def test_code_windows_keep_gaps_outside_the_code_selection(self):
        image=bytes(range(32))
        self.assertEqual(self.T.code_windows(image,0x1000,[(0x1000,0x1004),(0x1008,0x100c)]),[(0x1000,image[:4]),(0x1008,image[8:12])])

    def test_code_windows_reject_overlap_reversal_odd_and_untyped_ranges(self):
        for ranges in ([(0x1000,0x1008),(0x1004,0x100c)],[(0x1008,0x100c),(0x1000,0x1004)],[(0x1001,0x1004)],[(0x1000,0x1000)],[(0x1000,0x1022)],[(True,0x1004)]):
            with self.assertRaises(ValueError):self.T.code_windows(bytes(32),0x1000,ranges)


if __name__=='__main__':unittest.main()
