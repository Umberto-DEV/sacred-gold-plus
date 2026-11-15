"""Owned locator/BL/physical offset counterexamples; no ROM or CPU."""
from pathlib import Path
import importlib.util
import types
import unittest

p=Path(__file__).parents[1]/'tools/rileggi_mon_ppup_lineage.py';s=importlib.util.spec_from_file_location('Mon_lineage_tests',p)
L=importlib.util.module_from_spec(s);s.loader.exec_module(L)


class MonLineageTest(unittest.TestCase):
    def test_only_one_aligned_complete_signature(self):
        sig=bytes(range(56));section=types.SimpleNamespace(ramAddress=0x2000,data=b'xx'+sig+b'yy')
        self.assertEqual(L.locate([section],sig),0x2002)
        with self.assertRaises(ValueError):L.locate([section,section],sig)
        with self.assertRaises(ValueError):L.locate([types.SimpleNamespace(ramAddress=0x2001,data=sig)],sig)
    def test_short_signature_cannot_locate_by_similarity(self):
        with self.assertRaises(ValueError):L.locate([],bytes(54))
    def test_actual_BL_typed_pair_not_arbitrary_instruction(self):
        self.assertEqual(L.OLD.bl_target(0x206ec58,bytes.fromhex('03f0c2fc')),0x20725e0)
        for pc,blob in((0x206ec59,bytes.fromhex('03f0c2fc')),(0x206ec58,b'\0'*4),(True,b'\0'*4)):
            with self.assertRaises(ValueError):L.OLD.bl_target(pc,blob)
    def test_compressed_or_nonbase_owner_never_claims_plain_offset(self):
        owner=types.SimpleNamespace(ramAddress=0x2000000)
        self.assertEqual(L.OLD.physical_position(owner,0x2000000,0x4000,0x1000,0x2000010,2,False),0x4010)
        self.assertIsNone(L.OLD.physical_position(owner,0x2000000,0x4000,0x1000,0x2000010,2,True))
        self.assertIsNone(L.OLD.physical_position(types.SimpleNamespace(ramAddress=0x2100000),0x2000000,0x4000,0x1000,0x2100000,2,False))


if __name__=='__main__':unittest.main()
