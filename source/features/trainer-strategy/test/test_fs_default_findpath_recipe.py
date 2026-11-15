"""Protected outputs and independent verification of only the prefix ELF."""
from pathlib import Path
import importlib.util,os,tempfile,unittest
from unittest.mock import patch


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('default_findpath_builder_test',Path(__file__).parents[1]/'tools/compila_fs_default_findpath.py')


class Ownership(unittest.TestCase):
    def test_source_and_existing_fixture_rejected_before_compiler(self):
        target=M.D.C.SOURCE/'__refused_default_findpath_output__';self.assertFalse(target.exists())
        with patch.object(M.D.subprocess,'run',side_effect=AssertionError('compiler forbidden')):
            with self.assertRaises(ValueError):M.build(target)
            with tempfile.TemporaryDirectory()as name:
                p=Path(name);fixture=p/'original';fixture.write_bytes(b'original fixture')
                with self.assertRaises(ValueError):M.build(p)
                self.assertEqual(fixture.read_bytes(),b'original fixture')


@unittest.skipUnless(os.environ.get('SGP_FS_DEFAULT_FINDPATH_RECIPE_DIR'),'own recovered default prefix ELF required')
class Recovered(unittest.TestCase):
    def test_independent_prefix_extent_and_nested_call(self):
        L=load('default_findpath_reader_test',Path(__file__).parents[1]/'tools/rileggi_fs_default_findpath.py')
        body=L.object_text(Path(os.environ['SGP_FS_DEFAULT_FINDPATH_RECIPE_DIR'])/'fs-default-findpath-command.o',28,M.BODIES['command'][2])
        code=L.split_prefix(body);self.assertEqual(len(code),7)
        self.assertEqual([(x.address,x.mnemonic)for x in code],[(0x20D6DB0,'push'),(0x20D6DB4,'sub'),(0x20D6DB8,'mov'),
            (0x20D6DBC,'ldr'),(0x20D6DC0,'mov'),(0x20D6DC4,'ldr'),(0x20D6DC8,'bl')])
        self.assertEqual(code[-1].op_str,'#0x20d68c0')
        with self.assertRaises(ValueError):L.split_prefix(body+b'\0'*4)
        wrong=bytearray(body);wrong[-1]^=1
        with self.assertRaises(ValueError):L.split_prefix(bytes(wrong))


if __name__=='__main__':unittest.main()
