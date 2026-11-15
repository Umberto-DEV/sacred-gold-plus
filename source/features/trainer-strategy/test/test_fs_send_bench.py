"""Finite Send source semantics using synthetic owned inputs, no guest CPU."""
from pathlib import Path
import copy,importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('send_finite_bench',Path(__file__).with_name('fs_send_bench.py'))
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def fixture():
    frame=bytearray(b'\x39'*304);i=M.FILE-M.FRAME
    for off,value in((0,0),(4,0),(8,M.ARC),(12,0),(16,14),(24,0),(28,0),
                      (48,M.ARC),(52,0),(56,0),(60,M.PATH),(64,0),(68,M.ID)):
        struct.pack_into('<I',frame,i+off,value)
    archive=bytearray(92);struct.pack_into('<I',archive,28,3)
    entry=[M.FILE,4,0,M.FILE+48,1,0,M.ID,M.PATH,M.FILE,0x99999902,0xAAAAAA03,0xBBBBBB04,
           0,M.SP,0x20D80F8,0x6000001F]
    return dict(entry=entry,frame=frame.hex(),archive_before=archive.hex())


class Source(unittest.TestCase):
    def test_queue_fields_and_real_irq_residuals_without_completion(self):
        f=fixture();out=M.predict(f);after=bytes.fromhex(out['frame_after']);arc=bytes.fromhex(out['archive_after'])
        i=M.FILE-M.FRAME;prior=bytes.fromhex(f['frame']);expected=bytearray(prior[i:i+72])
        for off,value in((0,M.ARC+32),(4,0),(12,0x45),(16,4),(20,2)):struct.pack_into('<I',expected,off,value)
        self.assertEqual(after[i:i+72],bytes(expected))
        a=bytearray.fromhex(f['archive_before']);struct.pack_into('<I',a,28,0x13);struct.pack_into('<I',a,36,M.FILE)
        self.assertEqual(arc,bytes(a));self.assertEqual((len(out['flow']),len(out['stores']),len(out['reads'])),(90,15,19))
        self.assertEqual(out['native_peak'],24);self.assertEqual(out['steps'],92)
        want=list(f['entry']);want[0:3]=[1,0x2000009F,0x2000001F];want[14:16]=[0x20D7928,0x2000001F]
        self.assertEqual(out['returned'],want)
        self.assertEqual(out['services'][0]['entry'][13:15],[M.FRAME,0x20D7928])

    def test_false_and_truthy_two_keep_native_queue_ram_but_distinct_return(self):
        f=fixture();rows=[M.predict(f,value)for value in(0,1,2)]
        self.assertEqual([r['returned'][0]for r in rows],[0,1,2])
        for row in rows:
            self.assertEqual(row['frame_after'],rows[1]['frame_after']);self.assertEqual(row['archive_after'],rows[1]['archive_after'])
            self.assertEqual(row['returned'][15],0x2000001F)

    def test_clobber_r3_is_restored_by_native_pop(self):
        f=fixture();r=M.predict(f,1,True)
        self.assertEqual(r['returned'][3],f['entry'][3]);self.assertEqual(r['returned'][4:12],f['entry'][4:12])
        self.assertEqual(r['returned'][1:3],[0xA5000001,0xA5000002]);self.assertEqual(r['returned'][12],0xA500000C)
        self.assertEqual(r['returned'][14:16],[0x20D7928,0xA000001F])

    def test_unqualified_archive_state_and_typed_aliases_are_rejected(self):
        for kind in('register_bool','command','busy','suspended','activate','linked'):
            f=fixture()
            if kind=='register_bool':f['entry'][2]=False
            elif kind=='command':f['entry'][1]=6
            elif kind=='linked':
                frame=bytearray.fromhex(f['frame']);struct.pack_into('<I',frame,M.FILE-M.FRAME,4);f['frame']=frame.hex()
            else:
                archive=bytearray.fromhex(f['archive_before']);struct.pack_into('<I',archive,88 if kind=='activate'else 28,
                    0x200 if kind=='activate'else 3|16 if kind=='busy'else 3|8);f['archive_before']=archive.hex()
            with self.subTest(kind=kind),self.assertRaises(ValueError):M.predict(f)
        with self.assertRaises(ValueError):M.predict(fixture(),True)

    def test_native_owners_reject_guard_and_wrong_link_endpoint(self):
        want=M.predict(fixture())
        for event in want['stores']:
            self.assertTrue(M.write_allowed(int(event['pc'],16),event['address'],event['bytes']))
        for event in want['reads']:
            self.assertTrue(M.read_allowed(int(event['pc'],16),event['address'],event['bytes']))
        self.assertFalse(M.write_allowed(M.ENTRY,M.FRAME-4,4))
        self.assertFalse(M.write_allowed(0x20D782C,M.ARC+32,4))
        self.assertFalse(M.write_allowed(0x20D7800,0,4))
        self.assertFalse(M.read_allowed(0x20D787C,M.ARC+84,4))
        self.assertFalse(M.read_allowed(M.DISABLE,M.FILE,4))

    def test_restore_irq_retains_original_i_bit_in_r2(self):
        for irq in(0,0x80):
            r=[0]*15+[0x2000009F];r[0]=irq;trace=[]
            M.native_irq(r,lambda pc:trace.append((pc,list(r))),M.RESTORE)
            self.assertEqual(r[1:3],[0x2000009F,0x2000001F|irq]);self.assertEqual(r[15],0x2000001F|irq)
            self.assertEqual(r[0],0x80);self.assertEqual(len(trace),6)


if __name__=='__main__':unittest.main()
