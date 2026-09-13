#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-RIFINITURA-01 — i BERSAGLI DEL TOCCO della pagina Opzioni (v3).

Perche' esistono. Il menu Opzioni che ospita la pagina si usa **tutto con lo
stilo**: misurato in questo cantiere su `base-1.1-EN.nds`, toccando la pillola
«Off» di «Battle Scene» a (170, 57) e osservando il riquadro rosso spostarsi su
quella riga (`prove/tocco-vanilla-EN.png`, i due fotogrammi affiancati). La v2
consumava gli eventi di tocco e non aveva un solo bersaglio: chi giocava con lo
stilo apriva la pagina e trovava una schermata che non rispondeva. E' la
differenza piu' grossa che la revisione e l'autovalutazione avessero lasciato
aperta (criterio 4, fermo a 3/5).

Come nel resto del pacchetto: il codice non si legge, si **esegue**. Ogni prova
qui sotto apre la pagina davvero e poi manda un tocco vero alle coordinate di
schermo, come fa il gioco.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, indirizzo, APP                          # noqa: E402
from test_blob import frame, tutto_presente, K_SELECT, K_A, K_B  # noqa: E402

# Geometria dichiarata in sorgenti/sgp_ui.h, ripetuta qui apposta: se qualcuno la
# cambia nel sorgente, i test devono accorgersene invece di seguirla.
PANNELLO_X, PANNELLO_W, PASSO_PX = 32, 192, 24
META = PANNELLO_X + PANNELLO_W // 2          # 128: A a sinistra, B a destra
VAL_X = PANNELLO_X + 132                     # 164: la colonna dei valori


def apri():
    b = tutto_presente(Banco())
    frame(b, K_SELECT)
    return b


def y_riga(b, r):
    """Il centro verticale della riga `r` del pannello, in pixel di schermo."""
    return b.leggi_ui()["ycont"] * 8 + r * PASSO_PX + PASSO_PX // 2


def tocca(b, x, y):
    b.tocco(x, y)
    return b.chiama(indirizzo("sgp_ui_frame"), APP)


def suoni(b):
    return [c["r"][0] for c in b.chiamate if c["f"] == "PlaySE"]


class T1Reciproca(unittest.TestCase):
    """La riga toccata si ricava con una reciproca (y*2731)>>16 invece che con
    una divisione per 24, perche' il caricatore vieta __aeabi_uidiv. Se la
    reciproca fosse sbagliata anche per un solo pixel, un tocco finirebbe sulla
    riga sbagliata: qui si verificano TUTTI i 192 valori possibili."""

    def test_tocco_riga_senza_divisione(self):
        for d in range(192):
            self.assertEqual((d * 2731) >> 16, d // 24, f"d={d}")


class T2Selezione(unittest.TestCase):
    def test_toccare_una_voce_la_seleziona_e_suona(self):
        b = apri()
        prima = b.leggi_ui()["cursore"]
        n = b.leggi_ui()["n_vis"]
        self.assertGreaterEqual(n, 2, "servono almeno due voci per la prova")
        b.chiamate.clear()
        tocca(b, PANNELLO_X + 40, y_riga(b, 3))     # riga 3 = terza voce
        u = b.leggi_ui()
        self.assertEqual(u["cursore"], 2)
        self.assertNotEqual(u["cursore"], prima)
        self.assertIn(1500, suoni(b), "il tocco deve suonare come lo scorrimento")

    def test_ritoccare_la_voce_gia_scelta_non_suona(self):
        """Il vanilla non ripete il suono se lo stato non cambia: `opz_cambia`
        lo fa gia' coi tasti, e il tocco non deve essere piu' rumoroso."""
        b = apri()
        b.chiamate.clear()
        tocca(b, PANNELLO_X + 40, y_riga(b, 1))     # riga 1 = voce gia' scelta
        self.assertEqual(b.leggi_ui()["cursore"], 0)
        self.assertEqual(suoni(b), [])

    def test_il_titolo_non_e_un_bersaglio(self):
        b = apri()
        prima = b.leggi_ui()
        b.chiamate.clear()
        tocca(b, PANNELLO_X + 40, y_riga(b, 0))
        self.assertEqual(b.leggi_ui()["cursore"], prima["cursore"])
        self.assertEqual(suoni(b), [])
        self.assertEqual(b.leggi_ui()["aperta"], 1)

    def test_fuori_dal_pannello_non_succede_niente(self):
        """Sopra, sotto, a sinistra e a destra del pannello: quattro tocchi a
        vuoto. Nessuno deve chiudere la pagina ne' muovere il cursore — e la
        pagina deve restare viva ai tasti dopo (cancello A5c)."""
        b = apri()
        u = b.leggi_ui()
        fuori = [(PANNELLO_X - 4, y_riga(b, 2)),
                 (PANNELLO_X + PANNELLO_W + 4, y_riga(b, 2)),
                 (PANNELLO_X + 40, u["ycont"] * 8 - 4),
                 (PANNELLO_X + 40, 190)]
        for x, y in fuori:
            b.chiamate.clear()
            r0, _ = tocca(b, x, y)
            self.assertEqual(r0, 1, f"({x},{y}): l'evento resta della pagina")
            self.assertEqual(b.leggi_ui()["aperta"], 1, f"({x},{y})")
            self.assertEqual(b.leggi_ui()["cursore"], u["cursore"], f"({x},{y})")
            self.assertEqual(suoni(b), [], f"({x},{y})")
        # e dopo i quattro tocchi a vuoto i tasti funzionano ancora
        b.chiamate.clear()
        frame(b, 0x080)                             # K_DOWN
        self.assertEqual(b.leggi_ui()["cursore"], 1)


class T3Valori(unittest.TestCase):
    def test_toccare_la_colonna_dei_valori_cambia_il_valore(self):
        b = apri()
        u = b.leggi_ui()
        i = u["vis"][0]
        prima = u["val"][i]
        b.chiamate.clear()
        tocca(b, VAL_X + 10, y_riga(b, 1))
        u = b.leggi_ui()
        self.assertNotEqual(u["val"][i], prima)
        self.assertIn(1500, suoni(b))

    def test_il_valore_gira_e_ricomincia(self):
        """Toccare una pillola non ha un «verso»: il valore avanza e ricomincia.
        La voce del server ha tre valori, quindi tre tocchi tornano al punto."""
        b = apri()
        u = b.leggi_ui()
        riga = u["n_vis"]                    # l'ultima voce: il server, 3 valori
        i = u["vis"][riga - 1]
        partenza = u["val"][i]
        visti = []
        for _ in range(3):
            tocca(b, VAL_X + 10, y_riga(b, riga))
            visti.append(b.leggi_ui()["val"][i])
        self.assertEqual(visti[-1], partenza, "dopo tre tocchi si torna all'inizio")
        self.assertEqual(len(set(visti)), 3, "i tre valori sono tutti diversi")

    def test_un_solo_tocco_seleziona_E_cambia(self):
        """Come nel vanilla, dove toccare la pillola di una riga non selezionata
        fa tutte e due le cose: due tocchi per cambiare un valore sarebbero un
        gesto che il menu ospite non chiede."""
        b = apri()
        u = b.leggi_ui()
        riga = 2
        i = u["vis"][riga - 1]
        prima = u["val"][i]
        self.assertNotEqual(u["cursore"], riga - 1)
        tocca(b, VAL_X + 10, y_riga(b, riga))
        u = b.leggi_ui()
        self.assertEqual(u["cursore"], riga - 1)
        self.assertNotEqual(u["val"][i], prima)

    def test_i_tasti_restano_non_ciclici(self):
        """Il tocco gira, i tasti no: nel menu vanilla sinistra/destra si fermano
        agli estremi, e quel comportamento non deve cambiare."""
        b = apri()
        u = b.leggi_ui()
        i = u["vis"][0]
        for _ in range(4):
            frame(b, 0x020)                  # K_LEFT, fino in fondo
        self.assertEqual(b.leggi_ui()["val"][i], 0)
        b.chiamate.clear()
        frame(b, 0x020)                      # ancora a sinistra: non gira
        self.assertEqual(b.leggi_ui()["val"][i], 0)
        self.assertEqual(suoni(b), [], "nessun suono se il valore non cambia")


class T4VoceDisattivata(unittest.TestCase):
    def test_una_voce_disattivata_non_risponde_al_tocco(self):
        """W1 assente: la riga «Server online» e' grigia. Coi tasti non suona e
        non cambia; col tocco nemmeno, altrimenti la pagina direbbe due cose
        diverse a seconda di come la si usa."""
        b = Banco()
        b.stato_npc()
        b.stato_anim()                       # W1 NON applicato
        frame(b, K_SELECT)
        u = b.leggi_ui()
        riga = u["n_vis"]                    # l'ultima visibile e' il server
        i = u["vis"][riga - 1]
        prima = u["val"][i]
        b.chiamate.clear()
        tocca(b, VAL_X + 10, y_riga(b, riga))
        self.assertEqual(b.leggi_ui()["val"][i], prima)
        self.assertEqual(suoni(b), [])
        self.assertEqual(b.leggi_ui()["aperta"], 1)


class T5Comandi(unittest.TestCase):
    """La riga dei comandi e' divisa a meta': sinistra «A: salva», destra
    «B: annulla». Sono i Conferma/Chiudi del menu vanilla, nelle stesse due
    colonne delle voci."""

    def test_meta_sinistra_salva_e_chiude(self):
        b = apri()
        u = b.leggi_ui()
        i = u["vis"][0]
        frame(b, 0x010)                      # K_RIGHT: cambia il primo valore
        atteso = b.leggi_ui()["val"][i]
        b.chiamate.clear()
        tocca(b, PANNELLO_X + 8, y_riga(b, u["n_righe"] - 1))
        self.assertEqual(b.leggi_ui()["aperta"], 0, "la pagina si chiude")
        self.assertIn(1562, suoni(b), "suono di conferma, come il tasto A")
        self.assertEqual(b.leggi_d1()["plus"], atteso, "la scelta e' stata scritta")

    def test_meta_destra_annulla_e_chiude(self):
        b = apri()
        u = b.leggi_ui()
        prima = b.leggi_d1()["plus"]
        frame(b, 0x010)                      # K_RIGHT: cambia il primo valore
        b.chiamate.clear()
        tocca(b, META + 8, y_riga(b, u["n_righe"] - 1))
        self.assertEqual(b.leggi_ui()["aperta"], 0)
        self.assertIn(2368, suoni(b), "suono di annullamento, come il tasto B")
        self.assertEqual(b.leggi_d1()["plus"], prima, "niente e' stato scritto")

    def test_la_riga_dei_comandi_e_disegnata_in_due_meta(self):
        """Se la riga tornasse una stringa sola, la meta' toccabile non sarebbe
        piu' definita: si controlla che le due meta' siano due stampe distinte,
        una a sinistra (x=20) e una allineata a destra."""
        b = apri()
        stampe = [c for c in b.chiamate if c["f"] == "AddTextPrinterWithColor"]
        x = sorted({c["r"][3] for c in stampe})
        self.assertIn(20, x, "la meta' sinistra sta nella colonna delle etichette")
        self.assertTrue(any(v > 100 for v in x),
                        "la meta' destra sta nella colonna dei valori")

    def test_se_i_comandi_non_sono_a_schermo_il_tocco_non_chiude(self):
        """Con un salvataggio RIFIUTATO la riga in fondo dice «dati illeggibili»,
        non i comandi: toccarla non deve chiudere niente."""
        b = tutto_presente(Banco())
        b.stato_d1(load=3)                   # REJECT
        frame(b, K_SELECT)
        u = b.leggi_ui()
        if not u["aperta"]:
            self.skipTest("con REJECT la pagina non si apre: gia' coperto altrove")
        b.chiamate.clear()
        tocca(b, PANNELLO_X + 8, y_riga(b, u["n_righe"] - 1))
        self.assertEqual(b.leggi_ui()["aperta"], 1)
        self.assertEqual(suoni(b), [])


class T6Chiusa(unittest.TestCase):
    def test_col_tocco_la_pagina_non_si_apre(self):
        """Invariante della v2 che la v3 non deve rompere: SELECT apre la pagina
        SOLO se non c'e' un tocco nello stesso fotogramma."""
        b = tutto_presente(Banco())
        r0, _ = frame(b, K_SELECT, touch=1)
        self.assertEqual(b.leggi_ui()["aperta"], 0)
        self.assertEqual(r0, 0, "l'evento resta dell'ospite")

    def test_un_tocco_a_pagina_chiusa_non_e_consumato(self):
        b = tutto_presente(Banco())
        b.tocco(PANNELLO_X + 40, 100)
        r0, _ = b.chiama(indirizzo("sgp_ui_frame"), APP)
        self.assertEqual(r0, 0, "il menu vanilla deve continuare a ricevere i tocchi")
        self.assertEqual(b.leggi_ui()["aperta"], 0)


if __name__ == "__main__":
    unittest.main()
