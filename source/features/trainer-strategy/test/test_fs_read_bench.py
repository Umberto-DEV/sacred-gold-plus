"""Portable boundary, input inversion and independent dataflow checks; no CPU."""
import copy, importlib.util, struct, unittest
from pathlib import Path


s=importlib.util.spec_from_file_location('read_portable_bench',Path(__file__).with_name('fs_read_bench.py'))
B=importlib.util.module_from_spec(s);s.loader.exec_module(B)


def fixture():
    frame=bytearray([0x39])*240
    struct.pack_into('<4I',frame,B.FILE-B.FRAME+32,140,0x1000,0x1100,0x1010)
    struct.pack_into('<I',frame,B.FILE-B.FRAME+12,16)
    entry=[B.FILE,B.DEST,16,0x123,0x2000001,310,0x2200000,0,0x88888801,0x99999902,
        0xAAAAAA03,0xBBBBBB04,0,B.TOP-136,0x2007403,0x6000001F]
    return dict(ordinal=6,entry=entry,frame=frame.hex(),destination_before='A5'*16,payload='12'*16)


class Portable(unittest.TestCase):
    def test_parent_coverage_cannot_be_four_copies_of_one_valid_cell(self):
        path=Path(__file__).resolve().parents[1]/'tools/attribuisci_fs_read.py'
        spec=importlib.util.spec_from_file_location('read_parent_cells',path)
        Z=importlib.util.module_from_spec(spec);spec.loader.exec_module(Z)
        rows=[dict(plus=p,seed=s) for p in (0,1) for s in (0x12345678,0x12345679)]
        Z.require_parent_cells(rows)
        for bad in ([rows[2]]*4,rows[:-1],rows[::-1]):
            with self.assertRaises(ValueError):Z.require_parent_cells(bad)

    def test_native_sync_argument_and_tailcall_abi_are_distinct_from_parent_model(self):
        f=fixture();p=B.predict(f)
        self.assertEqual(len(p['stores']),10);self.assertEqual(p['returned'][0],16)
        self.assertEqual(p['returned'][3],0);self.assertEqual(p['returned'][4:12],f['entry'][4:12])
        self.assertEqual(p['returned'][12:15],[B.CORE,B.TOP-136,0x20D8168])
        self.assertEqual(p['returned'][15],0x2000003F)
        file=bytes.fromhex(p['frame_after'])[B.FILE-B.FRAME:B.FILE-B.FRAME+72]
        self.assertEqual(struct.unpack_from('<I',file,12)[0],20)
        self.assertEqual(struct.unpack_from('<3I',file,48),(B.DEST,16,16))

    def test_wait_false_and_send_false_separate_bytes_from_native_return(self):
        f=fixture();a=B.predict(f);b=B.predict(f,wait_value=0);c=B.predict(f,send_value=0)
        self.assertEqual(b['returned'][0],0xFFFFFFFF);self.assertEqual(b['returned'][15],0x6000003F)
        self.assertEqual(a['frame_after'],b['frame_after']);self.assertEqual(a['frame_after'],c['frame_after'])
        self.assertEqual(a['returned'],c['returned']);self.assertEqual(len(a['services']),2)

    def test_full_register_width_and_finite_types_cannot_be_masked(self):
        for value in (-1,True,0x10000001F):
            f=fixture();f['entry'][15]=value
            with self.subTest(value=value),self.assertRaises(ValueError):B.predict(f)
        for value in (True,1.0,-1,3):
            with self.subTest(wait=value),self.assertRaises(ValueError):B.predict(fixture(),wait_value=value)

    def test_output_and_saved_frame_overlap_and_geometry_rejected(self):
        for mode in ('file','saved','short','negative','thumb'):
            f=fixture()
            if mode=='file':f['entry'][1]=B.FILE
            elif mode=='saved':f['entry'][1]=f['entry'][13]-4
            elif mode=='short':f['destination_before']='AA'
            elif mode=='negative':f['entry'][2]=0xFFFFFFFF
            else:f['entry'][15]|=0x20
            with self.subTest(mode=mode),self.assertRaises(ValueError):B.predict(f)

    def test_initial_nzcv_overwritten_before_control_and_clobber_preserves_saved(self):
        f=fixture();normal=B.predict(f)
        for flags in range(16):
            g=copy.deepcopy(f);g['entry'][15]=(flags<<28)|0x1F
            p=B.predict(g);self.assertEqual(p['returned'],normal['returned'])
            self.assertEqual(p['frame_after'],normal['frame_after'])
        p=B.predict(f,clobber=True)
        self.assertEqual(p['returned'][4:12],f['entry'][4:12]);self.assertEqual(p['returned'][3],0)
        self.assertEqual(p['returned'][12],0xA500000C)


if __name__=='__main__':unittest.main()
