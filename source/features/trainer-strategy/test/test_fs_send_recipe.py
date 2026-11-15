"""Send recipe output ownership and optional independent recovered ELF readback."""
from pathlib import Path
import importlib.util,os,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('send_builder',Path(__file__).parents[1]/'tools/compila_fs_send.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Ownership(unittest.TestCase):
    def test_source_and_existing_fixture_rejected_before_compiler(self):
        target=M.D.C.SOURCE/'__refused_send_output__';self.assertFalse(target.exists())
        with patch.object(M.D.subprocess,'run',side_effect=AssertionError('must not invoke compiler')):
            with self.assertRaises(ValueError):M.build(target)
            with tempfile.TemporaryDirectory()as name:
                out=Path(name);fixture=out/'original';fixture.write_bytes(b'preserve fixture')
                with self.assertRaises(ValueError):M.build(out)
                self.assertEqual(fixture.read_bytes(),b'preserve fixture')
                self.assertEqual([p.name for p in out.iterdir()],['original'])
        self.assertFalse(target.exists())


@unittest.skipUnless(os.environ.get('SGP_FS_SEND_RECIPE_DIR'),'requires private recovered Send ELF')
class Recovered(unittest.TestCase):
    def test_exact_elf_has_no_pool_and_native_call_targets(self):
        L=M.load('send_independent_elf',Path(__file__).parents[1]/'tools/rileggi_fs_read.py')
        body=L.object_text(Path(os.environ['SGP_FS_SEND_RECIPE_DIR'])/'fs-send-command.o',420,M.BODIES['command'][2])
        from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
        code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,0x20D7788))
        self.assertEqual(len(code),105);self.assertEqual(code[-1].mnemonic,'pop')
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='bl'],[
            (0x20D77B4,'#0x20d3a38'),(0x20D77D0,'#0x20d6864'),(0x20D77D8,'#0x20d3a4c'),
            (0x20D7878,'#0x20d3a4c'),(0x20D7898,'#0x20d3a38'),(0x20D78C0,'#0x20d3a4c'),
            (0x20D78C8,'#0x20d76b0'),(0x20D78D4,'#0x20d3a4c'),(0x20D78F8,'#0x20d3a4c'),
            (0x20D7908,'#0x20d1e7c'),(0x20D791C,'#0x20d3a4c'),(0x20D7924,'#0x20d7744')])
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='blx'],[(0x20D7894,'r2')])


if __name__=='__main__':unittest.main()
