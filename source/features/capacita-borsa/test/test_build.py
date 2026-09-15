import hashlib,importlib.util,json,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'source'))
from sgp12.blocchi import capacita_borsa as cap
from sgp12.rom import Rifiuto
BUILD=ROOT/'source/sgp12/build/capacita_borsa'
class BuildTests(unittest.TestCase):
    def test_shipped_bundle_and_reserve(self):
        m,b=cap._carica_build(BUILD)
        for name in ('source/docs/arm9-reserve-map.json','source/sgp12/build/riserva/MAPPA-RISERVA-ARM9.json'):
            blocks=json.loads((ROOT/name).read_text())['blocchi']
            own=next(x for x in blocks if x['nome']=='sgp.capacita_borsa')
            self.assertEqual(int(own['base'],16),0x23dbf00);self.assertEqual(own['bytes'],0x2c00)
            self.assertEqual(own['impronte_parziali'][0],{'offset':0,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
            self.assertFalse(any(int(x['base'],16)<0x23deb00 and int(x['base'],16)+x['bytes']>0x23dbf00 for x in blocks if x is not own))
    def test_recompile_produces_shipped_code_and_symbols(self):
        path=ROOT/'source/features/capacita-borsa/tools/compila.py'
        spec=importlib.util.spec_from_file_location('_capacity_compile',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            m=mod.compila(td);original=json.loads((BUILD/'manifesto.json').read_text())
            self.assertEqual((Path(td)/'blob.bin').read_bytes(),(BUILD/'blob.bin').read_bytes())
            self.assertEqual(m['simboli'],original['simboli'])
    def test_build_tampering_is_rejected(self):
        for name in ('blob.bin','SHA256SUMS','origine.json','manifesto.json'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as td:
                d=Path(td)/'build';shutil.copytree(BUILD,d)
                p=d/name;b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
                with self.assertRaises(Rifiuto):cap._carica_build(d)
    def test_out_of_range_symbol_with_updated_checksum_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'build';shutil.copytree(BUILD,d)
            p=d/'manifesto.json';m=json.loads(p.read_text());m['simboli']['sgp_cap_get']='0x02000001';p.write_text(json.dumps(m))
            (d/'SHA256SUMS').write_text(''.join(hashlib.sha256((d/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in ('blob.bin','manifesto.json','origine.json')))
            with self.assertRaises(Rifiuto):cap._carica_build(d)
