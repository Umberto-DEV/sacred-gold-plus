"""Strict captured-input mutation coverage; projected inputs are not actual."""
from pathlib import Path
import copy,importlib.util,struct,unittest

path=Path(__file__).parents[1]/'tools/congela_fs_nested_seekdir_contract.py'
s=importlib.util.spec_from_file_location('nested_seekdir_freezer_test',path)
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def synthetic():
    before=bytearray(520);offset=M.FILE-(M.TOP-520)
    struct.pack_into('<3I',before,offset+12,0x45,4,2);struct.pack_into('<2I',before,offset+60,0x210F198,0)
    archive=bytearray(92);struct.pack_into('<I',archive,28,0x213)
    entry=list(range(16));entry[:2]=[M.FILE,0x20D6DB0];entry[13:16]=[M.TOP-336,0x20D6984,0x6000001F]
    frame=bytearray(before);stores=[]
    for j,index in enumerate((3,4,5,6,7,8,9,10,14)):
        i=148+4*j;stores.append(dict(pc='0x20d6db0',address=M.TOP-372+4*j,bytes=4,before=frame[i:i+4].hex(),value=entry[index]))
        struct.pack_into('<I',frame,i,entry[index])
    returned=list(entry);returned[13]-=184;returned[9]=M.FILE;returned[1]=2;returned[14]=0x20D6DCC;returned[5:7]=[0x210F198,0]
    guard=bytes(range(56));old=dict(language='EN',ordinal=0,plus=0,seed=1,synthetic=True)
    cp=dict(pc=hex(M.ENTRY),regs=returned,frame=frame.hex(),archive=archive.hex())
    parent=dict(entry=entry,returned=returned,halt_regs=returned,halt_pc=hex(M.ENTRY),stop=hex(M.ENTRY),
        observe=True,fault=None,policy=dict(prepush=False,lower_fill=None),services=[],model_stores=[],host_stores=[],
        flow=[dict(pc=hex(x),regs=list(entry))for x in range(0x20D6DB0,0x20D6DCC,4)],steps=8,stores=stores,
        reads=[dict(pc=pc,address=M.FILE+field,bytes=4,hex=before[offset+field:offset+field+4].hex())
               for field,pc in((60,'0x20d6dbc'),(64,'0x20d6dc4'))],checkpoints=dict(nested_translate_entry=cp),
        frame_before=before.hex(),frame_after=frame.hex(),archive_before=archive.hex(),archive_after=archive.hex(),
        guard_before=guard.hex(),guard_after=guard.hex(),before_whole_ram_sha256='0'*64,whole_ram_sha256='1'*64)
    inp=M.after_state(parent);f=dict(language='EN',ordinal=0,plus=0,seed=1,parent_default_fixture=old,entry=returned,
        observed_parent_after_whole_sha256='1'*64,parent_native_stores=stores,archive_before=archive.hex())
    cell=dict(language='EN',ordinal=0,plus=0,seed=1,parent_default_fixture_sha256=M.sha(M.wire(old).encode()),input=inp)
    row=dict(entry=list(returned),policy=dict(clear_sync=False),frame_before=(guard[-24:]+frame).hex(),
             guard_before=(b'Z'*24+guard[:32]).hex(),archive_before=archive.hex())
    return cell,f,row,parent


class Frozen(unittest.TestCase):
    def test_parent_native_journal_and_actual_delivery_are_required(self):
        _,_,_,p=synthetic();M.after_state(p)
        for key in('preimage','return','reads','host'):
            bad=copy.deepcopy(p)
            if key=='preimage':bad['stores'][0]['before']='39'*4
            elif key=='return':bad['returned'][1]=4
            elif key=='reads':bad['reads'][0]['address']+=4
            else:bad['host_stores']=[{}]
            with self.subTest(key=key),self.assertRaises(ValueError):M.after_state(bad)

    def test_every_captured_byte_and_input_register_is_covered(self):
        c,f,r,_=synthetic();M.compare_input(c,f,r)
        for i in range(16):
            bad=copy.deepcopy(r);bad['entry'][i]^=1
            with self.subTest(reg=i),self.assertRaises(ValueError):M.compare_input(c,f,bad)
        for field,start in(('frame_before',0),('guard_before',24),('archive_before',0)):
            for i in range(start,len(bytes.fromhex(r[field]))):
                bad=copy.deepcopy(r);raw=bytearray.fromhex(bad[field]);raw[i]^=1;bad[field]=raw.hex()
                with self.subTest(field=field,byte=i),self.assertRaises(ValueError):M.compare_input(c,f,bad)
        bad=copy.deepcopy(r);raw=bytearray.fromhex(bad['guard_before']);raw[:24]=b'9'*24;bad['guard_before']=raw.hex()
        self.assertEqual(M.compare_input(c,f,bad)['newly_derived_guard_bytes'],24)

    def test_flag_projection_is_rejected_as_actual_and_attested_separately(self):
        c,f,r,_=synthetic();projected=copy.deepcopy(r);projected['policy']['clear_sync']=True
        raw=bytearray.fromhex(projected['archive_before']);struct.pack_into('<I',raw,28,0x13);projected['archive_before']=raw.hex()
        with self.assertRaisesRegex(ValueError,'actual captured archive'):M.compare_input(c,f,projected)
        proof=M.compare_projection(c,f,projected);self.assertFalse(proof['actual_parent_input']);self.assertTrue(proof['strict_actual_input_rejected'])
        for kind in('extra_byte','register','int_policy'):
            bad=copy.deepcopy(projected)
            if kind=='extra_byte':raw=bytearray.fromhex(bad['archive_before']);raw[60]^=1;bad['archive_before']=raw.hex()
            elif kind=='register':bad['entry'][9]^=1
            else:bad['policy']['clear_sync']=1
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.compare_projection(c,f,bad)


if __name__=='__main__':unittest.main()
