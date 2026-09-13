#!/usr/bin/env python3
"""Mutanti T1-5: ogni guasto deve far diventare rosso il rilettore."""
import importlib.util
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
REPO = PKG.parents[2]
BUILD = Path(os.environ.get("SGP_BUILD", REPO / "source/sgp12/build/anim2"))
_ROM_DIR = os.environ.get("SGP_ROM_DIR")
ROM_DIR = Path(_ROM_DIR) if _ROM_DIR else None
BASE_ROM = Path(os.environ.get("SGP_ROM_BASE") or
                (ROM_DIR / "pre-anim2-EN.nds" if ROM_DIR else ""))
PATCHED = Path(os.environ.get("SGP_ROM_ANIM2") or
               (ROM_DIR / "sgp-1.2.1-EN.nds" if ROM_DIR else ""))
sys.path.insert(0, str(REPO / "source/features/anim/tools"))
from arm9 import Arm9  # noqa: E402
import overlay_patch as ovp  # noqa: E402


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reader = load("anim2_reader", PKG / "tools/rileggi_anim2.py")


def guasta_arm9(rom, addr):
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.nds"
        p.write_bytes(rom)
        a = Arm9(p)
        a.scrivi(addr, bytes([a.leggi(addr, 1)[0] ^ 1]))
        return bytes(a.raw)


def guasta_overlay(rom, addr):
    tab = reader.tabelle(rom)
    ent = reader.leggi_overlay(rom, tab, 12)
    img = reader.immagine_overlay(rom, ent)
    off = addr - ent["ram"]
    pre = img[off:off + 4]
    post = bytes([pre[0] ^ 1]) + pre[1:]
    mut, _ = ovp.applica(rom, 12, [(addr, pre)],
                         [{"addr": addr, "pre": pre, "post": post}],
                         strategia="auto")
    return mut


class MutantiAnim2(unittest.TestCase):
    @unittest.skipUnless(BASE_ROM.is_file() and PATCHED.is_file(),
                         "serve SGP_ROM_BASE e SGP_ROM_ANIM2")
    def test_tredici_mutanti_tutti_uccisi(self):
        prima = BASE_ROM.read_bytes()
        buona = PATCHED.read_bytes()
        baseline = reader.rileggi(prima, buona, BUILD)
        self.assertEqual(baseline["esito_finale"], "verde",
                         "la coppia pre-anim2/finale non ha baseline verde")
        blob_n = len((BUILD / "blob.bin").read_bytes())
        arm9 = {
            "codice": 0x023DB500,
            "margine_codice": 0x023DB500 + blob_n,
            "canarino": 0x023DBB00,
            "tabella_u": 0x023DBB20,
            "parametri": 0x023DBB40,
            "siti_lr": 0x023DBB60,
            "guardia_stato": 0x023DBBA1,
            "stato_iniziale": 0x023DBBA2,
            "slot_iniziale": 0x023DBBE0,
        }
        overlay = {
            "gancio_avvio": 0x0225DC8A,
            "gancio_task": 0x0226200C,
            "gancio_stop": 0x02262016,
            "byte_overlay_estraneo": 0x02262020,
        }
        esiti = []
        for nome, addr in arm9.items():
            r = reader.rileggi(prima, guasta_arm9(buona, addr), BUILD)
            esiti.append({"mutante": nome, "ucciso": r["esito_finale"] == "ROSSO"})
        for nome, addr in overlay.items():
            r = reader.rileggi(prima, guasta_overlay(buona, addr), BUILD)
            esiti.append({"mutante": nome, "ucciso": r["esito_finale"] == "ROSSO"})
        rapporto = os.environ.get("SGP_MUTANTI_REPORT")
        if rapporto:
            Path(rapporto).write_text(
                json.dumps({"totale": len(esiti),
                            "uccisi": sum(x["ucciso"] for x in esiti),
                            "esiti": esiti}, indent=2) + "\n")
        self.assertEqual(13, len(esiti))
        self.assertTrue(all(x["ucciso"] for x in esiti), esiti)

    @unittest.skipUnless(BASE_ROM.is_file() and PATCHED.is_file(),
                         "serve SGP_ROM_BASE e SGP_ROM_ANIM2")
    def test_mutante_nella_coda_fat_viene_ucciso(self):
        prima = BASE_ROM.read_bytes()
        buona = PATCHED.read_bytes()
        baseline = reader.rileggi(prima, buona, BUILD)
        self.assertEqual(baseline["esito_finale"], "verde",
                         "la coppia pre-anim2/finale non ha baseline verde")

        tab = reader.tabelle(buona)
        ov12 = reader.leggi_overlay(buona, tab, 12)
        inizi = [struct.unpack_from("<I", buona, tab["fat"] + i * 8)[0]
                 for i in range(tab["fat_len"] // 8)]
        fine_slot = min(x for x in inizi if x > ov12["inizio"])
        self.assertLess(ov12["fine"], fine_slot, "la fixture non ha una coda FAT")

        mutante = bytearray(buona)
        mutante[ov12["fine"]] ^= 1
        letto = reader.rileggi(prima, mutante, BUILD)
        self.assertEqual(letto["esito_finale"], "ROSSO",
                         "il rilettore ha accettato una coda FAT alterata")


if __name__ == "__main__":
    unittest.main(verbosity=2)
