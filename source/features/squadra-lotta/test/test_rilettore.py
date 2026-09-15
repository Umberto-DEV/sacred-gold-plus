#!/usr/bin/env python3
"""Contratto e mutanti del rilettore indipendente ``sgp.squadra_lotta``."""
import importlib.util
import json
import os
import shutil
import struct
import tempfile
import unittest
from pathlib import Path


PACCHETTO = Path(__file__).resolve().parents[1]
REPO = PACCHETTO.parents[2]
BUILD = REPO / "source/sgp12/build/squadra_lotta"
PRIMA = Path(os.environ.get("SGP_ROM_SQUADRA_PRIMA", ""))
DOPO = Path(os.environ.get("SGP_ROM_SQUADRA_DOPO", ""))


def carica():
    spec = importlib.util.spec_from_file_location(
        "squadra_lotta_rilettore", PACCHETTO / "tools/rileggi.py"
    )
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


reader = carica()


class DecodificaBlTest(unittest.TestCase):
    def test_decodifica_la_preimmagine_nativa(self):
        self.assertEqual(reader.bersaglio_bl(0x0221D3DE, bytes.fromhex("55f6a5ff")),
                         0x0207332C)

    def test_rifiuta_un_opcode_che_non_e_bl_thumb(self):
        self.assertIsNone(reader.bersaglio_bl(0x0221D3DE, b"\0\0\0\0"))


@unittest.skipUnless(PRIMA.is_file() and DOPO.is_file() and
                     (BUILD / "manifesto.json").is_file(),
                     "servono SGP_ROM_SQUADRA_PRIMA/DOPO e la build squadra_lotta")
class MutantiClasseBTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prima = PRIMA.read_bytes()
        cls.dopo = DOPO.read_bytes()

    def copia_build(self):
        td = tempfile.TemporaryDirectory(prefix="squadra-lotta-reader-")
        self.addCleanup(td.cleanup)
        dst = Path(td.name)
        for nome in ("blob.bin", "canarino.bin", "manifesto.json"):
            shutil.copy2(BUILD / nome, dst / nome)
        return dst

    def guasta_arm9(self, raw, addr):
        td = tempfile.TemporaryDirectory(prefix="squadra-lotta-rom-")
        self.addCleanup(td.cleanup)
        p = Path(td.name) / "r.nds"
        p.write_bytes(raw)
        arm = reader.Arm9RO(p)
        guasto = bytearray(raw)
        off = arm.off(addr)
        guasto[off] ^= 1
        return bytes(guasto)

    def test_baseline_verde(self):
        self.assertEqual(reader.rileggi(self.prima, self.dopo, BUILD)["esito_finale"],
                         "verde")

    def test_mutanti_blocco_e_bundle_sono_rossi(self):
        blob_n = len((BUILD / "blob.bin").read_bytes())
        mutanti = {
            "codice": self.guasta_arm9(self.dopo, 0x023DBE00),
            "margine_zero": self.guasta_arm9(self.dopo, 0x023DBE00 + blob_n),
            "canarino": self.guasta_arm9(self.dopo, 0x023DBEF0),
            "arm9_estraneo": self.guasta_arm9(self.dopo, 0x023DBCF0),
        }
        for nome, rom in mutanti.items():
            with self.subTest(nome=nome):
                self.assertEqual(reader.rileggi(self.prima, rom, BUILD)["esito_finale"],
                                 "ROSSO")

        build = self.copia_build()
        man = json.loads((build / "manifesto.json").read_text())
        man["simboli"]["sgp_squadra_attr_hook"] = "0x023dbd01"
        (build / "manifesto.json").write_text(json.dumps(man))
        self.assertEqual(reader.rileggi(self.prima, self.dopo, build)["esito_finale"],
                         "ROSSO")

    def test_byte_fuori_regioni_e_coda_fat_sono_rossi(self):
        guasto = bytearray(self.dopo)
        guasto[0x100] ^= 1
        self.assertEqual(reader.rileggi(self.prima, guasto, BUILD)["esito_finale"],
                         "ROSSO")

        tab = reader.tabelle(self.dopo)
        ov = reader.leggi_overlay(self.dopo, tab, 8)
        inizi = [struct.unpack_from("<I", self.dopo, tab["fat"] + i * 8)[0]
                 for i in range(tab["fat_len"] // 8)]
        fine_slot = min(x for x in inizi if x > ov["inizio"])
        self.assertLess(ov["fine"], fine_slot, "la fixture non ha coda FAT")
        guasto = bytearray(self.dopo)
        guasto[ov["fine"]] ^= 1
        self.assertEqual(reader.rileggi(self.prima, guasto, BUILD)["esito_finale"],
                         "ROSSO")

    def test_bundle_malformato_restituisce_rosso(self):
        build = self.copia_build()
        (build / "manifesto.json").write_text("{")
        risultato = reader.rileggi(self.prima, self.dopo, build)
        self.assertEqual(risultato["esito_finale"], "ROSSO")
        self.assertIn("malformato", risultato["cancelli"][0]["dettaglio"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
