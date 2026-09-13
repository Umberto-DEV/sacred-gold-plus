#!/usr/bin/env python3
"""Classe B: applicatore e quattro rilettori sulla catena reale EN/IT."""
import os
import sys
import unittest
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
REPO = FEATURE.parents[2]
SOURCE = REPO / "source"
sys.path.insert(0, str(SOURCE))

from sgp12.rom import Rifiuto  # noqa: E402
from sgp12.blocchi import (riserva, camera, plus_chunk, testi, npc, anim,
                           opzioni, wifi, titolo, guida, caramelle, borsa)  # noqa: E402

BUILD = SOURCE / "sgp12" / "build" / "borsa"
BUILD_ROOT = SOURCE / "sgp12" / "build"
MAPPA = SOURCE / "sgp12" / "build" / "riserva" / "MAPPA-RISERVA-ARM9.json"
ROM_NOME = "base-1.1-%s.nds"


def ingressi_disponibili():
    cartella = os.environ.get("SGP_ROM_DIR")
    return bool(cartella and borsa.pret_disponibile(BUILD)
                and all((Path(cartella) / (ROM_NOME % l)).is_file()
                        for l in ("EN", "IT")))


def fino_a_caramelle(base: bytes, lingua: str) -> bytes:
    """La stessa catena pubblica del costruttore, fermata prima di Borsa."""
    rom, _ = riserva.applica(base, BUILD_ROOT / "riserva", etichetta=lingua)
    rom, _ = camera.applica(rom)
    rom, _ = plus_chunk.applica(rom, BUILD_ROOT, manifest_path=MAPPA)
    rom, _ = testi.applica(rom, BUILD_ROOT / "testi", lingua)
    rom, _ = npc.applica(rom, BUILD_ROOT / "npc", manifest_path=MAPPA,
                         attivo=1, tetto=1)
    rom, _ = anim.applica(rom, BUILD_ROOT / "anim", manifest_path=MAPPA, flags=0)
    rom, _ = opzioni.applica(rom, BUILD_ROOT / "opzioni", lingua=lingua,
                             manifest_path=MAPPA)
    rom, _ = wifi.applica(rom, BUILD_ROOT / "wifi", manifest_path=MAPPA)
    rom, _ = titolo.applica(rom)
    rom, _ = titolo.applica_credito(rom)
    rom, _ = guida.applica(rom)
    rom, _ = caramelle.applica(rom, BUILD_ROOT / "caramelle", manifest_path=MAPPA)
    return rom


@unittest.skipUnless(ingressi_disponibili(),
                     "classe B: servono SGP_ROM_DIR e SGP_PRET_SOURCE")
class ProveCatenaComposta(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.casi = {}
        for lingua in ("EN", "IT"):
            base = (Path(os.environ["SGP_ROM_DIR"]) / (ROM_NOME % lingua)).read_bytes()
            prima = fino_a_caramelle(base, lingua)
            dopo, rapporto = borsa.applica(prima, BUILD, lingua, MAPPA)
            cls.casi[lingua] = (prima, dopo, rapporto)

    def test_applica_e_rilegge_en_it(self):
        for lingua in ("EN", "IT"):
            with self.subTest(lingua=lingua):
                prima, dopo, rapporto = self.casi[lingua]
                self.assertEqual(rapporto["esito"], "applicato")
                self.assertEqual(list(rapporto["stadi"]),
                                 ["premi", "testo199", "appendici", "arm9"])
                riletto = borsa.rileggi(prima, dopo, BUILD, lingua)
                self.assertEqual(riletto["esito_finale"], "verde", riletto["problemi"])

    def test_110_chiavi_finali_uniche_e_quattro_spostamenti(self):
        for lingua in ("EN", "IT"):
            with self.subTest(lingua=lingua):
                voci = self.casi[lingua][2]["stadi"]["arm9"]["voci"]
                self.assertEqual(len(voci), 110)
                self.assertEqual(len({v["chiave"] for v in voci}), 110)
                self.assertEqual(sum(v["stato"] == "spostato" for v in voci), 4)

    def test_idempotenza_wrapper_rifiutata(self):
        for lingua in ("EN", "IT"):
            with self.subTest(lingua=lingua):
                with self.assertRaises(Rifiuto):
                    borsa.applica(self.casi[lingua][1], BUILD, lingua, MAPPA)

    def test_rilettore_boccia_un_byte_estraneo(self):
        lingua = "EN"
        prima, dopo, _ = self.casi[lingua]
        mutata = bytearray(dopo)
        mutata[-1] ^= 1
        riletto = borsa.rileggi(prima, bytes(mutata), BUILD, lingua)
        self.assertEqual(riletto["esito_finale"], "ROSSO")
        self.assertIn("USCITA_DIVERSA_DALLA_RICOSTRUZIONE_ATTESA",
                      riletto["problemi"])


if __name__ == "__main__":
    unittest.main()
