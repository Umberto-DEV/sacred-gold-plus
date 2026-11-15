"""Finite ExecuteSync source semantics, synthetic inputs and no guest CPU."""
from pathlib import Path
import importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('exec_sync_bench',Path(__file__).with_name('fs_exec_sync_bench.py'))
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def fixture():
    frame=bytearray(b'\x39'*312);i=M.FILE-M.FRAME
    for off,value in((0,M.ARC+32),(4,0),(8,M.ARC),(12,0x45),(16,4),(20,2),(24,0),(28,0),
                      (48,M.ARC),(52,0),(56,0),(60,M.PATH),(64,0),(68,M.ID)):
        struct.pack_into('<I',frame,i+off,value)
    archive=bytearray(92);struct.pack_into('<I',archive,28,0x13);struct.pack_into('<I',archive,36,M.FILE)
    entry=[M.FILE,0x2000009F,0x2000001F,M.FILE+48,M.ARC,0,M.FILE,16,M.FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
           0,M.SP,M.RETURN,0x2000001F]
    return dict(entry=entry,frame=frame.hex(),archive_before=archive.hex())


class Source(unittest.TestCase):
    def test_final_success_uses_error_and_preserves_command_four(self):
        f=fixture();r=M.predict(f);image=bytes.fromhex(r['frame_after']);i=M.FILE-M.FRAME
        self.assertEqual(struct.unpack_from('<6I',image,i),(0,0,M.ARC,0,4,0))
        self.assertEqual(struct.unpack_from('<3I',bytes.fromhex(r['archive_after']),28),(3,0,0))
        self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps']),(16,2,5,20))
        self.assertEqual([len(s['writes'])for s in r['services']],[1,5,1])
        want=list(f['entry']);want[0:2]=[1,0];want[14:16]=[0x20D7768,0x6000001F]
        self.assertEqual(r['returned'],want)

    def test_failure_and_release_fault_read_actual_post_release_word(self):
        f=fixture();normal=M.predict(f)
        for r in(M.predict(f,result=1),M.predict(f,release_error=1)):
            self.assertEqual(r['returned'][0],0);self.assertEqual(r['returned'][15],0x2000001F)
            a,b=bytes.fromhex(normal['frame_after']),bytes.fromhex(r['frame_after'])
            self.assertEqual([i for i,(x,y)in enumerate(zip(a,b))if x!=y],[92])
            self.assertEqual(r['archive_after'],normal['archive_after'])
        fault=M.predict(f,release_error=1)
        self.assertEqual(fault['services'][0]['returned'][0],0)
        self.assertEqual(fault['services'][1]['entry'][1],0)

    def test_void_r0_is_overwritten_before_next_and_changes_no_memory(self):
        f=fixture();normal=M.predict(f)
        for value in(M.FILE,0xFFFFFFFF):
            r=M.predict(f,void_value=value)
            self.assertEqual(r['returned'],normal['returned']);self.assertEqual(r['frame_after'],normal['frame_after'])
            self.assertEqual(r['archive_after'],normal['archive_after'])
            self.assertEqual([e['pc']for e,w in zip(r['flow'],normal['flow'])if e!=w],['0x20d7760'])

    def test_clobber_r3_persists_because_this_wrapper_does_not_push_it(self):
        f=fixture();r=M.predict(f,clobber=True)
        self.assertEqual(r['returned'][3],0xA5000003);self.assertEqual(r['returned'][4:12],f['entry'][4:12])
        self.assertEqual(r['returned'][12],0xA500000C);self.assertEqual(r['returned'][15],0x6000001F)

    def test_bool_and_unqualified_state_are_rejected(self):
        f=fixture();f['entry'][5]=False
        with self.assertRaises(ValueError):M.predict(f)
        with self.assertRaises(ValueError):M.predict(fixture(),result=True)
        with self.assertRaises(ValueError):M.predict(fixture(),void_value=0.0)
        with self.assertRaises(ValueError):M.predict(fixture(),result=1,release_error=1)
        f=fixture();archive=bytearray.fromhex(f['archive_before']);struct.pack_into('<I',archive,36,0);f['archive_before']=archive.hex()
        with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
