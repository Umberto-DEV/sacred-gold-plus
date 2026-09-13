#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-OVERLAY-01 — cancelli eseguibili.

Girano sulla base 1.1 EN e IT, senza scrivere niente fuori dalla cartella
temporanea. Non richiedono `hg_runtime`: le corse sono in `corse/` e in
RAPPORTO.md.

    python3 -m unittest discover -s test -p 'test_*.py' -v
"""

import os
import struct
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI.parent / "tools"))

import overlay_patch as OP          # noqa: E402
import overlay_rileggi as OR        # noqa: E402

ROMS = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))
BASE_EN = ROMS / "base-1.1-EN.nds"
BASE_IT = ROMS / "base-1.1-IT.nds"

# ancore dei due cantieri che useranno questo applicatore
G_ANIM = [(0x0226200C, bytes.fromhex("3d202602")),
          (0x0226203C, bytes.fromhex("38b50c1c67218900605a14306052081c"))]
G_PLUS = [(0x02246C94, bytes.fromhex("00880328")),
          (0x02247D3A, bytes.fromhex("04a80078"))]
BXLR = bytes.fromhex("a5ce2302")     # 0x0223CEA5: un `bx lr` di ov012, Thumb


def carica(p):
    if not p.exists():
        raise unittest.SkipTest("ROM assente: %s" % p)
    return p.read_bytes()


class TestBLZ(unittest.TestCase):
    """Il codec, sui due overlay veri."""

    @classmethod
    def setUpClass(cls):
        cls.d = carica(BASE_EN)
        cls.rom = OP.Rom(cls.d)

    def test_C1_trailer_letto_come_il_gioco(self):
        for oid in (2, 12):
            v, crudo, img = self.rom.immagine_overlay(oid)
            hdr, enc, inc, grezzo, dim = OP.blz_leggi_trailer(crudo)
            self.assertEqual(dim, v["ram_size"])
            self.assertEqual(len(img), v["ram_size"])
            self.assertEqual(len(crudo), v["dim_compressa"])
            self.assertEqual(grezzo, len(crudo) - enc)

    def test_C2_due_decodificatori_indipendenti_concordano(self):
        for oid in (2, 12):
            v, crudo, img = self.rom.immagine_overlay(oid)
            altra, _ = OR.srotola_blz(crudo)
            self.assertEqual(img, altra, "ov%03d: i due decodificatori divergono" % oid)

    def test_C3_roundtrip_ottimo(self):
        for oid in (2, 12):
            v, crudo, img = self.rom.immagine_overlay(oid)
            c = OP.blz_comprimi_ottimo(img)
            self.assertEqual(OP.blz_decomprimi(c), img)
            self.assertEqual(OR.srotola_blz(c)[0], img)

    def test_C4_ottimo_batte_originale_e_avido(self):
        for oid in (2, 12):
            v, crudo, img = self.rom.immagine_overlay(oid)
            ott = len(OP.blz_comprimi_ottimo(img))
            avi = len(OP.blz_comprimi(img))
            self.assertLess(ott, len(crudo),
                            "ov%03d: l'analisi ottima non batte l'originale" % oid)
            self.assertLess(ott, avi)

    def test_C5_bersaglio_centrato(self):
        for oid in (2, 12):
            v, crudo, img = self.rom.immagine_overlay(oid)
            c = OP.blz_comprimi_ottimo(img, bersaglio=len(crudo))
            self.assertEqual(len(c), len(crudo))
            self.assertEqual(OP.blz_decomprimi(c), img)

    def test_C6_flusso_che_scavalca_e_rifiutato(self):
        """Il guasto che ha bloccato A1-B per un giorno: un flusso che un
        decodificatore su buffer separato accetta e il gioco no."""
        v, crudo, img = self.rom.immagine_overlay(2)
        rotto = bytearray(OP.blz_comprimi_ottimo(img))
        # si gonfia inc_len: la destinazione parte troppo in alto e la
        # decompressione finisce fuori posto
        struct.pack_into("<I", rotto, len(rotto) - 4,
                         struct.unpack_from("<I", rotto, len(rotto) - 4)[0] + 64)
        with self.assertRaises(OP.Rifiuto):
            OP.blz_decomprimi(bytes(rotto))

    def test_C7_decodificatore_A_vede_la_sovrapposizione(self):
        """Un flusso costruito tenendo i byte SBAGLIATI della coda codificata
        (l'errore misurato il 12/09) riferisce byte mai scritti."""
        v, crudo, img = self.rom.immagine_overlay(12)
        dati = bytes(reversed(img))
        best, dist = OP._riscontri_massimi(dati)
        costo, scelta, token = OP._analisi_ottima(dati, best)
        k = len(img) // 2
        pak = OP._emetti(dati, scelta, dist, k)
        buono = OP._confeziona(img, dati, pak, k)
        self.assertEqual(OP.blz_decomprimi(buono), img)
        # la versione sbagliata: la coda codificata NON rovesciata
        cattivo = bytearray(buono)
        raw_tmp = len(img) - k
        cattivo[raw_tmp:raw_tmp + len(pak)] = pak
        with self.assertRaises(OP.Rifiuto):
            OP.blz_decomprimi(bytes(cattivo))


class TestApplicatore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = carica(BASE_EN)
        cls.tmp = tempfile.mkdtemp(prefix="sgp-ov01-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # -- scelta dell'overlay ---------------------------------------------
    def test_G1_guardia_sceglie_un_solo_overlay(self):
        rom = OP.Rom(self.d)
        for guardie, atteso in ((G_ANIM, 12), (G_PLUS, 2)):
            scelto, cand = OP.scegli_overlay(rom, guardie, None)
            self.assertEqual(cand, [atteso])
            self.assertEqual(scelto, atteso)

    def test_M1_indirizzo_da_solo_NON_basta(self):
        """Il mutante «scegli per indirizzo»: cinque overlay contengono
        0x0226200C, otto contengono 0x02246C94."""
        rom = OP.Rom(self.d)
        for addr, minimo in ((0x0226200C, 2), (0x02246C94, 2)):
            n = sum(1 for i in range(rom.n_overlay)
                    if rom.voce_overlay(i)["ram"] <= addr <
                    rom.voce_overlay(i)["ram"] + rom.voce_overlay(i)["ram_size"])
            self.assertGreaterEqual(n, minimo)

    def test_M2_guardia_sbagliata_e_rifiutata(self):
        cattiva = [(0x0226203C, bytes.fromhex("deadbeef"))]
        with self.assertRaises(OP.Rifiuto):
            OP.applica(self.d, 12, cattiva, [])
        with self.assertRaises(OP.Rifiuto):
            OP.applica(self.d, None, cattiva, [])

    def test_M3_guardia_giusta_ma_overlay_sbagliato(self):
        with self.assertRaises(OP.Rifiuto):
            OP.applica(self.d, 13, G_ANIM, [])

    def test_M4_preimmagine_sbagliata_e_rifiutata(self):
        p = [{"addr": 0x0226200C, "pre": bytes.fromhex("deadbeef"), "post": BXLR}]
        with self.assertRaises(OP.Rifiuto):
            OP.applica(self.d, 12, G_ANIM, p)

    def test_M5_postimmagine_al_posto_della_preimmagine(self):
        """L'errore documentato della 1.1: prendere la POSTimmagine per
        preimmagine."""
        p = [{"addr": 0x0226200C, "pre": BXLR, "post": BXLR}]
        with self.assertRaises(OP.Rifiuto):
            OP.applica(self.d, 12, G_ANIM, p)

    def test_M6_patch_fuori_dal_modulo(self):
        p = [{"addr": 0x02300000, "pre": b"\0\0\0\0", "post": b"\1\1\1\1"}]
        with self.assertRaises(OP.Rifiuto):
            OP.applica(self.d, 12, G_ANIM, p)

    def test_M7_lunghezze_diverse(self):
        with self.assertRaises(OP.Rifiuto):
            OP.analizza_patch("0x0226200C:3d202602:a5ce")

    # -- comportamento ----------------------------------------------------
    def test_P1_giro_a_vuoto_identico_al_byte(self):
        out, r = OP.applica(self.d, None, G_ANIM, [])
        self.assertEqual(out, self.d)
        self.assertEqual(r["cancelli"]["C5_resto_identico"]["byte_aggiunti_in_coda"], 0)

    def test_P1b_ricompressione_forzata_cambia_solo_il_corpo(self):
        out, r = OP.applica(self.d, None, G_ANIM, [], forza_ricompressione=True)
        self.assertEqual(len(out), len(self.d))
        v = OP.Rom(self.d).voce_overlay(12)
        f = OP.Rom(self.d).voce_fat(v["file_id"])
        diversi = [i for i in range(len(self.d)) if self.d[i] != out[i]]
        self.assertTrue(all(f["inizio"] <= i < f["fine"] for i in diversi),
                        "cambia qualcosa fuori dal corpo dell'overlay")
        # e l'immagine decompressa e' identica
        self.assertEqual(OP.Rom(out).immagine_overlay(12)[2],
                         OP.Rom(self.d).immagine_overlay(12)[2])

    def test_P3_patch_reale_in_luogo(self):
        p = [{"addr": 0x0226200C, "pre": bytes.fromhex("3d202602"), "post": BXLR}]
        out, r = OP.applica(self.d, None, G_ANIM, p)
        self.assertEqual(len(out), len(self.d))
        self.assertEqual(r["strategia"]["collocazione"], "in luogo")
        img = OP.Rom(out).immagine_overlay(12)[2]
        self.assertEqual(img[0x0226200C - 0x022378C0:0x0226200C - 0x022378C0 + 4], BXLR)
        # e cambia SOLO quel letterale nell'immagine
        orig = OP.Rom(self.d).immagine_overlay(12)[2]
        diversi = [i for i in range(len(orig)) if orig[i] != img[i]]
        dentro = range(0x0226200C - 0x022378C0, 0x0226200C - 0x022378C0 + 4)
        self.assertTrue(diversi and all(i in dentro for i in diversi),
                        "cambia qualcosa fuori dal letterale: %s" % diversi[:8])

    def test_P5_seconda_applicazione_rifiutata(self):
        p = [{"addr": 0x0226200C, "pre": bytes.fromhex("3d202602"), "post": BXLR}]
        out, _ = OP.applica(self.d, None, G_ANIM, p)
        with self.assertRaises(OP.Rifiuto):
            OP.applica(out, None, G_ANIM, p)   # guardia: il letterale non c'e' piu'
        with self.assertRaises(OP.Rifiuto):
            OP.applica(out, 12, [G_ANIM[1]], p)   # preimmagine: idem

    def test_P6_riloco_vietato_senza_permesso(self):
        """Con l'analisi avida il corpo non entra nello slot: deve RIFIUTARE."""
        rom = OP.Rom(self.d)
        v, crudo, img = rom.immagine_overlay(12)
        avido = OP.blz_comprimi(img)
        self.assertGreater(len(avido), rom.capienza_slot(v["file_id"]))
        # il percorso normale non ci finisce mai, perche' usa l'analisi ottima
        out, r = OP.applica(self.d, None, G_ANIM, [], forza_ricompressione=True)
        self.assertEqual(r["strategia"]["collocazione"], "in luogo")

    def test_P7_EN_e_IT_hanno_le_stesse_ancore(self):
        it = carica(BASE_IT)
        a, b = OP.Rom(self.d), OP.Rom(it)
        for oid in (2, 12):
            ia = a.immagine_overlay(oid)[2]
            ib = b.immagine_overlay(oid)[2]
            base = a.voce_overlay(oid)["ram"]
            self.assertEqual(base, b.voce_overlay(oid)["ram"])
            for addr, atteso in (G_ANIM + G_PLUS):
                if base <= addr < base + len(ia):
                    self.assertEqual(ia[addr - base:addr - base + len(atteso)],
                                     ib[addr - base:addr - base + len(atteso)],
                                     "ancora %#x diversa fra EN e IT" % addr)

    def test_P8_IT_si_applica_con_le_stesse_preimmagini(self):
        it = carica(BASE_IT)
        p = [{"addr": 0x0226200C, "pre": bytes.fromhex("3d202602"), "post": BXLR}]
        out, r = OP.applica(it, None, G_ANIM, p)
        self.assertEqual(len(out), len(it))
        self.assertEqual(r["strategia"]["collocazione"], "in luogo")


class TestRilettore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.d = carica(BASE_EN)
        cls.tmp = Path(tempfile.mkdtemp(prefix="sgp-ov01-ril-"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def scrivi(self, dati, nome):
        p = self.tmp / nome
        p.write_bytes(dati)
        return p

    def test_R1_verde_sulla_rom_patchata(self):
        p = [{"addr": 0x0226200C, "pre": bytes.fromhex("3d202602"), "post": BXLR}]
        out, _ = OP.applica(self.d, None, G_ANIM, p)
        f = self.scrivi(out, "ok.nds")
        rc = OR.main(["--rom", str(f), "--overlay", "12",
                      "--guardia", "0x0226203C:38b50c1c67218900605a14306052081c",
                      "--post", "0x0226200C:a5ce2302",
                      "--ingresso", str(BASE_EN)])
        self.assertEqual(rc, 0)

    def test_R2_postimmagine_assente_e_rosso(self):
        f = self.scrivi(self.d, "vergine.nds")
        with self.assertRaises(OR.Rosso):
            OR.main(["--rom", str(f), "--overlay", "12",
                     "--post", "0x0226200C:a5ce2302"])

    def test_M8_overlay_corrotto_di_un_byte_e_rosso(self):
        p = [{"addr": 0x0226200C, "pre": bytes.fromhex("3d202602"), "post": BXLR}]
        out, r = OP.applica(self.d, None, G_ANIM, p)
        inizio = int(r["overlay"]["fat_in_ingresso"][0], 16)
        rotta = bytearray(out)
        rotta[inizio + 5000] ^= 0x01      # un solo bit dentro il flusso compresso
        f = self.scrivi(bytes(rotta), "rotta.nds")
        with self.assertRaises(OR.Rosso):
            OR.main(["--rom", str(f), "--overlay", "12",
                     "--guardia", "0x0226203C:38b50c1c67218900605a14306052081c",
                     "--post", "0x0226200C:a5ce2302",
                     "--ingresso", str(BASE_EN)])

    def test_M9_crc_dell_header_sbagliato_e_rosso(self):
        rotta = bytearray(self.d)
        rotta[0x15E] ^= 0xFF
        f = self.scrivi(bytes(rotta), "crc.nds")
        with self.assertRaises(OR.Rosso):
            OR.main(["--rom", str(f), "--overlay", "12"])

    def test_M10_dimensione_y9_incoerente_e_rossa(self):
        rotta = bytearray(self.d)
        t = OR.tabelle(bytes(rotta))
        voce = t["y9"] + 12 * 32 + 28
        parola = struct.unpack_from("<I", rotta, voce)[0]
        struct.pack_into("<I", rotta, voce, (parola & 0xFF000000) | ((parola & 0xFFFFFF) - 4))
        struct.pack_into("<H", rotta, 0x15E, OR.crc16_header(bytes(rotta[:0x15E])))
        f = self.scrivi(bytes(rotta), "y9.nds")
        with self.assertRaises(OR.Rosso):
            OR.main(["--rom", str(f), "--overlay", "12"])

    def test_M11_fat_sovrapposta_e_rossa(self):
        rotta = bytearray(self.d)
        t = OR.tabelle(bytes(rotta))
        e = OR.leggi_overlay(bytes(rotta), t, 12)
        struct.pack_into("<II", rotta, e["fat_voce"], e["inizio"], e["fine"] + 0x4000)
        struct.pack_into("<H", rotta, 0x15E, OR.crc16_header(bytes(rotta[:0x15E])))
        f = self.scrivi(bytes(rotta), "fat.nds")
        with self.assertRaises(OR.Rosso):
            OR.main(["--rom", str(f), "--overlay", "12"])

    def test_M12_i_due_CRC16_concordano(self):
        self.assertEqual(OP.crc16(self.d[:0x15E]), OR.crc16_header(self.d[:0x15E]))
        self.assertEqual(OP.crc16(self.d[:0x15E]),
                         struct.unpack_from("<H", self.d, 0x15E)[0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
