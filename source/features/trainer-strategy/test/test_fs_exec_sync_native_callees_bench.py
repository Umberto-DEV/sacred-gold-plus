"""One wrapper context, one declared model, and exact Next counter preimages."""
from pathlib import Path
import copy,importlib.util,struct,unittest


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


M=load('native_sync_bench',Path(__file__).with_name('fs_exec_sync_native_callees_bench.py'))
T=load('native_sync_old_fixture',Path(__file__).with_name('test_fs_release_bench.py'))


def fixture(result=0):
    release=T.fixture(result);frame=bytearray.fromhex(release['frame'])[-304:]
    struct.pack_into('<I',frame,M.FILE-(M.TOP-304)+20,2)
    entry=[M.FILE,0x2000009F,0x2000001F,M.FILE+48,M.ARC,0,M.FILE,16,M.FILE,0x99999902,
           0xAAAAAA03,0xBBBBBB04,0,M.TOP-304,M.RETURN,0x2000001F]
    return dict(entry=entry,captured304=frame.hex(),captured_guard56='a5'*56,archive_before=release['archive_before'],
                translated_result=result,parent_whole_ram_sha256='0'*64)


class Source(unittest.TestCase):
    def test_positive_single_model_counts_and_actual_native_final(self):
        for value in(0,1):
            f=fixture(value);r=M.predict(f)
            self.assertEqual((len(r['flow']),r['unique_native_starts'],len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),
                             (131,109,26,35,133,112))
            self.assertEqual(len(r['services']),1);self.assertEqual(len(r['model_stores']),1)
            self.assertEqual(r['model_stores'][0]['before'],'02000000');self.assertEqual(r['model_stores'][0]['value'],value)
            self.assertEqual(r['returned'][0],int(value==0));self.assertEqual(r['returned'][4],M.ARC)
            self.assertEqual(r['returned'][1:3],[0x6000009F,0x6000001F]);self.assertEqual(r['returned'][14],0x20D76A4)
            self.assertEqual(r['returned'][13],M.TOP-304)
            self.assertEqual(len(r['checkpoints']),9)

    def test_native_release_store_must_record_preimage_from_model(self):
        r=M.predict(fixture(1));event=next(e for e in r['stores']if e['pc']=='0x20d68ac')
        self.assertEqual((event['before'],event['value']),('01000000',1))
        t=r['services'][0];a,b=bytes.fromhex(t['frame_before']),bytes.fromhex(t['frame_after'])
        self.assertEqual([i for i,(x,y)in enumerate(zip(a,b))if x!=y],[M.FILE-M.FRAME+20])

    def test_bypass_has_same_public_output_but_only_eight_final_stack_bytes_differ(self):
        for value in(0,1):
            normal=M.predict(fixture(value));counter=M.predict(fixture(value),bypass_wakeup=True)
            self.assertEqual((len(counter['flow']),counter['unique_native_starts'],len(counter['stores']),len(counter['reads']),counter['steps']),
                             (110,99,20,28,113))
            self.assertEqual(normal['returned'],counter['returned']);self.assertEqual(normal['archive_after'],counter['archive_after'])
            a,b=bytes.fromhex(normal['frame_after']),bytes.fromhex(counter['frame_after'])
            self.assertEqual([i for i,(x,y)in enumerate(zip(a,b))if x!=y],list(range(64,72)))
            self.assertEqual(struct.unpack_from('<2I',a,64),(M.FILE+48,value))
            self.assertEqual(len(counter['services']),2);self.assertEqual(len(counter['model_stores']),1)

    def test_next_adapter_clones_only_input_checker_and_keeps_counter_bytes(self):
        f=fixture();normal=M.predict(f);counter=M.predict(f,bypass_wakeup=True)
        nf,cf=normal['next_prestate'],counter['next_prestate']
        self.assertNotEqual(nf['captured408'],cf['captured408'])
        saved=copy.deepcopy((nf,cf))
        fn,setup=M.next_predictor(cf,nf,True)
        self.assertIs(fn.__code__,M.N.predict.__code__);self.assertIs(setup.__code__,M.N.input_state.__code__)
        actual=fn(cf);self.assertEqual(actual['frame_before'][16:],cf['captured408'])
        self.assertEqual((nf,cf),saved)
        for change in('entry','archive_before','captured408','profile'):
            bad=copy.deepcopy(cf)
            if change=='entry':bad[change][0]^=1
            elif change=='profile':bad[change]='normal'
            else:
                raw=bytearray.fromhex(bad[change]);raw[0]^=1;bad[change]=raw.hex()
            with self.subTest(change=change),self.assertRaises(ValueError):fn(bad)
        bad=copy.deepcopy(cf);raw=bytearray.fromhex(bad['captured408']);raw[56]^=1;bad['captured408']=raw.hex()
        with self.assertRaises(ValueError):fn(bad)
        M.N.check_fixture(dict(nf,parent_whole_ram_sha256='0'*64))
        with self.assertRaises(ValueError):M.N.check_fixture(dict(cf,parent_whole_ram_sha256='0'*64))

    def test_initial_capture_and_model_types_are_strict(self):
        for key,value in(('translated_result',True),('translated_result',2),('captured_guard56','a5'*55)):
            f=fixture();f[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):M.predict(f)

    def test_counter_model_uses_queue24_not_argument48(self):
        incoming=M.predict(fixture())['checkpoints']['wake_entry']['regs']
        self.assertEqual(incoming[0],M.FILE+24)
        M.check_wake_bypass_input(incoming,True,1)
        wrong=list(incoming);wrong[0]=M.FILE+48
        with self.assertRaises(ValueError):M.check_wake_bypass_input(wrong,True,1)


if __name__=='__main__':unittest.main()
