"""ROM-free ownership/projection/delta/CLI contracts for the whole PP getter."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest


class WholePPMemoryContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('pp_memory_bench.py');s=importlib.util.spec_from_file_location('whole_PP_contract_test',p)
        cls.B=importlib.util.module_from_spec(s);s.loader.exec_module(cls.B)

    def test_pp_projection_is_typed_and_finite_before_reading_parts(self):
        for value in(True,False,0,2,16,-1,1.0,'1'):
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'typed PP15/PP1'):
                self.B.F.make_input({},value)

    def test_pp_leaf_can_only_read_the_actual_native_buffer_byte6(self):
        b=self.B
        self.assertTrue(b.read_owner(0x2073390,b.F.DEST+6,1))
        for a,n in((b.F.DEST+5,1),(b.F.DEST+6,2),(b.F.P.P.MEMBER_SOURCE+6,1)):
            self.assertFalse(b.read_owner(0x2073390,a,n))

    def test_literal_and_switch_exact_site_address_width(self):
        b=self.B
        self.assertTrue(b.read_owner(0x20733b0,0x20733bc,4))
        self.assertTrue(b.read_owner(0x207335c,0x207336e,2))
        for pc,a,n in((0x20733b0,0x20733b8,4),(0x20733b0,b.F.DEST,4),(0x207335c,0x207336c,2),(0x207335c,0x207336e,4)):
            self.assertFalse(b.read_owner(pc,a,n))

    def test_getter_saved_pair_has_exact_addresses(self):
        b=self.B
        for a in(b.R.TOP-8,b.R.TOP-4):
            self.assertTrue(b.write_owner(0x2073314,a,4));self.assertTrue(b.read_owner(0x207332a,a,4))
        self.assertFalse(b.write_owner(0x2073314,b.R.TOP-12,4))
        self.assertFalse(b.read_owner(0x207332a,b.R.TOP-12,4))

    def test_old_external_destination_and_payload_sources_are_not_writable(self):
        b=self.B
        self.assertTrue(b.write_owner(0x20d4b7c,b.F.DEST+4,4))
        for a in(0x22f0240,b.F.P.P.MEMBER_SOURCE,b.R.TOP):self.assertFalse(b.write_owner(0x20d4b7c,a,4))
        self.assertFalse(b.write_owner(0x2073390,b.F.DEST+6,1))

    def test_new_stack_bottom_excludes_guard(self):
        b=self.B
        self.assertTrue(b.write_owner(0x200732c,b.R.TOP-640,4))
        self.assertFalse(b.write_owner(0x200732c,b.R.TOP-644,4))

    def test_delta_replay_requires_actual_word_and_chronological_preimage(self):
        b=self.B;base=b.F.DEST&~4095;initial={base:b'\xa5'*4096};final={base:bytearray(initial[base])}
        e=dict(pc=0x20d4b7c,address=b.F.DEST+4,bytes=4,before='a5'*4,value=0x1e016407)
        b.M.put(final,e['address'],e['value'].to_bytes(4,'little'));out={a:bytes(v)for a,v in final.items()}
        b.require_memory_delta(initial,out,[e])
        with self.assertRaisesRegex(ValueError,'whole map'):b.require_memory_delta(initial,out,[])
        e['before']='00'*4
        with self.assertRaisesRegex(ValueError,'preimage'):b.require_memory_delta(initial,out,[e])

    def test_four_cli_help_and_required_args_without_optional_imports(self):
        tools=Path(__file__).parents[1]/'tools'
        for name in('rileggi_pp_memory.py','congela_pp_memory.py','attribuisci_pp_memory.py','qualifica_dispatch_pp.py'):
            with self.subTest(tool=name):
                r=subprocess.run([sys.executable,'-I','-S','-B',str(tools/name),'--help'],capture_output=True,timeout=15)
                self.assertEqual(r.returncode,0,r.stderr.decode())
                r=subprocess.run([sys.executable,'-I','-S','-B',str(tools/name)],capture_output=True,timeout=15)
                self.assertEqual(r.returncode,2,r.stderr.decode());self.assertIn(b'required',r.stderr)


if __name__=='__main__':unittest.main()
