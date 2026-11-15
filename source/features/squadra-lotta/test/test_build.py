"""Contratti del bundle e della prenotazione della Squadra in battaglia."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / 'source'))
from sgp12.blocchi import squadra_lotta
from sgp12.rom import Rifiuto

BUILD = REPO / 'source/sgp12/build/squadra_lotta'


def aggiorna_somme(folder):
    names = ('blob.bin', 'canarino.bin', 'manifesto.json', 'origine.json')
    (folder / 'SHA256SUMS').write_text(''.join(
        hashlib.sha256((folder / name).read_bytes()).hexdigest() + '  ' + name + '\n'
        for name in names))


class TestBuild(unittest.TestCase):
    def test_bundle_spedito_conforme(self):
        man, block = squadra_lotta._carica_build(BUILD)
        self.assertEqual(len(block), 256)
        self.assertLessEqual(man['blob']['byte'], 240)

    def test_impronte_mappe_descrivono_intero_blob(self):
        man = json.loads((BUILD / 'manifesto.json').read_text())
        for name in ('source/docs/arm9-reserve-map.json',
                     'source/sgp12/build/riserva/MAPPA-RISERVA-ARM9.json'):
            m = json.loads((REPO / name).read_text())
            block = next(b for b in m['blocchi'] if b['nome'] == 'sgp.squadra_lotta')
            self.assertEqual(block['impronte_parziali'][0], {
                'offset': 0, 'bytes': man['blob']['byte'], 'sha256': man['blob']['sha256']})

    def test_blob_manomesso_rifiutato(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'build'
            shutil.copytree(BUILD, folder)
            p = folder / 'blob.bin'
            data = bytearray(p.read_bytes())
            data[0] ^= 1
            p.write_bytes(data)
            with self.assertRaises(Rifiuto):
                squadra_lotta._carica_build(folder)

    def test_simbolo_fuori_blocco_rifiutato(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'build'
            shutil.copytree(BUILD, folder)
            p = folder / 'manifesto.json'
            man = json.loads(p.read_text())
            man['simboli']['sgp_squadra_attr_hook'] = '0x023dc001'
            p.write_text(json.dumps(man))
            aggiorna_somme(folder)
            with self.assertRaises(Rifiuto):
                squadra_lotta._carica_build(folder)

    def test_provenienza_obsoleta_o_sorgente_imprevista_rifiutata(self):
        for mutation in ('hash_obsoleto', 'percorso_imprevisto'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp) / 'build'
                shutil.copytree(BUILD, folder)
                p = folder / 'origine.json'
                origin = json.loads(p.read_text())
                source = next(iter(origin['sorgenti']))
                if mutation == 'hash_obsoleto':
                    origin['sorgenti'][source] = '0' * 64
                else:
                    origin['sorgenti']['../imprevisto.c'] = origin['sorgenti'].pop(source)
                p.write_text(json.dumps(origin))
                aggiorna_somme(folder)
                with self.assertRaises(Rifiuto):
                    squadra_lotta._carica_build(folder)

    def test_elenco_somme_manomesso_rifiutato(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / 'build'
            shutil.copytree(BUILD, folder)
            (folder / 'SHA256SUMS').write_text('')
            with self.assertRaises(Rifiuto):
                squadra_lotta._carica_build(folder)

    def test_registro_prenota_blocco_e_rifiuta_sovrapposizione_sintetica(self):
        path = REPO / 'source/docs/arm9-reserve-map.json'
        m = json.loads(path.read_text())
        squadra_lotta._controlla_mappa(m)
        overlap = copy.deepcopy(m)
        overlap['blocchi'].append({
            'nome': 'mutante.libero', 'base': '0x023dbe00', 'bytes': 256})
        with self.assertRaises(Rifiuto):
            squadra_lotta._controlla_mappa(overlap)

class TestExactAttribution(unittest.TestCase):
    """Readback must reject corrupt installed bytes and noncontiguous loader data."""
    def reader(self):
        import importlib.util
        path = REPO / 'source/features/squadra-lotta/tools/attribuisci.py'
        self.assertTrue(path.is_file(), 'exact-image attribution reader is missing')
        spec = importlib.util.spec_from_file_location('squadra_attribution', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_installed_block_rejects_code_padding_canary_and_length(self):
        reader = self.reader()
        block = ((BUILD / 'blob.bin').read_bytes() + bytes(40)
                 + (BUILD / 'canarino.bin').read_bytes())
        self.assertEqual(reader.check_block(block, BUILD)['bytes'], 256)
        for at in (0, 199, 200, 239, 240, 255):
            bad = bytearray(block); bad[at] ^= 1
            with self.subTest(at=at), self.assertRaises(ValueError):
                reader.check_block(bad, BUILD)
        with self.assertRaises(ValueError):
            reader.check_block(block[:-1], BUILD)

    def test_move_loader_data_requires_contiguous_records(self):
        reader = self.reader()
        import ndspy.narc
        members = [bytes([i % 256]) * 16 for i in range(471)]
        raw = bytes(ndspy.narc.NARC.fromFilesAndNames(members).save())
        start, table = reader.move_table(raw)
        self.assertEqual(table, b''.join(members[:468]))
        self.assertEqual(raw[start:start+7488], table)
        # An aligned gap preserves per-member values but breaks LoadMoveTbl.
        gap = ndspy.narc.NARC.fromFilesAndNames([members[0] + bytes(4), *members[1:]])
        with self.assertRaises(ValueError):
            reader.move_table(bytes(gap.save()))
        bad = bytearray(raw)
        struct = __import__('struct')
        struct.pack_into('<I', bad, 0x1C + 8 * 200, 200 * 16 + 4)
        with self.assertRaises(ValueError):
            reader.move_table(bad)

    def test_wrong_thumb_branch_is_rejected(self):
        reader = self.reader()
        site = 0x0221D3DE
        with self.assertRaises(ValueError):
            reader.check_call(site, bytes(4), 0x023DBEBE)
        with self.assertRaises(ValueError):
            reader.check_call(site, bytes.fromhex('55f6a5ff'), 0x023DBEBE)

    def test_exact_identity_rejects_wrong_language_or_revision(self):
        reader = self.reader()
        for language in ('EN', 'IT'):
            with self.assertRaises(ValueError):
                reader.check_identity(bytes(512), language)

class TestPartyExecutionReadback(unittest.TestCase):
    def test_trace_rejects_false_values_broken_ancestry_and_wrong_context(self):
        import importlib.util
        path = REPO / 'source/features/squadra-lotta/tools/rileggi_esecuzione.py'
        self.assertTrue(path.is_file(), 'Party execution verifier is missing')
        spec = importlib.util.spec_from_file_location('party_execution', path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        # Authored fixture: one occupied move, five callers, each with cache and
        # record children. Values and expected stack frames are hand specified.
        table = bytearray(7488); table[16+2:16+7] = bytes((2,40,10,85,20))
        ram = bytearray(4194304)
        app,args,bs,ctx = 0x022D0000,0x022D1000,0x022D2000,0x022E0000
        for a,v in ((app,args),(args+8,bs),(bs+0x30,ctx)):
            ram[a-0x02000000:a-0x02000000+4]=v.to_bytes(4,'little')
        ram[ctx+0x3DE-0x02000000:ctx+0x3DE-0x02000000+7488]=table
        events=[]
        def event(site,parent,sp,lr,arg0,arg1,arg2,result,start,end):
            events.append(dict(event=len(events),site=site,parent=parent,sp=sp,lr=lr,
                arg0=arg0,arg1=arg1,arg2=arg2,result=result,entry_order=start,exit_order=end,
                first_frame=1,last_frame=1,complete=1,mode=31,entry_cpsr=63,exit_cpsr=63))
        event(0x0221D184,0xFFFFFFFF,0x027E3000,0x0221C07F,app,0,0,1,1,32)
        for i,(site,shim,core,attr,value) in enumerate((
            (0x0221D3DE,0x023DBEBE,0x023DBE7C,0,20),
            (0x0221D3E8,0x023DBEB4,0x023DBE00,3,10),
            (0x0221D3F2,0x023DBEB4,0x023DBE00,1,2),
            (0x0221D3FC,0x023DBEB4,0x023DBE00,4,85),
            (0x0221D406,0x023DBEB4,0x023DBE00,2,40))):
            order=2+i*6; w=len(events)
            event(shim,0,0x027E2FD8,site+5,1,attr,0,value,order,order+5)
            event(core,w,0x027E2FD0,shim+9,1,attr,app,value,order+1,order+4)
            event(0x023DBE2C,w+1,0x027E2FC0,core+(13 if core==0x023DBE7C else 21),1,app,0,ctx+0x3DE+16,order+2,order+3)
        self.assertEqual(module.verify(events,ram,table)['cached_getters'],5)
        # These break executable/data relationships, not report text.
        for index,key,value in ((1,'lr',0x02000001),(2,'arg2',0),(3,'result',ctx+0x3E0+16),
                                (2,'result',255),(3,'parent',0),(1,'sp',0x027E2FDC),
                                (1,'complete',0),(1,'exit_order',1)):
            bad=copy.deepcopy(events);bad[index][key]=value
            with self.subTest(index=index,key=key),self.assertRaises(ValueError):
                module.verify(bad,ram,table)
        bad_ram=bytearray(ram);bad_ram[ctx+0x3DE-0x02000000+16+5]^=1
        with self.assertRaises(ValueError):module.verify(events,bad_ram,table)


if __name__ == '__main__':
    unittest.main()
