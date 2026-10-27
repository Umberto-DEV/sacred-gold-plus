import hashlib
import json
import runpy
from pathlib import Path
import tempfile
import unittest
import zipfile
import pack

class PackageTests(unittest.TestCase):
    def test_player_root_has_current_pdfs_without_obsolete_install_guides(self):
        for lang in ('EN', 'IT'):
            with self.subTest(lang=lang), tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                cfg = pack.config()
                original = b'original gameplay manual'
                cfg['original_documents'] = {'Evolution Changes.pdf': {
                    'bytes': len(original), 'sha256': hashlib.sha256(original).hexdigest()}}
                ref = directory / 'reference.zip'
                license_name = 'LICENZA.txt' if lang == 'IT' else 'LICENSE.txt'
                with zipfile.ZipFile(ref, 'w') as z:
                    z.writestr('Manual/Evolution Changes.pdf', original)
                    z.writestr('Manual/How-to-install-EN.pdf', b'old install')
                    z.writestr('Manual/Whats-New-1.2-EN.pdf', b'old news')
                    z.writestr(license_name, b'license')
                cfg['references'][lang] = {'name': ref.name, 'sha256': pack.digest(ref)}
                expected = (['How-to-install-1.2.5-EN.pdf', 'Whats-New-1.2.5-EN.pdf']
                            if lang == 'EN' else ['Come-installare-1.2.5-IT.pdf', 'Novita-1.2.5-IT.pdf'])
                for name in expected:
                    (directory / name).write_bytes(b'current PDF')
                members = pack.reference_members(lang, directory, directory, cfg)
                self.assertEqual(sorted(n for n in members if '/' not in n), sorted(expected + [license_name]))
                self.assertEqual(members['Manual/Evolution Changes.pdf'], original)
                self.assertNotIn('Manual/How-to-install-EN.pdf', members)
                self.assertNotIn('Manual/Whats-New-1.2-EN.pdf', members)

    def test_source_archive_allows_only_declared_assistant_omissions(self):
        check = runpy.run_path(str(pack.HERE.parents[1] / '.github/check_public.py'))['check']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / '.github').mkdir()
            files = ['.github/public-files.json', 'README.md', 'AGENTS.md', 'CLAUDE.md']
            (root / '.github/public-files.json').write_text(json.dumps(files))
            (root / 'README.md').write_text('Public source archive')
            self.assertEqual(check(root), 2)
            (root / 'README.md').unlink()
            with self.assertRaises(ValueError):
                check(root)

    def test_route_folders_identify_source_version_language_and_variant(self):
        cases = {
            'clean-us': 'Patch/From Clean ROM/US/from-clean-us.xdelta',
            'clean-it': 'Patch/From Clean ROM/IT/from-clean-it.xdelta',
            'plus-1.01': 'Patch/From Plus 1.01/US/from-plus-1.01.xdelta',
            'plus-1.1-it': 'Patch/From Plus 1.1/IT/from-plus-1.1-it.xdelta',
            'plus-1.04-en-classic': 'Patch/From Plus 1.04/US/Normal Angle/from-plus-1.04-en-classic.xdelta',
            'plus-1.04-it-plus': 'Patch/From Plus 1.04/IT/New Angle/from-plus-1.04-it-plus.xdelta',
            'plus-1.2.2-en-prima': 'Patch/From Plus 1.2.2/US/First Edition 2026-09-19/from-plus-1.2.2-en-prima.xdelta',
            'plus-1.2.2-it': 'Patch/From Plus 1.2.2/IT/Second Edition/from-plus-1.2.2-it.xdelta',
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(pack.patch_path(source), expected)
        routes = [pack.patch_path(s['id']) for s in pack.config()['sources']]
        self.assertEqual(len(set(routes)), 21)
        self.assertFalse(any('From Plus 1.01/IT' in p for p in routes))

    def test_extracted_package_has_versioned_root_and_resolvable_inventory(self):
        route = 'Patch/From Clean ROM/US/from-clean-us.xdelta'
        manifest = {'version': '1.2.5', 'patches': [{'file': route}]}
        members = pack.finalize_members({'HOW-TO-INSTALL.txt': b'guide', route: b'delta'}, manifest)
        root = 'Sacred Gold Plus 1.2.5/'
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / 'package.zip'
            pack.write_zip(archive, members)
            with zipfile.ZipFile(archive) as z:
                self.assertTrue(all(n.startswith(root) for n in z.namelist()))
                inventory = json.loads(z.read(root + 'Patch/CONTENTS.json'))
                for name, pin in inventory['files'].items():
                    pack.verify_bytes(z.read(root + name), pin)
                saved = json.loads(z.read(root + 'Patch/manifest.json'))
                self.assertEqual(z.read(root + saved['patches'][0]['file']), b'delta')

    def test_both_guides_name_every_source_and_exact_patch_path(self):
        for lang in ('EN', 'IT'):
            text = pack.install_text(lang, pack.config())
            for source in pack.config()['sources']:
                self.assertIn(pack.patch_path(source['id']), text)
                self.assertIn(source['sha256'], text)
            self.assertIn(pack.config()['targets'][lang]['sha256'], text)
            names = {p.name for p in (pack.HERE / 'documents' / lang).glob('*.txt')}
            expected = ({'HOW-TO-INSTALL.txt', 'WHATS-NEW-1.2.5.txt'} if lang == 'EN'
                        else {'COME-INSTALLARE.txt', 'NOVITA-1.2.5.txt'})
            self.assertEqual(names, expected)

    def test_original_document_corruption_is_rejected(self):
        with self.assertRaises(ValueError): pack.verify_bytes(b'bad', {'bytes':3,'sha256':'0'*64})
    def test_archives_are_reproducible_and_read_back(self):
        with tempfile.TemporaryDirectory() as temp:
            a,b=Path(temp)/'a.zip',Path(temp)/'b.zip'
            members={'guide.txt':b'guide','Patch/a.xdelta':b'patch'}
            pack.write_zip(a,members);pack.write_zip(b,members)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            with zipfile.ZipFile(a) as z:self.assertEqual(set(z.namelist()),set(members))
    def test_existing_archive_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'a.zip';p.write_bytes(b'keep')
            with self.assertRaises(FileExistsError):pack.write_zip(p,{'guide':b'text'})
            self.assertEqual(p.read_bytes(),b'keep')
    def test_all_previously_supported_inputs_and_124_are_present(self):
        ids={x['id'] for x in pack.config()['sources']}
        self.assertEqual(len(ids),21)
        self.assertTrue({'clean-us','clean-it','plus-1.01','plus-1.02','plus-1.03','plus-1.2.3-en','plus-1.2.3-it','plus-1.2.4-en','plus-1.2.4-it'}<=ids)
