"""Earlier native-output export has no oracle/ROM/guest dependencies."""
from pathlib import Path
import copy,importlib.util,json,tempfile,unittest
s=importlib.util.spec_from_file_location('freeze_composition',Path(__file__).parents[1]/'tools/congela_release_wakeup_contract.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def parent(language):
    fixtures=[dict(plus=i//4,seed=123+i//2%2,translated_result=i%2,frame='00'*328,archive_before='00'*92,entry=[0]*16)for i in range(8)]
    wake=[0]*16;wake[0]=0x1008;wake[13]=0x1000
    service=dict(pc='0x20d1ecc',entry=wake,frame_before='00'*328,frame_after='00'*328,archive_before='00'*92,archive_after='00'*92,writes=[])
    row=dict(services=[service],frame_before='00'*328,frame_after='00'*328,archive_after='00'*92,
        guard_before='a5'*56,guard_after='a5'*56,returned=[0]*16,halt_pc='0x20d7760')
    return dict(schema='native-fs-release-isolated-v1',language=language,cpu_executed=True,probe_only=False,fixtures=fixtures,
        cases=[dict(label='normal'if i%6==0 else'other',result=row)for i in range(48)])


class EarlierExport(unittest.TestCase):
    def test_full16_caller_outputs_and_six_stack_words_exported_without_ram_dump(self):
        with tempfile.TemporaryDirectory()as d:
            paths={k:Path(d)/(k+'.json')for k in('EN','IT')}
            for language,p in paths.items():p.write_text(json.dumps(parent(language)))
            r=M.freeze(paths);self.assertEqual(len(r['cells']),16)
            for c in r['cells']:
                self.assertEqual(c['expected_returned'],[0]*16);self.assertEqual(c['native_stack24_words'],[0]*6)
                self.assertEqual(c['stack24_preimage'],'a5'*24);self.assertNotIn('frame_after',c)
                self.assertEqual(c['expected_frame328_after_sha256'],M.sha(bytes(328)))

    def test_nonempty_queue_guard_write_probe_and_bool_register_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            paths={k:Path(d)/(k+'.json')for k in('EN','IT')}
            for language,p in paths.items():p.write_text(json.dumps(parent(language)))
            for mode in('queue','guard','write','probe','boolreg'):
                r=copy.deepcopy(parent('EN'));row=r['cases'][0]['result'];s=row['services'][0]
                if mode=='queue':s['frame_before']=s['frame_after']='00'*8+'01'+'00'*319
                if mode=='guard':row['guard_after']='39'*56
                if mode=='write':s['writes']=[{}]
                if mode=='probe':r['probe_only']=True
                if mode=='boolreg':row['returned'][0]=False
                paths['EN'].write_text(json.dumps(r))
                with self.assertRaises(ValueError):M.freeze(paths)


if __name__=='__main__':unittest.main()
