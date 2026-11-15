"""Independent frozen-model/native comparison; synthetic public inputs and own reports."""
from pathlib import Path
import copy,gzip,importlib.util,json,os,struct,tempfile,unittest
s=importlib.util.spec_from_file_location('release_frozen_holdout',Path(__file__).parents[1]/'tools/confronta_release_holdout.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def pair(value=0):
    entry=[M.FILE,value,0x2000001F,M.FILE+48,M.FILE,0,M.FILE,16,M.FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,0,M.SP,M.RETURN,0x2000001F]
    before=bytearray(b'\x39'*312);i=M.FILE-(M.FRAME+16)
    for off,x in((0,M.ARC+32),(4,0),(8,M.ARC),(12,0x45),(16,4),(20,value),(24,0),(28,0)):
        struct.pack_into('<I',before,i+off,x)
    archive=bytearray(92);struct.pack_into('<I',archive,28,0x13);struct.pack_into('<I',archive,36,M.FILE)
    after=bytearray(before);arc_after=bytearray(archive);writes=[]
    for address,x in((M.ARC+36,0),(M.FILE,0),(M.FILE+4,0),(M.FILE+12,0),(M.FILE+20,value)):
        image,offset=(arc_after,address-M.ARC)if address>=M.ARC and address<M.ARC+92 else(after,address-(M.FRAME+16))
        writes.append(dict(pc='0x20d6864',address=address,bytes=4,before=bytes(image[offset:offset+4]).hex(),value=x))
        struct.pack_into('<I',image,offset,x)
    model_return=list(entry);model_return[0]=0
    model=dict(pc='0x20d6864',entry=entry,returned=model_return,frame_before=before.hex(),frame_after=after.hex(),
        archive_before=archive.hex(),archive_after=arc_after.hex(),writes=writes)
    guard=b'\xA5'*56;new_before=guard[-16:]+before;new_after=struct.pack('<4I',*(entry[i]for i in(4,5,6,14)))+after
    stores=[dict(pc='0x20d6864',address=M.FRAME+4*j,bytes=4,before=new_before[4*j:4*j+4].hex(),value=entry[i])for j,i in enumerate((4,5,6,14))]
    for pc,w in zip(M.FIELD_PCS,writes):stores.append({**w,'pc':hex(pc)})
    returned=list(entry);returned[:3]=[0x80,0x6000009F,0x6000001F];returned[14:16]=[0x20D68BC,0x6000001F]
    flow=[dict(pc=hex(0x20D6864+4*j),regs=list(entry))for j in range(34)]
    witness=next(e for e in flow if e['pc']=='0x20d68ac');witness['regs'][4]=value;witness['regs'][5]=M.FILE
    native=dict(fixture=dict(entry=entry,frame=bytes(new_before).hex(),archive_before=archive.hex(),translated_result=value),entry=entry,returned=returned,frame_before=bytes(new_before).hex(),frame_after=bytes(new_after).hex(),archive_after=arc_after.hex(),
        stores=stores,flow=flow,reads=[{}]*7,services=[dict(pc='0x20d1ecc',writes=[],frame_before=bytes(new_after).hex(),frame_after=bytes(new_after).hex(),
        archive_before=arc_after.hex(),archive_after=arc_after.hex())],observe=True,fault=None,steps=36,native_peak=16,stop=hex(M.RETURN),halt_pc=hex(M.RETURN),halt_regs=returned,
        guard_before='a5'*56,guard_after='a5'*56)
    return model,native,guard


class FrozenContract(unittest.TestCase):
    def test_independent_parent_frame_archive_events_and_owned_new_stack(self):
        for value in(0,1):
            model,native,guard=pair(value);r=M.compare_pair(model,native,guard)
            self.assertEqual(r['matched_parent_frame_bytes'],312);self.assertEqual(r['matched_archive_bytes'],92)
            self.assertEqual(r['matched_field_stores'],5);self.assertEqual(r['new_native_stack_bytes'],16)
            self.assertEqual([x['register']for x in r['abi_differences']],['R0','R1','R2','LR','CPSR'])
            self.assertEqual(r['abi_differences'][0]['native'],0x80)

    def test_frozen_wrong_error_contract_rejected_despite_same_input_and_void_return(self):
        model,native,guard=pair();wrong=copy.deepcopy(model);image=bytearray.fromhex(wrong['frame_after']);image[M.FILE-(M.FRAME+16)+20]=1
        wrong['frame_after']=image.hex();wrong['writes'][-1]['value']=1
        self.assertEqual(wrong['entry'],model['entry']);self.assertEqual(native['returned'][0],0x80)
        with self.assertRaisesRegex(ValueError,'parent frame'):M.compare_pair(wrong,native,guard)

    def test_extra_stack_is_verified_rather_than_masked(self):
        model,native,guard=pair();image=bytearray.fromhex(native['frame_after']);image[0]^=1;native['frame_after']=image.hex()
        self.assertEqual(native['frame_after'][32:],model['frame_after'])
        with self.assertRaises(ValueError):M.compare_pair(model,native,guard)

    def test_native_field_preimage_type_and_witness_corruption_rejected(self):
        for kind in('preimage','bool','source_register','callee_saved','extra_write','wake_write'):
            model,native,guard=pair();x=copy.deepcopy(native)
            if kind=='preimage':x['stores'][-1]['before']='02000000'
            elif kind=='bool':x['stores'][-1]['value']=False
            elif kind=='source_register':next(e for e in x['flow']if e['pc']=='0x20d68ac')['regs'][4]=1
            elif kind=='callee_saved':x['returned'][7]^=1
            elif kind=='extra_write':x['stores'].append(copy.deepcopy(x['stores'][-1]))
            else:x['services'][0]['writes']=[dict(address=M.FILE,value=0)]
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.compare_pair(model,x,guard)

    def test_empty_or_unbound_wakeup_snapshots_are_rejected(self):
        for kind in('empty','different'):
            model,native,guard=pair();service=native['services'][0]
            if kind=='empty':
                for key in('frame_before','frame_after','archive_before','archive_after'):service[key]=''
            else:
                image=bytearray.fromhex(service['frame_before']);image[0]^=1
                service['frame_before']=service['frame_after']=image.hex()
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.compare_pair(model,native,guard)

    def test_fault_must_be_the_declared_error_only_contract(self):
        model,native,guard=pair();fault=copy.deepcopy(model);image=bytearray.fromhex(fault['frame_after']);image[92]=1
        fault['frame_after']=image.hex();fault['writes'][-1]['value']=1
        self.assertTrue(M.require_fault_contract(model,fault))
        for kind in('pc','write_pc','void_return','wrong_word'):
            x=copy.deepcopy(fault)
            if kind=='pc':x['pc']='0xdeadbeef'
            elif kind=='write_pc':x['writes'][0]['pc']='0xdeadbeef'
            elif kind=='void_return':x['returned'][0]=1
            else:x['writes'][-1]['value']=2
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.require_fault_contract(model,x)

    def test_bounded_report_reader_and_parent_provenance_guard(self):
        with tempfile.TemporaryDirectory()as name:
            path=Path(name)/'report.json.gz';path.write_bytes(gzip.compress(b'x'*1000))
            with self.assertRaises(ValueError):M.read_report(path,maximum=100)
            path.write_bytes(gzip.compress(b'{"schema": "own"}'));data,digest=M.read_report(path)
            self.assertEqual(data,dict(schema='own'));self.assertEqual(len(digest),64)
        old=dict(schema='native-fs-exec-sync-isolated-v1',language='EN',cpu_executed=True,probe_only=False)
        new=dict(schema='native-fs-release-isolated-v1',language='IT',cpu_executed=True,probe_only=False)
        with self.assertRaises(ValueError):M.compare_reports(old,new,'a'*64,'b'*64)


@unittest.skipUnless(os.environ.get('SGP_RELEASE_HOLDOUT_CONFIG'),'requires own exact ExecuteSync and Release matrix reports')
class RetainedReports(unittest.TestCase):
    def test_both_languages_frozen_contract_and_fault_controls(self):
        config=json.loads(Path(os.environ['SGP_RELEASE_HOLDOUT_CONFIG']).read_bytes())
        for language in('EN','IT'):
            r=M.analyze(Path(config[language]['model_report']),Path(config[language]['native_report']))
            self.assertEqual(r['language'],language);self.assertEqual(len(r['matched_pairs']),8)
            self.assertEqual(len(r['rejected_fault_contracts']),4);self.assertIs(r['whole_ram_equivalence_claimed'],False)

    def test_fixture_parent_and_noncausal_negative_receipts_are_rejected(self):
        config=json.loads(Path(os.environ['SGP_RELEASE_HOLDOUT_CONFIG']).read_bytes())
        for language in('EN','IT'):
            old,a=M.read_report(Path(config[language]['model_report']));new,b=M.read_report(Path(config[language]['native_report']))
            wrong=copy.deepcopy(new)
            for f in wrong['fixtures']:f['provenance']['parent_report_sha256']='0'*64
            for cell in wrong['cases']:cell['result']['fixture']['provenance']['parent_report_sha256']='0'*64
            with self.assertRaises(ValueError):M.compare_reports(old,wrong,a,b)
            changed=copy.deepcopy(old);changed['cases'][3]['result']['services'][1]['pc']='0xdeadbeef'
            # Consistent outer hash/fixture graph must not hide an invalid negative control.
            digest=M.sha(M.wire(changed).encode());child=copy.deepcopy(new);child['proof']['parent_report_sha256']=digest
            for f in child['fixtures']:f['provenance']['parent_report_sha256']=digest
            for cell in child['cases']:cell['result']['fixture']['provenance']['parent_report_sha256']=digest
            with self.assertRaises(ValueError):M.compare_reports(changed,child,digest,b)


if __name__=='__main__':unittest.main()
