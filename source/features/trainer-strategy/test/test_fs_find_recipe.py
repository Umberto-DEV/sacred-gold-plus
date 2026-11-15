"""Protect inputs and replay recovered Find ELF with developer-owned artifacts."""
from pathlib import Path
import importlib.util,os,struct,tempfile,unittest
s=importlib.util.spec_from_file_location('find_builder',Path(__file__).parents[1]/'tools/compila_fs_find.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


class OutputOwnership(unittest.TestCase):
    def test_source_definition_does_not_start_at_a_forward_declaration(self):
        text='BOOL Lookup(int x);\nvoid Other(void)\n{\n}\nBOOL Lookup(int x)\n{\n    return x;\n}\n'
        self.assertEqual(M.definition_source(text,'BOOL','Lookup'),'BOOL Lookup(int x)\n{\n    return x;\n}\n')

    def test_source_tree_cannot_be_a_build_destination(self):
        target=M.D.C.SOURCE/'__refused_find_output__'
        self.assertFalse(target.exists())
        with self.assertRaises(ValueError):M.build(target)
        self.assertFalse(target.exists())

    def test_existing_files_are_preserved_before_any_compiler_invocation(self):
        with tempfile.TemporaryDirectory()as name:
            out=Path(name);fixture=out/'fixture';fixture.write_bytes(b'original input')
            with self.assertRaises(ValueError):M.build(out,cc='nonexistent-compiler')
            self.assertEqual(fixture.read_bytes(),b'original input')
            self.assertEqual([p.name for p in out.iterdir()],['fixture'])


@unittest.skipUnless(os.environ.get('SGP_FS_FIND_RECIPE_DIR'),'requires private recovered Find ELF')
class RecoveredObject(unittest.TestCase):
    def test_independent_elf_readback_and_literal_boundary(self):
        L=M.load('find_independent_elf',Path(__file__).parents[1]/'tools/rileggi_fs_read.py')
        path=Path(os.environ['SGP_FS_FIND_RECIPE_DIR'])/'fs-find-path.o'
        body=L.object_text(path,324,'baf1c233ca8efcaa3ca58e996fe2f01e437fad5753dca7bbe1e6e782dd9abcf8')
        self.assertEqual(struct.unpack_from('<I',body,320)[0],0x21E362C)
        from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
        code=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body[:320],0x20D7FC0))
        self.assertEqual(len(code),80)
        self.assertEqual([(i.address,i.op_str)for i in code if i.mnemonic=='bl'],
                         [(0x20D8044,'#0x20d7958'),(0x20D80F4,'#0x20d7788')])
        with self.assertRaises(ValueError):L.object_text(path,320,M.BODIES['path'][2])
        with self.assertRaises(ValueError):L.object_text(path,324,'0'*64)


if __name__=='__main__':unittest.main()
