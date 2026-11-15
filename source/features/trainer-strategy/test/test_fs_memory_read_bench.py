"""Synthetic owner/ledger checks for native multi-byte writes."""
from pathlib import Path
import importlib.util
import unittest


class DeltaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).with_name('fs_memory_read_bench.py')
        spec=importlib.util.spec_from_file_location('memory_read_delta_test',path)
        cls.B=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.B)

    def example(self):
        B=self.B;base=B.L.HEADER_DEST&~4095;initial={base:bytes(b'\xa5'*4096)};final={base:bytearray(initial[base])}
        event=dict(pc=0x20d4b7c,address=B.L.HEADER_DEST,bytes=4,before='a5a5a5a5',value=B.R.ARC)
        final[base][B.L.HEADER_DEST-base:B.L.HEADER_DEST-base+4]=B.R.ARC.to_bytes(4,'little')
        return initial,{a:bytes(b)for a,b in final.items()},[event]

    def test_authorized_word_store_is_not_rejudged_as_four_byte_stores(self):
        initial,final,stores=self.example();error=None
        try:self.B.require_memory_delta(initial,final,stores)
        except ValueError as failure:error=str(failure)
        self.assertIsNone(error,error)

    def test_memory_site_guard_rejects_unknown_pc_and_wrong_instruction_class(self):
        B=self.B
        self.assertFalse(B.write_owner(0xdeadbeef,B.R.TOP-4,4))
        self.assertFalse(B.write_owner(0x20d6bf8,B.R.TOP-4,4)) # native LDR, not a store
        self.assertFalse(B.read_owner(0xdeadbeef,B.R.FILE+8,4))
        self.assertFalse(B.write_owner(0x20d4b7c,B.R.TOP-4,2)) # STR word, not STRH

    def test_unrecorded_neighbor_change_fails(self):
        initial,final,stores=self.example();base=self.B.L.HEADER_DEST&~4095;blob=bytearray(final[base]);blob[self.B.L.HEADER_DEST-base+4]=0
        final[base]=bytes(blob)
        with self.assertRaises(ValueError):self.B.require_memory_delta(initial,final,stores)

    def test_unauthorized_width_or_store_preimage_fails(self):
        for key,value,label in (('bytes',1,'source delta owner/site'),('before','00000000','store preimage')):
            initial,final,stores=self.example();stores[0][key]=value
            if key=='bytes':stores[0]['value']&=255
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,label):self.B.require_memory_delta(initial,final,stores)


if __name__=='__main__':unittest.main()
