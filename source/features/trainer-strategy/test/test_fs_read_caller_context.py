"""Finite post-Read ABI contexts; no ROM input or guest CPU required."""
from pathlib import Path
import importlib.util,unittest,os,json,gzip
s=importlib.util.spec_from_file_location('read_caller_context',Path(__file__).resolve().parents[1]/'tools/attribuisci_fs_read_chiamante.py')
Z=importlib.util.module_from_spec(s);s.loader.exec_module(Z)
DATA=dict(fs_geometry=dict(file_id=140,top=0x1093800,bottom=0x109645C),pp_reader={'11':dict(oracle=dict(
    btaf=16,btnf=3796,btnf_bytes=16,member_bytes=16,member_archive_offset=8780))})


class Context(unittest.TestCase):
    def test_seek_after_read_preserves_the_new_native_ip(self):
        entry=[0x23BEE50,20,0,0,16,310,0x2200080,0,0x88888801,0x99999902,
               0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x2007373,0x4000001F]
        try:r=Z.expected_seek(dict(pp_clobber=False),DATA,1,entry)
        except ValueError as error:self.fail('Valid post-Read Seek context rejected: '+str(error))
        self.assertEqual(r['returned'],[1,0x1093814,0x109645C,0,16,310,0x2200080,0,
            0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x2007373,0x8000003F])

    def test_close_starts_with_read_irq_residuals_and_keeps_its_own_final_lr(self):
        r=Z.expected_close(dict(close_value=1,pp_clobber=False),DATA)
        self.assertEqual(r['entry'],[0x23BEE50,0x6000009F,0x6000001F,0,28,310,3796,16,
            0x88888801,0x99999902,0xAAAAAA03,0xBBBBBB04,0x20D8104,0x23BEE38,0x2007409,0x2000001F])
        self.assertEqual(r['returned'][2],0x6000001F);self.assertEqual(r['returned'][14],0x20D82D0)


@unittest.skipUnless(os.environ.get('SGP_FS_SEEK_REPORT_DIR'),'requires private qualified Seek report')
class Prefix(unittest.TestCase):
    def test_all_native_prefix_writes_remain_identical_before_first_read(self):
        report=json.loads(gzip.decompress((Path(os.environ['SGP_FS_SEEK_REPORT_DIR'])/'fs-seek-EN.json.gz').read_bytes()))
        actual=report['positives'][0]['pp_reader']['native_writes'][:46]
        self.assertEqual(Z.native_prefix(),actual)


if __name__=='__main__':unittest.main()
