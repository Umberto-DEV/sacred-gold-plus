"""Small owned synthetic NARC and archive fixtures; no ROM or guest needed."""
from pathlib import Path
import importlib.util
import struct
import unittest


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


class MetadataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.L=load(Path(__file__).parents[1]/'tools/rileggi_fs_memory_read.py','memory_metadata_test')

    def fixture(self):
        count=311;btaf=12+count*8;btnf=16+btaf;gmif=btnf+8;size=gmif+8+32
        data=bytearray(size)
        struct.pack_into('<4sHHIHH',data,0,b'NARC',0xfffe,0x100,size,16,3)
        struct.pack_into('<4sIHH',data,16,b'BTAF',btaf,count,0)
        struct.pack_into('<II',data,28+310*8,8,24)
        struct.pack_into('<4sI',data,btnf,b'BTNF',8)
        struct.pack_into('<4sI',data,gmif,b'GMIF',40)
        data[gmif+8:]=bytes(range(32))
        return bytes(data),btnf,gmif

    def parse(self,data):
        return self.L.narc_metadata(lambda address,n:data[address:address+n],0,len(data))

    def test_six_tiny_reads_find_member_without_loading_an_archive_object(self):
        data,_,gmif=self.fixture();meta,header,payload=self.parse(data)
        self.assertEqual(payload,bytes(range(8,24)));self.assertEqual(header,data[:16])
        self.assertEqual(meta['member_file_offset'],gmif+16)
        self.assertEqual(len(meta['physical_reads']),6)
        self.assertEqual(sum(x['bytes']for x in meta['physical_reads']),68)
        self.assertLessEqual(max(x['bytes']for x in meta['physical_reads']),16)

    def test_member_count_and_chunk_order_are_validated_before_payload_read(self):
        for offset,value,label in((24,310,'BTAF'),(20,8,'BTAF')):
            data,_,_=self.fixture();data=bytearray(data)
            if offset==24:struct.pack_into('<H',data,offset,value)
            else:struct.pack_into('<I',data,offset,value)
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,label):self.parse(bytes(data))

    def test_bad_member_extent_and_declared_block_size_fail_closed(self):
        data,btnf,gmif=self.fixture()
        for offset,pair,label in((28+310*8,(40,56),'GMIF'),(28+310*8,(24,8),'order'),(btnf+4,(0x7fffffff,None),'bounds')):
            d=bytearray(data)
            if pair[1]is None:struct.pack_into('<I',d,offset,pair[0])
            else:struct.pack_into('<II',d,offset,*pair)
            with self.subTest(label=label),self.assertRaisesRegex(ValueError,label):self.parse(bytes(d))

    def test_wrong_header_and_short_slice_rejected(self):
        data,_,_=self.fixture();bad=bytearray(data);bad[0]=0
        with self.assertRaisesRegex(ValueError,'header'):self.parse(bytes(bad))
        with self.assertRaisesRegex(ValueError,'complete NARC physical slice'):
            self.L.narc_metadata(lambda address,n:b'',0,len(data))
        with self.assertRaisesRegex(ValueError,'typed bounded'):
            self.L.narc_metadata(lambda address,n:b'',0,len(data),True)


class ArchiveDomainTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.B=load(Path(__file__).with_name('fs_memory_read_bench.py'),'memory_archive_domain_test')

    def fixture(self):
        a=bytearray(92);struct.pack_into('<I',a,28,7);struct.pack_into('<I',a,40,self.B.L.ARCHIVE_BASE)
        struct.pack_into('<I',a,48,4104);struct.pack_into('<I',a,72,0x20d7448);struct.pack_into('<I',a,88,2)
        return bytes(a)

    def test_explicit_memory_archive_and_separate_synthetic_unused_mask(self):
        self.B.require_memory_archive(self.fixture())
        a=bytearray(self.fixture());struct.pack_into('<I',a,88,0);self.B.require_memory_archive(bytes(a))

    def test_natural_card_and_absolute_table_callbacks_are_not_memory_payload(self):
        for callback in(0x20d84c4,0x20d7484,0):
            a=bytearray(self.fixture());struct.pack_into('<I',a,72,callback)
            with self.subTest(callback=callback),self.assertRaisesRegex(ValueError,'hybrid memory archive'):self.B.require_memory_archive(bytes(a))

    def test_unprojected_base_running_flags_and_protocol_bits_fail_closed(self):
        for offset,value in((40,0),(28,0x17),(88,0x602),(48,1120),(36,0x1234)):
            a=bytearray(self.fixture());struct.pack_into('<I',a,offset,value)
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,'hybrid memory archive'):self.B.require_memory_archive(bytes(a))
        with self.assertRaisesRegex(ValueError,'typed archive92'):self.B.require_memory_archive(b'bad')


if __name__=='__main__':unittest.main()
