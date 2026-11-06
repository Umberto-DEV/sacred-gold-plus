import copy
import hashlib
import json
import os
import runpy
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile
import pack
from test_document_sources import write_private_document_fixture

class PackageTests(unittest.TestCase):
    def setUp(self):
        self.document_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.document_temp.cleanup)
        root = Path(self.document_temp.name).resolve()
        write_private_document_fixture(root, pack.config())
        env = mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(root)})
        env.start()
        self.addCleanup(env.stop)

    def test_reference_rejects_methods_without_bounded_python_decompression(self):
        for method in (zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
            with self.subTest(method=method), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                cfg, reference, _ = self.reference_fixture(directory)
                with zipfile.ZipFile(reference, 'a', compression=method) as archive:
                    archive.writestr('Cheats/unsupported.txt', b'controlled')
                cfg['references']['EN']['sha256'] = pack.digest(reference)
                with self.assertRaisesRegex(ValueError, 'compression method'):
                    pack.reference_members('EN', directory, directory, cfg)

    def test_reference_member_decompression_has_individual_and_total_limits(self):
        for total_case in (False, True):
            with self.subTest(total=total_case), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                cfg, reference, _ = self.reference_fixture(directory)
                with zipfile.ZipFile(reference, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr('Cheats/expanded.txt', b'X' * (16 if total_case else 33))
                    # An unused oversized patch is never decompressed by packaging.
                    archive.writestr('Patch/unused.xdelta', b'Y' * 1024)
                cfg['references']['EN']['sha256'] = pack.digest(reference)
                with mock.patch.object(pack, 'MAX_REFERENCE_MEMBER_BYTES', 128 if total_case else 32, create=True), \
                     mock.patch.object(pack, 'MAX_REFERENCE_TOTAL_BYTES', 64 if total_case else 1024, create=True):
                    with self.assertRaisesRegex(ValueError, 'decompress'):
                        pack.reference_members('EN', directory, directory, cfg)

    def test_decompression_exact_boundary_and_unselected_large_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            cfg, reference, _ = self.reference_fixture(directory)
            cfg['cheats_policy'] = 'omit-unverified'
            with zipfile.ZipFile(reference, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('Patch/unused.xdelta', b'X' * 1024)
                archive.writestr('Cheats/unused.txt', b'Y' * 1024)
            cfg['references']['EN']['sha256'] = pack.digest(reference)
            # 24-byte original manual + 18-byte guide + 15-byte license.
            with mock.patch.object(pack, 'MAX_REFERENCE_MEMBER_BYTES', 24), \
                 mock.patch.object(pack, 'MAX_REFERENCE_TOTAL_BYTES', 57):
                members = pack.reference_members('EN', directory, directory, cfg)
                self.assertEqual(members['LICENSE.txt'], b'trusted license')
                self.assertNotIn('Cheats/unused.txt', members)
            with mock.patch.object(pack, 'MAX_REFERENCE_TOTAL_BYTES', 56):
                with self.assertRaisesRegex(ValueError, 'decompress'):
                    pack.reference_members('EN', directory, directory, cfg)

    def test_archive_members_reject_traversal_windows_aliases_and_collisions(self):
        invalid = ['../escape', '/absolute', 'Cheats/../../escape',
                   r'Cheats/..\..\escape', 'Cheats/C:escape', 'Cheats/NUL.txt',
                   'Cheats/file.', 'Cheats/file ', 'Cheats//file', 'Cheats/./file',
                   'Cheats/a\x00b', 'Cheats/COM¹.txt', 'Cheats/LPT².txt', 'Cheats/COM³']
        for name in invalid:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                destination = Path(tmp) / 'out.zip'
                with self.assertRaises(ValueError):
                    pack.write_zip(destination, {name: b'controlled'})
                self.assertFalse(destination.exists())
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                pack.write_zip(Path(tmp) / 'out.zip', {'Guide.txt': b'a', 'guide.txt': b'b'})

    def test_contract_version_and_source_ids_cannot_control_paths(self):
        for version in ('../../escape', r'..\escape', 'x:y'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                pack.finalize_members({'guide.txt': b'guide'}, {'version': version})
        for source in ('clean-us/../../escape', r'clean-us\escape', 'clean-C:'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                pack.patch_path(source)

    def test_reference_names_cannot_collide_after_version_relabel(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            cfg, reference, _ = self.reference_fixture(directory)
            with zipfile.ZipFile(reference, 'a') as archive:
                archive.writestr('Cheats/Name-1.2.3.txt', b'first')
                archive.writestr('Cheats/Name-' + cfg['version'] + '.txt', b'second')
            cfg['references']['EN']['sha256'] = pack.digest(reference)
            with self.assertRaisesRegex(ValueError, 'collision'):
                pack.reference_members('EN', directory, directory, cfg)

    def test_authored_cheat_notice_explicitly_replaces_inherited_notice(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            cfg, reference, _ = self.reference_fixture(directory)
            with zipfile.ZipFile(reference, 'a') as archive:
                archive.writestr('Cheats/ABOUT-CHEATS.txt', b'old notice')
            cfg['references']['EN']['sha256'] = pack.digest(reference)
            members = pack.reference_members('EN', directory, directory, cfg)
            authored = pack.documents_dir(cfg) / 'EN/Cheats/ABOUT-CHEATS.txt'
            self.assertEqual(members['Cheats/ABOUT-CHEATS.txt'], authored.read_bytes())

    def rompatcher_git_fixture(self, directory):
        checkout = directory / 'rompatcher'
        modules = checkout / 'rom-patcher-js' / 'modules'
        modules.mkdir(parents=True)
        (checkout / 'rom-patcher-js' / 'RomPatcher.js').write_text(
            "module.exports = require('./modules/HashCalculator');\n")
        (modules / 'BinFile.js').write_text(
            "module.exports = require('./HashCalculator');\n")
        (modules / 'HashCalculator.js').write_text("module.exports = 'trusted';\n")
        subprocess.run(['git', 'init', '-q', checkout], check=True)
        subprocess.run(['git', '-C', checkout, 'config', 'user.name', 'Package test'], check=True)
        subprocess.run(['git', '-C', checkout, 'config', 'user.email', 'package-test@example.invalid'], check=True)
        subprocess.run(['git', '-C', checkout, 'add', '.'], check=True)
        subprocess.run(['git', '-C', checkout, 'commit', '-qm', 'pinned fixture'], check=True)
        commit = subprocess.run(
            ['git', '-C', checkout, 'rev-parse', 'HEAD'], check=True,
            capture_output=True, text=True).stdout.strip()
        return checkout, commit

    def test_rompatcher_snapshot_excludes_untracked_module_and_later_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout, commit = self.rompatcher_git_fixture(Path(temp))
            modules = checkout / 'rom-patcher-js' / 'modules'
            (modules / 'HashCalculator').write_text("module.exports = 'untracked';\n")

            with pack.pinned_git_snapshot(checkout, commit) as snapshot:
                self.assertFalse((snapshot / 'rom-patcher-js' / 'modules' / 'HashCalculator').exists())
                snap_bin = snapshot / 'rom-patcher-js' / 'modules' / 'BinFile.js'
                self.assertEqual(snap_bin.read_text(), "module.exports = require('./HashCalculator');\n")
                (modules / 'BinFile.js').write_text("module.exports = 'replaced';\n")
                self.assertEqual(snap_bin.read_text(), "module.exports = require('./HashCalculator');\n")

    def test_rompatcher_snapshot_uses_commit_when_index_hides_worktree_change(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout, commit = self.rompatcher_git_fixture(Path(temp))
            relative = 'rom-patcher-js/modules/BinFile.js'
            tracked = checkout / relative
            tracked.write_text("module.exports = 'hidden replacement';\n")
            subprocess.run(['git', '-C', checkout, 'update-index', '--skip-worktree', relative], check=True)

            with pack.pinned_git_snapshot(checkout, commit) as snapshot:
                self.assertEqual(
                    (snapshot / relative).read_text(),
                    "module.exports = require('./HashCalculator');\n")

    def test_rompatcher_snapshot_never_runs_lazy_fetch_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            source, commit = self.rompatcher_git_fixture(directory)
            subprocess.run(
                ['git', '-C', source, 'config', 'uploadpack.allowFilter', 'true'], check=True)
            partial = directory / 'partial'
            subprocess.run([
                'git', 'clone', '-q', '--filter=blob:none', '--no-checkout',
                source.resolve().as_uri(), partial,
            ], check=True)
            marker = directory / 'LAZY_FETCH_EXECUTED'
            helper = directory / 'upload-pack-helper'
            helper.write_text(
                '#!/bin/sh\n'
                'printf executed > "$SGP_LAZY_FETCH_MARKER"\n'
                'exit 1\n')
            helper.chmod(0o700)
            subprocess.run(
                ['git', '-C', partial, 'config', 'remote.origin.uploadpack', str(helper)],
                check=True)

            with mock.patch.dict(os.environ, {'SGP_LAZY_FETCH_MARKER': str(marker)}):
                with self.assertRaises(ValueError):
                    with pack.pinned_git_snapshot(partial, commit):
                        pass
            self.assertFalse(marker.exists())

    def test_git_config_fsmonitor_cannot_execute_during_snapshot_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            checkout, commit = self.rompatcher_git_fixture(directory)
            marker = directory / 'FSMONITOR_EXECUTED'
            helper = directory / 'fsmonitor-helper'
            helper.write_text('#!/bin/sh\nprintf executed > "$SGP_FSMONITOR_MARKER"\nprintf "\\000"\n')
            helper.chmod(0o700)
            subprocess.run(['git', '-C', checkout, 'config', 'core.fsmonitor', str(helper)], check=True)
            with mock.patch.dict(os.environ, {'SGP_FSMONITOR_MARKER': str(marker)}):
                # Positive attack control: the old cleanliness check runs it.
                subprocess.run(['git', '-C', checkout, 'status', '--porcelain',
                                '--untracked-files=no'], capture_output=True)
                self.assertTrue(marker.exists())
                marker.unlink()
                with pack.pinned_git_snapshot(checkout, commit) as snapshot:
                    self.assertEqual((snapshot / 'rom-patcher-js/modules/HashCalculator.js').read_text(),
                                     "module.exports = 'trusted';\n")
                self.assertFalse(marker.exists())

    def test_rompatcher_snapshot_rejects_nested_and_symlink_checkout_roots(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            checkout, commit = self.rompatcher_git_fixture(directory)
            nested = checkout / 'untracked-checkout'
            (nested / 'rom-patcher-js').mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, 'root'):
                with pack.pinned_git_snapshot(nested, commit):
                    pass

            linked = directory / 'linked-checkout'
            linked.symlink_to(checkout, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                with pack.pinned_git_snapshot(linked, commit):
                    pass

    def test_build_executes_rompatcher_only_from_private_commit_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            checkout, commit = self.rompatcher_git_fixture(directory)
            shadow = checkout / 'rom-patcher-js' / 'modules' / 'HashCalculator'
            shadow.write_text("module.exports = 'untracked';\n")
            source = directory / 'source.nds'
            target = directory / 'target.nds'
            source.write_bytes(b'source bytes')
            target.write_bytes(b'target bytes')

            def pin(path):
                return {'name': path.name, 'bytes': path.stat().st_size,
                        'sha256': pack.digest(path)}

            contract = directory / 'contract.json'
            contract.write_text(json.dumps({
                'version': 'test',
                'documents': 'documents',
                'cheats_policy': 'omit-unverified',
                'rompatcher_commit': commit,
                'sources': [dict(id='clean-us', **pin(source))],
                'targets': {'EN': pin(target)},
                'references': {'EN': {'name': 'unused.zip', 'sha256': '0' * 64}},
                'original_documents': {},
            }))
            inputs = directory / 'inputs.json'
            inputs.write_text(json.dumps({'clean-us': str(source), 'target-EN': str(target)}))
            observed_snapshots = []

            def fake_external_run(args):
                args = [str(value) for value in args]
                if args[0] == 'git':
                    return commit + '\n' if 'rev-parse' in args else ''
                if args[0] == 'xdelta3':
                    if '-e' in args:
                        Path(args[-1]).write_bytes(bytes.fromhex('d6c3c40000') + b'fixture')
                    else:
                        Path(args[-1]).write_bytes(target.read_bytes())
                    return ''
                if args[0] == 'node':
                    snapshot = Path(args[2])
                    observed_snapshots.append(snapshot)
                    self.assertNotEqual(snapshot.resolve(), checkout.resolve())
                    self.assertFalse(
                        (snapshot / 'rom-patcher-js' / 'modules' / 'HashCalculator').exists())
                    Path(args[-1]).write_bytes(target.read_bytes())
                    return json.dumps({
                        'result': 'PASS',
                        'patch_sha256': hashlib.sha256(Path(args[4]).read_bytes()).hexdigest(),
                    })
                self.fail('Unexpected command: ' + repr(args))

            with mock.patch.object(pack, 'reference_members', return_value={}):
                with mock.patch.object(pack, 'run', side_effect=fake_external_run):
                    results = pack.build(inputs, directory, directory, directory / 'output',
                                         checkout, contract=contract)

            self.assertEqual(len(observed_snapshots), 1)
            self.assertEqual(results[0]['routes'], 1)

    def reference_fixture(self, directory, lang='EN'):
        cfg = copy.deepcopy(pack.config())
        cfg['cheats_policy'] = 'inherit-reference'
        original = b'original gameplay manual'
        cfg['original_documents'] = {'Evolution Changes.pdf': {
            'bytes': len(original), 'sha256': hashlib.sha256(original).hexdigest()}}
        reference = directory / 'reference.zip'
        license_name = 'LICENZA.txt' if lang == 'IT' else 'LICENSE.txt'
        with zipfile.ZipFile(reference, 'w') as archive:
            archive.writestr('Manual/Evolution Changes.pdf', original)
            archive.writestr('Manual/Game Guide.txt', b'trusted game guide')
            archive.writestr(license_name, b'trusted license')
        cfg['references'][lang] = {'name': reference.name, 'sha256': pack.digest(reference)}
        for name in pack.guide_names(lang, cfg):
            (directory / name).write_bytes(b'current PDF')
        return cfg, reference, license_name

    def test_reference_zip_path_swap_cannot_change_authenticated_members(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            cfg, reference, license_name = self.reference_fixture(directory)
            forged = directory / 'forged.zip'
            with zipfile.ZipFile(forged, 'w') as archive:
                archive.writestr('Manual/Evolution Changes.pdf', b'original gameplay manual')
                archive.writestr('Manual/Game Guide.txt', b'forged game guide')
                archive.writestr(license_name, b'forged license')

            real_zip = zipfile.ZipFile
            path_opened = []

            def swap_before_path_open(file, *args, **kwargs):
                if isinstance(file, (str, os.PathLike)):
                    path_opened.append(Path(file))
                    forged.replace(reference)
                return real_zip(file, *args, **kwargs)

            with mock.patch.object(pack.zipfile, 'ZipFile', side_effect=swap_before_path_open):
                members = pack.reference_members('EN', directory, directory, cfg)

            self.assertEqual(members[license_name], b'trusted license')
            self.assertEqual(members['Manual/Game Guide.txt'], b'trusted game guide')
            self.assertEqual(path_opened, [])

    def test_reference_zip_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            cfg, reference, _ = self.reference_fixture(directory)
            target = directory / 'target.zip'
            reference.replace(target)
            reference.symlink_to(target.name)
            cfg['references']['EN']['sha256'] = pack.digest(target)

            with self.assertRaisesRegex(ValueError, 'regular|symlink'):
                pack.reference_members('EN', directory, directory, cfg)

    def test_guide_file_and_directory_symlinks_are_rejected_before_packaging(self):
        for root_link in (False, True):
            with self.subTest(root_link=root_link), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                guides = root / 'guides'
                guides.mkdir()
                cfg, _, _ = self.reference_fixture(guides)
                supplied = guides
                if root_link:
                    supplied = root / 'linked-guides'
                    supplied.symlink_to(guides, target_is_directory=True)
                else:
                    name = pack.guide_names('EN', cfg)[0]
                    outside = root / 'host-secret.pdf'
                    outside.write_bytes(b'HOST_SECRET_SENTINEL')
                    (guides / name).unlink()
                    (guides / name).symlink_to(outside)
                with self.assertRaisesRegex(ValueError, 'guide|regular|symlink'):
                    pack.reference_members('EN', guides, supplied, cfg)

    def test_guide_directory_swap_cannot_escape_after_link_check(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            guides = root / 'guides'
            guides.mkdir()
            external = root / 'external'
            external.mkdir()
            moved = root / 'original-guides'
            real_lstat = pack.os.lstat
            swapped = False

            def swap_after_check(path):
                nonlocal swapped
                result = real_lstat(path)
                if not swapped and Path(path).name == guides.name:
                    guides.rename(moved)
                    guides.symlink_to(external, target_is_directory=True)
                    swapped = True
                return result

            with mock.patch.object(pack.os, 'lstat', side_effect=swap_after_check):
                with self.assertRaisesRegex(ValueError, 'symlink'):
                    with pack.guide_directory_descriptor(guides):
                        self.fail('swapped guide directory was opened')

    def test_guide_fifo_is_opened_nonblocking_then_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            guides = Path(temp) / 'guides'
            guides.mkdir()
            fifo = guides / 'guide.pdf'
            os.mkfifo(fifo)
            real_open = pack.os.open

            def require_nonblocking(path, flags, *args, **kwargs):
                if path == fifo.name and kwargs.get('dir_fd') is not None:
                    self.assertTrue(flags & os.O_NONBLOCK)
                return real_open(path, flags, *args, **kwargs)

            with pack.guide_directory_descriptor(guides) as descriptor:
                with mock.patch.object(pack.os, 'open', side_effect=require_nonblocking):
                    with self.assertRaisesRegex(ValueError, 'regular'):
                        pack.guide_file_bytes(descriptor, fifo.name)

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
                expected = pack.guide_names(lang, cfg)
                for name in expected:
                    (directory / name).write_bytes(b'current PDF')
                members = pack.reference_members(lang, directory, directory, cfg)
                self.assertEqual(sorted(n for n in members if '/' not in n), sorted(expected + [license_name]))
                self.assertEqual(members['Manual/Evolution Changes.pdf'], original)
                self.assertNotIn('Manual/How-to-install-EN.pdf', members)
                self.assertNotIn('Manual/Whats-New-1.2-EN.pdf', members)

    def test_source_archive_excludes_assistant_instructions(self):
        check = runpy.run_path(str(pack.HERE.parents[1] / '.github/check_public.py'))['check']
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root / '.github').mkdir()
            files = ['.github/public-files.json', 'README.md']
            (root / '.github/public-files.json').write_text(json.dumps(files))
            (root / 'README.md').write_text('Public source archive')
            self.assertEqual(check(root), 2)
            (root / 'AGENTS.md').write_text('Private instructions')
            (root / '.github/public-files.json').write_text(json.dumps(files + ['AGENTS.md']))
            with self.assertRaisesRegex(ValueError, 'Assistant-only'):
                check(root)
            (root / 'AGENTS.md').unlink()
            for private in ('PRODUCT.md', 'DESIGN.md',
                            'source/docs/HANDOFF-debug-optimization.md',
                            'source/docs/deep-debug-2026-10-28-plan.md',
                            'source/docs/graphics-engine-exploration.md'):
                with self.subTest(private=private):
                    target = root / private
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text('Private working notes')
                    (root / '.github/public-files.json').write_text(json.dumps(files + [private]))
                    try:
                        with self.assertRaisesRegex(ValueError, 'Assistant-only'):
                            check(root)
                    finally:
                        target.unlink()
            (root / '.github/public-files.json').write_text(json.dumps(files))
            (root / 'README.md').unlink()
            with self.assertRaises(ValueError):
                check(root)

    def test_public_gate_rejects_tracked_xdelta_release_assets(self):
        check = runpy.run_path(str(pack.HERE.parents[1] / '.github/check_public.py'))['check']
        payload = bytes.fromhex('d6c3c40000') + b'controlled-patch-payload'
        for name in ('leak.xdelta', 'leak.XDELTA', 'leak.xdelta.txt',
                     'images/leak.vcdiff', 'source/sgp12/build/leak.bin'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                (root / '.github').mkdir()
                files = ['.github/public-files.json', 'README.md', name]
                (root / '.github/public-files.json').write_text(json.dumps(files))
                (root / 'README.md').write_text('Patch/a.xdelta is a release asset name, not a tracked file.')
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                (root / name).write_bytes(payload)
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
        self.assertEqual(len(set(routes)), 25)
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
            names = {p.name for p in (pack.documents_dir(pack.config()) / lang).glob('*.txt')}
            expected = ({'HOW-TO-INSTALL.txt', 'WHATS-NEW-1.3.1.txt'} if lang == 'EN'
                        else {'COME-INSTALLARE.txt', 'NOVITA-1.3.1.txt'})
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
        self.assertEqual(len(ids),25)
        self.assertTrue({'clean-us','clean-it','plus-1.01','plus-1.02','plus-1.03','plus-1.2.3-en','plus-1.2.3-it','plus-1.2.4-en','plus-1.2.4-it'}<=ids)
