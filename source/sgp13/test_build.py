import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from sgp13.build import write_new, build

class OutputSafetyTests(unittest.TestCase):
    def test_existing_output_is_never_replaced_and_temporary_is_removed(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'result.nds';path.write_bytes(b'previous release')
            with self.assertRaises(FileExistsError):write_new(path,b'new bytes')
            self.assertEqual(path.read_bytes(),b'previous release')
            self.assertEqual(list(Path(d).iterdir()),[path])

    def test_complete_new_output_is_published_without_temporary_siblings(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'new.nds';payload=bytes(range(256))*30
            write_new(path,payload)
            self.assertEqual(path.read_bytes(),payload)
            self.assertEqual(list(Path(d).iterdir()),[path])

    def test_unrecognized_input_creates_neither_output_nor_build_workspace(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=root/'foreign.nds';base.write_bytes(bytes(512));output=root/'new'/'out.nds';work=root/'work'
            with self.assertRaisesRegex(ValueError,'exact supported'):
                build(base,output,root/'missing-charmap',work)
            self.assertFalse(output.exists());self.assertFalse(work.exists());self.assertFalse(output.parent.exists())

class WorkspaceCleanupTests(unittest.TestCase):
    def test_failed_build_removes_only_its_own_intermediates(self):
        # The real builder writes its first stage before an injected installer
        # failure. A missing cleanup used to leave a full ROM on every retry.
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            base = root / 'input.nds'
            base.write_bytes(b'private input fixture')
            charmap = root / 'charmap.txt'
            charmap.write_text('fixture')
            commands = root / 'tools/py_scripts/scrcmd.json'
            commands.parent.mkdir(parents=True)
            commands.write_text('{}')
            work = root / 'work'
            work.mkdir()
            sentinel = work / 'older-evidence.txt'
            sentinel.write_text('keep')
            output = root / 'result.nds'
            with patch('sgp13.space.identify', return_value='EN'), \
                 patch('sgp13.mew.load_commands', return_value=({}, 'unused')), \
                 patch('sgp13.space.expand_rom', return_value=b'expanded stage'), \
                 patch('sgp13.training.install', side_effect=ValueError('installer failed')):
                for _ in range(2):
                    with self.assertRaisesRegex(ValueError, 'installer failed'):
                        build(base, output, charmap, work)
            self.assertEqual(list(work.iterdir()), [sentinel])
            self.assertEqual(sentinel.read_text(), 'keep')
            self.assertEqual(base.read_bytes(), b'private input fixture')
            self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
