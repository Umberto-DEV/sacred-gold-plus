"""Current release defaults and explicit private player-document inputs."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import pack


def write_private_document_fixture(root, cfg):
    """English synthetic localization inputs; no player translation is bundled."""
    import shutil
    bundled = pack.HERE / cfg['documents'] / 'EN'
    shutil.copytree(bundled, root / 'EN')
    italian = root / 'IT'
    italian.mkdir()
    text = 'Synthetic localized installation fixture\n' + '\n'.join(
        pack.patch_path(row['id']) + ' ' + row['sha256'] for row in cfg['sources'])
    text += '\n' + cfg['targets']['IT']['sha256']
    (italian / 'COME-INSTALLARE.txt').write_text(text)
    (italian / ('NOVITA-' + cfg['version'] + '.txt')).write_text('Synthetic current feature fixture')
    for folder, name in [('Cheats', 'LEGGIMI-CHEAT.txt'), ('Manual', 'LEGGIMI-MANUALI.txt')]:
        (italian / folder).mkdir()
        (italian / folder / name).write_text('Synthetic current player notice')


class DocumentSourceTests(unittest.TestCase):
    def test_default_contract_is_current_and_covers_upgrade_routes(self):
        cfg = pack.config()
        self.assertEqual(cfg['version'], '1.3.1')
        self.assertEqual(len(cfg['sources']), 25)
        self.assertEqual(cfg['cheats_policy'], 'omit-unverified')

    def test_explicit_private_documents_are_used_without_mutating_contract(self):
        cfg = pack.config(pack.HERE / 'release-1.3.1.json')
        before = copy.deepcopy(cfg)
        text = 'Private localized document fixture\n' + '\n'.join(
            pack.patch_path(s['id']) + ' ' + s['sha256'] for s in cfg['sources'])
        text += '\n' + cfg['targets']['IT']['sha256']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'IT').mkdir()
            (root / 'IT/COME-INSTALLARE.txt').write_text(text)
            with mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(root)}):
                self.assertEqual(pack.install_text('IT', cfg), text)
        self.assertEqual(cfg, before)

    def test_private_document_symlink_is_rejected(self):
        cfg = pack.config(pack.HERE / 'release-1.3.1.json')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'IT').mkdir()
            secret = root / 'private.txt'
            secret.write_text('not a player guide')
            (root / 'IT/COME-INSTALLARE.txt').symlink_to(secret)
            with mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(root)}):
                with self.assertRaisesRegex(ValueError, 'symlink|regular'):
                    pack.install_text('IT', cfg)

    def test_missing_private_localization_fails_with_actionable_message(self):
        cfg = pack.config(pack.HERE / 'release-1.3.1.json')
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(Path(tmp).resolve())}):
                with self.assertRaisesRegex(ValueError, 'SGP_PLAYER_DOCUMENTS_DIR'):
                    pack.install_text('IT', cfg)

    def test_missing_required_notices_are_rejected(self):
        for lang, notice in [('EN', 'Cheats/ABOUT-CHEATS.txt'),
                             ('EN', 'Manual/ABOUT-THESE-GUIDES.txt'),
                             ('IT', 'Cheats/LEGGIMI-CHEAT.txt'),
                             ('IT', 'Manual/LEGGIMI-MANUALI.txt')]:
            with self.subTest(lang=lang, notice=notice), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                cfg = pack.config()
                docs = root / 'documents'
                write_private_document_fixture(docs, cfg)
                (docs / lang / notice).unlink()
                cfg['original_documents'] = {}
                reference = root / 'reference.zip'
                with zipfile.ZipFile(reference, 'w') as archive:
                    archive.writestr('LICENZA.txt' if lang == 'IT' else 'LICENSE.txt', b'license')
                cfg['references'][lang] = {'name': reference.name, 'sha256': pack.digest(reference)}
                for name in pack.guide_names(lang, cfg):
                    (root / name).write_bytes(b'%PDF-fixture')
                with mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(docs)}):
                    with self.assertRaisesRegex(ValueError, 'notice|document'):
                        pack.reference_members(lang, root, root, cfg)

    def test_guide_inputs_are_checked_before_creating_outputs(self):
        import guide
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            docs = root / 'documents'
            write_private_document_fixture(docs, pack.config())
            (docs / 'IT/COME-INSTALLARE.txt').unlink()
            output = root / 'generated'
            with mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(docs)}), \
                 mock.patch.object(guide, 'install_guide') as install, \
                 mock.patch.object(guide, 'news_guide') as news:
                with self.assertRaisesRegex(ValueError, 'SGP_PLAYER_DOCUMENTS_DIR'):
                    guide.build(output)
                install.assert_not_called()
                news.assert_not_called()
                self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
