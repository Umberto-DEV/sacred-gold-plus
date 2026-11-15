"""Pure Release/IRQ semantics with an explicit empty-Wakeup value boundary."""
from pathlib import Path
import importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('release_bench',Path(__file__).with_name('fs_release_bench.py'))
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def fixture(result=0):
    frame=bytearray(b'\x39'*328);i=M.FILE-M.FRAME
    for off,value in((0,M.ARC+32),(4,0),(8,M.ARC),(12,0x45),(16,4),(20,result),(24,0),(28,0),
                      (48,M.ARC),(52,0),(56,0),(60,M.PATH),(64,0),(68,M.ID)):
        struct.pack_into('<I',frame,i+off,value)
    entry=[M.FILE,result,0x2000001F,M.FILE+48,M.FILE,0,M.FILE,16,M.FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
        0,M.SP,M.RETURN,0x2000001F]
    return dict(entry=entry,frame=frame.hex(),archive_before=M.ARCHIVE.hex(),translated_result=result)


class Source(unittest.TestCase):
    def test_unlink_stat_error_and_preserved_command_four(self):
        for value in(0,1):
            f=fixture(value);r=M.predict(f);frame=bytes.fromhex(r['frame_after']);i=M.FILE-M.FRAME
            self.assertEqual(struct.unpack_from('<6I',frame,i),(0,0,M.ARC,0,4,value))
            self.assertEqual(struct.unpack_from('<3I',bytes.fromhex(r['archive_after']),28),(0x13,0,0))
            self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),(34,9,7,36,16))
            want=list(f['entry']);want[:3]=[0x80,0x6000009F,0x6000001F];want[14:16]=[0x20D68BC,0x6000001F]
            self.assertEqual(r['returned'],want)

    def test_void_wakeup_poison_is_ignored_and_queue_has_no_modeled_ram_writes(self):
        f=fixture();normal=M.predict(f);r=M.predict(f,wake_value=0xFFFFFFFF)
        self.assertEqual(r['returned'],normal['returned']);self.assertEqual(r['frame_after'],normal['frame_after'])
        self.assertEqual([e['pc']for e,w in zip(r['flow'],normal['flow'])if e!=w],['0x20d68b4'])
        service=r['services'][0];self.assertEqual(service['entry'][0],M.FILE+24)
        self.assertTrue(service['entry'][15]&128);self.assertEqual(service['frame_before'],service['frame_after'])
        self.assertEqual(service['archive_before'],service['archive_after']);self.assertEqual(service['writes'],[])

    def test_stale_error_input_projection_is_overwritten_from_actual_r1(self):
        for value in(0,1):
            f=fixture(value);normal=M.predict(f);r=M.predict(f,stale_error=True)
            self.assertEqual(r['frame_after'],normal['frame_after']);self.assertEqual(r['archive_after'],normal['archive_after'])
            self.assertEqual(r['flow'],normal['flow']);self.assertEqual(r['returned'],normal['returned'])
            self.assertEqual([j for j,(a,b)in enumerate(zip(bytes.fromhex(r['frame_before']),bytes.fromhex(normal['frame_before'])))if a!=b],[108])
            store=next(e for e in r['stores']if e['pc']=='0x20d68ac')
            self.assertEqual(store['before'],'02000000');self.assertEqual(store['value'],value)
            self.assertEqual([i for i,(a,b)in enumerate(zip(r['stores'],normal['stores']))if a!=b],[8])

    def test_clobber_r3_persists_and_restore_preserves_clobbered_flags(self):
        f=fixture();r=M.predict(f,clobber=True)
        self.assertEqual(r['returned'][0],0x80);self.assertEqual(r['returned'][1:4],[0xA000009F,0xA000001F,0xA5000003])
        self.assertEqual(r['returned'][4:12],f['entry'][4:12]);self.assertEqual(r['returned'][12],0xA500000C)
        self.assertEqual(r['returned'][15],0xA000001F)

    def test_typed_policy_and_unqualified_state_rejected(self):
        for kwargs in(dict(wake_value=True),dict(clobber=1),dict(stale_error=1)):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):M.predict(fixture(),**kwargs)
        f=fixture();f['entry'][1]=False
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();f['entry'][15]|=128
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();image=bytearray.fromhex(f['frame']);struct.pack_into('<I',image,M.FILE-M.FRAME+24,1);f['frame']=image.hex()
        with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
