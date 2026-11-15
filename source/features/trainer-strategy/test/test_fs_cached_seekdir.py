"""Synthetic, ROM-free source-oracle checks; no Unicorn guest required."""
from pathlib import Path
import importlib.util
import struct
import unittest


def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def fixture(B,own_id=0,precompleted=False):
    F,R=B.F,B.R
    spans=[(R.ARC,92),(R.FILE-16,104),(R.TOP-128,128),(R.FNT,16),(0x20d6c80,4)]
    pages={}
    for address,size in spans:
        for a in range(address&~4095,(address+size+4095)&~4095,4096):pages[a]=bytearray(b'\xa5'*4096)
    file=bytearray(72)
    for off,value in((8,R.ARC),(12,45),(16,4),(20,2),(48,R.ARC)):struct.pack_into('<I',file,off,value)
    struct.pack_into('<H',file,52,own_id);file[32:48]=b'\xa5'*16
    if precompleted:file[32:48]=struct.pack('<IHHII',R.ARC,0,129,R.FNT+368,46)
    F.put(pages,R.FILE-16,b'\xd3'*16+file+b'\xd3'*16)
    arc=bytearray(92)
    for off,value in((28,7),(52,R.FNT),(80,0x20d7484)):struct.pack_into('<I',arc,off,value)
    F.put(pages,R.ARC,arc);F.put(pages,R.FNT,struct.pack('<IHHIHH',368,129,46,431,129,0xf000))
    F.put(pages,0x20d6c80,struct.pack('<I',0xfff))
    return dict(own_id=own_id,precompleted_prop=precompleted,entry_pc=F.ENTRY,
        entry_regs=[R.FILE]+[0xB0000000+i*0x010101 for i in range(1,13)]+[R.TOP,F.RETURN,0x6000001f],
        pages={a:bytes(b)for a,b in pages.items()})


class OracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.B=load(Path(__file__).with_name('fs_cached_seekdir_bench.py'),'cached_seekdir_test_bench')

    def test_complete_root_path_and_raw_parent_count(self):
        B=self.B;f=fixture(B);p=B.predict(f)
        self.assertEqual((len(p['flow']),len(p['stores']),len(p['reads']),p['native_peak']),(100,27,35,72))
        self.assertEqual(len({x['pc']for x in p['flow']}),96)
        self.assertEqual(B.F.read(p['pages'],B.R.FILE+32,16),struct.pack('<IHHII',B.R.ARC,0,129,B.R.FNT+368,46))
        self.assertEqual(B.F.read(p['pages'],B.R.ARC,92),B.F.read(f['pages'],B.R.ARC,92))
        self.assertEqual(B.F.read(p['pages'],B.R.TOP-128,56),b'\xa5'*56)

    def test_pop_pc_keeps_residual_lr_at_every_postcopy_boundary(self):
        B=self.B;p=B.predict(fixture(B))
        for pc in (0x20d7494,0x20d6ad0,0x20d6c24):
            self.assertEqual(next(x['regs'][14]for x in p['flow']if x['pc']==pc),0x20d7494)
        self.assertEqual(p['returned'][14],0x20d7494)
        self.assertEqual(p['returned'][13],B.R.TOP)
        self.assertEqual(p['returned'][4:12],fixture(B)['entry_regs'][4:12])

    def test_valid_directory1_masks_parent_without_normalizing_root(self):
        B=self.B;p=B.predict(fixture(B,own_id=1))
        self.assertEqual(B.F.read(p['pages'],B.R.FILE+32,16),struct.pack('<IHHII',B.R.ARC,1,129,B.R.FNT+431,0))
        self.assertEqual(p['returned'][1],0xf000)

    def test_completed_initial_property_converges_but_four_native_preimages_differ(self):
        B=self.B;p=B.predict(fixture(B));q=B.predict(fixture(B,precompleted=True))
        for key in ('flow','reads','returned','pages'):self.assertEqual(p[key],q[key],key)
        diff=[i for i,(a,b)in enumerate(zip(p['stores'],q['stores']))if a!=b]
        self.assertEqual(diff,[21,22,23,26])
        for i in diff:
            self.assertNotEqual(p['stores'][i]['before'],q['stores'][i]['before'])
            self.assertEqual({k:v for k,v in p['stores'][i].items()if k!='before'},
                             {k:v for k,v in q['stores'][i].items()if k!='before'})

    def test_nonfresh_index_or_position_is_rejected_before_conditional_read(self):
        B=self.B
        for offset,n in ((54,2),(56,4)):
            f=fixture(B);pages={a:bytearray(b)for a,b in f['pages'].items()}
            B.F.put(pages,B.R.FILE+offset,(1).to_bytes(n,'little'));f['pages']=pages
            with self.subTest(offset=offset),self.assertRaisesRegex(ValueError,'fresh directory'):
                B.predict(f)

    def test_wrong_callback_and_bool_input_fail_before_prediction(self):
        B=self.B;f=fixture(B);pages={a:bytearray(b)for a,b in f['pages'].items()}
        B.F.put(pages,B.R.ARC+80,struct.pack('<I',0x20d84c4));f['pages']=pages
        with self.assertRaisesRegex(ValueError,'callback'):B.predict(f)
        f=fixture(B);f['own_id']=True
        with self.assertRaisesRegex(ValueError,'typed'):B.predict(f)


if __name__=='__main__':unittest.main()
