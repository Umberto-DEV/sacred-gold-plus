#!/usr/bin/env python3
"""SGP-1.2-OPZIONI-03 — cancello G4: la schermata al «Continua» / «Nuova partita».

Si esegue il blob: si entra dalle sei entrate che i due template della riserva
registrano, si premono tasti, si guarda lo stato D1 e la sequenza di chiamate.
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, indirizzo, CANARINI, IND                     # noqa: E402

K_A, K_B = 1, 2
K_RIGHT, K_LEFT, K_UP, K_DOWN = 0x10, 0x20, 0x40, 0x80
STATO_PTR = 0x02240000
TPL_CONTINUA = 0x020FA16C
TPL_NUOVA = 0x020FA15C


def passo(b, entrata, stato, tasti=0):
    b.tasti(tasti)
    b.uc.mem_write(STATO_PTR, struct.pack("<i", stato))
    r0, fin = b.chiama(indirizzo(entrata), 0x02250000, STATO_PTR)
    nuovo = struct.unpack("<i", b.uc.mem_read(STATO_PTR, 4))[0]
    return r0, nuovo, fin


class G4Condizione(unittest.TestCase):
    def test_chunk_assente_la_domanda_appare(self):
        b = Banco()
        b.stato_d1(load=1)
        r0, stato, _ = passo(b, "sgp_cont_init", 0)
        self.assertEqual(r0, 0, "init non finisce al primo frame: c'e' il fade")
        self.assertEqual(stato, 1)
        self.assertEqual(b.leggi_ui()["esito"] & 8, 0, "non deve saltare")
        n = b.nomi_chiamate()
        for f in ("GfGfx_SetBanks", "SetScreenModesDisable", "Heap_Create",
                  "BgConfig_Alloc", "InitBgFromTemplate", "LoadFontPal0",
                  "AddWindowParameterized", "CopyWindowToVram", "ToggleBgLayer",
                  "PaletteFadeBegin"):
            self.assertIn(f, n, f"manca {f} nell'accensione della grafica")
        self.assertLess(n.index("BgConfig_Alloc"), n.index("AddWindowParameterized"))
        self.assertLess(n.index("CopyWindowToVram"), n.index("PaletteFadeBegin"),
                        "si disegna PRIMA di riaccendere lo schermo")

    def test_gia_vista_non_appare_e_non_tocca_la_grafica(self):
        b = Banco()
        b.stato_d1(load=2)              # chunk valido: la scelta c'e' gia'
        r0, _, _ = passo(b, "sgp_cont_init", 0)
        self.assertEqual(r0, 1, "init finisce subito")
        self.assertEqual(b.leggi_ui()["esito"] & 8, 8)
        self.assertEqual(b.nomi_chiamate(), [],
                         "nessuna chiamata al gioco quando la domanda non serve")

    def test_chunk_rifiutato_non_appare(self):
        b = Banco()
        b.stato_d1(load=3)
        r0, _, _ = passo(b, "sgp_cont_init", 0)
        self.assertEqual(r0, 1)
        self.assertEqual(b.nomi_chiamate(), [])

    def test_stato_D1_mai_inizializzato_non_appare(self):
        b = Banco()
        b.stato_d1(guard=0)
        r0, _, _ = passo(b, "sgp_cont_init", 0)
        self.assertEqual(r0, 1)
        self.assertEqual(b.nomi_chiamate(), [])


class G4Interazione(unittest.TestCase):
    def apri(self, entrata="sgp_cont_init"):
        b = Banco()
        b.stato_d1(load=1)
        passo(b, entrata, 0)
        passo(b, entrata, 1)                     # fade finito → init TRUE
        return b

    def test_proposta_predefinita_simmetrica(self):
        """REVISIONE-QUALITA §5: la v1 proponeva «Difficolta' Plus = SI» e
        «Livelli selvatici = NO» senza dire perche'. Chi premeva A senza leggere
        ne accendeva una e non l'altra. Ora le due proposte partono uguali."""
        b = self.apri()
        u = b.leggi_ui()
        self.assertEqual((u["val"][0], u["val"][1]), (1, 1))
        self.assertEqual((u["val0"][0], u["val0"][1]), (1, 1))

    def test_su_giu_cambia_riga_sinistra_destra_cambia_valore(self):
        b = self.apri()
        m = "sgp_cont_main"
        passo(b, m, 0, K_RIGHT)
        self.assertEqual(b.leggi_ui()["val"][0], 0)
        passo(b, m, 0, K_DOWN)
        self.assertEqual(b.leggi_ui()["cursore"], 1)
        passo(b, m, 0, K_LEFT)
        self.assertEqual(b.leggi_ui()["val"][1], 0)

    def test_A_conferma_scrive_nel_chunk(self):
        b = self.apri()
        r0, stato, _ = passo(b, "sgp_cont_main", 0, K_A)
        self.assertEqual(r0, 0, "prima si sbiadisce, poi si esce")
        self.assertEqual(stato, 1)
        d = b.leggi_d1()
        self.assertEqual((d["plus"], d["selvatici"]), (1, 1))
        self.assertEqual((d["active_plus"], d["active_wild"]), (1, 1))
        self.assertIn("PaletteFadeBegin", b.nomi_chiamate())

    def test_B_dopo_non_scrive_niente(self):
        b = self.apri()
        passo(b, "sgp_cont_main", 0, K_B)
        d = b.leggi_d1()
        self.assertEqual((d["plus"], d["active_plus"]), (0, 0))
        self.assertEqual(d["versione"], 2, "la pagina non tocca i campi di D1")
        self.assertEqual(b.leggi_ui()["salvataggi"], 0)

    def test_uscita_libera_tutto_e_registra_l_originale(self):
        b = self.apri()
        passo(b, "sgp_cont_main", 0, K_A)
        passo(b, "sgp_cont_main", 1)
        r0, _, _ = passo(b, "sgp_cont_exit", 0)
        self.assertEqual(r0, 1)
        n = b.nomi_chiamate()
        for f in ("ClearWindowTilemapAndCopyToVram", "RemoveWindow",
                  "String_Delete", "FreeBgTilemapBuffer", "Heap_Destroy"):
            self.assertIn(f, n)
        self.assertEqual(n[-1], "RegisterMainOverlay")
        reg = [c for c in b.chiamate if c["f"] == "RegisterMainOverlay"][0]
        self.assertEqual(reg["r"][0], 0xFFFFFFFF, "FS_OVERLAY_ID_NONE")
        self.assertEqual(reg["r"][1], TPL_CONTINUA,
                         "si deve registrare gApplication_ContinueFieldsys")
        self.assertLess(n.index("RemoveWindow"), n.index("Heap_Destroy"),
                        "prima si rende, poi si distrugge l'heap che possiede")

    def test_nuova_partita_registra_l_altro_template(self):
        b = self.apri("sgp_new_init")
        self.assertEqual(b.leggi_ui()["esito"] >> 2 & 1, 1, "modo = nuova partita")
        passo(b, "sgp_new_main", 0, K_A)
        passo(b, "sgp_new_main", 1)
        passo(b, "sgp_new_exit", 0)
        reg = [c for c in b.chiamate if c["f"] == "RegisterMainOverlay"][0]
        self.assertEqual(reg["r"][1], TPL_NUOVA,
                         "si deve registrare gApplication_NewGameFieldsys")

    def test_uscita_saltata_non_libera_niente_ma_registra(self):
        b = Banco()
        b.stato_d1(load=2)
        passo(b, "sgp_cont_init", 0)
        r0, _, _ = passo(b, "sgp_cont_exit", 0)
        self.assertEqual(r0, 1)
        self.assertEqual(b.nomi_chiamate(), ["RegisterMainOverlay"],
                         "quando la domanda non appare si registra e basta")

    def test_una_sola_riga_di_aiuto_e_il_titolo_e_centrato(self):
        """REVISIONE-QUALITA §5: la v1 ammassava tre righe in fondo, tutte a x=8
        mentre il corpo stava a x=20. Qui il titolo e' centrato (una sola stampa
        che misura il testo) e c'e' una riga di aiuto sola, allineata al corpo."""
        b = self.apri()
        b.chiamate = []
        passo(b, "sgp_cont_main", 0, K_DOWN)
        st = [c for c in b.chiamate if c["f"] == "AddTextPrinterWithColor"]
        self.assertEqual(len(st), 10, "titolo + 2 righe di prosa + cursore + "
                                      "2 etichette + 2 valori + nota + aiuto")
        xs = [c["r"][3] for c in st]         # 4o argomento = x
        ys = [c["sp"][0] for c in st]        # 5o argomento = y
        # A8: il corpo sta a x=20; solo il cursore sporge a x=8, com'e' giusto.
        self.assertIn(20, xs)
        self.assertIn(8, xs)
        self.assertEqual([x for x in xs if x < 8], [])
        # le due righe di scelta hanno il passo del menu: 24 px
        righe = sorted({y for y in ys if ys.count(y) > 1})
        self.assertEqual(righe[1] - righe[0], 24)
        mis = [c for c in b.chiamate if c["f"] == "FontID_String_GetWidth"]
        self.assertEqual(len(mis), 3, "titolo centrato + i due valori a destra")

    def test_canarini_intatti(self):
        b = self.apri()
        for entrata, k in (("sgp_cont_main", K_DOWN), ("sgp_cont_main", K_RIGHT),
                           ("sgp_cont_main", K_A)):
            _, _, fin = passo(b, entrata, 0, k)
            for r, v in CANARINI.items():
                self.assertEqual(fin[r], v)


if __name__ == "__main__":
    unittest.main(verbosity=2)
