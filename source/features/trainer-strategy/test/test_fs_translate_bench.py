"""Native Translate source semantics; final agreement does not identify a writer."""
from pathlib import Path
import copy,importlib.util,struct,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('translate_source',Path(__file__).with_name('fs_translate_bench.py'))
T=load('translate_older_source_fixture',Path(__file__).with_name('test_fs_send_native_callees_bench.py'))


def fixture(value=0):
    old=T.M.predict(T.fixture(value))['services'][0]
    return dict(entry=old['entry'],frame=old['frame_before'],guard='a5'*56,archive_before=old['archive_before'],default_result=value)


class Source(unittest.TestCase):
    def test_native_dispatch_fsresult_and_flags_are_not_bool(self):
        for value in(0,1):
            f=fixture(value);prior=copy.deepcopy(f);r=M.predict(f)
            self.assertEqual((len(r['flow']),r['unique_native_starts'],len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),
                (39,39,9,14,41,24))
            self.assertEqual(r['returned'][0],value);self.assertEqual(r['returned'][15],0x2000001F)
            self.assertEqual(r['returned'][1],M.DEFAULT);self.assertEqual(r['returned'][14],0x20D6984)
            self.assertEqual(r['returned'][2:14],f['entry'][2:14]);self.assertEqual(f,prior)
            self.assertEqual(len(r['services']),1);self.assertEqual(r['model_stores'],[])
            self.assertEqual(r['services'][0]['entry'][13:15],[M.TOP-336,0x20D6984])
            self.assertEqual([(e['address'],e['hex'])for e in r['reads']if int(e['pc'],16)in(0x20D6974,0x20D697C)],
                [(M.POOL,struct.pack('<I',M.TABLE).hex()),(M.TABLE+16,struct.pack('<I',M.DEFAULT).hex())])

    def test_native_archive_transient_and_error_preimage(self):
        r=M.predict(fixture(1));arc=[e for e in r['stores']if e['address']==M.ARC+28]
        self.assertEqual([(e['before'],e['value'])for e in arc],[('13000000',0x213),('13020000',0x13)])
        self.assertEqual(r['services'][0]['frame_before'],r['services'][0]['frame_after'])
        event=next(e for e in r['stores']if e['pc']=='0x20d6a40')
        self.assertEqual((event['before'],event['value']),('02000000',1))

    def test_early_error_has_identical_final_cpu_memory_but_different_writer_preimage(self):
        for value in(0,1):
            normal=M.predict(fixture(value));early=M.predict(fixture(value),early_error=True)
            for key in('returned','frame_after','archive_after','flow','reads','steps','native_peak'):
                self.assertEqual(normal[key],early[key])
            self.assertEqual(len(early['model_stores']),1)
            a=next(e for e in normal['stores']if e['pc']=='0x20d6a40');b=next(e for e in early['stores']if e['pc']=='0x20d6a40')
            self.assertEqual(a['before'],'02000000');self.assertEqual(b['before'],struct.pack('<I',value).hex())
            self.assertNotEqual(normal['checkpoints']['before_error_store'],early['checkpoints']['before_error_store'])

    def test_callback_async_nonsync_and_typed_policies_are_outside_scope(self):
        for change in('result_bool','async6','early_int','callback','nonsync','error_preapplied'):
            f=fixture()
            if change=='result_bool':f['default_result']=True
            elif change=='async6':f['default_result']=6
            elif change=='callback':
                a=bytearray.fromhex(f['archive_before']);struct.pack_into('<I',a,88,16);f['archive_before']=a.hex()
            elif change in('nonsync','error_preapplied'):
                a=bytearray.fromhex(f['frame']);struct.pack_into('<I',a,M.FILE-M.FRAME+(12 if change=='nonsync'else 20),0);f['frame']=a.hex()
            with self.subTest(change=change),self.assertRaises(ValueError):M.predict(f,early_error=1 if change=='early_int'else False)


if __name__=='__main__':unittest.main()
