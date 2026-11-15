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


class CurrentCompositionTests(unittest.TestCase):
    def test_exact_current_code_requires_both_source_recipes(self):
        path=ROOT/'source/features/capacita-borsa/tools/attribuisci.py'
        self.assertTrue(path.is_file(),'current component attestor missing')
        spec=importlib.util.spec_from_file_location('current_capacity_attribution',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        base=(BUILD/'blob.bin').read_bytes()
        current,proof=mod.compose_current(base)
        self.assertEqual(len(current),3584)
        self.assertEqual(hashlib.sha256(current).hexdigest(),
                         '88a6736f0cecbc681864ac765c6309ad8480c406f3150fb54b6d1743f3468448')
        changed={i for i,(a,b) in enumerate(zip(base,current)) if a!=b}
        allowed=set(range(0x9B0,0x9B0+28))|set(range(0xD9C,0xD9C+8))
        self.assertEqual(len(changed),30);self.assertTrue(changed<=allowed)
        self.assertEqual(len(proof['patches']),2)
        for offset in (0,0x9B0,0xD9C):
            mutant=bytearray(base);mutant[offset]^=1
            with self.subTest(offset=offset),self.assertRaises(ValueError):mod.compose_current(bytes(mutant))

    def test_attribution_artifact_cannot_be_used_as_installer_build(self):
        path=ROOT/'source/features/capacita-borsa/tools/attribuisci.py'
        spec=importlib.util.spec_from_file_location('current_capacity_bridge',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            mod.write_bridge(BUILD,Path(td))
            with self.assertRaises(Rifiuto):cap._carica_build(td)
            blob=Path(td)/'blob.bin';bad=bytearray(blob.read_bytes());bad[0]^=1;blob.write_bytes(bad)
            with self.assertRaises(ValueError):mod.write_bridge(BUILD,Path(td))

    def test_checked_execution_rejects_loop_clobber_and_foreign_write(self):
        from types import SimpleNamespace
        from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB
        from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR
        path=ROOT/'source/features/capacita-borsa/tools/attribuisci.py'
        spec=importlib.util.spec_from_file_location('current_capacity_oracle',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        # All programs set r0=0. A result-only oracle would accept all four.
        programs=(('return',bytes.fromhex('00207047'),True),
                  ('loop',bytes.fromhex('0020fee7'),False),
                  ('clobber r4',bytes.fromhex('002000247047'),False),
                  ('foreign store',bytes.fromhex('002001490860704700000002'),False))
        for name,code,accepted in programs:
            with self.subTest(name=name):
                uc=Uc(UC_ARCH_ARM,UC_MODE_THUMB);uc.mem_map(0x02000000,0x400000)
                uc.mem_write(0x02000000,code)
                machine=SimpleNamespace(mu=uc,symbols={},errors=0,original_saves=0,writes=[])
                def run():
                    uc.reg_write(UC_ARM_REG_SP,0x023B0000);uc.reg_write(UC_ARM_REG_LR,0x023AF001)
                    uc.emu_start(0x02000001,0x023AF000,count=32)
                    return 0
                if accepted:self.assertEqual(mod.checked(machine,run)[0],0)
                else:
                    with self.assertRaises(ValueError):mod.checked(machine,run)

    def test_in_range_symbol_drift_rejected_even_with_updated_receipt(self):
        path=ROOT/'source/features/capacita-borsa/tools/attribuisci.py'
        spec=importlib.util.spec_from_file_location('current_capacity_symbols',path)
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)/'build';shutil.copytree(BUILD,d)
            p=d/'manifesto.json';m=json.loads(p.read_text());m['simboli']['sgp_cap_original_save']='0x023DBF01'
            p.write_text(json.dumps(m))
            (d/'SHA256SUMS').write_text(''.join(hashlib.sha256((d/n).read_bytes()).hexdigest()+'  '+n+'\n' for n in ('blob.bin','manifesto.json','origine.json')))
            cap._carica_build(d)  # Legacy range-only symbol gate accepts this metadata.
            with self.assertRaisesRegex(ValueError,'symbol/flag drift'):mod.load_baseline(d)
