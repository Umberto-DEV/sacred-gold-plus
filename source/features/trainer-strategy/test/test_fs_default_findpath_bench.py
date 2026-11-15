"""Finite prefix ABI, causal PUSH evidence and uninitialized-stack neutrality."""
from pathlib import Path
import copy,importlib.util,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('default_findpath_source_test',Path(__file__).with_name('fs_default_findpath_bench.py'))
F=load('default_findpath_synthetic_ancestor',Path(__file__).with_name('test_fs_send_native_callees_bench.py'))


def fixture():
    old=F.fixture();cp=M.H.predict(old)['checkpoints']['default_entry']
    return dict(parent_send_fixture=old,entry=cp['regs'],frame=(b'Z'*48+bytes.fromhex(old['guard'])+bytes.fromhex(cp['frame'])).hex(),
                archive_before=cp['archive'],guard='a7'*56)


class Source(unittest.TestCase):
    def test_prefix_counts_and_nested_call_abi_not_fsresult(self):
        f=fixture();before=copy.deepcopy(f);r=M.predict(f)
        self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),(7,9,2,8,184))
        self.assertEqual(r['returned'][0:2],[M.FILE,2]);self.assertEqual(r['returned'][5:7],[M.H.T.H.S.PATH,0])
        self.assertEqual(r['returned'][9],M.FILE);self.assertEqual(r['returned'][13:16],[M.TOP-520,0x20D6DCC,0x6000001F])
        self.assertEqual(r['services'],[]);self.assertEqual(r['model_stores'],[]);self.assertEqual(r['host_stores'],[]);self.assertEqual(f,before)

    def test_only_saved36_changes_and_no_path_byte_or_arg_write(self):
        r=M.predict(fixture());a,b=bytes.fromhex(r['frame_before']),bytes.fromhex(r['frame_after'])
        self.assertEqual(a[:148],b[:148]);self.assertEqual(a[184:],b[184:]);self.assertEqual(r['guard_before'],r['guard_after'])
        self.assertEqual(r['archive_before'],r['archive_after'])
        self.assertEqual([w['address']for w in r['stores']],[M.TOP-372+4*i for i in range(9)])
        self.assertEqual([x['address']for x in r['reads']],[M.FILE+60,M.FILE+64])
        self.assertFalse(M.write_allowed(M.ENTRY,M.FILE+48,4));self.assertFalse(M.read_allowed(0x20D6DBC,M.FILE+64,4))

    def test_prepush_fault_converges_but_changes_all_native_preimages(self):
        n=M.predict(fixture());bad=M.predict(fixture(),prepush=True)
        for key in('returned','frame_before','frame_after','archive_before','archive_after','guard_before','guard_after','flow','reads','steps','checkpoints'):
            self.assertEqual(n[key],bad[key])
        self.assertEqual(len(bad['host_stores']),9)
        self.assertEqual([i for i,(a,b)in enumerate(zip(n['stores'],bad['stores']))if a!=b],list(range(9)))
        for a,b in zip(n['stores'],bad['stores']):
            self.assertEqual({k:v for k,v in a.items()if k!='before'},{k:v for k,v in b.items()if k!='before'})

    def test_lower_fill_changes_only_new104_and_does_not_change_execution(self):
        n=M.predict(fixture());filled=M.predict(fixture(),lower_fill=0x39)
        for key in('returned','stores','reads','flow','steps'):self.assertEqual(n[key],filled[key])
        self.assertEqual(bytes.fromhex(filled['frame_before'])[:48],b'9'*48)
        self.assertEqual(bytes.fromhex(filled['guard_before']),b'9'*56)
        self.assertEqual(n['frame_after'][96:],filled['frame_after'][96:])
        self.assertEqual(filled['frame_before'][:96],filled['frame_after'][:96])

    def test_policies_and_actual_entry_are_strict(self):
        for kwargs in(dict(prepush=1),dict(lower_fill=True),dict(lower_fill=0xA5)):
            with self.assertRaises(ValueError):M.predict(fixture(),**kwargs)
        for index,value in((1,2),(13,M.TOP-520),(14,0x20D6DCC)):
            f=fixture();f['entry'][index]=value
            with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
