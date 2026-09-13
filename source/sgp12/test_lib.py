#!/usr/bin/env python3
"""Test della libreria `sgp12` (non delle ROM: quelli sono `verifica.py` +
`verifiche/test_riserva.py`). Copre: roundtrip BLZ, idempotenza (mutante
principale per blocco), offset del chunk, mappa/canarini della riserva, e
(criterio 4, `TestCostruisciIdentico`) che `costruisci.py` da `base-1.1-EN`/
`base-1.1-IT` produca ROM IDENTICHE, sha256 per sha256, a quelle registrate in
`$SGP_ROM_DIR/SHA256SUMS`.

Uso (da dentro `source/`):
    python3 -m unittest sgp12.test_lib -v

(serve ndspy: vedi `source/requirements.txt`.)
"""
import os
import random
import struct
import tempfile
import unittest
from pathlib import Path

from . import blz, chunk, rom as romlib
from .blocchi import (riserva as bloc_riserva, camera as bloc_camera, plus_chunk as bloc_plus,
                      npc as bloc_npc, anim as bloc_anim, opzioni as bloc_opzioni, wifi as bloc_wifi,
                      titolo as bloc_titolo, testi as bloc_testi, guida as bloc_guida)
from . import costruisci as costruisci_mod

# Le ROM non stanno in questo repository. Chi vuole eseguire anche i test
# di classe B (quelli che aprono un file di gioco) indica la propria
# cartella privata con SGP_ROM_DIR; senza, quelli SALTANO e i test di
# classe A (BLZ, chunk, canarini, logica dei blocchi) restano attivi.
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))
BASE_EN = ROM_DIR / "base-1.1-EN.nds"
BASE_IT = ROM_DIR / "base-1.1-IT.nds"
SHA256SUMS = ROM_DIR / "SHA256SUMS"
BUILD_RISERVA = Path(__file__).resolve().parent / "build" / "riserva"
BUILD_DEFAULT = Path(__file__).resolve().parent / "build"
MANIFEST = BUILD_RISERVA / "MAPPA-RISERVA-ARM9.json"


def _dati_casuali(seed, n_max=4000):
    rnd = random.Random(seed)
    n = rnd.randint(1, n_max)
    data = bytearray()
    while len(data) < n:
        if rnd.random() < 0.5 and len(data) > 8:
            start = rnd.randint(0, len(data) - 1)
            length = rnd.randint(1, min(20, len(data) - start))
            data += data[start:start + length]
        else:
            data.append(rnd.randint(0, 255))
    return bytes(data[:n])


class TestBLZ(unittest.TestCase):
    def test_roundtrip_ottimo_e_avido_su_dati_casuali(self):
        for seed in range(30):
            dati = _dati_casuali(seed)
            with self.subTest(seed=seed):
                comp = blz.blz_comprimi_ottimo(dati)
                self.assertEqual(blz.blz_decomprimi(comp), dati)
                comp2 = blz.blz_comprimi(dati)
                self.assertEqual(blz.blz_decomprimi(comp2), dati)

    def test_ottimo_non_e_piu_lungo_dell_avido(self):
        for seed in range(10):
            dati = _dati_casuali(seed, 2000)
            with self.subTest(seed=seed):
                self.assertLessEqual(len(blz.blz_comprimi_ottimo(dati)), len(blz.blz_comprimi(dati)))

    def test_bersaglio_centrato_quando_raggiungibile(self):
        dati = _dati_casuali(1)
        naturale = blz.blz_comprimi_ottimo(dati)
        di_nuovo = blz.blz_comprimi_ottimo(dati, bersaglio=len(naturale))
        self.assertEqual(len(di_nuovo), len(naturale))

    def test_trailer_rifiuta_flusso_troppo_corto(self):
        with self.assertRaises(romlib.Rifiuto):
            blz.blz_decomprimi(b"1234567")


class TestChunk(unittest.TestCase):
    def test_roundtrip_assente(self):
        c = chunk.chunk_assente()
        self.assertTrue(c.valido())
        self.assertEqual(chunk.Chunk.unpack(c.pack()), c)

    def test_roundtrip_footer(self):
        c = chunk.Chunk(plus=1, selvatici=1, anim=1, npc=1, wifi_server=2, picco=42)
        foot = chunk.pack_footer(c.pack(), saveno=5, idx=3)
        self.assertEqual(len(foot), 32)
        self.assertEqual(chunk.unpack_footer(foot), c)

    def test_footer_corrotto_rifiutato(self):
        c = chunk.chunk_assente()
        foot = bytearray(chunk.pack_footer(c.pack(), 1, 0))
        foot[0] ^= 0xFF
        with self.assertRaises(chunk.ChunkNonValido):
            chunk.unpack_footer(bytes(foot))

    def test_invarianti_respingono_campi_fuori_dominio(self):
        c = chunk.Chunk(wifi_server=9)
        self.assertFalse(c.valido())
        self.assertTrue(any("wifi_server" in m for m in c.invarianti()))
        c2 = chunk.Chunk(picco=0)
        self.assertFalse(c2.valido())
        c3 = chunk.Chunk(riservato0=1)
        self.assertFalse(c3.valido())


class TestRiservaCanarino(unittest.TestCase):
    def test_formula_canarino(self):
        from .riserva import canarino
        b = canarino(0xCA5A1000, 8)
        self.assertEqual(len(b), 32)
        self.assertEqual(struct.unpack_from("<I", b, 0)[0], 0xCA5A1000)
        self.assertEqual(struct.unpack_from("<I", b, 28)[0], 0xCA5A1007)


@unittest.skipUnless(BASE_EN.exists(), "classe B: nessuna base-1.1-EN.nds in $SGP_ROM_DIR")
class TestBloccoRiserva(unittest.TestCase):
    """Mutante principale: applicare due volte deve fallire (G0 idempotenza),
    non produrre una seconda riduzione silenziosa."""

    @classmethod
    def setUpClass(cls):
        cls.base = BASE_EN.read_bytes()

    def test_applica_e_rileggi_verde(self):
        out, _ = bloc_riserva.applica(self.base, BUILD_RISERVA, etichetta="EN")
        rep = bloc_riserva.rileggi(self.base, out, BUILD_RISERVA)
        self.assertEqual(rep["verdetto"], "VERDE")

    def test_idempotenza_mutante_doppia_applicazione(self):
        out, _ = bloc_riserva.applica(self.base, BUILD_RISERVA, etichetta="EN")
        with self.assertRaises(romlib.Rifiuto):
            bloc_riserva.applica(out, BUILD_RISERVA, etichetta="EN")

    def test_mutante_preimmagine_alterata_e_rifiutata(self):
        """Se il letterale d'arena non e' quello di una base 1.1, G1 deve
        rifiutare (non scrivere una riserva sopra un layout sconosciuto)."""
        mutata = bytearray(self.base)
        off = None
        from .blocchi.riserva import ARENA_HI_LIT
        with tempfile_arm9(bytes(mutata)) as a:
            off = a.off(ARENA_HI_LIT, 4)
        mutata[off:off + 4] = b"\x00\x00\x00\x00"
        with self.assertRaises(romlib.Rifiuto):
            bloc_riserva.applica(bytes(mutata), BUILD_RISERVA, etichetta="EN")


def tempfile_arm9(dati):
    import contextlib
    import tempfile

    @contextlib.contextmanager
    def _cm():
        with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
            tf.write(dati)
            tf.flush()
            yield romlib.Arm9(tf.name)
    return _cm()


@unittest.skipUnless(BASE_EN.exists(), "manca la ROM base 1.1 EN")
class TestBloccoCamera(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base = BASE_EN.read_bytes()
        cls.dopo_riserva, _ = bloc_riserva.applica(base, BUILD_RISERVA, etichetta="EN")

    def test_applica_e_rileggi_verde(self):
        out, _ = bloc_camera.applica(self.dopo_riserva)
        rep = bloc_camera.rileggi(self.dopo_riserva, out)
        self.assertEqual(rep["esito"], "VERDE")

    def test_mutante_voce_vecchia_persa_rifiutata(self):
        tabella = dict(bloc_camera.CANONICA)
        del tabella[2]  # una delle 16 voci storiche (G5)
        with self.assertRaises(romlib.Rifiuto):
            bloc_camera.applica(self.dopo_riserva, tabella=tabella)

    def test_idempotenza_applicare_due_volte_non_rompe_G0(self):
        out, _ = bloc_camera.applica(self.dopo_riserva)
        out2, log2 = bloc_camera.applica(out)
        self.assertEqual(log2.get("esito"), "gia-applicato")
        self.assertEqual(out2, out)


@unittest.skipUnless(BASE_EN.exists() and BASE_IT.exists(), "mancano le ROM base 1.1 EN/IT")
class TestBloccoGuida(unittest.TestCase):
    """GUIDA-EVIV-02 (13/09/2026): spegne l'etichetta automatica "START
    Guida" nella pagina ABILITA'/Dati, applicato direttamente su base-1.1
    (non serve la riserva 1.2: la zona toccata e' l'ITCM storica r5). Patch
    chirurgica di 96 byte dentro `guide_main` (nessuna ricompilazione: vedi
    RAPPORTO di SGP-1.2-GUIDA-EVIV-02 per la regressione trovata e scartata
    nel primo tentativo, che ricompilava e rompeva START)."""

    def test_applica_e_rileggi_verde_en_it(self):
        for base_path, lingua in ((BASE_EN, "EN"), (BASE_IT, "IT")):
            base = base_path.read_bytes()
            out, log = bloc_guida.applica(base)
            self.assertEqual(log["esito"], "applicato", "%s: %s" % (lingua, log))
            self.assertEqual(log["lingua"], lingua)
            rep = bloc_guida.rileggi(base, out)
            self.assertEqual(rep["esito"], "VERDE", "%s: %s" % (lingua, rep))

    def test_idempotenza(self):
        base = BASE_EN.read_bytes()
        out1, log1 = bloc_guida.applica(base)
        out2, log2 = bloc_guida.applica(out1)
        self.assertEqual(log1["esito"], "applicato")
        self.assertEqual(log2["esito"], "gia-applicato")
        self.assertEqual(log2["byte_diversi"], 0)
        self.assertEqual(out1, out2)

    def test_mutante_preimmagine_alterata_e_rifiutata(self):
        base = bytearray(BASE_EN.read_bytes())
        a = romlib.Arm9(BASE_EN)
        off = a.off(bloc_guida.PATCH_ADDR, 1)
        base[off] ^= 0xFF  # un byte della regione patchata cambiato: A1 deve rifiutare
        with self.assertRaises(romlib.Rifiuto):
            bloc_guida.applica(bytes(base))

    def test_solo_la_regione_dichiarata_cambia(self):
        base = BASE_EN.read_bytes()
        out, log = bloc_guida.applica(base)
        self.assertGreater(log["byte_diversi"], 0)
        self.assertLessEqual(log["byte_diversi"], bloc_guida.PATCH_N)


@unittest.skipUnless(BASE_EN.exists() and BASE_IT.exists(), "mancano le ROM base 1.1 EN/IT")
class TestBlocchiVFinale(unittest.TestCase):
    """Un test per blocco (QUALITA-STRUMENTI-02): pianta definitiva
    (QUALITA-NATIVO-01 v-finale: plus+salvataggio, npc, wifi; RIFINITURA-01
    v3: opzioni, anim; TITOLO-01) — `applica()` + `rileggi()` VERDE, identici
    per costruzione EN/IT (stessa base, stesso `build/`, stesso codice)."""

    @classmethod
    def _stadio_prima_di_plus(cls, base, lingua):
        dopo_riserva, _ = bloc_riserva.applica(base, BUILD_RISERVA, etichetta=lingua)
        dopo_camera, _ = bloc_camera.applica(dopo_riserva)
        return dopo_camera

    @classmethod
    def setUpClass(cls):
        cls.stadi = {}
        for lingua, base_path in (("EN", BASE_EN), ("IT", BASE_IT)):
            base = base_path.read_bytes()
            cls.stadi[lingua] = {"camera": cls._stadio_prima_di_plus(base, lingua)}

    def _catena(self, lingua):
        """Costruisce (una volta, con cache su self) tutti gli stadi fino a
        `wifi` per la lingua data: serve come precondizione per applicare e
        rileggere ciascun blocco al suo posto nella catena."""
        s = self.stadi[lingua]
        if "wifi" in s:
            return s
        dopo_plus, _ = bloc_plus.applica(s["camera"], BUILD_DEFAULT, manifest_path=MANIFEST)
        s["plus"] = dopo_plus
        dopo_testi, _ = bloc_testi.applica(dopo_plus, BUILD_DEFAULT / "testi", lingua)
        s["testi"] = dopo_testi
        dopo_npc, _ = bloc_npc.applica(dopo_testi, BUILD_DEFAULT / "npc", manifest_path=MANIFEST)
        s["npc"] = dopo_npc
        dopo_anim, _ = bloc_anim.applica(dopo_npc, BUILD_DEFAULT / "anim", manifest_path=MANIFEST, flags=0)
        s["anim"] = dopo_anim
        dopo_opzioni, _ = bloc_opzioni.applica(dopo_anim, BUILD_DEFAULT / "opzioni", lingua=lingua,
                                               manifest_path=MANIFEST)
        s["opzioni"] = dopo_opzioni
        dopo_wifi, _ = bloc_wifi.applica(dopo_opzioni, BUILD_DEFAULT / "wifi", manifest_path=MANIFEST)
        s["wifi"] = dopo_wifi
        return s

    def test_plus_chunk_en_it(self):
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            rep = bloc_plus.rileggi(s["camera"], s["plus"], BUILD_DEFAULT)
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))

    def test_npc_en_it(self):
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            rep = bloc_npc.rileggi(s["testi"], s["npc"], BUILD_DEFAULT / "npc")
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))

    def test_anim_en_it(self):
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            rep = bloc_anim.rileggi(s["npc"], s["anim"], BUILD_DEFAULT / "anim")
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))

    def test_anim_v4_due_ganci_en_it(self):
        """SGP-1.2-ANIM-SOLIDO-01 (v4, 13/09/2026): blob 752 B (scomparto
        PIENO) e SECONDO gancio G2 (0x02262032, BL sgp_idle_stop) -- L5 del
        rilettore, assente in v3."""
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            man, blob, _tab_u, _par, _canarino = bloc_anim._carica_build(BUILD_DEFAULT / "anim")
            self.assertEqual(len(blob), 752, "%s: blob v4 atteso a 752 B" % lingua)
            self.assertIn("sgp_idle_stop", man["simboli"], "%s: manca sgp_idle_stop nel build" % lingua)
            rep = bloc_anim.rileggi(s["npc"], s["anim"], BUILD_DEFAULT / "anim")
            cancelli = {c["cancello"]: c["esito"] for c in rep["cancelli"]}
            self.assertEqual(cancelli.get("L5"), "verde", "%s: %s" % (lingua, rep))

    def test_opzioni_v3_en_it(self):
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            rep = bloc_opzioni.rileggi(s["anim"], s["opzioni"], BUILD_DEFAULT / "opzioni", lingua,
                                       manifest_path=MANIFEST)
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))

    def test_wifi_vfinale_en_it(self):
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            rep = bloc_wifi.rileggi(s["opzioni"], s["wifi"], BUILD_DEFAULT / "wifi")
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))

    def test_titolo_en_it(self):
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            dopo_titolo, log = bloc_titolo.applica(s["wifi"])
            rep = bloc_titolo.rileggi(dopo_titolo)
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))
            self.assertEqual(log["stato_dopo"], "già-applicato")

    def test_titolo_idempotente(self):
        s = self._catena("EN")
        dopo1, log1 = bloc_titolo.applica(s["wifi"])
        dopo2, log2 = bloc_titolo.applica(dopo1)
        self.assertEqual(log1["esito"], "applicato")
        self.assertEqual(log2["esito"], "gia-applicato")
        self.assertEqual(dopo1, dopo2)

    def test_credito_en_it(self):
        """SGP-1.2-TITOLO-02, applicato in luogo da SGP-1.2-INTEGRAZIONE-
        FINALE-02 (13/09/2026): rilettore INDIPENDENTE `rileggi_credito.py`
        (ndspy, ridisegna i tre livelli BG, non importa `applica_credito.py`)."""
        for lingua in ("EN", "IT"):
            s = self._catena(lingua)
            dopo_titolo, _ = bloc_titolo.applica(s["wifi"])
            dopo_credito, log = bloc_titolo.applica_credito(dopo_titolo)
            self.assertEqual(log["esito"], "applicato", "%s: %s" % (lingua, log))
            self.assertEqual(log["byte_cambiati"], 119, "%s: %s" % (lingua, log))
            rep = bloc_titolo.rileggi_credito(dopo_titolo, dopo_credito)
            self.assertEqual(rep["esito_finale"], "verde", "%s: %s" % (lingua, rep))

    def test_credito_idempotente(self):
        s = self._catena("EN")
        dopo_titolo, _ = bloc_titolo.applica(s["wifi"])
        dopo1, log1 = bloc_titolo.applica_credito(dopo_titolo)
        dopo2, log2 = bloc_titolo.applica_credito(dopo1)
        self.assertEqual(log1["esito"], "applicato")
        self.assertEqual(log1["byte_cambiati"], 119)
        self.assertEqual(log2["esito"], "gia-applicato")
        self.assertEqual(log2["byte_cambiati"], 0)
        self.assertEqual(dopo1, dopo2)


def _sha_attesi():
    if not SHA256SUMS.exists():
        return {}
    attesi = {}
    for riga in SHA256SUMS.read_text().splitlines():
        if not riga.strip():
            continue
        h, nome = riga.split(None, 1)
        attesi[nome.strip()] = h
    return attesi


@unittest.skipUnless(SHA256SUMS.exists(), "classe B: nessun SHA256SUMS in $SGP_ROM_DIR")
class TestCostruisciIdentico(unittest.TestCase):
    """Criterio 4: `costruisci.py` da base-1.1-{EN,IT} deve produrre ROM
    IDENTICHE, sha256 per sha256, a quelle di `$SGP_ROM_DIR/`.
    Se in futuro la ROM cambia per la rifinitura in corso, questo test dice
    subito SE `sgp12/build/` va riallineato con `estrai_build.py` (vedi
    README.md §4): non va "corretto" abbassando la pretesa."""

    def _prova(self, lingua):
        attesi = _sha_attesi()
        base_nome = "base-1.1-%s.nds" % lingua
        bersaglio_nome = "sgp-1.2-%s.nds" % lingua
        self.assertIn(base_nome, attesi)
        self.assertIn(bersaglio_nome, attesi)
        base_path = ROM_DIR / base_nome
        base = base_path.read_bytes()
        self.assertEqual(romlib.sha(base), attesi[base_nome],
                         "%s non ha piu' lo sha256 registrato: aggiornare gli hash" % base_nome)
        rom, rapporto = costruisci_mod.costruisci(base, lingua, costruisci_mod.BUILD_DEFAULT)
        self.assertEqual(rapporto["uscita_sha256"], attesi[bersaglio_nome],
                         "%s NON identica: sgp12/build/ non riflette piu' la ROM di lavoro "
                         "(rieseguire estrai_build.py sulla ROM attuale)" % bersaglio_nome)

    def test_identico_EN(self):
        self._prova("EN")

    def test_identico_IT(self):
        self._prova("IT")


if __name__ == "__main__":
    unittest.main()
