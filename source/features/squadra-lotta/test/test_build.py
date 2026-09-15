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

    def test_registro_prenota_blocco_e_scala_libero(self):
        path = REPO / 'source/docs/arm9-reserve-map.json'
        m = json.loads(path.read_text())
        squadra_lotta._controlla_mappa(m)
        overlap = copy.deepcopy(m)
        free = next(b for b in overlap['blocchi'] if b['nome'] == 'libero.1.2.finale')
        free['base'] = '0x023dbe00'
        free['bytes'] += 256
        with self.assertRaises(Rifiuto):
            squadra_lotta._controlla_mappa(overlap)


if __name__ == '__main__':
    unittest.main()
