"""Versioned packaging must not relabel the published contract or old cheats."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import pack

class Release131Tests(unittest.TestCase):
    def test_contract_is_explicit_and_preserves_every_old_source(self):
        old = pack.config()
        new = pack.config(pack.HERE/'release-1.3.1.json')
        self.assertEqual(old['version'], '1.2.5')
        self.assertEqual(new['version'], '1.3.1')
        self.assertEqual(new['status'], 'release-package-verified')
        self.assertEqual(new['open_gates'], [])
        self.assertEqual(len(new['sources']), 25)
        self.assertEqual(new['sources'][:21], old['sources'])
        self.assertEqual(set(x['id'] for x in new['sources'][21:]),
                         {'plus-1.2.5-en','plus-1.2.5-it','plus-1.3-en','plus-1.3-it'})
        for lang in ('EN','IT'):
            self.assertNotEqual(new['targets'][lang]['sha256'], old['targets'][lang]['sha256'])
            text = pack.install_text(lang,new)
            self.assertIn(new['targets'][lang]['sha256'],text)
            self.assertIn('1.3.1',text)
            finished=text.split('\nREFERENCE B - FINISHED GAME\n'if lang=='EN'else'\nRIFERIMENTO B - GIOCO OTTENUTO\n')[1]
            self.assertNotIn(old['targets'][lang]['sha256'],finished)

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
                cfg=json.loads((pack.HERE/'release.json').read_text());cfg[key]=value
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
