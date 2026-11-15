"""Finite complete Send source composition, including the actual readonly POP."""
from pathlib import Path
import copy,importlib.util,struct,unittest


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


M=load('send_native_test_bench',Path(__file__).with_name('fs_send_native_callees_bench.py'))
T=load('send_native_test_fixture',Path(__file__).with_name('test_fs_send_bench.py'))


def fixture(value=0):
    f=T.fixture();raw=bytearray.fromhex(f['frame'])
    struct.pack_into('<6I',raw,0,0,0,0,0,M.S.ID,0x02200088)
    struct.pack_into('<I',raw,M.FILE-(M.TOP-304)+20,0)
    f.update(frame=raw.hex(),guard='a5'*56,translated_result=value,parent_whole_ram_sha256='0'*64)
    return f


class Source(unittest.TestCase):
    def test_preserves_predecessor_guard_preimages_until_native_push(self):
        f=fixture();raw=bytes.fromhex(f['frame']);self.assertNotEqual(raw[:24],b'\xa5'*24)
        r=M.predict(f);self.assertEqual(bytes.fromhex(r['frame_before'])[-304:],raw)
        pushes=[e for e in r['stores']if e['pc']=='0x20d7788']
        self.assertEqual(len(pushes),6)
        for j,e in enumerate(pushes):self.assertEqual(e['before'],raw[4*j:4*j+4].hex())

    def test_counts_stack_peak_and_native_volatile_return(self):
        for value in(0,1):
            f=fixture(value);saved=copy.deepcopy(f);r=M.predict(f)
            self.assertEqual((len(r['flow']),r['unique_native_starts'],len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),
                (221,177,41,54,223,136))
            self.assertEqual(len(r['services']),1);self.assertEqual(len(r['model_stores']),1)
            self.assertEqual(r['returned'][0:3],[int(value==0),0x6000009F,0x6000001F])
            self.assertEqual(r['returned'][3:8],f['entry'][3:8]);self.assertEqual(r['returned'][13],M.TOP-280)
            self.assertEqual(r['returned'][14],0x20D76A4);self.assertEqual(r['returned'][15],0x6000001F if value==0 else 0x2000001F)
            self.assertEqual(len(r['checkpoints']),11);self.assertEqual(f,saved)

    def test_initial_send_fields_are_produced_by_native_stores(self):
        f=fixture();r=M.predict(f);initial=bytes.fromhex(r['frame_before']);exec_state=r['checkpoints']['exec_entry']
        i=M.FILE-M.FRAME
        self.assertEqual(struct.unpack_from('<3I',initial,i+12),(0,14,0))
        reached=bytes.fromhex(exec_state['frame']);self.assertEqual(struct.unpack_from('<3I',reached,i+12),(0x45,4,2))
        self.assertEqual(r['model_stores'][0]['before'],'02000000')
        self.assertEqual([e['pc']for e in r['flow']if e['pc']=='0x20d7928'],['0x20d7928'])
        self.assertEqual(r['flow'][-1]['regs'],r['checkpoints']['send_pop']['regs'])
        self.assertEqual([e['address']for e in r['reads'][-6:]],[M.TOP-304+4*j for j in range(6)])

    def test_bypass_difference_survives_readonly_pop(self):
        for value in(0,1):
            n=M.predict(fixture(value));b=M.predict(fixture(value),bypass_wakeup=True)
            self.assertEqual((len(b['flow']),b['unique_native_starts'],len(b['stores']),len(b['reads']),b['steps']),
                (200,167,35,47,203))
            self.assertEqual(n['returned'],b['returned']);self.assertEqual(n['archive_after'],b['archive_after'])
            x,y=bytes.fromhex(n['frame_after']),bytes.fromhex(b['frame_after'])
            self.assertEqual([i for i,(a,c)in enumerate(zip(x,y))if a!=c],list(range(64,72)))
            self.assertEqual(n['reads'][-6:],b['reads'][-6:]);self.assertEqual(len(b['services']),2)

    def test_input_rejects_earlier_poststate_and_policy_type_confusion(self):
        for change in('result_bool','bypass_int','frame_preapplied','guard','hash'):
            f=fixture()
            if change=='result_bool':f['translated_result']=False
            elif change=='frame_preapplied':
                raw=bytearray.fromhex(f['frame']);struct.pack_into('<I',raw,M.FILE-(M.TOP-304)+12,0x45);f['frame']=raw.hex()
            elif change=='guard':f['guard']='39'*56
            elif change=='hash':f['parent_whole_ram_sha256']='invalid'
            with self.subTest(change=change),self.assertRaises(ValueError):
                M.predict(f,bypass_wakeup=1 if change=='bypass_int'else False)


if __name__=='__main__':unittest.main()
