"""ExecuteSync protected output and independent recovered ELF qualification."""
from pathlib import Path
import importlib.util,os,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('exec_sync_builder',Path(__file__).parents[1]/'tools/compila_fs_exec_sync.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class Ownership(unittest.TestCase):
    def test_inputs_and_source_tree_rejected_before_compiler(self):
        target=M.D.C.SOURCE/'__refused_exec_sync_output__';self.assertFalse(target.exists())
        with patch.object(M.D.subprocess,'run',side_effect=AssertionError('compiler forbidden')):
            with self.assertRaises(ValueError):M.build(target)
            with tempfile.TemporaryDirectory()as name:
                out=Path(name);fixture=out/'original';fixture.write_bytes(b'original fixture')
                with self.assertRaises(ValueError):M.build(out)
                self.assertEqual(fixture.read_bytes(),b'original fixture')
        self.assertFalse(target.exists())


@unittest.skipUnless(os.environ.get('SGP_FS_EXEC_SYNC_RECIPE_DIR'),'requires private recovered ExecuteSync object')
class Recovered(unittest.TestCase):
    def test_independent_elf_and_all_four_native_calls(self):
        L=M.load('exec_sync_independent_elf',Path(__file__).parents[1]/'tools/rileggi_fs_read.py')
        body=L.object_text(Path(os.environ['SGP_FS_EXEC_SYNC_RECIPE_DIR'])/'fs-exec-sync-command.o',68,M.BODIES['command'][2])
        from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
        code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,0x20D7744))
        self.assertEqual(len(code),17);self.assertEqual(code[-1].mnemonic,'pop')
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='bl'],[
            (0x20D7750,'#0x20d68c0'),(0x20D775C,'#0x20d6864'),(0x20D7764,'#0x20d749c'),(0x20D7770,'#0x20d76b0')])


if __name__=='__main__':unittest.main()
