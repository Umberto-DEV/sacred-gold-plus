"""Finite Find wrapper source-oracle tests with synthetic frames, no ROM/CPU."""
from pathlib import Path
import importlib.util,struct,unittest
s=importlib.util.spec_from_file_location('find_profile',Path(__file__).with_name('fs_find_bench.py'))
M=importlib.util.module_from_spec(s);s.loader.exec_module(M)


def fixture():
    entry=[M.DIR,M.PATH,M.ID,0,M.PATH,M.ID,0x2200080,0,0x88888801,0x99999902,
           0xAAAAAA03,0xBBBBBB04,0,M.DIR,0x20D81AC,0x1F]
    frame=bytearray(b'\x39'*280)
    struct.pack_into('<3I',frame,M.DIR-M.FRAME+8,0,0,14)
    return dict(entry=entry,frame=frame.hex(),path='a/0/1/1',current_dir=struct.pack('<3I',M.ARC,0,0).hex(),
                file_id=140,destination_before=bytes(frame[M.ID-M.FRAME:M.ID-M.FRAME+8]).hex())


class FindSource(unittest.TestCase):
    def test_push_frame_and_native_aggregate_reach_send4(self):
        f=fixture();r=M.predict(f);event=r['services'][0]
        self.assertEqual(event['entry'],[M.DIR,4,0,M.DIR+48,1,0,M.ID,M.PATH,M.DIR,
            0x99999902,0xAAAAAA03,0xBBBBBB04,0,M.DIR-40,0x20D80F8,0x6000001F])
        self.assertEqual((len(r['flow']),len(r['stores']),len(r['reads'])),(47,17,18))
        self.assertEqual(r['returned'][3:12],f['entry'][3:12]);self.assertEqual(r['returned'][13],M.DIR)
        self.assertEqual(r['returned'][14],0x20D80F8)

    def test_false_send_preserves_output_but_returns_false(self):
        f=fixture();a=M.predict(f);b=M.predict(f,send_value=0)
        self.assertEqual(a['frame_after'],b['frame_after']);self.assertEqual(b['returned'][0],0)
        self.assertEqual(b['returned'][15],0x6000001F)

    def test_truthy2_is_not_normalized_and_clobber_cannot_escape_saved_r3(self):
        f=fixture();r=M.predict(f,send_value=2,clobber=True)
        self.assertEqual(r['returned'][0:4],[2,0xA5000001,0xA5000002,0])
        self.assertEqual(r['returned'][12],0xA500000C);self.assertEqual(r['returned'][15],0xA000001F)
        self.assertEqual(r['returned'][4:12],f['entry'][4:12])

    def test_data_reads_do_not_admit_the_archive_or_unscanned_path_tail(self):
        self.assertTrue(M.read_allowed(0x20D8014,M.CURRENT+8,4))
        self.assertFalse(M.read_allowed(0x20D8014,M.ARC,4))
        self.assertFalse(M.read_allowed(0x20D8020,M.PATH+2,1))
        self.assertFalse(M.read_allowed(0x20D800C,M.LITERAL,2))

    def test_native_stores_do_not_admit_model_output_or_command_fields(self):
        self.assertTrue(M.write_allowed(M.ENTRY,M.DIR-28,4))
        self.assertTrue(M.write_allowed(0x20D80C8,M.DIR+56,4))
        self.assertFalse(M.write_allowed(0x20D80C8,M.ID,4))
        self.assertFalse(M.write_allowed(0x20D80D4,M.DIR+16,4))
        self.assertFalse(M.write_allowed(M.ENTRY,M.DIR-28,2))

    def test_fnt_counterexample_cannot_reuse_the_expected_id(self):
        from ndspy.fnt import Folder,save
        def table(file_id):
            node=Folder(files=['1'],firstID=file_id)
            for name in('1','0','a'):node=Folder(folders=[(name,node)])
            return bytes(save(node))
        self.assertEqual(M.require_fnt(fixture(),table(140)),140)
        with self.assertRaises(ValueError):M.require_fnt(fixture(),table(141))

    def test_boolean_registers_and_nonroot_state_are_rejected(self):
        f=fixture();f['entry'][3]=False
        with self.assertRaises(ValueError):M.predict(f)
        f=fixture();f['current_dir']=struct.pack('<3I',M.ARC,1,0).hex()
        with self.assertRaises(ValueError):M.predict(f)


if __name__=='__main__':unittest.main()
