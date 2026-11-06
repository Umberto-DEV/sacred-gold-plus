"""Synthetic evidence-shaped unit fixtures; no Android execution is claimed."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from . import activation as A, controls, portable, rematches

CANDIDATE='a'*64

def proof(owner,candidate=CANDIDATE,language='EN'):
    if owner=='controls':
        return dict(kind='summary-window-inventory',capture_rom_sha256=candidate,build_id='SYNTHETIC-UNIT-TEST-NOT-A-CAPTURE',language=language,
                    geometry=dict(controls.PROPOSAL),views=['stats','ev','iv'],button_modes=['normal','L=A'],contexts=['field','pc'],
                    captures=[{'name':'SYNTHETIC-UNIT-TEST','sha256':'b'*64}],free_tiles=[955,1023],hidden_windows=[])
    if owner=='portable':
        return dict(sha256='b'*64,origin='SYNTHETIC UNIT TEST of measured-shaped schema, not a capture',status='measured',
                    capture_file='SYNTHETIC-UNIT-TEST',capture_rom_sha256=candidate,build_id='UNIT-TEST',language=language)
    abi=rematches.load_abi();context=abi['gate']['context']
    return dict(language=language,capture_file='SYNTHETIC-UNIT-TEST',capture_rom_sha256=candidate,build_id='UNIT-TEST',
                observations=[dict(trainer=t,family=f,battle_type=v['battle_type'],enemy_index=context['enemy_indexes'][0])
                              for t in abi['gate']['trainers'] for f,v in context['families'].items()])

def document(candidate=CANDIDATE):
    return {'schema':1,'language':'EN','stage_options':{
        'controls':{'mode':'active','geometry':dict(controls.PROPOSAL),'variant':'compact','candidate_sha256':candidate,'evidence':proof('controls',candidate)},
        'portable':{'mode':'active','activation':dict(bridge=1,input=1,prompt=1,travel_mask=3),'candidate_sha256':candidate,'context_proof':proof('portable',candidate)},
        'rematches':{'mode':'active','candidate_sha256':candidate,'context_proof':proof('rematches',candidate)}}}

class Options(unittest.TestCase):
    def test_direct_owner_options_require_supported_language(self):
        with self.assertRaises(ValueError):
            A.owner_kwargs(None, 'controls', None)
    def parse(self,value):return A.StageOptions.parse(json.dumps(value).encode())
    def test_valid_all_three_use_one_candidate(self):
        parsed=self.parse(document());self.assertEqual(parsed.candidate_sha256,CANDIDATE)
        self.assertEqual(parsed.active_owners,('controls','portable','rematches'))
    def test_wrong_language_or_hash_proofs_refused(self):
        for owner in ('controls','portable','rematches'):
            for field,value in (('language','IT'),('capture_rom_sha256','c'*64)):
                d=document();key='evidence' if owner=='controls' else 'context_proof';d['stage_options'][owner][key][field]=value
                with self.subTest(owner=owner,field=field),self.assertRaises(ValueError):self.parse(d)
    def test_distinct_individually_bound_roots_refused(self):
        d=document();o=d['stage_options']['portable'];o['candidate_sha256']='c'*64;o['context_proof']=proof('portable','c'*64)
        with self.assertRaisesRegex(ValueError,'same inert candidate'):self.parse(d)
    def test_extra_mutable_float_duplicate_and_synthetic_options_refused(self):
        for raw in (bytearray(b'{}'),{},b'{"schema":1,"schema":1}',b'{"n":NaN}',b'{"n":1.2}'):
            with self.subTest(raw=str(raw)),self.assertRaises(ValueError):A.StageOptions.parse(raw)
        for owner in ('controls','portable','rematches'):
            d=document();d['stage_options'][owner]['allow_synthetic']=True
            with self.assertRaises(ValueError):self.parse(d)
        d=document();d['stage_options']['rematches']['context_proof']['synthetic_harness_only']=True
        with self.assertRaises(ValueError):self.parse(d)
        d=document();d['stage_options']['portable']['context_proof']['status']='synthetic'
        with self.assertRaises(ValueError):self.parse(d)
    def test_inert_geometry_and_travel_options_need_no_fabricated_proof(self):
        d={'schema':1,'language':'EN','stage_options':{
            'controls':{'mode':'inert','geometry':dict(controls.PROPOSAL),'variant':'compact'},
            'portable':{'mode':'inert','activation':dict(bridge=0,input=0,prompt=0,travel_mask=3)},'rematches':{'mode':'inert'}}}
        parsed=self.parse(d);self.assertIsNone(parsed.candidate_sha256);self.assertFalse(parsed.active_owners)
        self.assertFalse(A.owner_kwargs(parsed,'controls','EN')['active'])
    def test_unused_owner_and_language_rejected_before_pipeline(self):
        parsed=self.parse(document())
        with self.assertRaises(ValueError):A.validate_for_chain(parsed,'IT',('controls','portable','rematches'))
        with self.assertRaises(ValueError):A.validate_for_chain(parsed,'EN',('controls','portable'))
    def test_extracted_options_are_copies_and_raw_dict_is_refused(self):
        parsed=self.parse(document());o=A.owner_kwargs(parsed,'controls','EN');o['geometry']['top']=99
        self.assertEqual(A.owner_kwargs(parsed,'controls','EN')['geometry']['top'],18)
        with self.assertRaises(ValueError):A.owner_kwargs(document(),'controls','EN')
    def test_active_portable_mode_requires_a_function_and_closed_integer_words(self):
        for activation in (dict(bridge=0,input=0,prompt=0,travel_mask=3),dict(bridge=True,input=1,prompt=1,travel_mask=3),dict(bridge=1,input=1,prompt=1,travel_mask=3,context_proof=1)):
            d=document();d['stage_options']['portable']['activation']=activation
            with self.assertRaises(ValueError):self.parse(d)

class CommonRoot(unittest.TestCase):
    def test_all_activation_words_clear_together_and_foreign_byte_still_fails(self):
        inert=bytes(40);active=bytearray(inert)
        locations=((0,4,'controls'),(8,4,'portable'),(12,4,'portable'),(16,4,'portable'),(20,4,'portable'),(28,1,'rematches'))
        for at,size,owner in locations:active[at]=1
        root=__import__('hashlib').sha256(inert).hexdigest();parsed=A.StageOptions.parse(json.dumps(document(root)).encode())
        with patch.object(A,'_locations',return_value=locations),patch.object(A,'_check_owner_receipts'):
            result=A.final_gate(bytes(active),parsed,{'controls':{},'portable':{},'rematches':{}},language='EN')
            self.assertEqual(result['all_inert_sha256'],root)
            self.assertNotEqual(__import__('hashlib').sha256(active).hexdigest(),root)
            broken=bytearray(active);broken[36]=1
            with self.assertRaisesRegex(ValueError,'all-inert'):A.final_gate(bytes(broken),parsed,{'controls':{},'portable':{},'rematches':{}},language='EN')
            with self.assertRaises(ValueError):A.final_gate(active,parsed,{'controls':{},'portable':{},'rematches':{}},language='EN')
    def test_projection_refuses_overlap_out_of_bounds_or_nonboolean_values(self):
        for raw,locations in ((bytes(8),((0,4,'a'),(2,4,'b'))),(bytes(8),((7,4,'a'),)),(b'\2'+bytes(7),((0,4,'a'),))):
            with self.assertRaises(ValueError):A._clear(raw,locations)

class SnapshotsAndLocations(unittest.TestCase):
    def test_file_snapshot_is_bounded_immutable_and_rechecked(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp).resolve()/'mechanics.json';path.write_text(json.dumps(document()))
            options,record=A.snapshot_config(path);A.refresh_config(record,options)
            path.write_text(json.dumps(document())+' ')
            with self.assertRaisesRegex(ValueError,'config changed'):A.refresh_config(record,options)
            link=path.parent/'linked.json';link.symlink_to(path)
            with self.assertRaisesRegex(ValueError,'symlink'):A.snapshot_config(link)
            path.write_bytes(b' '* (A.MAX_CONFIG_BYTES+1))
            with self.assertRaises(ValueError):A.snapshot_config(path)
    def test_closed_proof_inputs_end_as_valueerror(self):
        for owner in ('controls','portable','rematches'):
            for bad in (None,[],True,{'status':'measured'}):
                d=document();d['stage_options'][owner]['evidence' if owner=='controls' else 'context_proof']=bad
                with self.subTest(owner=owner,bad=bad),self.assertRaises(ValueError):A.StageOptions.parse(json.dumps(d).encode())
    def fixture(self):
        import struct
        data=bytearray(0x21800)
        struct.pack_into('<4I',data,0x20,0x4000,0x02000000,0x02000000,0x1900c)
        struct.pack_into('<6I',data,0x4000+0xba0,0x02019000,0x0201900c,0x02001000,0,0,0)
        struct.pack_into('<3I',data,0x4000+0x19000,0x023c8000,0x18000,0)
        struct.pack_into('<4I',data,0x48,0x1e000,513*8,0,0)
        struct.pack_into('<II',data,0x1e000+126*8,0x21000,0x21800)
        part=A._slots()[portable.SLOT_NAME];address=part['start']+64
        segments=portable.arm9_segments(bytes(data))
        travel=portable.locate(segments,address+portable.CONFIG_OFFSETS['travel_mask'],4)
        struct.pack_into('<I',data,travel,3)
        root=__import__('hashlib').sha256(data).hexdigest();options=A.StageOptions.parse(json.dumps(document(root)).encode())
        kwargs=A.owner_kwargs(options,'portable','EN')
        receipts={
            'controls':dict(language='EN',function_state='active',candidate_sha256=root,evidence=proof('controls',root),geometry=dict(controls.PROPOSAL),variant='compact'),
            'portable':dict(language='EN',function_state='active',candidate_sha256=root,context_proof=portable._proof(proof('portable',root),False,'EN',root),
                            state={'address':part['start']},config={'address':address,'values':dict(bridge=1,input=1,prompt=1,travel_mask=3,context_proof=1)}),
            'rematches':dict(language='EN',function_state='active',activation={'candidate_sha256':root,'context_proof':proof('rematches',root)})}
        for at,size,owner in A._locations(bytes(data),receipts):data[at]=1
        return bytes(data),options,receipts,root
    def test_real_address_mappers_and_full_receipt_options_share_one_root(self):
        data,options,receipts,root=self.fixture()
        self.assertEqual(len(A._locations(data,receipts)),6)
        result=A.final_gate(data,options,receipts,language='EN')
        self.assertEqual(result['all_inert_sha256'],root)
        forged=copy.deepcopy(receipts);forged['portable']['config']['address']=0x02000000
        with self.assertRaises(ValueError):A.final_gate(data,options,forged,language='EN')
        forged=copy.deepcopy(receipts);forged['controls']['function_state']='inert'
        with self.assertRaises(ValueError):A.final_gate(data,options,forged,language='EN')
        with self.assertRaises(ValueError):A.final_gate(data,options,{'controls':receipts['controls']},language='EN')
    def test_inert_requested_geometry_is_bound_even_without_a_candidate(self):
        d={'schema':1,'language':'EN','stage_options':{'controls':{'mode':'inert','geometry':dict(controls.PROPOSAL),'variant':'compact'}}}
        options=A.StageOptions.parse(json.dumps(d).encode())
        receipt=dict(language='EN',function_state='inert',candidate_sha256=None,evidence=None,geometry=dict(controls.PROPOSAL),variant='compact')
        A.check_owner_options('controls',receipt,options,'EN')
        receipt['geometry']['top']=17
        with self.assertRaises(ValueError):A.check_owner_options('controls',receipt,options,'EN')

if __name__=='__main__':unittest.main()
