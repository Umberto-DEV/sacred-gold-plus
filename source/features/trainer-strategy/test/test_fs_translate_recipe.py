"""Protected outputs and independent code/pool/ELF extent qualification."""
from pathlib import Path
import importlib.util,os,tempfile,unittest
from unittest.mock import patch


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


M=load('translate_builder',Path(__file__).parents[1]/'tools/compila_fs_translate.py')


class Ownership(unittest.TestCase):
    def test_source_and_existing_fixture_rejected_before_compiler(self):
        target=M.D.C.SOURCE/'__refused_translate_output__';self.assertFalse(target.exists())
        with patch.object(M.D.subprocess,'run',side_effect=AssertionError('compiler forbidden')):
            with self.assertRaises(ValueError):M.build(target)
            with tempfile.TemporaryDirectory()as name:
                root=Path(name);fixture=root/'original';fixture.write_bytes(b'original fixture')
                with self.assertRaises(ValueError):M.build(root)
                self.assertEqual(fixture.read_bytes(),b'original fixture')


@unittest.skipUnless(os.environ.get('SGP_FS_TRANSLATE_RECIPE_DIR'),'own recovered Translate ELF required')
class Recovered(unittest.TestCase):
    def test_independent_elf99_instructions_pool_and_call_targets(self):
        L=load('translate_elf_reader',Path(__file__).parents[1]/'tools/rileggi_fs_translate.py')
        body=L.object_text(Path(os.environ['SGP_FS_TRANSLATE_RECIPE_DIR'])/'fs-translate-command.o',400,M.BODIES['command'][2])
        code=L.split_extent(body)
        self.assertEqual(len(code),99);self.assertEqual(code[-1].address,0x20D6A48)
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='bl'],[
            (0x20D69A8,'#0x20d3a38'),(0x20D69D4,'#0x20d1e7c'),(0x20D69F8,'#0x20d3a4c'),(0x20D6A2C,'#0x20d6864')])
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='blx'],[(0x20D6910,'r2'),(0x20D6980,'r1')])
        self.assertEqual(int.from_bytes(body[-4:],'little'),0x210E124)
        wrong=bytearray(body);wrong[-1]^=1
        with self.assertRaises(ValueError):L.split_extent(bytes(wrong))
        with self.assertRaises(ValueError):L.split_extent(body[:396])


if __name__=='__main__':unittest.main()
