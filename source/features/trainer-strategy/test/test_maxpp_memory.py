"""ROM-free MaxPP argument, owner, corpus-separation and CLI contracts."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import unittest


class MaxPPMemoryContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p=Path(__file__).with_name('maxpp_memory_bench.py');s=importlib.util.spec_from_file_location('MaxPP_contract_test',p)
        cls.B=importlib.util.module_from_spec(s);s.loader.exec_module(cls.B)

    def test_argument_projection_profiles_are_typed_and_finite(self):
        for ups,pp in((True,15),(3,True),(5,15),(4,1),(0,1),(3,0),(-1,15),(3.0,15)):
            with self.subTest(ups=ups,pp=pp),self.assertRaisesRegex(ValueError,'typed finite MaxPP'):
                self.B.F.make_input({},ups,pp)

    def test_maxpp_four_saved_words_have_exact_sites_and_addresses(self):
        b=self.B
        for offset in(16,12,8,4):
            self.assertTrue(b.write_owner(0x207332c,b.R.TOP-offset,4))
            self.assertTrue(b.read_owner(0x2073352,b.R.TOP-offset,4))
        self.assertFalse(b.write_owner(0x207332c,b.R.TOP-20,4))
        self.assertFalse(b.read_owner(0x2073352,b.R.TOP-20,4))

    def test_child_saved_pair_moves_down_with_real_caller_frame(self):
        b=self.B
        for offset in(24,20):
            self.assertTrue(b.write_owner(0x2073314,b.R.TOP-offset,4))
            self.assertTrue(b.read_owner(0x207332a,b.R.TOP-offset,4))
        for offset in(8,4):
            self.assertFalse(b.write_owner(0x2073314,b.R.TOP-offset,4))
            self.assertFalse(b.read_owner(0x207332a,b.R.TOP-offset,4))

    def test_child_pp_leaf_reads_only_the_new_stack_buffer_byte(self):
        b=self.B
        self.assertTrue(b.read_owner(0x2073390,b.R.TOP-34,1))
        for a in(b.R.TOP-18,b.R.TOP-33,b.F.SDK.MEMBER_SOURCE+6):self.assertFalse(b.read_owner(0x2073390,a,1))
        self.assertFalse(b.read_owner(0x2073390,b.R.TOP-34,2))

    def test_division_can_neither_read_nor_write_data(self):
        b=self.B
        for pc in(0x20f2998,0x20f2a04,0x20f2b5c,0x20f2ba0):
            self.assertFalse(b.read_owner(pc,b.F.DEST,4));self.assertFalse(b.write_owner(pc,b.F.DEST,4))

    def test_sdk_interpreter_corpus_excludes_division_but_cpu_corpus_includes_it(self):
        b=self.B;entry=b.A.DIV_ENTRY
        self.assertFalse(any(a<=entry<a+n for a,n in b.SDK_CODE_SPANS))
        self.assertEqual([(a,n)for a,n in b.CODE_SPANS if a<=entry<a+n],[(entry,524)])

    def test_new_stack_owner_excludes_guard_and_old_external_destination(self):
        b=self.B
        self.assertTrue(b.write_owner(0x200732c,b.R.TOP-656,4))
        self.assertFalse(b.write_owner(0x200732c,b.R.TOP-660,4))
        self.assertFalse(b.write_owner(0x20d4b7c,0x22f0240,4))

    def test_replay_checks_preimage_and_whole_page(self):
        b=self.B;page=b.F.DEST&~4095;initial={page:b'\xa5'*4096};final={page:bytearray(initial[page])}
        e=dict(pc=0x20d4b7c,address=b.F.DEST+4,bytes=4,before='a5'*4,value=0x1e016407)
        b.M.put(final,e['address'],e['value'].to_bytes(4,'little'));out={a:bytes(v)for a,v in final.items()}
        b.require_memory_delta(initial,out,[e])
        e['before']='00'*4
        with self.assertRaisesRegex(ValueError,'preimage'):b.require_memory_delta(initial,out,[e])
        e['before']='a5'*4;final[page][0]=0
        with self.assertRaisesRegex(ValueError,'whole map'):b.require_memory_delta(initial,{a:bytes(v)for a,v in final.items()},[e])

    def test_five_cli_help_and_required_arguments_without_optional_imports(self):
        tools=Path(__file__).parents[1]/'tools'
        for name in('rileggi_maxpp_memory.py','congela_maxpp_memory.py','attribuisci_maxpp_memory.py','qualifica_maxpp_aritmetica.py','compila_s32_div.py'):
            with self.subTest(tool=name):
                r=subprocess.run([sys.executable,'-I','-S','-B',str(tools/name),'--help'],capture_output=True,timeout=15)
                self.assertEqual(r.returncode,0,r.stderr.decode())
                r=subprocess.run([sys.executable,'-I','-S','-B',str(tools/name)],capture_output=True,timeout=15)
                self.assertEqual(r.returncode,2,r.stderr.decode());self.assertIn(b'required',r.stderr)


if __name__=='__main__':unittest.main()
