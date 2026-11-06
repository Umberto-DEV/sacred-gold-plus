"""Offline adapter smoke; declared test policy and zero-slot retirement fixture, no authorization/Android claim."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import mechanics_stages as ms, controls, portable
ROOT=Path(__file__).resolve().parents[2]
from sgp131 import baseline, ui, ui_verify
from sgp131.test_ui import CONFIG

CHARMAP=ROOT/'local/tools/pokeheartgold/charmap.txt'
class OwnersOnUi(unittest.TestCase):
    def language(self, language):
        rom=ROOT/'local/experiments/balance493-2026-10-28'/('candidate-v4-'+language+'.nds')
        if not rom.is_file():
            self.skipTest('immutable V4 candidate unavailable: '+str(rom))
        if not CHARMAP.is_file():
            self.skipTest('pinned charmap unavailable: '+str(CHARMAP))
        data=rom.read_bytes()
        self.assertEqual(baseline.identify(data),language)
        policy={'version':'PRIVATE-CONTROLS-PORTABLE-TEST','conditional_parents':[], 'subdivisions':[]}
        rows=[]
        for name in ('controls','portable'):
            stage=ms.require_stage(name)
            _,part=ms.reserve_slot(stage.slot)
            policy['subdivisions'].append({'parent':'test.declared-parent','parts':[part]})
            rows.append(dict(name=stage.slot,parent='test.declared-parent',start=part['start'],bytes=part['bytes'],capacity=part['bytes']))
        digest=hashlib.sha256(b'PRIVATE CONTROLS PORTABLE TEST POLICY NOT A PRODUCTION GRANT').hexdigest()
        allocation={'schema':1,'input_sha256':hashlib.sha256(data).hexdigest(),'language':language,
                    'policy_version':policy['version'],'policy_sha256':digest,'audit_sha256':'0'*64,
                    'requested':{r['name']:r['bytes'] for r in rows},'assignments':rows,
                    'preservation':{},'address_reserved':True,'installed':False,'installation_authorized':False}
        with tempfile.TemporaryDirectory(prefix='private-owners-ui-') as directory:
            work=Path(directory)
            (work/'ui-candidate.json').write_text(json.dumps(CONFIG))
            image, ui_receipt=ui.install(data,language,CHARMAP,work)
            view=ui_verify.Image(image)
            # Explicit synthetic retirement preimage. Production must use Guide verifier's independently checked clearing.
            initial=bytearray(image)
            for row in rows:
                at=view.offset(row['start'],row['bytes'])
                initial[at:at+row['bytes']]=bytes(row['bytes'])
            initial=bytes(initial)
            controls.audit(initial,language)
            portable.audit_native(initial,language)
            names=['controls','portable']
            ms.require_disjoint([ms.require_stage(n).regions(initial) for n in names])
            with patch.object(controls,'_reserve_policy',return_value=(policy,digest)), patch.object(portable,'_reserve_policy',return_value=(policy,digest)):
                image=initial
                receipts=[]
                for name in names:
                    image,receipt=ms.run_stage(name,image,language,allocation=allocation,work_dir=work,charmap=CHARMAP)
                    receipts.append(receipt)
                    self.assertEqual(receipt['stage_receipt']['function_state'],'inert')
                def verify_ui(candidate):
                    self.assertEqual(candidate,initial)
                    return {'synthetic_retirement_fixture':True}
                result=ms.verify_chain(initial,image,names,receipts,verify_ui,allocation=allocation,charmap=CHARMAP)
                self.assertEqual(result['stages'],names)
                ms.check_ui_seeds(image)
                # Source mutation, even with outer output hash rewritten, cannot pass owner readback.
                broken=bytearray(image)
                at=ms.require_stage('controls').regions(initial)[0].start+40
                broken[at]^=1
                with self.assertRaises(ValueError):
                    ms.verify_chain(initial,bytes(broken),names,receipts,verify_ui,allocation=allocation,charmap=CHARMAP)
                # Neither source language nor allocation policy may be swapped on replay.
                forged=copy.deepcopy(receipts)
                forged[0]['stage_receipt']['allocation']['language']='IT' if language=='EN' else 'EN'
                forged[0]['stage_receipt_sha256']=ms._sha(ms.canonical(forged[0]['stage_receipt']))
                with self.assertRaisesRegex(ValueError,'allocation differs'):
                    ms.verify_chain(initial,image,names,forged,verify_ui,allocation=allocation,charmap=CHARMAP)
        print(language,'PASS exact V4',hashlib.sha256(data).hexdigest(),'inert fixture output',hashlib.sha256(image).hexdigest(),flush=True)
    def test_EN(self):self.language('EN')
    def test_IT(self):self.language('IT')
if __name__=='__main__':unittest.main()
