"""Owned tiny images distinguish initialized bytes from BSS provenance."""
from pathlib import Path
import importlib.util
import struct
import tempfile
import unittest
from unittest import mock


class PhysicalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).parents[1]/'tools/rileggi_fs_cached_convert.py'
        s=importlib.util.spec_from_file_location('convert_reader_test',p)
        cls.L=importlib.util.module_from_spec(s);s.loader.exec_module(cls.L)

    def image(self):
        b=bytearray(0x2000);struct.pack_into('<I',b,0x20,0x200)
        struct.pack_into('<II',b,0x28,0x02000000,0x1000)
        b[0x300:0x304]=b'OWN!';b[0x400:0x408]=self.L.PATH_BYTES
        struct.pack_into('<9I',b,0x200+0xba0,0,0,0,0x02111860,0x021e5900,0,0,0xdec00621,0x2106c0de)
        return b

    def check(self,blob):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'owned-tiny.bin';p.write_bytes(blob)
            with mock.patch.dict(self.L.NEW,{'owned':(0x02000100,4,self.L.sha(b'OWN!'))},clear=True),mock.patch.object(self.L,'PATH',0x02000200):
                return self.L.physical(p)

    def test_root_bss_has_no_initialized_rom_offset(self):
        parts,rows,loader=self.check(self.image())
        self.assertEqual(parts['owned'],b'OWN!');self.assertEqual(rows['owned']['rom_offset'],0x300)
        self.assertIsNone(loader['root_physical_offset']);self.assertLessEqual(loader['bss_start'],self.L.ROOT)
        self.assertGreaterEqual(loader['bss_end'],self.L.ROOT+12)

    def test_bss_descriptor_must_contain_all_twelve_root_bytes(self):
        b=self.image();struct.pack_into('<I',b,0x200+0xba0+16,self.L.ROOT+8)
        with self.assertRaisesRegex(ValueError,'Root BSS descriptor'):self.check(b)

    def test_initialized_component_bounds_are_not_bss_bounds(self):
        b=self.image();struct.pack_into('<I',b,0x2c,0x100)
        with self.assertRaisesRegex(ValueError,'initialized ARM9 bounds'):self.check(b)

    def test_changed_component_and_descriptor_magic_fail_closed(self):
        for offset,label in((0x300,'physical Convert component'),(0x200+0xba0+28,'code settings magic')):
            b=self.image();b[offset]^=1
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,label):self.check(b)


if __name__=='__main__':unittest.main()
