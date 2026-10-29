"""ROM-free compiler/config checks and opt-in private cartridge installation."""
from pathlib import Path
import json,struct,sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from sgp13 import shiny
class InstallTests(unittest.TestCase):
    def test_config_requires_owner_capabilities_and_exact_species_count(self):
        self.assertTrue(hasattr(shiny,'configuration'),'Guarded configuration is not implemented')
        with self.assertRaises(ValueError):shiny.configuration('EN',{}, {}, {}, {}, {})
    def config_for(self, species, language='EN'):
        # Exercise the serializer with real JSON input; native address capabilities
        # remain distinct so accidental movement of the public prefix is visible.
        groups=(('training_shiny_access','training_shiny_bind','training_read'),
                ('sgp_ui_frame','opz_apri','opz_chiudi','opz_disegna'),
                tuple('sgp_shiny_'+n for n in ('snapshot','candidate','apply')),
                ('sgp_shiny_capture','sgp_shiny_dispatch'),
                tuple('sgp_shiny_'+n for n in ('valid','denominator','select','complete','draw','transform')))
        tables=[{name:0x023E0001+0x100*i+4*j for j,name in enumerate(group)} for i,group in enumerate(groups)]
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=root/'sgp13/data';data.mkdir(parents=True)
            (data/'species-changes.json').write_text(json.dumps({'changes':[{'species':n} for n in species]}))
            with patch.object(shiny,'ROOT',root):return shiny.configuration(language,*tables)
    def test_bitmap_serializes_more_than_17_and_boundary_ids_canonically(self):
        ids=list(range(1,20))+[31,32,63,64,127,128,255,256,487,488,493]
        cfg=self.config_for(ids)
        self.assertEqual(len(cfg),152)
        self.assertEqual(struct.unpack_from('<IHH',cfg),(0x594E4853,2,152))
        self.assertEqual(struct.unpack_from('<HH',cfg,84),(30,0))
        self.assertEqual([i for i in range(512) if cfg[88+i//8]&(1<<(i%8))],ids)
        self.assertEqual(self.config_for(list(reversed(ids))),cfg)
        self.assertEqual(cfg[8:84],struct.pack('<19I',
            0x023E0201,0x023E0205,0x023E0209,
            0x023E0401,0x023E0405,0x023E0409,0x023E040D,0x023E0411,0x023E0415,
            0x023E0001,0x023E0005,0x023E0009,0x023E0301,0x023E0305,
            0x023E0101,0x023E0105,0x023E0109,0x023E010D,0))
        italian=self.config_for(ids,'IT');self.assertEqual(italian[:80],cfg[:80]);self.assertEqual(italian[84:],cfg[84:])
        self.assertEqual(struct.unpack_from('<I',italian,80),(1,))
    def test_bitmap_accepts_single_high_id_and_all_493_species(self):
        single=self.config_for([493]);self.assertEqual(single[88:],bytes(61)+b'\x20\0\0')
        full=self.config_for(list(range(1,494)))
        self.assertEqual(struct.unpack_from('<HH',full,84),(493,0))
        self.assertEqual(full[88:],b'\xfe'+b'\xff'*60+b'\x3f\0\0')
    def test_bitmap_rejects_empty_duplicates_and_non_species_ids(self):
        for ids in ([],[1,1],[0],[494],[-1],[True],['25'],[1.5],list(range(1,494))+[493]):
            with self.subTest(ids=ids[:4]),self.assertRaisesRegex(ValueError,'species'):
                self.config_for(ids)
    def test_compartments_are_bounded_and_self_contained(self):
        with tempfile.TemporaryDirectory() as tmp:
            for part in ('native','search'):
                blob,sym=shiny.compile_native(tmp,part)
                self.assertLessEqual(len(blob),shiny.LIMITS[part]);self.assertTrue(sym)
    def test_hook_contract_includes_outer_failure_and_existing_plus_guard(self):
        self.assertTrue(hasattr(shiny,'HOOKS'),'Native guarded hook map is not implemented')
        self.assertEqual(shiny.HOOKS['overlay2'][0x02247D96],'sgp_shiny_regular')
        self.assertNotIn(0x02247D3A,shiny.HOOKS['overlay2'])
        self.assertEqual(shiny.HOOKS['overlay1'][0x021FC450],'sgp_shiny_scent_cleanup')

class CartridgeInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os,json
        folder=os.environ.get('SGP_SHINY_PRE_NATIVE_DIR')
        if not folder:raise unittest.SkipTest('set SGP_SHINY_PRE_NATIVE_DIR for private composed cartridge checks')
        cls.directory=Path(folder);cls.temp=tempfile.TemporaryDirectory()
        cls.inputs={}
        for lang in ('EN','IT'):
            receipt=json.loads((cls.directory/f'pre-native-{lang}.json').read_text())
            stages={r['stage']:r['details'] for r in receipt['stages']}
            cls.inputs[lang]=((cls.directory/f'pre-native-{lang}.nds').read_bytes(),stages['training']['symbols'],stages['plus-ui']['symbols'])
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_install_readback_and_mutation_rejections_both_languages(self):
        from sgp12.rom import Arm9
        for lang,(before,training,legacy) in self.inputs.items():
            with self.subTest(language=lang):
                work=Path(self.temp.name)/lang
                after,receipt=shiny.install(before,lang,training,legacy,work)
                self.assertTrue(receipt['verified']);self.assertTrue(shiny.verify(after,lang,receipt,work)['verified'])
                path=work/'mutant.nds';path.write_bytes(before);arm=Arm9(path)
                changed=bytearray(before);changed[arm.off(0x0206DE38)]^=1
                with self.assertRaisesRegex(ValueError,'preimage'):shiny.install(bytes(changed),lang,training,legacy,work)
                changed=bytearray(before);changed[arm.off(0x023C9100)]=1
                with self.assertRaisesRegex(ValueError,'occupied'):shiny.install(bytes(changed),lang,training,legacy,work)
                path.write_bytes(after);arm=Arm9(path);changed=bytearray(after);changed[arm.off(0x023C9100)]^=1
                with self.assertRaisesRegex(ValueError,'payload'):shiny.verify(bytes(changed),lang,receipt,work)
                changed=bytearray(after);changed[arm.off(0x0206DE38)]^=1
                with self.assertRaisesRegex(ValueError,'ABI'):shiny.verify(bytes(changed),lang,receipt,work)
                changed=bytearray(after);changed[arm.off(0x02000000)]^=1
                with self.assertRaisesRegex(ValueError,'unowned'):shiny.readback(before,bytes(changed),lang,training,legacy,work)

if __name__=='__main__':unittest.main()
