"""Schema-2 packaging probes use small non-game fixture bytes."""
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

LOCALES=('EN','IT','FR','ES','DE')
FOLDERS=dict(zip(LOCALES,('EN-English','IT-Italiano','FR-Francais','ES-Espanol','DE-Deutsch')))
PDFS=('Installation','Whats-New','Special-Events','Pokemon-Changes','Pokemon-Locations',
      'Evolutions','Items-TMs','Trainers','Game-Guide')
SOURCE_IDS=('clean-us','clean-it','plus-1.01','plus-1.02','plus-1.03',
    'plus-1.04-en-plus','plus-1.04-en-classic','plus-1.04-it-plus','plus-1.04-it-classic',
    'plus-1.1-en','plus-1.1-it','plus-1.2.1-en','plus-1.2.1-it',
    'plus-1.2.2-en-prima','plus-1.2.2-it-prima','plus-1.2.2-en','plus-1.2.2-it',
    'plus-1.2.3-en','plus-1.2.3-it','plus-1.2.4-en','plus-1.2.4-it',
    'plus-1.2.5-en','plus-1.2.5-it','plus-1.3-en','plus-1.3-it',
    'plus-1.3.1-en','plus-1.3.1-it','clean-fr','clean-es','clean-de')
def pin(raw):return {'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def pdf_bytes(name):return b'%PDF-fixture '+name.encode()
def cheat_bytes(lang,name):
    return (('Localized policy '+lang)if name.endswith('.txt')else('<cheats locale="'+lang+'"/>')).encode()
def contract_fixture():
    legacy=json.loads((pack.HERE/'release-1.3.1.json').read_text())
    sources=copy.deepcopy(legacy['sources'])
    for lang in ('EN','IT'):
        row=legacy['targets'][lang];sources.append(dict(id='plus-1.3.1-'+lang.lower(),label='Published '+lang,sha256=row['sha256'],bytes=row['bytes']))
    metadata=json.loads((pack.HERE.parent/'localization/languages.json').read_text())['languages']
    for lang in ('FR','ES','DE'):
        row=metadata[lang]['retail'];sources.append(dict(id='clean-'+lang.lower(),label='Retail '+lang,sha256=row['sha256'],bytes=row['bytes']))
    return {'schema':2,'version':'1.3.2','sources':sources,
      'targets':{lang:pin(('target '+lang).encode())for lang in LOCALES},
      'routes_by_target':{lang:list(SOURCE_IDS)for lang in LOCALES},
      'locales':{lang:{'folder':FOLDERS[lang],'documents':[dict(name=f'{n}-1.3.2-{lang}.pdf',**pin(pdf_bytes(f'{n}-1.3.2-{lang}.pdf')))for n in PDFS],
                       'cheats':[dict(name=n,**pin(cheat_bytes(lang,n)))for n in ('ABOUT-CHEATS.txt','Cheats.xml')]}for lang in LOCALES},
      'references':{l:{'name':l+'.zip','sha256':'0'*64}for l in ('EN','IT')},'original_documents':{},'rompatcher_commit':'1'*40,'cheats_policy':'verified-localized'}

class MultilingualPackageTests(unittest.TestCase):
    def load(self,cfg,root):
        p=root/'contract.json';p.write_text(json.dumps(cfg));return pack.config(p)
    def test_rejects_missing_historical_extra_duplicate_routes_and_missing_sources(self):
        cases=[]
        c=contract_fixture();c['routes_by_target']['FR'].remove('plus-1.03');cases.append(c)
        c=contract_fixture();c['routes_by_target']['ES'].append('plus-1.03-fix');cases.append(c)
        c=contract_fixture();c['routes_by_target']['IT'].append('plus-1.3.1-en');cases.append(c)
        c=contract_fixture();c['routes_by_target']['DE']*=2;cases.append(c)
        c=contract_fixture();c['routes_by_target']['JP']=['clean-fr'];cases.append(c)
        c=contract_fixture();c['sources'].pop();cases.append(c)
        for i,cfg in enumerate(cases):
            with self.subTest(case=i),tempfile.TemporaryDirectory()as td:
                with self.assertRaisesRegex(ValueError,'route|source|locale'):self.load(cfg,Path(td))
    def test_requires_exact_localized_pdf_names_and_folder(self):
        for kind in ('wrong-locale','missing','order','pin','folder'):
            c=contract_fixture();row=c['locales']['FR']
            if kind=='wrong-locale':row['documents'][0]['name']='Installation-1.3.2-EN.pdf'
            elif kind=='missing':row['documents'].pop()
            elif kind=='order':row['documents'][:2]=row['documents'][1::-1]
            elif kind=='pin':row['documents'][0].pop('sha256')
            else:row['folder']='EN-English'
            with self.subTest(kind=kind),tempfile.TemporaryDirectory()as td:
                with self.assertRaisesRegex(ValueError,'document|folder|locale'):self.load(c,Path(td))
    def test_all_recognized_sources_route_explicitly_to_five_latest_targets(self):
        with tempfile.TemporaryDirectory()as td:
            c=self.load(contract_fixture(),Path(td));self.assertEqual(sum(map(len,c['routes_by_target'].values())),150)
            self.assertEqual(set(s['id']for s in c['sources']),set(SOURCE_IDS))
            for lang in LOCALES:self.assertEqual(set(c['routes_by_target'][lang]),set(SOURCE_IDS))
        c=pack.config();self.assertEqual((c['schema'],c['version']),(1,'1.3.1'))
        self.assertEqual(len(c['sources']),25)
        self.assertEqual(pack.patch_path('clean-us'),'Patch/From Clean ROM/US/from-clean-us.xdelta')
    def test_rejects_unknown_bases_and_changed_known_base_pins(self):
        for kind in ('unknown','sha256','bytes'):
            c=contract_fixture()
            if kind=='unknown':
                c['sources'].append(dict(id='unknown-base',label='Unknown',**pin(b'unknown')))
                for routes in c['routes_by_target'].values():routes.append('unknown-base')
            elif kind=='sha256':c['sources'][4]['sha256']='0'*64
            else:c['sources'][4]['bytes']+=1
            with self.subTest(kind=kind),tempfile.TemporaryDirectory()as td,self.assertRaisesRegex(ValueError,'source|pin'):
                self.load(c,Path(td))
    def test_cheats_contract_rejects_absent_files_path_aliases_and_rom_names(self):
        for rows in ([],[{'name':'../codes.txt',**pin(b'x')}],
                     [{'name':'game.nds',**pin(b'x')}],
                     [{'name':'codes.txt',**pin(b'x')},{'name':'CODES.TXT',**pin(b'x')}]):
            c=contract_fixture();c['locales']['FR']['cheats']=rows
            with self.subTest(rows=rows),tempfile.TemporaryDirectory()as td:
                with self.assertRaises(ValueError):self.load(c,Path(td))
    def fixtures(self,root):
        c=contract_fixture();refs=root/'refs';refs.mkdir();guides=root/'guides';guides.mkdir()
        original=b'unchanged historical PDF';c['original_documents']={'Original.pdf':dict(language='EN',**pin(original))}
        for lang in ('EN','IT'):
            p=refs/(lang+'.zip')
            with zipfile.ZipFile(p,'w')as z:
                z.writestr('Manual/Original.pdf',original);z.writestr('Manual/Game Guide.txt',('historical '+lang).encode())
                z.writestr('LICENZA.txt'if lang=='IT'else'LICENSE.txt',('credits '+lang).encode())
                z.writestr('Cheats/old.xml',b'not inherited');z.writestr('Patch/unused.xdelta',b'not inherited')
            c['references'][lang]={'name':p.name,'sha256':pack.digest(p)}
        for lang in LOCALES:
            d=guides/lang;d.mkdir()
            for row in c['locales'][lang]['documents']:(d/row['name']).write_bytes(pdf_bytes(row['name']))
            (d/'Cheats').mkdir()
            for row in c['locales'][lang]['cheats']:(d/'Cheats'/row['name']).write_bytes(cheat_bytes(lang,row['name']))
        paths={}
        for s in c['sources']:
            s.update(pin(s['id'].encode()))
            p=root/(s['id']+'.input');p.write_bytes(s['id'].encode());paths[s['id']]=str(p)
        for lang in LOCALES:
            p=root/('target-'+lang+'.input');p.write_bytes(('target '+lang).encode());paths['target-'+lang]=str(p)
        inputs=root/'inputs.json';inputs.write_text(json.dumps(paths));cp=root/'contract.json';cp.write_text(json.dumps(c))
        return c,refs,guides,inputs,cp
    @contextmanager
    def decoders(self,root,corrupt=False):
        # Seam only external executables: real input hashing, contracts,
        # reference/guide readers, manifests, ZIP writer/readback all execute.
        snapshot=root/'snapshot';snapshot.mkdir()
        @contextmanager
        def pinned(*args):yield snapshot
        def external(args):
            a=list(map(str,args))
            if a[0]=='xdelta3':
                if '-e'in a:Path(a[-1]).write_bytes(bytes.fromhex('d6c3c40000')+Path(a[-2]).read_bytes())
                else:Path(a[-1]).write_bytes(b'wrong'if corrupt=='xdelta'else Path(a[-2]).read_bytes()[5:])
                return ''
            if a[0]=='node':
                raw=Path(a[4]).read_bytes();Path(a[-1]).write_bytes(b'wrong'if corrupt=='node'else raw[5:]);return json.dumps({'result':'PASS','patch_sha256':hashlib.sha256(raw).hexdigest()})
            raise AssertionError(a)
        # Replace the read-only trusted ROM registry with explicit tiny fixture pins;
        # contract validation and actual file hashing remain active.
        registry={s:pin(s.encode())for s in SOURCE_IDS}
        with mock.patch.object(pack,'pinned_git_snapshot',pinned),mock.patch.object(pack,'run',external),mock.patch.object(pack,'multilingual_source_registry',return_value=registry):yield
    def test_one_zip_exact_routes_pdfs_shared_originals_and_full_inventory(self):
        with tempfile.TemporaryDirectory()as td:
            root=Path(td);c,refs,guides,inputs,cp=self.fixtures(root);out=root/'out'
            with self.decoders(root):results=pack.build(inputs,refs,guides,out,root/'unused',contract=cp)
            self.assertEqual(len(results),1);self.assertEqual(results[0]['routes'],150)
            with zipfile.ZipFile(out/results[0]['file'])as z:
                names=z.namelist();prefix='Sacred Gold Plus 1.3.2/'
                self.assertTrue(all(n.startswith(prefix)for n in names));self.assertEqual(len([n for n in names if n.endswith('.xdelta')]),150)
                self.assertFalse(any(n.endswith(('.nds','.sav'))for n in names))
                self.assertNotIn(str(root).encode(),b'\n'.join(z.read(n)for n in names))
                self.assertEqual([n for n in names if n.endswith('Original.pdf')],[prefix+'Originals/Original.pdf'])
                self.assertEqual(z.read(prefix+'Originals/Original.pdf'),b'unchanged historical PDF')
                for lang in ('EN','IT'):self.assertIn(prefix+'Credits-and-Licenses/'+FOLDERS[lang]+'/'+('LICENSE.txt'if lang=='EN'else'LICENZA.txt'),names)
                self.assertIn(prefix+'START-HERE.txt',names)
                for lang in LOCALES:
                    folder=prefix+FOLDERS[lang]+'/';m=json.loads(z.read(folder+'Patch/manifest.json'))
                    self.assertEqual(m['language'],lang);self.assertEqual({p['source']['id']for p in m['patches']},set(c['routes_by_target'][lang]))
                    for s in c['routes_by_target'][lang]:self.assertIn(folder+'Patch/'+s+'.xdelta',names)
                    for pdf in c['locales'][lang]['documents']:
                        name=folder+'Documents/'+pdf['name'];self.assertIn(name,names)
                        self.assertEqual(pin(z.read(name)),{k:pdf[k]for k in ('sha256','bytes')})
                    for row in c['locales'][lang]['cheats']:
                        self.assertEqual(z.read(folder+'Cheats/'+row['name']),cheat_bytes(lang,row['name']))
                    self.assertNotIn(folder+'Cheats/old.xml',names)
                for line in z.read(prefix+'SHA256SUMS').decode().splitlines():
                    digest,name=line.split('  ',1);self.assertEqual(hashlib.sha256(z.read(prefix+name)).hexdigest(),digest)
                checked={line.split('  ',1)[1]for line in z.read(prefix+'SHA256SUMS').decode().splitlines()}
                self.assertEqual(checked,{n[len(prefix):]for n in names}-{ 'SHA256SUMS'})
                inventory=json.loads(z.read(prefix+'CONTENTS.json'))['files']
                self.assertEqual(set(inventory),{n[len(prefix):]for n in names}-{'CONTENTS.json','SHA256SUMS'})
                for name,p in inventory.items():self.assertEqual(pin(z.read(prefix+name)),p)
            self.assertFalse(list(out.glob('sgp-package-*')))
    def test_changed_or_wrong_locale_pdf_rejected_before_output(self):
        for kind in ('tampered','wrong-locale','stale'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory()as td:
                root=Path(td);c,refs,guides,inputs,cp=self.fixtures(root);out=root/'out'
                pdf=guides/'FR/Installation-1.3.2-FR.pdf'
                if kind=='wrong-locale':pdf.write_bytes((guides/'EN/Installation-1.3.2-EN.pdf').read_bytes())
                elif kind=='stale':pdf.write_bytes(b'%PDF-old candidate and obsolete target')
                else:pdf.write_bytes(pdf.read_bytes()+b'changed')
                with self.decoders(root),self.assertRaisesRegex(ValueError,'pin'):
                    pack.build(inputs,refs,guides,out,root/'unused',contract=cp)
                self.assertFalse(out.exists())
    def test_missing_pdf_or_wrong_source_refuses_before_output(self):
        for kind in ('pdf','source','missing-cheat','wrong-cheat'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory()as td:
                root=Path(td);c,refs,guides,inputs,cp=self.fixtures(root);out=root/'out'
                if kind=='pdf':(guides/'FR/Trainers-1.3.2-FR.pdf').unlink()
                elif kind=='missing-cheat':(guides/'FR/Cheats/Cheats.xml').unlink()
                elif kind=='wrong-cheat':(guides/'FR/Cheats/Cheats.xml').write_bytes(b'unpinned')
                else:
                    paths=json.loads(inputs.read_text());paths['clean-fr']=paths['clean-es'];inputs.write_text(json.dumps(paths))
                with self.decoders(root),self.assertRaises(ValueError):pack.build(inputs,refs,guides,out,root/'unused',contract=cp)
                self.assertFalse(out.exists())
    def test_wrong_decoded_target_rejected_and_intermediate_rom_removed(self):
        for decoder in ('xdelta','node'):
            with self.subTest(decoder=decoder),tempfile.TemporaryDirectory()as td:
                root=Path(td);c,refs,guides,inputs,cp=self.fixtures(root);out=root/'out'
                with self.decoders(root,decoder),self.assertRaisesRegex(ValueError,'pin'):pack.build(inputs,refs,guides,out,root/'unused',contract=cp)
                self.assertFalse(list(out.rglob('*.nds')));self.assertFalse(list(out.glob('sgp-package-*')))
if __name__=='__main__':unittest.main()
