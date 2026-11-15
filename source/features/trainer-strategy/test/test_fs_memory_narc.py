"""ROM-free ownership, readback selection and CLI contracts for native NARC."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest


class NativeNarcContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('fs_memory_narc_bench.py')
        s=importlib.util.spec_from_file_location('native_narc_contract_test',p)
        cls.B=importlib.util.module_from_spec(s);s.loader.exec_module(cls.B)

    def test_stack_boundaries_exclude_guard_and_top(self):
        b=self.B
        self.assertTrue(b.write_owner(0x200732c,b.R.TOP-616,4))
        self.assertFalse(b.write_owner(0x200732c,b.R.TOP-620,4))
        self.assertFalse(b.write_owner(0x200732c,b.R.TOP,4))
        self.assertFalse(b.read_owner(0x200740a,b.R.TOP,4))

    def test_halfword_source_can_read_two_bytes_but_not_neighbor_gap(self):
        b=self.B;source=b.F.P.ARCHIVE_BASE+0x1093800+0xc
        self.assertTrue(b.read_owner(0x20d4a68,source,2))
        self.assertFalse(b.read_owner(0x20d4a68,source+2,2))
        self.assertFalse(b.read_owner(0x20d4b78,source,4))

    def test_member_destination_requires_native_word_writer_and_bounds(self):
        b=self.B
        self.assertTrue(b.write_owner(0x20d4b7c,b.F.DEST+12,4))
        for pc,a,n in((0x20d4b7c,b.F.DEST+16,4),(0x2007334,b.F.DEST,4),(0x20d4b7c,b.F.DEST,2)):
            self.assertFalse(b.write_owner(pc,a,n))

    def test_payload_source_is_read_only_and_gap_not_a_source(self):
        b=self.B;a=b.F.P.MEMBER_SOURCE
        self.assertTrue(b.read_owner(0x20d4b78,a,4))
        self.assertFalse(b.write_owner(0x20d4b7c,a,4))
        self.assertFalse(b.read_owner(0x20d4b78,a-4,4))

    def test_only_actual_row11_pool_and_path_are_mapped(self):
        b=self.B
        self.assertTrue(b.read_owner(0x2007510,0x2007520,4))
        self.assertTrue(b.read_owner(0x2007514,0x210f23c,4))
        self.assertFalse(b.read_owner(0x2007514,0x210f240,4))
        self.assertTrue(b.read_owner(0x20d7fcc,b.F.PATH,1))
        self.assertFalse(b.read_owner(0x20d7fcc,b.F.PATH+8,1))

    def test_previous_project_driver_sites_are_excluded(self):
        b=self.B
        self.assertFalse(any(pc>=0x22f0000 for pc,n in b.READ_SITES|b.WRITE_SITES))
        self.assertFalse(b.write_owner(0x22f0818,0x22f0280,4))

    def test_chronological_preimage_and_unrelated_page_delta_are_enforced(self):
        b=self.B;page=b.F.DEST&~4095;initial={page:b'\xa5'*4096}
        event=dict(pc=0x20d4b7c,address=b.F.DEST,bytes=4,before='a5'*4,value=0x11223344)
        final={page:bytearray(initial[page])};b.M.put(final,b.F.DEST,bytes.fromhex('44332211'))
        b.require_memory_delta(initial,{a:bytes(v)for a,v in final.items()},[event])
        event['before']='00'*4
        with self.assertRaisesRegex(ValueError,'preimage'):b.require_memory_delta(initial,{a:bytes(v)for a,v in final.items()},[event])
        event['before']='a5'*4;final[page][0]=0
        with self.assertRaisesRegex(ValueError,'whole map'):b.require_memory_delta(initial,{a:bytes(v)for a,v in final.items()},[event])

    def test_boolean_store_value_is_not_an_integer_delta(self):
        b=self.B
        event=dict(pc=0x20d4b7c,address=b.F.DEST,bytes=4,before='a5'*4,value=True)
        with self.assertRaisesRegex(ValueError,'typed native delta'):
            b.require_memory_delta({b.F.DEST&~4095:b'\xa5'*4096},{},[event])

    def test_cli_help_and_required_argument_errors(self):
        tools=Path(__file__).parents[1]/'tools'
        for name in('rileggi_fs_memory_narc.py','congela_fs_memory_narc.py','attribuisci_fs_memory_narc.py','qualifica_interworking_narc.py'):
            with self.subTest(tool=name):
                r=subprocess.run([sys.executable,'-I','-S','-B',str(tools/name),'--help'],capture_output=True,timeout=15)
                self.assertEqual(r.returncode,0,r.stderr.decode())
                r=subprocess.run([sys.executable,'-I','-S','-B',str(tools/name)],capture_output=True,timeout=15)
                self.assertEqual(r.returncode,2,r.stderr.decode())
                self.assertIn(b'required',r.stderr)


if __name__=='__main__':unittest.main()
