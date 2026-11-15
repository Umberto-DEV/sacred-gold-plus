"""Metadata export uses the stdlib; it does not qualify a synthetic native run."""
from pathlib import Path
import copy,importlib.util,json,struct,tempfile,unittest
s=importlib.util.spec_from_file_location('freeze_next',Path(__file__).parents[1]/'tools/congela_fs_next_contract.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def parent():
    fixtures=[dict(language=language,ordinal=i,plus=i//4,seed=123+i//2%2,translated_result=i%2)for language in('EN','IT')for i in range(8)]
    groups=[dict(ordinal=g,members=[dict(language=f['language'],ordinal=f['ordinal'])for f in fixtures if f['plus']*2+f['translated_result']==g])for g in range(4)]
    frame=bytearray(352);struct.pack_into('<I',frame,120,0x21E3654);arc=bytearray(92);struct.pack_into('<I',arc,28,0x13)
    regs=[0]*16;regs[4]=0x1070;regs[13]=0x1028
    row=dict(policy=dict(bypass_wakeup=False),observe=True,fill=0xA5,services=[],frame_after=frame.hex(),guard_before='a5'*56,
        guard_after='a5'*56,archive_after=arc.hex(),returned=regs,halt_pc='0x20d7760',whole_ram_sha256='a'*64)
    return dict(schema='native-release-wakeup-composed-v1',cpu_executed=True,compiler_invoked=False,probe_only=False,
        fixtures=fixtures,groups=groups,cases=[dict(group=i//4,label='normal'if i%4==0 else'other',result=row)for i in range(16)])


class Export(unittest.TestCase):
    def test_live312_hash_archive_word_and_actual_file_arc_bridge(self):
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'parent.json';r=parent();p.write_text(json.dumps(r));c=M.freeze(p)
            self.assertEqual(len(c['cells']),16)
            for cell in c['cells']:
                self.assertEqual(cell['expected_next_entry'][0],0x21E3654);self.assertEqual(cell['expected_next_entry'][14],0x20D7768)
                self.assertEqual(cell['expected_R0'],0);self.assertNotIn('frame_after',cell)
                arc=bytearray.fromhex(r['cases'][0]['result']['archive_after']);struct.pack_into('<I',arc,28,3)
                self.assertEqual(cell['expected_archive92_after_sha256'],M.sha(bytes(arc)))

    def test_probe_idle_callback_bad_live_pointer_and_bool_register_rejected(self):
        with tempfile.TemporaryDirectory()as name:
            p=Path(name)/'parent.json'
            for mode in('probe','idle','pointer','bool','membership'):
                r=copy.deepcopy(parent());row=r['cases'][0]['result']
                if mode=='probe':r['probe_only']=True
                if mode=='idle':arc=bytearray.fromhex(row['archive_after']);struct.pack_into('<I',arc,88,0x400);row['archive_after']=arc.hex()
                if mode=='pointer':row['returned'][4]=0
                if mode=='bool':row['returned'][0]=False
                if mode=='membership':r['groups'][0]['members']=[]
                p.write_text(json.dumps(r))
                with self.assertRaises(ValueError):M.freeze(p)


if __name__=='__main__':unittest.main()
