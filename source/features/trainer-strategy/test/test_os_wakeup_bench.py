"""Pure native empty-Wakeup/IRQ predictions; no guest or compiler calls."""
from pathlib import Path
import importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('empty_wakeup_bench',Path(__file__).with_name('os_wakeup_bench.py'))
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def fixture(value=0,guard=None):
    guard=bytes([0xA5])*56 if guard is None else guard
    frame=bytearray(b'\x39'*352);frame[:24]=guard[-24:];i=M.FILE-M.FRAME
    for off,x in((0,0),(4,0),(8,M.ARC),(12,0),(16,4),(20,value),(24,0),(28,0),
                 (48,M.ARC),(52,0),(56,0),(60,M.PATH),(64,0),(68,M.ID)):
        struct.pack_into('<I',frame,i+off,x)
    entry=[M.QUEUE,0,0x2000001F,M.FILE+48,value,M.FILE,0,16,M.FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
        0,M.SP,M.RETURN,0x6000009F]
    return dict(entry=entry,frame=frame.hex(),archive_before=M.ARCHIVE.hex(),translated_result=value,captured_parent_guard56=guard.hex())


class NativeSource(unittest.TestCase):
    def test_native_irq_path_and_void_residue_restore_original_caller(self):
        for value in(0,1):
            f=fixture(value);r=M.predict(f)
            self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads']),r['steps'],r['native_peak']),(21,6,7,22,24))
            expected=list(f['entry']);expected[:3]=[0x80,0x6000009F,0x6000009F];expected[14]=0x20D1F30
            self.assertEqual(r['returned'],expected);self.assertEqual(r['services'],[])
            self.assertEqual(r['returned'][15]&128,128)
            self.assertNotIn('0x20d1750',[e['pc']for e in r['flow']]);self.assertNotIn('0x20d18b0',[e['pc']for e in r['flow']])

    def test_complete_parent_frame_archive_unchanged_new_push_is_fully_owned(self):
        for value in(0,1):
            f=fixture(value);r=M.predict(f);after=bytes.fromhex(r['frame_after'])
            self.assertEqual(after[24:],bytes.fromhex(f['frame'])[24:]);self.assertEqual(r['archive_after'],f['archive_before'])
            self.assertEqual(after[:24],struct.pack('<6I',*(f['entry'][i]for i in(3,4,5,6,7,14))))
            self.assertEqual([e['address']for e in r['stores']],[M.FRAME+4*i for i in range(6)])
            self.assertEqual(r['reads'][0]['address'],M.QUEUE);self.assertEqual(r['reads'][0]['hex'],'00000000')

    def test_guard_retains_actual_parent32_and_declares_only_new24(self):
        f=fixture(guard=bytes(range(56)))
        for fill in(0xA5,0x39):self.assertEqual(M.guard_before(f,fill),bytes([fill])*24+bytes(range(32)))
        self.assertEqual(bytes.fromhex(f['frame'])[:24],bytes(range(32,56)))
        bad=dict(f);bad['frame']='00'+bad['frame'][2:]
        with self.assertRaises(ValueError):M.predict(bad)

    def test_irq_r2_is_after_restoring_i1_not_intermediate_i0(self):
        r=M.predict(fixture());by_pc={e['pc']:e['regs']for e in r['flow']}
        self.assertEqual(by_pc['0x20d3a54'][2],0x6000001F)
        self.assertEqual(by_pc['0x20d3a5c'][2],0x6000009F)
        self.assertEqual(r['returned'][2],0x6000009F)

    def test_strict_i1_empty_queue_and_parent_preimage_types(self):
        f=fixture();f['entry'][1]=False
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();f['entry'][15]&=~128
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();b=bytearray.fromhex(f['frame']);struct.pack_into('<I',b,M.QUEUE-M.FRAME,1);f['frame']=b.hex()
        with self.assertRaises(ValueError):M.predict(f)
        with self.assertRaises(ValueError):M.guard_before(fixture(),True)


if __name__=='__main__':unittest.main()
