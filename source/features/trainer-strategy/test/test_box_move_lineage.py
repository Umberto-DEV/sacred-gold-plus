"""Owned ROM-to-function locator and physical mapping contracts, no ROM/CPU."""
from pathlib import Path
import importlib.util
from types import SimpleNamespace
import unittest


class CallerLineageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_box_move_lineage.py';s=importlib.util.spec_from_file_location('owned_caller_lineage',p)
        cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)

    def section(self,pattern,offset=128):
        data=bytearray(b'\xa5'*4096);data[offset:offset+len(pattern)]=pattern
        return SimpleNamespace(ramAddress=0x2000000,data=data)

    def test_unique_even_caller_fingerprint_is_located_without_known_entry(self):
        pattern=bytes(range(66));section=self.section(pattern,258)
        self.assertEqual(self.L.locate_caller([section],pattern),0x2000102)

    def test_missing_odd_or_ambiguous_fingerprints_fail(self):
        pattern=bytes(range(66));section=self.section(pattern)
        for sections in([], [self.section(pattern,129)], [section,self.section(pattern,512)]):
            with self.assertRaisesRegex(ValueError,'unique caller'):
                self.L.locate_caller(sections,pattern)

    def test_piece_requires_one_bounded_decoded_owner(self):
        section=self.section(bytes(range(66)))
        self.assertEqual(self.L.piece([section],0x2000080,66)[0],bytes(range(66)))
        for a,n in((0x2000000,True),(0x2000000,0),(0x1ffffff,2),(0xffffffff,2)):
            with self.assertRaises(ValueError):self.L.piece([section],a,n)
        with self.assertRaises(ValueError):self.L.piece([section,section],0x2000080,66)

    def test_compressed_or_non_linear_owner_never_gets_physical_offset(self):
        section=self.section(bytes(range(66)))
        self.assertIsNone(self.L.physical_position(section,0x2000000,0x4000,4096,0x2000080,66,True))
        other=SimpleNamespace(ramAddress=0x2200000,data=bytearray(4096))
        self.assertIsNone(self.L.physical_position(other,0x2000000,0x4000,4096,0x2200080,66,False))
        self.assertEqual(self.L.physical_position(section,0x2000000,0x4000,4096,0x2000080,66,False),0x4080)

    def test_bl_decode_preserves_thumb_target_without_symbol_names(self):
        self.assertEqual(self.L.bl_target(0x1000,bytes.fromhex('00f000f8')),0x1004)
        self.assertEqual(self.L.bl_target(0x2000,bytes.fromhex('fff7feff')),0x2000)
        with self.assertRaises(ValueError):self.L.bl_target(0x1000,bytes.fromhex('00f000e8'))


if __name__=='__main__':unittest.main()
