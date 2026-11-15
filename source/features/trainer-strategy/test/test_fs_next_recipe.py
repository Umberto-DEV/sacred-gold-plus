"""Next recovered body/layout artifacts are separate from runtime qualification."""
from pathlib import Path
import importlib.util,os,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('fs_next_builder',Path(__file__).parents[1]/'tools/compila_fs_next.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Ownership(unittest.TestCase):
    def test_source_and_existing_fixture_rejected_before_compiler(self):
        target=M.D.C.SOURCE/'__refused_fs_next_output__';self.assertFalse(target.exists())
        with patch.object(M.D.subprocess,'run',side_effect=AssertionError('compiler forbidden')):
            with self.assertRaises(ValueError):M.build(target)
            with tempfile.TemporaryDirectory()as name:
                out=Path(name);fixture=out/'original';fixture.write_bytes(b'original fixture')
                with self.assertRaises(ValueError):M.build(out)
                self.assertEqual(fixture.read_bytes(),b'original fixture')


@unittest.skipUnless(os.environ.get('SGP_FS_NEXT_RECIPE_DIR'),'own private recovered Next object required')
class Recovered(unittest.TestCase):
    def test_independent_elf133_arm_starts_and_external_call_targets(self):
        L=M.load('fs_next_independent_elf',Path(__file__).parents[1]/'tools/rileggi_fs_read.py')
        body=L.object_text(Path(os.environ['SGP_FS_NEXT_RECIPE_DIR'])/'fs-next-command.o',532,M.BODIES['command'][2])
        from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
        code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,0x20D749C));self.assertEqual(len(code),133)
        self.assertEqual((code[0].mnemonic,code[1].op_str,code[-1].mnemonic),('push','sp, sp, #0x48','pop'))
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='bl'],[
            (0x20D74A8,'#0x20d3a38'),(0x20D7518,'#0x20d6864'),(0x20D759C,'#0x20d3a4c'),
            (0x20D75C4,'#0x20d3a38'),(0x20D75F4,'#0x20d1ecc'),(0x20D75FC,'#0x20d3a4c'),
            (0x20D7610,'#0x20d3a4c'),(0x20D7654,'#0x20d7f98'),(0x20D7698,'#0x20d1ecc'),(0x20D76A0,'#0x20d3a4c')])
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='blx'],[(0x20D75C0,'r2'),(0x20D7668,'r2')])


if __name__=='__main__':unittest.main()
