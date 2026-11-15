"""Release protected output and independent recovered ELF qualification."""
from pathlib import Path
import importlib.util,os,tempfile,unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('release_builder',Path(__file__).parents[1]/'tools/compila_fs_release.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class InlineSource(unittest.TestCase):
    def test_single_line_definition_skips_prototype_and_requires_unique_complete_line(self):
        definition='static inline void cut(int x) { work(x); }\n'
        self.assertEqual(M.single_line_inline('static inline void cut(int x);\n'+definition,'cut'),definition)
        for text in(definition*2,'static inline void cut(int x);\n','static inline void cut(int x) {\n work(x);\n}\n'):
            with self.subTest(text=text),self.assertRaises(ValueError):M.single_line_inline(text,'cut')


class Ownership(unittest.TestCase):
    def test_inputs_and_source_tree_rejected_before_compiler(self):
        target=M.D.C.SOURCE/'__refused_release_output__';self.assertFalse(target.exists())
        with patch.object(M.D.subprocess,'run',side_effect=AssertionError('compiler forbidden')):
            with self.assertRaises(ValueError):M.build(target)
            with tempfile.TemporaryDirectory()as name:
                out=Path(name);fixture=out/'original';fixture.write_bytes(b'original fixture')
                with self.assertRaises(ValueError):M.build(out)
                self.assertEqual(fixture.read_bytes(),b'original fixture')
        self.assertFalse(target.exists())


@unittest.skipUnless(os.environ.get('SGP_FS_RELEASE_RECIPE_DIR'),'requires private recovered Release object')
class Recovered(unittest.TestCase):
    def test_independent_elf_and_all_three_native_calls(self):
        L=M.load('release_independent_elf',Path(__file__).parents[1]/'tools/rileggi_fs_read.py')
        body=L.object_text(Path(os.environ['SGP_FS_RELEASE_RECIPE_DIR'])/'fs-release-command.o',92,M.BODIES['command'][2])
        from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
        code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,0x20D6864))
        self.assertEqual(len(code),23);self.assertEqual(code[-1].mnemonic,'pop')
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='bl'],[
            (0x20D6870,'#0x20d3a38'),(0x20D68B0,'#0x20d1ecc'),(0x20D68B8,'#0x20d3a4c')])



if __name__=='__main__':unittest.main()
