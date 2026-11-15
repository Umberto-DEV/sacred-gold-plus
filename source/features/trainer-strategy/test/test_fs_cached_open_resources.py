"""Owned metadata fixtures exercise the native start-only FAT boundary."""
from pathlib import Path
import importlib.util
import struct
import unittest


class FATTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_fs_cached_open.py'
        s=importlib.util.spec_from_file_location('open_fat_test',p)
        cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)

    def fixture(self):
        fat=bytearray(4104);struct.pack_into('<II',fat,140*8,0x100,0x123)
        return bytes(fat)

    def test_equal_and_below_start_return_failure_before_reading_bad_record(self):
        # Inverted record would fail if accidentally read on the error route.
        fat=bytearray(self.fixture());struct.pack_into('<II',fat,1120,0x200,0x100)
        for size in(0,1119,1120):
            with self.subTest(size=size):self.assertEqual(self.L.fat_metadata(bytes(fat),140,size),dict(success=False,file_id=140,offset=1120,FSResult=1))

    def test_normal_record_reports_ordered_extent_and_size(self):
        r=self.L.fat_metadata(self.fixture(),140,4104)
        self.assertEqual(r,dict(success=True,file_id=140,offset=1120,FSResult=0,top=0x100,bottom=0x123,bytes=35))

    def test_source_start_only_check_is_not_silently_strengthened_to_record_end(self):
        # Document the original source limit rather than invent archive validity.
        self.assertTrue(self.L.fat_metadata(self.fixture(),140,1121)['success'])

    def test_wrong_types_unknown_file_and_inverted_extent_are_rejected(self):
        for index,size in((True,4104),(141,4104),(140,True),(140,4105)):
            with self.subTest(index=index,size=size),self.assertRaisesRegex(ValueError,'typed finite'):self.L.fat_metadata(self.fixture(),index,size)
        fat=bytearray(self.fixture());struct.pack_into('<II',fat,1120,0x200,0x100)
        with self.assertRaisesRegex(ValueError,'extent order'):self.L.fat_metadata(bytes(fat),140,4104)


if __name__=='__main__':unittest.main()
