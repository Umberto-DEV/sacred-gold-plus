"""Actual-entry comparator coverage with explicitly synthetic ancestor inputs."""
from pathlib import Path
import copy,importlib.util,struct,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('default_findpath_freezer_test',Path(__file__).parents[1]/'tools/congela_fs_default_findpath_contract.py')


def synthetic():
    # Synthetic ledger for comparator admission only: it is not a source oracle
    # or a purported historical/native capture.
    before=bytearray(416);struct.pack_into('<3I',before,M.FILE-M.FRAME+12,0x45,4,2)
    archive=bytearray(92);struct.pack_into('<I',archive,28,0x13)
    frame=bytearray(before);stores=[]
    for index in range(23):
        value=index+1;offset=index*4
        stores.append(dict(pc='0x20d7788',address=M.FRAME+offset,bytes=4,before=frame[offset:offset+4].hex(),value=value))
        struct.pack_into('<I',frame,offset,value)
    stores.append(dict(pc='0x20d68f4',address=M.ARC+28,bytes=4,before='13000000',value=0x213))
    after_arc=bytearray(archive);struct.pack_into('<I',after_arc,28,0x213)
    entry=list(range(16));entry[:2]=[M.FILE,0x20D6DB0];entry[13:16]=[M.TOP-336,0x20D6984,0x6000001F]
    delivered=list(entry);delivered[14]=0x20D7754
    flow=[dict(pc='0x20d7788',regs=list(delivered))for _ in range(115)]+[dict(pc='0x20d68f4',regs=list(delivered)),dict(pc='0x20d6980',regs=list(delivered)),dict(pc='0x20d6984',regs=list(entry))]
    cp=dict(pc='0x20d6db0',regs=entry,frame=frame.hex(),archive=after_arc.hex())
    old=dict(language='EN',ordinal=0,plus=0,seed=1,translated_result=0,entry=list(entry),frame=before.hex(),guard='a5'*56)
    row=dict(observe=True,fault=None,policy=dict(early_error=False),model_stores=[],flow=flow,stores=stores+[dict(pc='0x20d6a3c')],
        frame_before=before.hex(),archive_before=archive.hex(),guard_before=old['guard'],guard_after=old['guard'],before_whole_ram_sha256='0'*64,
        checkpoints=dict(default_entry=cp,translate_entry=dict(whole_ram_sha256='1'*64)),
        services=[dict(pc='0x20d6db0',entry=entry,writes=[],early_error=False,frame_before=frame.hex(),archive_before=after_arc.hex())])
    inp=M.prefix_state(row);cp=row['checkpoints']['default_entry']
    f=dict(language='EN',ordinal=0,plus=0,seed=1,parent_send_fixture=old,entry=cp['regs'],
           prefix_stores=row['stores'][:24],observed_before_Send_whole_sha256='0'*64)
    cell=dict(language='EN',ordinal=0,plus=0,seed=1,ancestral_result_policy=0,parent_send_fixture_sha256=M.sha(M.wire(old).encode()),input=inp)
    # The extra lower48 is deliberately not A5. The comparator only claims
    # parent-captured fields; whole-image authentication is a separate gate.
    result=dict(entry=f['entry'],frame_before=(b'Z'*48+bytes.fromhex(old['guard'])+bytes.fromhex(cp['frame'])).hex(),archive_before=cp['archive'])
    return cell,f,result,row


class Frozen(unittest.TestCase):
    def test_causal_prefix_rejects_preimage_and_delivery_forgeries(self):
        _,_,_,r=synthetic();M.prefix_state(r)
        for kind in('preimage','entry','command','host_write'):
            bad=copy.deepcopy(r)
            if kind=='preimage':bad['stores'][0]['before']='39'*4
            elif kind=='entry':bad['checkpoints']['default_entry']['regs'][14]^=4
            elif kind=='command':bad['checkpoints']['default_entry']['regs'][1]=2
            else:bad['model_stores']=[{}]
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.prefix_state(bad)

    def test_all_captured_input_registers_and_bytes_are_covered(self):
        c,f,r,_=synthetic();M.compare_input(c,f,r)
        for i in range(16):
            bad=copy.deepcopy(r);bad['entry'][i]^=1
            with self.subTest(reg=i),self.assertRaises(ValueError):M.compare_input(c,f,bad)
        for field,start in(('frame_before',48),('archive_before',0)):
            for i in range(start,len(bytes.fromhex(r[field]))):
                bad=copy.deepcopy(r);raw=bytearray.fromhex(bad[field]);raw[i]^=1;bad[field]=raw.hex()
                with self.subTest(field=field,byte=i),self.assertRaises(ValueError):M.compare_input(c,f,bad)

    def test_added_lower_bytes_are_explicitly_not_claimed_as_captured(self):
        c,f,r,_=synthetic();bad=copy.deepcopy(r);raw=bytearray.fromhex(bad['frame_before']);raw[:48]=b'9'*48;bad['frame_before']=raw.hex()
        proof=M.compare_input(c,f,bad)
        self.assertEqual(proof['derived_additional_bytes'],104);self.assertFalse(proof['output_or_activation_proved_here'])
        changed=copy.deepcopy(f);changed['prefix_stores'][0]['value']^=1
        with self.assertRaises(ValueError):M.compare_input(c,changed,r)


if __name__=='__main__':unittest.main()
