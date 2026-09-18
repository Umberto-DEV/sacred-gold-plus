#!/usr/bin/env python3
"""SGP-1.2-CARAMELLE-01 — la suite. Gira sull'ARM9 VERO di una ROM patchata.

    SGP_ROM_DIR=<dir con sgp-1.2.2-{EN,IT}.nds> \
        python3 -m unittest discover -s test -v

Ogni caso parte dal sito del gancio 0x02081E96 e legge l'esito dai byte: lo
stato reso, `args->selectedAction`, la sequenza di chiamate native. Nessun caso
consulta il sorgente C.

Gli esiti attesi vengono dal decomp, non da noi:
    PARTY_MENU_STATE_USE_ITEM_SELECT_MON = 4     (include/party_menu.h:36)
    PARTY_MENU_STATE_BEGIN_EXIT          = 0x20  (include/party_menu.h:64)
    PARTY_MENU_ACTION_RETURN_0           = 0     (include/party_menu.h:137)
    PARTY_MENU_ACTION_RETURN_EVO_RARE_CANDY = 9  (include/party_menu.h:146)

GPL-3.0-or-later.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, rom_dir, manifesto, rom_presenti, ROM_NOME, CALLEE  # noqa: E402
from unicorn.arm_const import UC_ARM_REG_R4  # noqa: E402

RESTA = 4
ESCI = 0x20
AZ_0 = 0
AZ_EVO = 9

LINGUE = ("EN", "IT")


def rom(lingua):
    return rom_dir() / (ROM_NOME % lingua)


MOTIVO = ("classe B: serve $SGP_ROM_DIR con " + ROM_NOME % "{EN,IT}"
          + " (ROM gia' patchate: vedi source/README.md)")


@unittest.skipUnless(rom_presenti(), MOTIVO)
class ProveCaramelle(unittest.TestCase):
    """Ogni prova gira su EN e su IT: gli indirizzi ARM9 statici coincidono
    (RAPPORTO §2), e questa suite è il controllo che continuino a coincidere."""

    def banco(self, lingua):
        return Banco(rom(lingua))

    # -- (i) caso pulito: si resta nel menu ---------------------------------
    def test_i_item_valido_senza_evoluzione_resta_nel_menu(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(species=0, item=50, context=5, slot=0, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], RESTA,
                                 "atteso USE_ITEM_SELECT_MON (4), avuto %#x" % r["stato"])
                self.assertEqual(r["azione"], AZ_0)
                nomi = [c[0] for c in r["chiamate"]]
                self.assertEqual(
                    nomi,
                    ["Bag_GetItemQuantity", "Party_GetCount", "Party_GetCapacity",
                     "ClearFrameAndWindow2", "PartyMenu_PrintMessageOnWindow32",
                     "thunk_Sprite_SetPaletteOverride"],
                    "la sequenza di rientro non è quella di UX105_BAG_Tail")

    def test_i_bis_la_sequenza_di_rientro_ha_gli_argomenti_giusti(self):
        from banco import PM, PM_WIN34, PM_SPR_CURSOR, SPRITE, BAG, PARTY
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                r = b.esegui()
                c = dict((x[0], x) for x in r["chiamate"])
                self.assertEqual(c["Bag_GetItemQuantity"][1], BAG)
                self.assertEqual(c["Bag_GetItemQuantity"][2], 50, "itemId passato")
                self.assertEqual(c["Bag_GetItemQuantity"][3], 12, "heap 12")
                self.assertEqual(c["Party_GetCount"][1], PARTY)
                self.assertEqual(c["ClearFrameAndWindow2"][1], PM + PM_WIN34,
                                 "dev'essere &windows[34]")
                self.assertEqual(c["ClearFrameAndWindow2"][2], 1)
                self.assertEqual(c["PartyMenu_PrintMessageOnWindow32"][1], PM)
                self.assertEqual(c["PartyMenu_PrintMessageOnWindow32"][2], 33,
                                 "msg_0300_00033, «Su quale Pokémon usarlo?»")
                self.assertEqual(c["thunk_Sprite_SetPaletteOverride"][1], SPRITE)
                self.assertEqual(c["thunk_Sprite_SetPaletteOverride"][2], 0)
                self.assertEqual(r["search"], 0,
                                 "levelUpMoveSearchState dev'essere azzerato")

    # -- (ii) itemId == ITEM_NONE: uscita vanilla ---------------------------
    def test_ii_item_none_esce_come_il_vanilla(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(species=0, item=0, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertEqual(r["chiamate"], [],
                                 "con ITEM_NONE non si deve chiamare nulla")

    # -- (iii) evoluzione in coda: uscita vanilla, azione 9 -----------------
    def test_iii_evoluzione_in_coda_esce_con_azione_9(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(species=157, item=50, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_EVO)
                self.assertEqual(r["chiamate"], [])

    # -- (iv) registri callee-saved -----------------------------------------
    def test_iv_callee_saved_preservati(self):
        from banco import PM
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                r = b.esegui_blob()
                self.assertEqual(r["stato"], RESTA)
                self.assertEqual(r["r4"], PM, "r4 non è tornato al chiamante")
                for reg, atteso in CALLEE.items():
                    if reg == UC_ARM_REG_R4:
                        continue
                    self.assertEqual(r["callee"][reg], atteso,
                                     "registro callee-saved %d corrotto" % reg)

    def test_iv_bis_la_pila_torna_al_suo_posto(self):
        from banco import PILA
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                r = b.esegui_blob()
                self.assertEqual(r["sp"], PILA - 64, "sp sbilanciato")

    # -- gli altri cancelli --------------------------------------------------
    def test_g2_contesto_sbagliato_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(context=8)      # REPLACE_MOVE_LEVELUP
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertEqual(r["chiamate"], [])

    def test_g4_scorta_finita_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                b.quantita = 0
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertEqual([c[0] for c in r["chiamate"]],
                                 ["Bag_GetItemQuantity"])

    def test_g5_slot_fuori_squadra_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=7)          # la sentinella PARTY_MON_SELECTION_CONFIRM
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], AZ_0)
                self.assertNotIn("ClearFrameAndWindow2", [c[0] for c in r["chiamate"]])

    def test_g5_slot_oltre_il_conteggio_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=3)
                b.conteggio = 2            # squadra di due
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)

    def test_g5_slot_oltre_la_capienza_esce(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=3)
                b.capienza = 2
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)

    def test_slot_al_limite_resta(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(slot=5)
                b.conteggio = 6
                b.capienza = 6
                r = b.esegui()
                self.assertEqual(r["stato"], RESTA)

    def test_args_nullo_esce_senza_scrivere(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara(args_nullo=True, azione=0xEE)
                r = b.esegui()
                self.assertEqual(r["stato"], ESCI)
                self.assertEqual(r["azione"], 0xEE, "con args nullo non si scrive")

    def test_due_usi_di_fila_rendono_lo_stesso_esito(self):
        """R4 di M: la seconda caramella non deve comportarsi diversamente
        dalla prima. Si esegue due volte senza rifare lo stato."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b = self.banco(L)
                b.prepara()
                uno = b.esegui()
                due = b.esegui()
                self.assertEqual(uno["stato"], RESTA)
                self.assertEqual(due["stato"], RESTA)
                self.assertEqual([c[0] for c in uno["chiamate"]],
                                 [c[0] for c in due["chiamate"]])

    def test_il_gancio_e_una_bl_verso_il_blocco(self):
        """Il blob in ROM è quello del manifesto e il gancio ci punta."""
        m = manifesto()
        self.assertEqual(int(m["simboli"]["sgp_caramelle_gancio"], 16), 0x023DAC01)
        self.assertLessEqual(m["blob"]["byte"], 240)


if __name__ == "__main__":
    unittest.main()
