"""Portable earlier-contract export; no project oracle, guest or ROM imports."""
from pathlib import Path
import copy,importlib.util,json,tempfile,unittest
s=importlib.util.spec_from_file_location('freeze_wakeup',Path(__file__).parents[1]/'tools/congela_wakeup_contract.py')
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def parent(language):
    fixtures=[dict(plus=i//4,seed=123+i//2%2,translated_result=i%2)for i in range(8)]
    entry=[0]*16;entry[0]=0x1008;entry[13]=0x1000
    service=dict(pc='0x20d1ecc',entry=entry,frame_before='00'*328,frame_after='00'*328,
        archive_before='00'*92,archive_after='00'*92,writes=[])
    return dict(schema='native-fs-release-isolated-v1',language=language,cpu_executed=True,probe_only=False,
        fixtures=fixtures,cases=[dict(label='normal'if i%6==0 else'other',result=dict(services=[service]))for i in range(48)])


class Freeze(unittest.TestCase):
    def test_export_contains_hashes_and_entry_but_no_ram_payload(self):
        with tempfile.TemporaryDirectory()as d:
            paths={language:Path(d)/(language+'.json')for language in('EN','IT')}
            for language,p in paths.items():p.write_text(json.dumps(parent(language)))
            r=M.freeze(paths);self.assertEqual(len(r['cells']),16)
            for c in r['cells']:
                self.assertEqual(c['caller_frame_before_sha256'],M.sha(bytes(328)))
                self.assertNotIn('frame_before',c);self.assertEqual(c['input_queue8'],'00'*8)
            self.assertEqual(sum(c['held_out_from_first_guest_probe']for c in r['cells']),2)

    def test_incomplete_parent_and_nonempty_queue_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            paths={language:Path(d)/(language+'.json')for language in('EN','IT')}
            for language,p in paths.items():p.write_text(json.dumps(parent(language)))
            for mode in('short','queue','write','boolreg'):
                r=copy.deepcopy(parent('EN'))
                if mode=='short':r['cases'].pop()
                else:
                    s=r['cases'][0]['result']['services'][0]
                    if mode=='queue':s['frame_before']=s['frame_after']='00'*8+'01'+'00'*319
                    if mode=='write':s['writes']=[{}]
                    if mode=='boolreg':s['entry'][1]=False
                paths['EN'].write_text(json.dumps(r))
                with self.assertRaises(ValueError):M.freeze(paths)


if __name__=='__main__':unittest.main()
