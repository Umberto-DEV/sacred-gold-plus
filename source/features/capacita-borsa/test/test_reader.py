import os,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'source'))
from sgp12.blocchi import capacita_borsa as cap
from sgp12.rom import Arm9,Rom,Rifiuto
from sgp12.blz import blz_comprimi
@unittest.skipUnless(os.environ.get('SGP_CAPACITY_BEFORE') and os.environ.get('SGP_CAPACITY_ROM'),'requires private before/after Bag ROMs')
class ReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=Path(os.environ['SGP_CAPACITY_BEFORE']).read_bytes();cls.after=Path(os.environ['SGP_CAPACITY_ROM']).read_bytes()
        cls.build=os.environ.get('SGP_CAPACITY_BUILD',str(ROOT/'source/sgp12/build/capacita_borsa'))
    def test_independent_reader_accepts_patch(self):
        self.assertEqual(cap.rileggi(self.before,self.after,self.build)['esito'],'VERDE')
    def test_header_code_abi_and_native_save_size_mutants_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'rom.nds';p.write_bytes(self.after);a=Arm9(p)
            for off in (0x100,a.off(0x2078240),a.off(0x2077b5c),a.off(0x2078180),a.off(0x23dbf00),a.off(0x23dd700)):
                with self.subTest(offset=off):
                    b=bytearray(self.after);b[off]^=1
                    with self.assertRaises(Rifiuto):cap.rileggi(self.before,b,self.build)
    def test_wrong_last_page_capacity_rejected(self):
        r=Rom(self.after);info,raw,image=r.immagine_overlay(15);v=bytearray(image);v[0x22008b0-info['ram']]=251;v[0x22008c8-info['ram']]=251
        encoded=blz_comprimi(v);f=r.voce_fat(info['file_id']);b=bytearray(self.after)
        self.assertEqual(len(encoded),len(raw));b[f['inizio']:f['fine']]=encoded
        with self.assertRaises(Rifiuto):cap.rileggi(self.before,b,self.build)
