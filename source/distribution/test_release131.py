"""Versioned packaging must not relabel the published contract or old cheats."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile
import pack
from test_document_sources import write_private_document_fixture

class Release131Tests(unittest.TestCase):
    def setUp(self):
        self.document_temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.document_temp.cleanup)
        root = Path(self.document_temp.name).resolve()
        write_private_document_fixture(root, pack.config())
        env = mock.patch.dict(os.environ, {'SGP_PLAYER_DOCUMENTS_DIR': str(root)})
        env.start()
        self.addCleanup(env.stop)

    def test_current_contract_covers_every_supported_upgrade(self):
        cfg = pack.config()
        self.assertEqual(pack.digest(pack.HERE / 'release-1.3.1.json'),
                         'ecee7bef3cc14f2a4ce05938cffe221cea0489bb2282b123664a2ab8351903a9')
        self.assertEqual(cfg, pack.config(pack.HERE / 'release-1.3.1.json'))
        self.assertEqual(cfg['version'], '1.3.1')
        self.assertEqual(cfg['package_revision'], 2)
        self.assertEqual(cfg['status'], 'release-package-verified')
        self.assertEqual(cfg['open_gates'], [])
        self.assertEqual(len(cfg['sources']), 25)
        ids = {row['id'] for row in cfg['sources']}
        self.assertTrue({'clean-us', 'clean-it', 'plus-1.01', 'plus-1.02',
                         'plus-1.03', 'plus-1.2.5-en', 'plus-1.2.5-it',
                         'plus-1.3-en', 'plus-1.3-it'} <= ids)
        for lang in ('EN', 'IT'):
            text = pack.install_text(lang, cfg)
            self.assertIn(cfg['targets'][lang]['sha256'], text)
            for row in cfg['sources']:
                self.assertIn(row['sha256'], text)
                self.assertIn(pack.patch_path(row['id']), text)

    def test_131_keeps_original_manuals_but_never_relabels_legacy_codes(self):
        cfg=pack.config(pack.HERE/'release-1.3.1.json')
        for lang in ('EN','IT'):
            with self.subTest(lang=lang),tempfile.TemporaryDirectory() as temp:
                cfg=copy.deepcopy(cfg);directory=Path(temp);raw=b'original manual';ref=directory/'reference.zip'
                cfg['original_documents']={'Evolution Changes.pdf':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}}
                license_name='LICENZA.txt'if lang=='IT'else'LICENSE.txt'
                with zipfile.ZipFile(ref,'w')as z:
                    z.writestr('Manual/Evolution Changes.pdf',raw)
                    z.writestr('Cheats/SGP-1.2.3.xml',b'unverified old code')
                    z.writestr(license_name,b'license')
                cfg['references'][lang]={'name':ref.name,'sha256':pack.digest(ref)}
                for name in pack.guide_names(lang,cfg):(directory/name).write_bytes(b'%PDF-current')
                members=pack.reference_members(lang,directory,directory,cfg)
                self.assertEqual(members['Manual/Evolution Changes.pdf'],raw)
                self.assertFalse(any(n.endswith(('.xml','.mch'))for n in members))
                self.assertTrue(any(n.startswith('Cheats/')and n.endswith('.txt')for n in members))
                self.assertTrue(all(name in members for name in pack.guide_names(lang,cfg)))

    def test_contract_rejects_unknown_cheat_policy_and_document_escape(self):
        for key,value in [('cheats_policy','silently-copy'),('documents','../../local')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory()as temp:
                cfg=json.loads((pack.HERE/'release-1.3.1.json').read_text());cfg[key]=value
                path=Path(temp)/'bad.json';path.write_text(json.dumps(cfg))
                with self.assertRaises(ValueError):pack.config(path)

    def test_contract_rejects_title_and_feature_images_outside_image_root(self):
        cases = ('/' + 'private' + '/tmp/outside.png', '../outside.png',
                 '1.3.1/../../outside.png', './17-version-title-top.png',
                 r'..\outside.png', r'C:\outside.png', '//server/share.png')
        for field in ('title', 'feature'):
            for value in cases:
                with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as temp:
                    cfg = json.loads((pack.HERE / 'release-1.3.1.json').read_text())
                    if field == 'title':
                        cfg['title_images']['EN'] = value
                    else:
                        cfg['feature_images']['EN']['2'][0][0] = value
                    path = Path(temp) / 'bad.json'
                    path.write_text(json.dumps(cfg))
                    with self.assertRaises(ValueError):
                        pack.config(path)

if __name__=='__main__':unittest.main()
