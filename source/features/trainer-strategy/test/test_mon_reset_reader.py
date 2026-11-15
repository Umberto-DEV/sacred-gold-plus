"""Owned Reset BL/table/literal counterexamples, no ROM or optional packages."""
from pathlib import Path
import importlib.util
import struct
import unittest


class MonResetReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_mon_reset.py';s=importlib.util.spec_from_file_location('Reset_reader_tests',p)
        cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)
    def parts(self):
        body=bytearray(56)
        for offset,target in((10,0x20714e8),(26,0x206ec40),(34,0x207332c),(48,0x206ec40)):
            delta=target-(0x20714b0+offset+4);struct.pack_into('<HH',body,offset,0xf000|((delta>>12)&2047),0xf800|((delta>>1)&2047))
        table=bytearray(376);struct.pack_into('<h',table,116,0x2b6);struct.pack_into('<h',table,124,0x2c6)
        return dict(reset=bytes(body),mon_veneer=bytes.fromhex('004b1847'),mon_target=struct.pack('<I',0x20714f1),attribute_table=bytes(table))
    def test_four_actual_calls_and_two_distinct_setter_rows(self):
        self.L.validate_targets(self.parts())
        p=self.parts();p['attribute_table']=p['attribute_table'][:116]+b'\xc6\x02'+p['attribute_table'][118:]
        with self.assertRaises(ValueError):self.L.validate_targets(p)
    def test_wrong_second_MaxPP_call_not_accepted_by_name_similarity(self):
        p=self.parts();b=bytearray(p['reset']);b[34:38]=b[26:30];p['reset']=bytes(b)
        with self.assertRaises(ValueError):self.L.validate_targets(p)
    def test_veneer_literal_and_Thumb_bit_are_part_of_contract(self):
        for value in(0x20714f0,0x20714b1):
            p=self.parts();p['mon_target']=struct.pack('<I',value)
            with self.assertRaises(ValueError):self.L.validate_targets(p)
    def test_new_union_keeps_literal_out_of_code(self):
        l=self.L;self.assertEqual((sum(x[1]for x in l.THUMB.values()),sum(x[2]for x in l.THUMB.values())),(1132,512))
        a,n,_=l.NEW_DATA['mon_target']
        self.assertFalse(any(base<=a<base+size for base,size,count,digest in l.THUMB.values()))
        self.assertEqual((a,n),(0x20714ec,4));self.assertEqual(l.NEW_THUMB['reset'][1:3],(56,24))


if __name__=='__main__':unittest.main()
