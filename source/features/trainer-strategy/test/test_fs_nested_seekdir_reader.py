"""The reused ELF400 and the noncontiguous selected96 have distinct coverage."""
from pathlib import Path
import importlib.util,os,struct,unittest

path=Path(__file__).parents[1]/'tools/rileggi_fs_nested_seekdir.py'
s=importlib.util.spec_from_file_location('nested_seekdir_reader_test',path)
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


@unittest.skipUnless(os.environ.get('SGP_FS_NESTED_SEEKDIR_RECIPE_DIR'),'own retained Translate ELF400 required')
class Retained(unittest.TestCase):
    def body(self):
        return M.object_text(Path(os.environ['SGP_FS_NESTED_SEEKDIR_RECIPE_DIR'])/'fs-translate-command.o',400,M.C.BODIES['command'][2])

    def test_selected24_pcs_are_two_ranges_in_retained_elf(self):
        body=self.body();selected=M.selected(body)
        self.assertEqual(len(selected),96);self.assertNotEqual(selected,body[:96])
        self.assertEqual(M.SITES,tuple(range(0x20D68C0,0x20D6904,4))+tuple(range(0x20D6968,0x20D6984,4)))
        self.assertEqual(M.sha(selected),M.SELECTED_SHA)
        wrong=bytearray(body);wrong[0]^=1
        with self.assertRaises(ValueError):M.selected(bytes(wrong))

    def test_pool_relocation_does_not_become_instruction_or_whole_match(self):
        body=self.body();changed=bytearray(body);struct.pack_into('<I',changed,396,0x210E0B8)
        self.assertNotEqual(M.sha(changed),M.C.BODIES['command'][2]);self.assertEqual(M.selected(body),M.selected(bytes(changed)))
        self.assertEqual(M.COMPONENTS['default_gate'],(0x20D6BEC,4,M.GATE_SHA))
        with self.assertRaises(ValueError):M.selected(body[:396])


if __name__=='__main__':unittest.main()
