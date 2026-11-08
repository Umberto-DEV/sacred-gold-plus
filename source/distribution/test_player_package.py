"""Schema-3 player layout probes use small non-game fixture bytes."""
from contextlib import contextmanager
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import pack
import test_multilingual_pack as fixtures


class PlayerPackageTests(unittest.TestCase):
    def fixtures(self, root):
        cfg, refs, guides, inputs, contract = fixtures.MultilingualPackageTests().fixtures(root)
        cfg.update(schema=3, package_revision='r2')
        cfg['rompatcher_commit'] = json.loads((pack.HERE / 'release-1.3.2.json').read_text())['rompatcher_commit']
        cfg['shared_documents'] = copy.deepcopy(cfg['locales']['EN']['documents'][2:])
        for locale in fixtures.LOCALES:
            cfg['locales'][locale]['documents'] = cfg['locales'][locale]['documents'][:2]
        cfg['license'] = dict(name='LICENSE.txt', **fixtures.pin((pack.HERE.parents[1] / 'LICENSE').read_bytes()))
        cfg.pop('references')
        cfg.pop('original_documents')
        contract.write_text(json.dumps(cfg))
        return cfg, refs, guides, inputs, contract

    @contextmanager
    def decoders(self, root, cfg, corrupt=False):
        import player_package
        def external(args):
            values = list(map(str, args))
            if values[0] == 'xdelta3' and '-e' in values:
                source = Path(values[values.index('-s') + 1]).read_bytes()
                raw = bytes.fromhex('d6c3c40000') + bytes([len(source)]) + source + Path(values[-2]).read_bytes()
                Path(values[-1]).write_bytes(raw)
                return ''
            if values[0] == 'xdelta3':
                raw = Path(values[-2]).read_bytes()
                source = Path(values[values.index('-s') + 1]).read_bytes()
                self.assertEqual(raw[6:6 + raw[5]], source)
                Path(values[-1]).write_bytes(b'wrong' if corrupt == 'xdelta' else raw[6 + raw[5]:])
                return ''
            if values[0] == 'node':
                raw = Path(values[4]).read_bytes()
                self.assertEqual(raw[6:6 + raw[5]], Path(values[3]).read_bytes())
                Path(values[-1]).write_bytes(b'wrong' if corrupt == 'node' else raw[6 + raw[5]:])
                return json.dumps(dict(result='PASS', patch_sha256=hashlib.sha256(raw).hexdigest()))
            raise AssertionError(values)
        with fixtures.MultilingualPackageTests().decoders(root, corrupt), mock.patch.object(
                player_package, 'published_targets', return_value=cfg['targets']), \
                mock.patch.object(pack, 'run', external):
            yield

    def test_schema3_is_explicit_and_historical_default_stays_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg, refs, guides, inputs, contract = self.fixtures(root)
            try:
                with self.decoders(root, cfg):
                    actual = pack.config(contract)
            except (ValueError, ImportError) as exc:
                self.fail('The explicit schema-3 player contract must be accepted: ' + str(exc))
            self.assertEqual((actual['schema'], actual['package_revision']), (3, 'r2'))
        self.assertEqual((pack.config()['schema'], pack.config()['version']), (1, '1.3.1'))

    def test_primary_five_and_optional_150_have_exact_named_routes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg, refs, guides, inputs, contract = self.fixtures(root)
            output = root / 'out'
            with self.decoders(root, cfg):
                results = pack.build(inputs, root / 'no-historical-imports', guides, output,
                                     root / 'unused', contract=contract)
            self.assertEqual([r['routes'] for r in results], [5, 150])
            self.assertEqual([r['file'] for r in results], [
                'Sacred-Gold-Plus-1.3.2-r2-Multilingual.zip',
                'Sacred-Gold-Plus-1.3.2-r2-Optional-Updaters.zip'])
            prefix = 'Sacred Gold Plus 1.3.2/'
            with zipfile.ZipFile(output / results[0]['file']) as archive:
                names = archive.namelist()
                relative = {name[len(prefix):] for name in names}
                self.assertTrue(all(name.startswith(prefix) for name in names))
                self.assertEqual({name.split('/')[0] for name in relative},
                                 set(fixtures.FOLDERS.values()) | {'Originals', 'START-HERE.txt'})
                self.assertFalse(any(name.endswith('.json') or '/Documents/' in name for name in names))
                self.assertFalse(any(name.endswith(('.nds', '.sav')) for name in names))
                self.assertEqual(len([name for name in names if name.endswith('.xdelta')]), 5)
                self.assertNotIn(str(root).encode(), b'\n'.join(archive.read(name) for name in names))
                for locale in fixtures.LOCALES:
                    folder = prefix + fixtures.FOLDERS[locale] + '/'
                    patch = folder + 'Patch/Sacred-Gold-Plus-1.3.2-' + locale + '.xdelta'
                    raw = archive.read(patch)
                    expected_source = {'EN': b'clean-us', 'IT': b'clean-it', 'FR': b'clean-fr',
                                       'ES': b'clean-es', 'DE': b'clean-de'}[locale]
                    self.assertEqual(raw[6:6 + raw[5]], expected_source)
                    self.assertEqual(raw[6 + raw[5]:], ('target ' + locale).encode())
                    for row in cfg['locales'][locale]['documents']:
                        self.assertEqual(fixtures.pin(archive.read(folder + row['name'])),
                                         {key: row[key] for key in ('sha256', 'bytes')})
                    for row in cfg['locales'][locale]['cheats']:
                        self.assertEqual(fixtures.pin(archive.read(folder + 'Cheats/' + row['name'])),
                                         {key: row[key] for key in ('sha256', 'bytes')})
                    self.assertEqual(archive.read(folder + 'Credits-and-Licenses/LICENSE.txt'),
                                     (pack.HERE.parents[1] / 'LICENSE').read_bytes())
                    self.assertTrue(archive.read(folder + 'Credits-and-Licenses/ABOUT.txt'))
                self.assertEqual({name for name in relative if name.startswith('Originals/')},
                                 {'Originals/' + row['name'] for row in cfg['shared_documents']})
            updater_prefix = 'Sacred Gold Plus 1.3.2 Optional Updaters/'
            with zipfile.ZipFile(output / results[1]['file']) as archive:
                names = archive.namelist()
                self.assertTrue(all(name.startswith(updater_prefix) for name in names))
                self.assertEqual(len([name for name in names if name.endswith('.xdelta')]), 150)
                self.assertIn(results[0]['file'], archive.read(updater_prefix + 'README.txt').decode())
                for locale in fixtures.LOCALES:
                    folder = updater_prefix + fixtures.FOLDERS[locale] + '/'
                    self.assertTrue(archive.read(folder + 'Credits-and-Licenses/ABOUT.txt'))
                    self.assertEqual(archive.read(folder + 'Credits-and-Licenses/LICENSE.txt'),
                                     (pack.HERE.parents[1] / 'LICENSE').read_bytes())
                    manifest = json.loads(archive.read(folder + 'manifest.json'))
                    self.assertEqual(manifest['language'], locale)
                    self.assertEqual({row['source']['id'] for row in manifest['patches']},
                                     {row['id'] for row in cfg['sources']})
                    self.assertIn(folder + 'README-Updater.txt', names)
                    readme = archive.read(folder + 'README-Updater.txt').decode()
                    self.assertIn(cfg['targets'][locale]['sha256'], readme)
                    self.assertIn(str(cfg['targets'][locale]['bytes']), readme)
                    for row in manifest['patches']:
                        expected = 'Patch/Sacred-Gold-Plus-1.3.2-' + locale + '-from-' + row['source']['id'] + '.xdelta'
                        self.assertEqual(row['file'], expected)
                        self.assertIn(expected, readme)
                        self.assertIn(row['source']['sha256'], readme)
                        self.assertEqual(fixtures.pin(archive.read(folder + expected)),
                                         {key: row[key] for key in ('sha256', 'bytes')})
                inventory = json.loads(archive.read(updater_prefix + 'CONTENTS.json'))['files']
                self.assertEqual(set(inventory),
                                 {name[len(updater_prefix):] for name in names} - {'CONTENTS.json', 'SHA256SUMS'})
                for name, expected in inventory.items():
                    self.assertEqual(fixtures.pin(archive.read(updater_prefix + name)), expected)
                for line in archive.read(updater_prefix + 'SHA256SUMS').decode().splitlines():
                    expected, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(archive.read(updater_prefix + name)).hexdigest(), expected)
            receipt = json.loads((output / 'verification.json').read_text())
            self.assertEqual(receipt['assets'], results)
            self.assertEqual(receipt['verified_routes'], 150)
            self.assertFalse(list(output.glob('sgp-package-*')))

    def test_rejects_route_gaps_target_repin_wrong_documents_and_unsafe_license(self):
        mutations = (
            lambda cfg: cfg['routes_by_target']['FR'].pop(),
            lambda cfg: cfg['routes_by_target']['IT'].append('clean-it'),
            lambda cfg: cfg['targets']['DE'].update(sha256='0' * 64),
            lambda cfg: cfg['locales']['FR']['documents'].reverse(),
            lambda cfg: cfg['locales']['IT']['documents'].append(cfg['shared_documents'][0]),
            lambda cfg: cfg['shared_documents'].pop(),
            lambda cfg: cfg['shared_documents'][0].update(name='Special-Events-1.3.2-FR.pdf'),
            lambda cfg: cfg['license'].update(name='../LICENSE.txt'),
            lambda cfg: cfg.update(package_revision='r3'),
            lambda cfg: cfg['sources'][0].update(sha256='0' * 64),
            lambda cfg: cfg['sources'].pop(),
            lambda cfg: cfg['locales']['FR'].update(cheats=[]),
            lambda cfg: cfg['locales']['FR']['cheats'][0].update(name='../codes.txt'),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                cfg, refs, guides, inputs, contract = self.fixtures(root)
                accepted = copy.deepcopy(cfg['targets'])
                mutate(cfg)
                contract.write_text(json.dumps(cfg))
                import player_package
                with mock.patch.object(pack, 'multilingual_source_registry', return_value={
                        row['id']: fixtures.pin(row['id'].encode()) for row in cfg['sources']}), \
                        mock.patch.object(player_package, 'published_targets', return_value=accepted):
                    with self.assertRaises(ValueError):
                        pack.config(contract)

    def test_changed_document_cheat_or_license_refuses_before_output(self):
        for kind in ('missing-pdf', 'shared-pdf', 'cheat', 'license', 'symlink-pdf'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                cfg, refs, guides, inputs, contract = self.fixtures(root)
                document = guides / 'FR/Installation-1.3.2-FR.pdf'
                if kind == 'missing-pdf':
                    document.unlink()
                elif kind == 'shared-pdf':
                    (guides / 'EN' / cfg['shared_documents'][0]['name']).write_bytes(b'%PDF-changed')
                elif kind == 'cheat':
                    (guides / 'FR/Cheats/Cheats.xml').write_bytes(b'changed')
                elif kind == 'license':
                    cfg['license']['sha256'] = '0' * 64
                    contract.write_text(json.dumps(cfg))
                else:
                    raw = document.read_bytes()
                    document.unlink()
                    elsewhere = root / 'elsewhere.pdf'
                    elsewhere.write_bytes(raw)
                    document.symlink_to(elsewhere)
                output = root / 'out'
                with self.decoders(root, cfg), self.assertRaises(ValueError):
                    pack.build(inputs, refs, guides, output, root / 'unused', contract=contract)
                self.assertFalse(output.exists())

    def test_decoder_failure_removes_temporary_roms_and_emits_no_receipt(self):
        for decoder in ('node', 'xdelta'):
            with self.subTest(decoder=decoder), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                cfg, refs, guides, inputs, contract = self.fixtures(root)
                output = root / 'out'
                with self.decoders(root, cfg, decoder), self.assertRaisesRegex(ValueError, 'pin'):
                    pack.build(inputs, refs, guides, output, root / 'unused', contract=contract)
                self.assertFalse(list(output.rglob('*.nds')))
                self.assertFalse(list(output.glob('sgp-package-*')))
                self.assertFalse((output / 'verification.json').exists())


    def test_oversize_zip_emits_no_verification_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg, refs, guides, inputs, contract = self.fixtures(root)
            output = root / 'out'
            write_zip = pack.write_zip
            def oversized(path, members):
                write_zip(path, members)
                with path.open('r+b') as handle:
                    handle.truncate(2 * 1024 ** 3)
            with self.decoders(root, cfg), mock.patch.object(pack, 'write_zip', oversized):
                with self.assertRaisesRegex(ValueError, '2 GiB'):
                    pack.build(inputs, refs, guides, output, root / 'unused', contract=contract)
            self.assertFalse((output / 'verification.json').exists())
            self.assertFalse((output / 'SHA256SUMS').exists())

    def test_missing_extra_or_mismatched_input_refuses_before_output(self):
        for kind in ('missing', 'extra', 'mismatched'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                cfg, refs, guides, inputs, contract = self.fixtures(root)
                paths = json.loads(inputs.read_text())
                if kind == 'missing':
                    paths.pop('clean-us')
                elif kind == 'extra':
                    paths['unknown'] = paths['clean-us']
                else:
                    paths['clean-us'] = paths['clean-it']
                inputs.write_text(json.dumps(paths))
                output = root / 'out'
                with self.decoders(root, cfg), self.assertRaises(ValueError):
                    pack.build(inputs, refs, guides, output, root / 'unused', contract=contract)
                self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
