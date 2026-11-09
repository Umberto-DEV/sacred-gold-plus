"""ROM-free tests for authenticated, editable package workspaces."""
import hashlib
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import package_workspace as workspace


ROOT = 'Sacred Gold Plus 1.3.2'
PDF = ROOT + '/Originals/Game-Guide-1.3.2-EN.pdf'
PATCH = ROOT + '/EN-English/Patch/game.xdelta'
NESTED = ROOT + '/Optional-Updaters/SHA256SUMS'


class PackageWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.seed = self.base / 'seed.zip'
        self.work = self.base / 'package'
        self.members = {
            ROOT + '/START-HERE.txt': b'Player instructions\n',
            PATCH: b'opaque validated patch bytes\x00\x01',
            NESTED: b'nested checksums remain byte-identical\n',
            ROOT + '/Developer-Inputs/base.xdelta': b'historical input',
            ROOT + '/EN-English/Cheats/README.txt': b'cheat instructions',
            PDF: b'%PDF-1.4\noriginal guide\n%%EOF\n',
            ROOT + '/CONTENTS.json': json.dumps({
                'schema': 3, 'version': '1.3.2', 'package_revision': 'r4',
                'files': {},
            }).encode(),
            ROOT + '/SHA256SUMS': b'old root checksums\n',
        }
        self.write_archive(self.members.items())

    def write_archive(self, members):
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.seed, 'w', zipfile.ZIP_DEFLATED) as z:
                for name, data in members:
                    z.writestr(name, data)
        self.pin = {'bytes': self.seed.stat().st_size,
                    'sha256': hashlib.sha256(self.seed.read_bytes()).hexdigest()}

    def seed_workspace(self, **kwargs):
        return workspace.seed_workspace(self.seed, self.work,
                                        delivery=self.pin, **kwargs)

    def build(self, directory='out'):
        return workspace.build_workspace(self.work, self.base / directory)

    def test_documents_can_change_and_new_move_guide_can_be_added(self):
        self.seed_workspace()
        tree = self.work / 'contents'
        (tree / PDF).write_bytes(b'%PDF-1.4\nupdated guide\n%%EOF\n')
        moves = ROOT + '/Originals/Move-Changes-1.3.2-EN.pdf'
        (tree / moves).write_bytes(b'%PDF-1.4\nmoves\n%%EOF\n')
        index = ROOT + '/Originals/ABOUT-THESE-GUIDES.txt'
        (tree / index).write_text('Eight shared gameplay guides.\n')
        result = self.build()
        with zipfile.ZipFile(result['zip']) as z:
            self.assertEqual(z.read(PATCH), self.members[PATCH])
            self.assertEqual(z.read(NESTED), self.members[NESTED])
            self.assertEqual(z.read(moves), (tree / moves).read_bytes())
            contents = json.loads(z.read(ROOT + '/CONTENTS.json'))
            self.assertEqual(contents['files'][moves.split('/', 1)[1]]['sha256'],
                             hashlib.sha256(z.read(moves)).hexdigest())
            sums = z.read(ROOT + '/SHA256SUMS').decode()
            self.assertIn(hashlib.sha256(z.read(PDF)).hexdigest(), sums)
            self.assertEqual((tree / (ROOT + '/CONTENTS.json')).read_bytes(),
                             z.read(ROOT + '/CONTENTS.json'))

    def test_repeated_builds_are_byte_identical(self):
        self.seed_workspace()
        first = self.build('one')
        second = self.build('two')
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(Path(first['zip']).read_bytes(), Path(second['zip']).read_bytes())

    def test_changed_patch_cheat_developer_input_and_nested_metadata_are_rejected(self):
        for name in (PATCH, NESTED, ROOT + '/Developer-Inputs/base.xdelta',
                     ROOT + '/EN-English/Cheats/README.txt'):
            with self.subTest(name=name):
                self.seed_workspace()
                (self.work / 'contents' / name).write_bytes(b'tampered')
                with self.assertRaisesRegex(ValueError, 'changed|immutable'):
                    self.build()
                import shutil
                shutil.rmtree(self.work)

    def test_unknown_pdf_and_unknown_text_are_rejected(self):
        self.seed_workspace()
        for name in (ROOT + '/Originals/unreviewed.pdf', ROOT + '/other.txt'):
            p = self.work / 'contents' / name
            p.write_bytes(b'%PDF-1.4\nextra')
            with self.assertRaisesRegex(ValueError, 'Unexpected|unknown'):
                self.build()
            p.unlink()

    def test_missing_patch_or_original_guide_is_rejected(self):
        for name in (PATCH, PDF):
            with self.subTest(name=name):
                self.seed_workspace()
                (self.work / 'contents' / name).unlink()
                with self.assertRaisesRegex(ValueError, 'Missing|missing'):
                    self.build()
                import shutil
                shutil.rmtree(self.work)

    def test_generated_root_inventories_can_be_missing(self):
        self.seed_workspace()
        for name in ('CONTENTS.json', 'SHA256SUMS'):
            (self.work / 'contents' / ROOT / name).unlink()
        self.build()
        self.assertTrue((self.work / 'contents' / ROOT / 'CONTENTS.json').is_file())

    def test_wrong_seed_identity_does_not_create_contents(self):
        self.pin['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'identity|SHA|hash'):
            self.seed_workspace()
        self.assertFalse((self.work / 'contents').exists())

    def test_bad_size_pin_is_rejected(self):
        self.pin['bytes'] += 1
        with self.assertRaises(ValueError):
            self.seed_workspace()

    def test_replacing_seed_path_cannot_bypass_authentication(self):
        replacement = self.base / 'replacement.zip'
        changed = dict(self.members)
        changed[PATCH] = b'unauthenticated replacement payload'
        with zipfile.ZipFile(replacement, 'w') as z:
            for name, data in changed.items():
                z.writestr(name, data)
        actual_zipfile = zipfile.ZipFile

        def replace_before_open(source, *args, **kwargs):
            replacement.replace(self.seed)
            return actual_zipfile(source, *args, **kwargs)

        with patch.object(workspace.zipfile, 'ZipFile', side_effect=replace_before_open):
            try:
                self.seed_workspace()
            except ValueError:
                self.assertFalse((self.work / 'contents').exists())
                return
        self.assertEqual((self.work / 'contents' / PATCH).read_bytes(), self.members[PATCH])

    def test_path_traversal_absolute_windows_alias_and_wrong_root_are_rejected(self):
        for name in ('../escape', '/absolute', ROOT + '/a/../escape',
                     ROOT + '/CON.txt', ROOT + '/bad\\name', 'Other/file'):
            with self.subTest(name=name):
                self.write_archive([*self.members.items(), (name, b'bad')])
                with self.assertRaises(ValueError):
                    self.seed_workspace()
                self.assertFalse((self.work / 'contents').exists())
        self.assertFalse((self.base / 'escape').exists())

    def test_duplicate_and_case_alias_members_are_rejected(self):
        for name in (PDF, PDF.upper()):
            self.write_archive([*self.members.items(), (name, b'duplicate')])
            with self.assertRaises(ValueError):
                self.seed_workspace()

    def test_symlink_member_is_rejected(self):
        with zipfile.ZipFile(self.seed, 'a') as z:
            info = zipfile.ZipInfo(ROOT + '/link')
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, '../../outside')
        self.pin = {'bytes': self.seed.stat().st_size,
                    'sha256': hashlib.sha256(self.seed.read_bytes()).hexdigest()}
        with self.assertRaisesRegex(ValueError, 'regular|link|type'):
            self.seed_workspace()

    def test_expanded_size_limit_is_enforced_before_extraction(self):
        with self.assertRaisesRegex(ValueError, 'limit|large|size'):
            self.seed_workspace(limit=10)
        self.assertFalse((self.work / 'contents').exists())

    def test_derived_inventories_cannot_exceed_the_final_expanded_limit(self):
        self.seed_workspace()
        tree = self.work / 'contents'
        original_inventory = (tree / ROOT / 'CONTENTS.json').read_bytes()
        initial_size = sum(p.stat().st_size for p in tree.rglob('*') if p.is_file())
        limit = max(initial_size, self.seed.stat().st_size) + 1
        with patch.object(workspace, 'MAX_TREE_BYTES', limit):
            with self.assertRaisesRegex(ValueError, 'limit|large|size'):
                self.build()
        self.assertFalse((self.base / 'out').exists())
        self.assertEqual((tree / ROOT / 'CONTENTS.json').read_bytes(), original_inventory)

    def test_existing_contents_and_existing_output_are_preserved(self):
        self.seed_workspace()
        with self.assertRaises((ValueError, FileExistsError)):
            self.seed_workspace()
        out = self.base / 'out'
        out.mkdir()
        marker = out / 'keep.txt'
        marker.write_text('preserve')
        with self.assertRaises((ValueError, FileExistsError)):
            self.build()
        self.assertEqual(marker.read_text(), 'preserve')

    def test_workspace_file_and_directory_symlinks_are_rejected(self):
        self.seed_workspace()
        p = self.work / 'contents' / PATCH
        p.unlink()
        p.symlink_to(self.seed)
        with self.assertRaisesRegex(ValueError, 'link'):
            self.build()
        p.unlink()
        p.write_bytes(self.members[PATCH])
        (self.work / 'contents' / ROOT / 'linked').symlink_to(self.base,
                                                          target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'link'):
            self.build()

    def test_insufficient_disk_budget_prevents_seed(self):
        with patch.object(workspace.shutil, 'disk_usage',
                          return_value=type('Usage', (), {'free': 1})()):
            with self.assertRaisesRegex(ValueError, 'space|disk'):
                self.seed_workspace()

    def test_invalid_lock_cannot_add_arbitrary_mutable_payload(self):
        self.seed_workspace()
        lock = self.work / '.workspace-lock.json'
        lock.chmod(0o600)
        data = json.loads(lock.read_text())
        data['mutable'] = [PATCH]
        lock.write_text(json.dumps(data))
        (self.work / 'contents' / PATCH).write_bytes(b'changed')
        with self.assertRaises(ValueError):
            self.build()


if __name__ == '__main__':
    unittest.main()
