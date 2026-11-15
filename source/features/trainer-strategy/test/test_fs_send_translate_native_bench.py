"""Causal composition tests, including final-state-convergent writer forgery."""
from pathlib import Path
import copy,importlib.util,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('send_translate_source_test',Path(__file__).with_name('fs_send_translate_native_bench.py'))
F=load('send_translate_test_fixture',Path(__file__).with_name('test_fs_send_native_callees_bench.py'))


class Source(unittest.TestCase):
    def test_native_composition_and_stack_converge_to_earlier_final(self):
        for result in(0,1):
            f=F.fixture(result);saved=copy.deepcopy(f);r=M.predict(f);old=M.H.predict(f)
            self.assertEqual((len(r['flow']),r['unique_native_starts'],len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),
                             (260,216,50,68,262,136))
            for key in('returned','frame_after','archive_after'):self.assertEqual(r[key],old[key])
            self.assertEqual(r['model_stores'],[]);self.assertEqual(len(r['services']),1)
            self.assertEqual(r['services'][0]['pc'],hex(M.DEFAULT));self.assertEqual(f,saved)

    def test_native_volatile_bridge_and_saved24_washout(self):
        r=M.predict(F.fixture());old=M.H.predict(F.fixture())
        bridge=[e for e in r['flow']if e['pc']in('0x20d7754','0x20d7758','0x20d775c')]
        self.assertEqual(bridge[0]['regs'][1],M.DEFAULT)
        self.assertEqual([e['regs'][14]for e in bridge],[0x20D6984]*3)
        diffs=[]
        # The new9 stores precede the old downstream stores.
        for index in range(26,50):
            a,b=r['stores'][index],old['stores'][index-9]
            if a['before']!=b['before']:diffs.append(index)
        self.assertEqual(diffs,[26,27,28,29,39,40])
        for key in('wake_return','release_return','next_entry','next_return','send_pop','final'):
            self.assertEqual(r['checkpoints'][key],old['checkpoints'][key])

    def test_early_host_writer_converges_but_native_preimage_changes(self):
        for result in(0,1):
            n=M.predict(F.fixture(result));e=M.predict(F.fixture(result),True)
            for key in('returned','frame_after','archive_after','flow','reads','steps','native_peak'):
                self.assertEqual(n[key],e[key])
            differences=[i for i,(a,b)in enumerate(zip(n['stores'],e['stores']))if a!=b]
            self.assertEqual(differences,[25]);self.assertEqual(n['stores'][25]['pc'],'0x20d6a40')
            self.assertEqual(n['stores'][25]['before'],'02000000')
            self.assertEqual(e['stores'][25]['before'],result.to_bytes(4,'little').hex())
            self.assertEqual(len(n['model_stores']),0);self.assertEqual(len(e['model_stores']),1)

    def test_policy_is_typed_and_poststate_is_not_a_valid_input(self):
        with self.assertRaises(ValueError):M.predict(F.fixture(),early_error=1)
        f=F.fixture();f['translated_result']=False
        with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
