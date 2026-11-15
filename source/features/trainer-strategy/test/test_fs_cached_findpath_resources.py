"""Synthetic path metadata tests; no game bytes or CPU required."""
from pathlib import Path
import importlib.util
import struct
import unittest


class PathResourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_fs_cached_findpath.py'
        s=importlib.util.spec_from_file_location('cached_find_resource_test',p)
        cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)

    def table(self):
        # Three records; unrelated file before matching directory increments ID.
        return (struct.pack('<IHHIHHIHH',24,7,3,34,9,0xf000,39,9,0xf001)+
                b'\x01x\x81a\x01\xf0\x00\x00\x00\x00'+
                b'\x810\x02\xf0\x00'+b'\x010\x00')

    def test_path_uses_file_ids_not_directory_counts_or_csv_positions(self):
        r=self.L.resolve_path(self.table(),b'a/0/0')
        self.assertEqual(r['file_id'],9)
        self.assertEqual(r['directory_ids'],[0,1,2])
        self.assertEqual(r['directory_property'],{'own_id':2,'index':10,'offset':41,'parent':1})
        self.assertEqual(r['selected_names'],['a','0','0'])
        self.assertEqual(r['table_reads'][0],{'offset':0,'bytes':8})

    def test_case_insensitive_name_and_owned_bounds(self):
        self.assertEqual(self.L.resolve_path(self.table(),b'A/0/0')['file_id'],9)
        for path in (b'/a/0/0',b'a//0',b'a/../0',b'a/0/0\0hidden'):
            with self.subTest(path=path),self.assertRaises(ValueError):self.L.resolve_path(self.table(),path)
        with self.assertRaises(ValueError):self.L.resolve_path(self.table()[:-2],b'a/0/0')

    def test_bad_child_id_and_missing_file_fail(self):
        bad=bytearray(self.table());bad[29:31]=b'\xff\xff'
        with self.assertRaisesRegex(ValueError,'directory ID'):self.L.resolve_path(bytes(bad),b'a/0/0')
        with self.assertRaisesRegex(ValueError,'not found'):self.L.resolve_path(self.table(),b'a/0/1')


if __name__=='__main__':unittest.main()
