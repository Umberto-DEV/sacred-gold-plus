"""Mutation coverage of complete frozen fields and actual whole boundaries."""
from pathlib import Path
import copy,importlib.util,unittest

path=Path(__file__).parents[1]/'tools/congela_fs_send_translate_contract.py'
s=importlib.util.spec_from_file_location('send_translate_freezer_tests',path)
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def synthetic():
    f=dict(language='EN',ordinal=0,plus=0,seed=1,translated_result=0,entry=list(range(16)))
    frame=bytes(range(256))+bytes(range(160));arc=bytes(range(92));guard=b'\xa5'*56
    phases={k:dict(pc=pc,regs=list(range(16)),frame=frame.hex(),archive=arc.hex(),whole_ram_sha256='1'*64)
            for k,pc in(('translate_entry','0x20d68c0'),('translate_return','0x20d7754'))}
    row=dict(entry=f['entry'],returned=list(range(16)),halt_pc='0x20d80f8',frame_after=frame.hex(),archive_after=arc.hex(),
             guard_before=guard.hex(),guard_after=guard.hex(),checkpoints=phases)
    child={}
    for prefix in('entry','return'):
        child.update({prefix if prefix=='entry'else'returned':list(range(16)),
            prefix+'_frame416_sha256':M.sha(frame),prefix+'_archive92_sha256':M.sha(arc)})
    child.update(actual_before_whole_ram_sha256='1'*64,actual_after_whole_ram_sha256='1'*64)
    cell=dict(f,parent_fixture_sha256=M.sha(M.wire(f).encode()),translate=child,
        expected_final=dict(returned=list(range(16)),stop='0x20d80f8',frame416_sha256=M.sha(frame),
                            archive92_sha256=M.sha(arc),guard56_sha256=M.sha(guard)))
    return cell,f,row


class Frozen(unittest.TestCase):
    def test_every_final_register_and_owner_byte_is_covered(self):
        c,f,r=synthetic();M.compare(c,f,r)
        for index in range(16):
            bad=copy.deepcopy(r);bad['returned'][index]^=1
            with self.subTest(reg=index),self.assertRaises(ValueError):M.compare(c,f,bad)
        for key in('frame_after','archive_after','guard_before','guard_after'):
            for index in range(len(bytes.fromhex(r[key]))):
                bad=copy.deepcopy(r);raw=bytearray.fromhex(bad[key]);raw[index]^=1;bad[key]=raw.hex()
                with self.subTest(field=key,byte=index),self.assertRaises(ValueError):M.compare(c,f,bad)

    def test_both_actual_whole_boundaries_and_full_abi_are_covered(self):
        c,f,r=synthetic()
        for phase in r['checkpoints']:
            for field,value in(('whole_ram_sha256','2'*64),('pc','0x20d6984'),('regs',[0]*16),('frame','00'*416),('archive','00'*92)):
                bad=copy.deepcopy(r);bad['checkpoints'][phase][field]=value
                with self.subTest(phase=phase,field=field),self.assertRaises(ValueError):M.compare(c,f,bad)
        bad=copy.deepcopy(r);bad['entry'][1]=True
        with self.assertRaises(ValueError):M.compare(c,f,bad)
        bad=copy.deepcopy(f);bad['translated_result']=False
        with self.assertRaises(ValueError):M.compare(c,bad,r)


if __name__=='__main__':unittest.main()
