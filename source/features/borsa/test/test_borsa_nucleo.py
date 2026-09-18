#!/usr/bin/env python3
"""SGP-1.2-BORSA-GEN-03 — la suite. Gira sull'ARM9 VERO di una ROM 1.2.2.

    SGP_ROM_DIR=/percorso/alle/rom \
        python3 -m unittest discover -s test -v

E' la matrice T1 di `U-borsa-progetto-esecutivo.md` §5. Ogni caso parte dal
trampolino — l'indirizzo che l'applicatore scrivera' in `gScriptCmdTable` — e
legge l'esito dai byte: la variabile di risultato, la staffetta nel blocco,
il flag «scartato», la sequenza di chiamate native, l'avanzamento di
`script_ptr`. Nessun caso consulta il sorgente C.

La via NON permissiva non e' confrontata con un'imitazione del vanilla: chiama
gli originali 0x0204EA89 e 0x0204E9D9, che nel banco girano davvero. Per questo
la firma «e' davvero il vanilla» e' l'ASSENZA di `Bag_GetItemPocket` e
`Bag_GetItemQuantity` fra le chiamate — il vanilla non le fa mai.

GPL-3.0-or-later.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import (  # noqa: E402
    Banco, Membro, rom, rom_presenti, manifesto, ROM_NOME, LINGUE, CALLEE,
    BLOCCO, N_TABELLA, PILA, fnv16,
    POCKET_ITEMS, POCKET_MEDICINE, POCKET_TMHMS, POCKET_MAIL, POCKET_KEY_ITEMS)

ITEM = 50            # un oggetto qualunque: l'id e' un letterale (< 0x4000)
RETVAR = 0x4001      # la variabile in cui i due comandi scrivono il risultato
X_FLAG = 0x800A      # il flag «scartato» che legge l'appendice (sgp_borsa.h)
X800D = 0x800D       # VAR_SPECIAL_LAST_TALKED: del MOTORE, non nostro
SPAZZATURA = 0x2B0C  # un valore qualunque gia' presente nella variabile

OFF_DONO = 96        # sito «di dono»: finestra piena (96 + 8 > 32)
OFF_STD = 144        # il sito comune del membro 3, MAI in tabella
OFF_CORTO = 8        # sito vicino all'inizio: finestra accorciata a 16 B

MOTIVO = ("classe B: serve $SGP_ROM_DIR con " + ROM_NOME % "{EN,IT}")


def membro(off, opcode, qty=1, seme=0x5A):
    return Membro(off, opcode, (ITEM, qty, RETVAR), seme=seme)


@unittest.skipUnless(rom_presenti(), MOTIVO)
class ProveBorsa(unittest.TestCase):
    """Ogni prova gira su EN e su IT: gli indirizzi ARM9 statici coincidono
    (RAPPORTO §2), e questa suite e' il controllo che continuino a coincidere."""

    # ------------------------------------------------------------ utilita' ---
    def banco127(self, lingua, qty=1, permissivo=True, off=OFF_DONO, seme=0x5A):
        m = membro(off, 127, qty, seme)
        b = Banco(rom(lingua), tabella=[m.chiave()] if permissivo else [])
        b.prepara(m)
        return b, m

    def banco125(self, lingua, qty=1, permissivo=False, off=OFF_STD, seme=0x5A):
        m = membro(off, 125, qty, seme)
        b = Banco(rom(lingua), tabella=[m.chiave()] if permissivo else [])
        b.prepara(m)
        return b, m

    def assert_sano(self, r):
        """Cio' che deve valere in OGNI caso, permissivo o no."""
        self.assertEqual(r["reso"], 0, "le ScrCmd rendono sempre FALSE")
        self.assertEqual(r["avanzamento"], 6,
                         "script_ptr deve avanzare dei 3 argomenti, ne' piu' ne' meno")
        self.assertTrue(r["canarino"], "canarino del blocco toccato")
        self.assertEqual(r["sp"], PILA - 64, "pila sbilanciata")
        for reg, atteso in CALLEE.items():
            self.assertEqual(r["callee"][reg], atteso,
                             "registro callee-saved %d corrotto" % reg)

    def assert_vanilla(self, b, r):
        """Il vanilla non guarda mai la tasca ne' la scorta: se quelle due
        chiamate compaiono, non stiamo eseguendo l'originale."""
        nomi = b.nomi(r)
        self.assertNotIn("Bag_GetItemPocket", nomi)
        self.assertNotIn("Bag_GetItemQuantity", nomi)
        self.assertEqual(r["staffetta"]["armata"], 0)

    # ====================================================== [127] permissivo ===
    def test_t1a_al_tetto_999_dice_che_ce_spazio_e_arma(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=1)
                b.tasca, b.quantita = POCKET_ITEMS, 999
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(b.var(RETVAR), 1, "deve dire «c'e' spazio»")
                self.assertNotIn("Bag_HasSpaceForItem", b.nomi(r),
                                 "al tetto la risposta e' nostra, non della Borsa")
                self.assertEqual(r["staffetta"],
                                 {"armata": 1, "item": ITEM, "chieste": 1,
                                  "entrate": 0})

    def test_t1b_997_piu_5_arma_per_una_consegna_parziale(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=5)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 997, 1
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(r["staffetta"],
                                 {"armata": 1, "item": ITEM, "chieste": 5,
                                  "entrate": 2}, "999 - 997 = 2")
                sp = [c for c in r["chiamate"] if c[0] == "Bag_HasSpaceForItem"]
                self.assertEqual(len(sp), 1)
                self.assertEqual(sp[0][2], ITEM)
                self.assertEqual(sp[0][3], 2, "si chiede spazio per 2, non per 5")
                self.assertEqual(b.var(RETVAR), 1)

    def test_t1c_con_spazio_abbondante_si_comporta_come_il_vanilla(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=5)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 10, 1
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(r["staffetta"]["armata"], 0,
                                 "niente da scartare, niente staffetta")
                sp = [c for c in r["chiamate"] if c[0] == "Bag_HasSpaceForItem"]
                self.assertEqual(sp[0][3], 5, "la quantita' piena, come il vanilla")
                self.assertEqual(b.var(RETVAR), 1)
                self.assertEqual(b.var(X_FLAG), 0, "il flag resta basso")

    def test_t1d_slot_mancante_non_e_tetto_raggiunto(self):
        """Oggetto assente e tasca senza slot liberi: rifiuto vanilla e nessuna
        staffetta, cosi' `std_bag_is_full` (2009) compare come sempre."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=1)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 0, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(b.var(RETVAR), 0)
                self.assertEqual(r["staffetta"]["armata"], 0)

    def test_t1e_rifiuto_della_borsa_disarma_una_staffetta_parziale(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=5)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 997, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(b.var(RETVAR), 0)
                self.assertEqual(r["staffetta"]["armata"], 0,
                                 "rifiuto vero: niente messaggio, niente staffetta")

    # ----------------------------------------------------------- i tetti ---
    def test_t1f_mt_mn_hanno_tetto_99_non_999(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=1)
                b.tasca, b.quantita = POCKET_TMHMS, 99
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(r["staffetta"]["armata"], 1,
                                 "99 MT e' il tetto della tasca 3")
                self.assertEqual(b.var(RETVAR), 1)

    def test_t1f_bis_99_in_una_tasca_normale_non_e_il_tetto(self):
        """Il controllo che rende utile il precedente: stessa scorta, tasca
        diversa, esito opposto."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=1)
                b.tasca, b.quantita, b.spazio = POCKET_MEDICINE, 99, 1
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(r["staffetta"]["armata"], 0)
                sp = [c for c in r["chiamate"] if c[0] == "Bag_HasSpaceForItem"]
                self.assertEqual(sp[0][3], 1)

    def test_t1g_oggetti_chiave_e_posta_sono_immuni(self):
        for tasca in (POCKET_KEY_ITEMS, POCKET_MAIL):
            for L in LINGUE:
                with self.subTest(lingua=L, tasca=tasca):
                    b, _ = self.banco127(L, qty=1)
                    b.tasca, b.quantita, b.spazio = tasca, 999, 0
                    r = b.esegui(127)
                    self.assert_sano(r)
                    self.assertEqual(r["staffetta"]["armata"], 0)
                    self.assertNotIn("Bag_GetItemQuantity", b.nomi(r),
                                     "uscita anticipata: la scorta non si guarda")
                    self.assertEqual(b.var(RETVAR), 0, "rifiuto vanilla")

    # ================================================== [127] non permissivo ===
    def test_t1h_sito_fuori_tabella_e_vanilla_bit_per_bit(self):
        """Angolo dei Premi, negozi, scambi: 999 in borsa, rifiuto secco."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=1, permissivo=False)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 999, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assert_vanilla(b, r)
                self.assertEqual(b.var(RETVAR), 0)
                self.assertEqual(b.nomi(r),
                                 ["ScriptGetVar", "ScriptGetVar", "GetVarPointer",
                                  "Save_Bag_Get", "Bag_HasSpaceForItem"],
                                 "la sequenza di 0x0204EA89, nel suo ordine")

    def test_t1i_stesso_offset_impronta_diversa_non_e_permissivo(self):
        """Due membri diversi possono avere un sito allo stesso offset: e'
        l'impronta a separarli, ed e' questa la prova che serve davvero."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                altro = membro(OFF_DONO, 127, 1, seme=0x11)
                nostro = membro(OFF_DONO, 127, 1, seme=0x5A)
                self.assertEqual(altro.chiave() >> 16, nostro.chiave() >> 16)
                self.assertNotEqual(altro.chiave(), nostro.chiave())
                b = Banco(rom(L), tabella=[altro.chiave()])
                b.prepara(nostro)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 999, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assert_vanilla(b, r)
                self.assertEqual(b.var(RETVAR), 0)

    def test_t1j_blocco_a_zero_e_gioco_nudo(self):
        """Tabella tutta a zero e puntatori agli originali non scritti: il blob
        deve comportarsi come il gioco senza di noi, non saltare a 0."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                m = membro(OFF_DONO, 127, 1)
                b = Banco(rom(L), tabella=[], orig_da_blocco=False)
                b.prepara(m)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 999, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assert_vanilla(b, r)
                self.assertEqual(b.var(RETVAR), 0)

    # ------------------------------------------------------- la tabella ---
    def test_t1k_voce_nell_ultimo_posto_utile(self):
        """120 voci sono il limite dichiarato: l'ultima dev'essere raggiunta."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                m = membro(OFF_DONO, 127, 1)
                riempitivo = [0xDEAD0000 | i for i in range(N_TABELLA - 1)]
                b = Banco(rom(L), tabella=riempitivo + [m.chiave()])
                b.prepara(m)
                b.tasca, b.quantita = POCKET_ITEMS, 999
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(r["staffetta"]["armata"], 1)

    def test_t1l_uno_zero_chiude_la_tabella(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                m = membro(OFF_DONO, 127, 1)
                b = Banco(rom(L), tabella=[0xDEAD0001, 0, m.chiave()])
                b.prepara(m)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 999, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assert_vanilla(b, r)

    def test_t1m_sito_vicino_all_inizio_accorcia_la_finestra(self):
        """A 8 byte dall'inizio del membro la finestra vale 16 B, non 32: se il
        blob leggesse 32 byte, leggerebbe PRIMA del membro e l'impronta non
        combacerebbe."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                m = membro(OFF_CORTO, 127, 1)
                b = Banco(rom(L), tabella=[m.chiave()])
                b.prepara(m)
                b.tasca, b.quantita = POCKET_ITEMS, 999
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(r["staffetta"]["armata"], 1)

    def test_t1m_bis_una_finestra_piena_a_quell_offset_non_combacia(self):
        """Il rovescio del precedente: la chiave calcolata con 32 byte — cioe'
        sconfinando fuori dal membro — NON deve essere accettata."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                m = membro(OFF_CORTO, 127, 1)
                prima = bytes((0xA0 + i) & 0xFF for i in range(16))
                sbagliata = ((OFF_CORTO & 0xFFFF) << 16) | fnv16(
                    prima + m.byte[:OFF_CORTO + 8])
                self.assertNotEqual(sbagliata, m.chiave())
                b = Banco(rom(L), tabella=[sbagliata])
                b.prepara(m)
                b.tasca, b.quantita, b.spazio = POCKET_ITEMS, 999, 0
                r = b.esegui(127)
                self.assert_sano(r)
                self.assert_vanilla(b, r)

    # ============================================================== [125] ===
    def test_t2a_staffetta_armata_consegna_il_nulla_e_alza_il_flag(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1)
                b.arma(ITEM, 1, 0)
                b.tasca, b.quantita = POCKET_ITEMS, 999
                r = b.esegui(125)
                self.assert_sano(r)
                self.assertNotIn("Bag_AddItem", b.nomi(r),
                                 "non entra niente: Bag_AddItem non si chiama")
                self.assertEqual(b.var(RETVAR), 1, "«ricevuto»: l'evento passa")
                self.assertEqual(b.var(X_FLAG), 1, "il flag «scartato» dev'essere alto")
                self.assertEqual(r["staffetta"]["armata"], 0, "consumata")

    def test_t2b_consegna_parziale_aggiunge_due_e_alza_il_flag(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=5)
                b.arma(ITEM, 5, 2)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 997, 1
                r = b.esegui(125)
                self.assert_sano(r)
                add = [c for c in r["chiamate"] if c[0] == "Bag_AddItem"]
                self.assertEqual(len(add), 1)
                self.assertEqual(add[0][2], ITEM)
                self.assertEqual(add[0][3], 2, "ne devono entrare 2, non 5")
                self.assertEqual(b.var(RETVAR), 1)
                self.assertEqual(b.var(X_FLAG), 1)

    def test_t2c_sito_in_tabella_con_spazio_non_alza_il_flag(self):
        """I 5 `GiveItem` permissivi (membri 141, 145, 240, 938): quando c'e'
        posto devono comportarsi come il vanilla e tacere."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=5, permissivo=True, off=OFF_DONO)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 10, 1
                r = b.esegui(125)
                self.assert_sano(r)
                add = [c for c in r["chiamate"] if c[0] == "Bag_AddItem"]
                self.assertEqual(add[0][3], 5, "la quantita' piena")
                self.assertEqual(b.var(RETVAR), 1)
                self.assertEqual(b.var(X_FLAG), 0, "niente scartato, niente flag")

    def test_t2d_staffetta_non_armata_e_vanilla(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 999, 0
                r = b.esegui(125)
                self.assert_sano(r)
                self.assert_vanilla(b, r)
                self.assertEqual(b.var(RETVAR), 0)
                self.assertEqual(b.var(X_FLAG), 0)
                self.assertEqual(b.nomi(r),
                                 ["GetVarPointer",
                                  "ScriptGetVar", "ScriptGetVar", "ScriptGetVar",
                                  "ScriptGetVar", "GetVarPointer", "Save_Bag_Get",
                                  "Bag_AddItem"],
                                 "azzeramento del flag, due sbirciate nostre, "
                                 "poi la sequenza di 0x0204E9D9")

    def test_t2e_staffetta_per_un_altro_oggetto_e_vanilla(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1)
                b.arma(ITEM + 1, 1, 0)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 999, 0
                r = b.esegui(125)
                self.assert_sano(r)
                self.assert_vanilla(b, r)
                self.assertEqual(b.var(X_FLAG), 0)

    def test_t2f_staffetta_per_un_altra_quantita_e_vanilla(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1)
                b.arma(ITEM, 7, 0)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 999, 0
                r = b.esegui(125)
                self.assert_sano(r)
                self.assert_vanilla(b, r)

    def test_t2g_la_seconda_125_di_fila_e_vanilla(self):
        """La staffetta e' monouso: la consuma la prima 125."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, m = self.banco125(L, qty=1)
                b.arma(ITEM, 1, 0)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 999, 0
                uno = b.esegui(125)
                self.assertEqual(b.var(X_FLAG), 1)
                b.prepara(m)                      # rimette il membro e azzera le var
                due = b.esegui(125)
                self.assert_sano(due)
                self.assert_vanilla(b, due)
                self.assertEqual(b.var(RETVAR), 0)
                self.assertEqual(b.var(X_FLAG), 0, "la seconda non alza niente")
                self.assertEqual(uno["staffetta"]["armata"], 0)

    def test_t2h_oggetti_chiave_al_tetto_restano_vanilla_anche_col_125(self):
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1, permissivo=True, off=OFF_DONO)
                b.tasca, b.quantita, b.aggiunta = POCKET_KEY_ITEMS, 999, 1
                r = b.esegui(125)
                self.assert_sano(r)
                add = [c for c in r["chiamate"] if c[0] == "Bag_AddItem"]
                self.assertEqual(add[0][3], 1, "quantita' piena: nessuno sconto")
                self.assertEqual(b.var(X_FLAG), 0)

    # ==================================================== la coppia 127+125 ===
    def test_t3_la_staffetta_attraversa_due_ScriptContext(self):
        """Il caso vero: il 127 gira nel membro del sito, il 125 nel membro 3
        (`std_give_item_verbose`), che NON e' in tabella. E' l'unica ragione per
        cui la staffetta vive in RAM di riserva e non dentro `ScriptContext`."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                sito = membro(OFF_DONO, 127, 1)
                std = membro(OFF_STD, 125, 1)
                b = Banco(rom(L), tabella=[sito.chiave()])
                b.tasca, b.quantita = POCKET_ITEMS, 999

                b.prepara(sito)
                r1 = b.esegui(127)
                self.assert_sano(r1)
                self.assertEqual(b.var(RETVAR), 1, "il 127 dice «c'e' spazio»")

                b.prepara(std)
                r2 = b.esegui(125)
                self.assert_sano(r2)
                self.assertNotIn("Bag_AddItem", b.nomi(r2))
                self.assertEqual(b.var(RETVAR), 1)
                self.assertEqual(b.var(X_FLAG), 1)

    def test_t3_bis_un_127_di_negozio_chiude_la_staffetta(self):
        """Un 127 qualunque azzera la staffetta: se fra il dono e la consegna
        si infilasse un controllo di spazio a pagamento, l'oggetto pagato non
        potrebbe mai essere scartato."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                negozio = membro(OFF_DONO, 127, 1, seme=0x11)
                std = membro(OFF_STD, 125, 1)
                b = Banco(rom(L), tabella=[])
                b.tasca, b.quantita, b.spazio, b.aggiunta = POCKET_ITEMS, 999, 0, 0
                b.arma(ITEM, 1, 0)

                b.prepara(negozio)
                b.esegui(127)
                self.assertEqual(b.staffetta()["armata"], 0)

                b.prepara(std)
                r = b.esegui(125)
                self.assert_vanilla(b, r)
                self.assertEqual(b.var(X_FLAG), 0)


    # ================================== il flag «scartato» e LAST_TALKED ===
    # Regressione del difetto 1.2.1: il flag stava su VAR_SPECIAL_x800D, che e'
    # VAR_SPECIAL_LAST_TALKED — la variabile in cui il MOTORE mette l'id
    # dell'oggetto con cui si e' interagito (1 per le Poke Ball a terra). La
    # guardia dell'appendice risultava gia' soddisfatta e il messaggio
    # «Borsa piena / l'oggetto e' stato lasciato» usciva su una raccolta
    # perfettamente riuscita.
    def test_t4a_il_flag_non_e_last_talked(self):
        """Uno scarto vero alza il flag e NON tocca VAR_SPECIAL_LAST_TALKED."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1)
                b.scrivi_var(X800D, 1)          # il motore: «hai parlato con l'oggetto 1»
                b.arma(ITEM, 1, 0)
                b.tasca, b.quantita = POCKET_ITEMS, 999
                r = b.esegui(125)
                self.assert_sano(r)
                self.assertNotEqual(X_FLAG, X800D,
                                    "il flag non puo' essere LAST_TALKED")
                self.assertEqual(b.var(X_FLAG), 1, "il flag «scartato» e' alto")
                self.assertEqual(b.var(X800D), 1,
                                 "LAST_TALKED deve restare l'id dell'oggetto")

    def test_t4b_last_talked_uguale_a_uno_non_alza_il_flag(self):
        """Il caso del difetto: Ball a terra (LAST_TALKED = 1), c'e' posto,
        niente viene scartato. La guardia dell'appendice deve restare chiusa."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco125(L, qty=1, permissivo=True, off=OFF_DONO)
                b.scrivi_var(X800D, 1)
                b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 0, 1
                r = b.esegui(125)
                self.assert_sano(r)
                self.assertEqual(b.var(RETVAR), 1, "l'oggetto entra")
                self.assertEqual(b.var(X_FLAG), 0,
                                 "niente scartato: nessun messaggio")
                self.assertEqual(b.var(X800D), 1, "LAST_TALKED intatto")

    def test_t4c_il_125_azzera_sempre_il_flag_anche_sulla_via_vanilla(self):
        """La ScriptEnvironment sta sull'heap e la speciale nasce sporca
        (misurata in partita: 1 dopo una raccolta, 11 a riposo). Ogni 125 —
        permissivo, armato o vanilla — deve riportarla a un valore noto."""
        for L in LINGUE:
            for permissivo in (False, True):
                with self.subTest(lingua=L, permissivo=permissivo):
                    b, _ = self.banco125(L, qty=1, permissivo=permissivo,
                                         off=OFF_DONO if permissivo else OFF_STD)
                    b.scrivi_var(X_FLAG, 1)     # spazzatura: «scartato» acceso
                    b.tasca, b.quantita, b.aggiunta = POCKET_ITEMS, 0, 1
                    r = b.esegui(125)
                    self.assert_sano(r)
                    self.assertEqual(b.var(X_FLAG), 0,
                                     "il 125 deve riportare il flag a 0")

    def test_t4d_il_127_non_tocca_ne_il_flag_ne_last_talked(self):
        """Il controllo di spazio non consegna niente: non ha nulla da dire
        all'appendice, e non deve sporcare nessuna delle due variabili."""
        for L in LINGUE:
            with self.subTest(lingua=L):
                b, _ = self.banco127(L, qty=1)
                b.scrivi_var(X800D, SPAZZATURA)
                b.scrivi_var(X_FLAG, SPAZZATURA)
                b.tasca, b.quantita = POCKET_ITEMS, 999
                r = b.esegui(127)
                self.assert_sano(r)
                self.assertEqual(b.var(X800D), SPAZZATURA)
                self.assertEqual(b.var(X_FLAG), SPAZZATURA)

    def test_t4e_il_flag_e_lo_stesso_nel_C_e_nel_bytecode(self):
        """Le due meta' della staffetta lunga — il gancio ARM9 e l'appendice di
        bytecode — devono nominare la STESSA variabile, e non quella del motore."""
        import re
        import importlib.util
        pac = Path(__file__).resolve().parents[1]
        testo = (pac / "sorgenti" / "sgp_borsa.h").read_text()
        m = re.search(r"#define\s+SGP_VAR_SCARTATO\s+(0x[0-9A-Fa-f]+)u", testo)
        self.assertIsNotNone(m, "SGP_VAR_SCARTATO non trovata nell'intestazione")
        dal_c = int(m.group(1), 16)
        spec = importlib.util.spec_from_file_location(
            "_app_def", pac / "tools" / "appendici_def.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(dal_c, mod.VAR_SCARTATO)
        self.assertEqual(dal_c, X_FLAG)
        self.assertNotEqual(dal_c, 0x800D, "0x800D e' VAR_SPECIAL_LAST_TALKED")
        self.assertNotEqual(dal_c, 0x800C, "0x800C e' VAR_SPECIAL_RESULT")

    # ========================================================== il manifesto ===
    def test_i_trampolini_stanno_agli_offset_fissi(self):
        m = manifesto()
        self.assertEqual(int(m["simboli"]["sgp_borsa_cmd127"], 16), BLOCCO + 1)
        self.assertEqual(int(m["simboli"]["sgp_borsa_cmd125"], 16), BLOCCO + 9)
        self.assertEqual(m["indirizzi"]["ganci"]["valore_127"], hex(BLOCCO + 1))
        self.assertEqual(m["indirizzi"]["ganci"]["valore_125"], hex(BLOCCO + 9))
        self.assertLessEqual(m["blob"]["byte"], m["blob"]["max"])

    def test_le_due_voci_di_tabella_sono_quelle_che_crediamo(self):
        """La ROM finale installa i ganci e conserva i puntatori vanilla.

        Si legge il file prima che Banco rimpiazzi il blocco con la fixture.
        """
        import struct as _s
        from banco import segmenti_arm9
        for L in LINGUE:
            with self.subTest(lingua=L):
                segmenti = list(segmenti_arm9(rom(L)))

                def parola(addr):
                    for ram, dati in segmenti:
                        if ram <= addr <= ram + len(dati) - 4:
                            return _s.unpack_from("<I", dati, addr - ram)[0]
                    self.fail("Indirizzo fuori dai segmenti ARM9: %x" % addr)

                self.assertEqual(parola(0x020FAD00 + 4 * 125), 0x023DAD09)
                self.assertEqual(parola(0x020FAD00 + 4 * 127), 0x023DAD01)
                self.assertEqual(parola(0x023DB2E0), 0x0204EA89)
                self.assertEqual(parola(0x023DB2E4), 0x0204E9D9)
        g = manifesto()["indirizzi"]["ganci"]
        self.assertEqual(int(g["voce_125"], 16), 0x020FAD00 + 4 * 125)
        self.assertEqual(int(g["voce_127"], 16), 0x020FAD00 + 4 * 127)
        self.assertEqual(int(g["originale_125"], 16), 0x0204E9D9)
        self.assertEqual(int(g["originale_127"], 16), 0x0204EA89)


if __name__ == "__main__":
    unittest.main()
