"""The final Send POP projection preserves real native volatile registers."""
from pathlib import Path
import copy,importlib.util,struct,unittest

path=Path(__file__).parents[1]/'tools/congela_fs_send_native_contract.py'
spec=importlib.util.spec_from_file_location('send_native_freeze',path)
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


def inputs():
    r=[1,0x6000009F,0x6000001F,M.FILE+48,M.ARC,0,M.FILE,16,M.FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
       0,M.TOP-304,0x20D76A4,0x6000001F]
    frame=bytearray([0xA5])*416
    struct.pack_into('<6I',frame,112,M.FILE+48,1,0,M.ID,M.PATH,0x20D80F8)
    reads=[dict(pc='0x20d7928',address=M.TOP-304+4*i,bytes=4,hex=frame[112+4*i:116+4*i].hex())for i in range(6)]
    return r,frame.hex(),reads


class Pop(unittest.TestCase):
    def test_historical_final_is_not_silently_overwritten_or_renamed(self):
        r,frame,_=inputs()
        phases={name:dict(pc=hex(pc),regs=r,frame=frame,archive='00'*92)for name,pc in M.PHASE_PCS.items()}
        out=M.historical_checkpoints(phases)
        self.assertIn('send_pop',out);self.assertNotIn('final',out)
        bad=copy.deepcopy(phases);bad['send_pop']=bad.pop('final')
        with self.assertRaises(ValueError):M.historical_checkpoints(bad)
        bad=copy.deepcopy(phases);bad['final']['pc']='0x20d80f8'
        with self.assertRaises(ValueError):M.historical_checkpoints(bad)

    def test_projection_keeps_native_volatiles_flags_lr_and_inputs(self):
        for value in(0,1):
            r,frame,reads=inputs();r[0]=int(value==0);r[15]=0x6000001F if value==0 else 0x2000001F
            before=copy.deepcopy((r,frame,reads));out=M.project_send_pop(r,frame,reads)
            self.assertEqual(out[3:8],[M.FILE+48,1,0,M.ID,M.PATH]);self.assertEqual(out[13],M.TOP-280)
            for i in(0,1,2,8,9,10,11,12,14,15):self.assertEqual(out[i],r[i])
            self.assertEqual((r,frame,reads),before)

    def test_projection_rejects_wrong_context_saved_return_or_read_words(self):
        for field in('SP','R4','bool','return','read_address','read_hex'):
            r,frame,reads=inputs();old=copy.deepcopy((r,frame,reads))
            if field=='SP':r[13]+=4
            elif field=='R4':r[4]=M.FILE
            elif field=='bool':r[0]=True
            elif field=='return':raw=bytearray.fromhex(frame);raw[132]^=4;frame=raw.hex()
            elif field=='read_address':reads[-1]['address']+=4
            else:reads[-1]['hex']='00000000'
            self.assertNotEqual(M.wire((r,frame,reads)),M.wire(old))
            with self.subTest(field=field),self.assertRaises(ValueError):M.project_send_pop(r,frame,reads)


if __name__=='__main__':unittest.main()
