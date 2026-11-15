"""Owned metadata/merge contracts for the complete caller reader; no ROM/CPU."""
from pathlib import Path
import importlib.util
import unittest


class CallerReaderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_box_move_caller.py';s=importlib.util.spec_from_file_location('owned_caller_reader',p)
        cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)

    def test_merge_rejects_duplicate_even_when_bytes_equal(self):
        self.assertEqual(self.L.merge_unique({'a':b'x'},{'b':b'y'}),{'a':b'x','b':b'y'})
        with self.assertRaisesRegex(ValueError,'duplicate caller part'):
            self.L.merge_unique({'a':b'x'},{'a':b'x'})

    def test_merge_requires_named_byte_parts(self):
        for values in(({'a':bytearray(b'x')},),({1:b'x'},),([('a',b'x')],)):
            with self.assertRaises(ValueError):self.L.merge_unique(*values)

    def test_thumb_union_has_both_setter_leaves_and_getter(self):
        self.assertEqual((sum(x[1]for x in self.L.THUMB.values()),sum(x[2]for x in self.L.THUMB.values())),(924,420))
        self.assertEqual(self.L.THUMB['move_caller'][:3],(0x20714f0,66,29))
        self.assertEqual(self.L.THUMB['internal_leaf54_return'][:2],(0x206f0e4,16))
        self.assertEqual(self.L.THUMB['set_pp_leaf'][:2],(0x206f0f4,16))
        self.assertEqual(self.L.THUMB['get_internal_leaf62'][:2],(0x206e97e,12))

    def test_all_code_pool_and_SDK_intervals_are_disjoint(self):
        regions={name:item[:2]for name,item in{**self.L.THUMB,**self.L.DATA}.items()}
        regions.update({'sdk_'+name:item[:2]for name,item in self.L.F87.SDK.COMPONENTS.items()})
        regions['division']=self.L.MX.DIV[:2]
        self.L.R.require_disjoint(regions)

    def test_dispatch_tables_remain_data_not_code(self):
        self.assertEqual(self.L.DATA['attribute_table'][:2],(0x206ee3c,376))
        self.assertEqual(self.L.DATA['get_attribute_table'][:2],(0x206e6f6,376))
        self.assertFalse(any(a<=0x206ee3c<a+n or a<=0x206e6f6<a+n for a,n,*_ in self.L.THUMB.values()))


if __name__=='__main__':unittest.main()
