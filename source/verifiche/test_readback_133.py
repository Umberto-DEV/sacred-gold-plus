"""Small admission tests for the five-target readback CLI; no ROMs or guest CPU."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

P=Path(__file__).with_name('readback_133.py')
spec=importlib.util.spec_from_file_location('readback_133',P)
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)

class ReadbackAdmission(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve());self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.targets={}
        for lang in R.LANGUAGES:
            self.targets[lang]={}
            for role in ('candidate','receipt','baseline'):
                name=lang+'-'+role; (self.root/name).write_bytes(name.encode());self.targets[lang][role]=name
        self.manifest=self.root/'manifest.json';self.charmap=self.root/'charmap';self.charmap.write_bytes(b'charmap')
        self.write_manifest()
    def write_manifest(self):
        self.manifest.write_text(json.dumps(dict(schema='sgp-five-readback-inputs/1',targets=self.targets)))
    def test_manifest_schema_paths_and_order(self):
        refs=R.manifest_inputs(R.Input(self.manifest));self.assertEqual(tuple(refs),R.LANGUAGES)
        self.assertEqual(refs['EN']['candidate'].path,self.root/'EN-candidate')
        for change in ('missing','extra','wrong-fields','wrong-type'):
            data=json.loads(self.manifest.read_text())
            if change=='missing':del data['targets']['EN']
            elif change=='extra':data['targets']['ZZ']=data['targets']['EN']
            elif change=='wrong-fields':data['targets']['EN']['other']='x'
            else:data['targets']['EN']['receipt']=4
            self.manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):R.manifest_inputs(R.Input(self.manifest))
            self.write_manifest()
    def test_duplicate_keys_and_bound(self):
        self.manifest.write_text('{"schema":"x","schema":"x","targets":{}}')
        with self.assertRaises(ValueError):R.manifest_inputs(R.Input(self.manifest))
        self.manifest.write_bytes(b' '* (1024*1024+1))
        with self.assertRaises(ValueError):R.manifest_inputs(R.Input(self.manifest))
    def test_symlink_nonregular_and_hardlink_rejected(self):
        link=self.root/'link';link.symlink_to(self.root/'EN-candidate')
        with self.assertRaises(ValueError):R.Input(link)
        with self.assertRaises(ValueError):R.Input(self.root)
        fifo=self.root/'fifo';os.mkfifo(fifo)
        with self.assertRaises(ValueError):R.Input(fifo)
        os.link(self.root/'EN-candidate',self.root/'hardlink')
        with self.assertRaises(ValueError):R.admit_output(self.root/'out',[R.Input(self.root/'EN-candidate'),R.Input(self.root/'hardlink')])
        directory=self.root/'alias';directory.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):R.Input(directory/'EN-candidate')
        with self.assertRaises(ValueError):R.Input(directory/'..'/'EN-candidate')
    def test_output_fresh_outside_source_and_no_symlink_components(self):
        item=R.Input(self.root/'EN-candidate')
        for output in (item.path,R.SOURCE/'fresh-test-output',self.root/'manifest.json'):
            with self.assertRaises(ValueError):R.admit_output(output,[item])
        link=self.root/'outlink';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):R.admit_output(link/'report.json',[item])
        output=R.admit_output(self.root/'nested'/'report.json',[item]);R.write_report(output,{'ok':False})
        with self.assertRaises((ValueError,OSError)):R.write_report(output,{'ok':True})
        self.assertFalse(json.loads(output.read_text())['ok'])
    def test_receipt_and_baseline_identity(self):
        p=self.root/'receipt';p.write_text(json.dumps(dict(schema=2,through='identity',language='EN',output_sha256='a'*64,output_bytes=3)))
        self.assertEqual(R.read_receipt(R.Input(p),'EN')['output_bytes'],3)
        for key,value in (('language','IT'),('schema',1),('through','ui'),('output_bytes',True),('output_sha256','x'*64)):
            doc=json.loads(p.read_text());bad=dict(doc);bad[key]=value;p.write_text(json.dumps(bad))
            with self.assertRaises(ValueError):R.read_receipt(R.Input(p),'EN')
            p.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):R.authenticate_baseline(b'x',dict(sha256='0'*64,bytes=1),'EN')
    def test_candidate_hash_and_size_checked_against_bytes(self):
        class Ref:
            path=Path('unused')
            def __init__(self,data):self.data=data
            def check(self):pass
            def read(self,*_):return self.data
        codec=SimpleNamespace(carica_charmap=lambda _:({},None),codifica=lambda text,table:[1,65535])
        refs={'candidate':Ref(b'new'),'baseline':Ref(b'old'),'receipt':Ref(b'')}
        targets={'EN':refs};contract={'EN':dict(sha256=R.sha(b'old'),bytes=3)}
        for digest,size in (('0'*64,3),(R.sha(b'new'),4)):
            record=dict(output_sha256=digest,output_bytes=size)
            with patch.object(R.U,'_module',return_value=codec),patch.object(R,'read_receipt',return_value=record):
                with self.assertRaisesRegex(ValueError,'candidate receipt EN'):
                    R.check_targets(targets,contract,Ref(b''),[])

    def test_success_and_valid_failure_output(self):
        report=dict(schema='five-readback-133-v1',ok=True,targets=[],limits=['unindexed historical bytes and repacking gaps are not exhaustively compared','No gameplay/SAVE/cold/device/timing/complete-pivot proof.'])
        args=['--manifest',str(self.manifest),'--charmap',str(self.charmap),'--json',str(self.root/'success.json')]
        with patch.object(R,'CHARMAP_SHA',R.sha(b'charmap')),patch.object(R,'check_targets',return_value=report),contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(R.main(args),0)
        self.assertEqual(json.loads((self.root/'success.json').read_text())['limits'],report['limits'])
        args[-1]=str(self.root/'failed.json')
        with patch.object(R,'CHARMAP_SHA',R.sha(b'charmap')),patch.object(R,'check_targets',side_effect=ValueError('fixture failure')),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(R.main(args),1)
        self.assertFalse(json.loads((self.root/'failed.json').read_text())['ok'])
        args[-1]=str(self.root/'EN-candidate')
        with contextlib.redirect_stderr(io.StringIO()):self.assertEqual(R.main(args),1)
        self.assertEqual((self.root/'EN-candidate').read_bytes(),b'EN-candidate')

if __name__=='__main__':unittest.main()
