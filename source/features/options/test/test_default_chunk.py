#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-RIFINITURA-01 — i DEFAULT EFFETTIVI del chunk (v3).

IL DIFETTO CHE QUESTI TEST SORVEGLIANO E' REALE, ed e' stato trovato provando la
ROM nell'AVD (`SGP-1.2-AVD-02`, prova 4), non leggendo il codice.

Con un salvataggio della 1.1 il chunk e' ASSENTE (`load_status = 1`) e tutti i
suoi byte leggono 0. Ma il tetto NPC, con il chunk assente, e' **acceso**:
`sgp_npc_tetto` (`SGP-1.2-PRESTAZIONI-NPC-03/sorgenti/npc_tetto.c`) tratta
ASSENTE come «acceso di default». La pagina, che leggeva il byte, mostrava
«Fluidita' NPC: NO» su una funzione accesa; e confermando con A scriveva nel
chunk `npc = 0`, quindi al primo salvataggio il tetto si **spegneva davvero**.
Il giocatore vedeva una cosa, ne otteneva un'altra, e l'azione piu' innocua di
tutte — aprire la pagina e confermare senza cambiare niente — cambiava il
comportamento del gioco.

La cura NON sta in questa pagina, e questi test servono a tenerla fuori.
`SGP-1.2-QUALITA-NATIVO-01` (`sorgenti-v-finale/salva_blob.c`) la mette dove il
contratto dice che deve stare: D1, che possiede il formato, NORMALIZZA la copia
in RAM a ogni avvio e con chunk assente ci scrive i default 1.2 — `picco = 1` e
**`npc = 1`**. Da li' in poi il byte del chunk *e'* il valore effettivo.

Quello che la pagina deve garantire, e che qui si verifica, e' allora:
  1. **mostra** il byte del chunk, qualunque sia, senza inventarsi default;
  2. **non lo riscrive** per il solo fatto di essere aperta o confermata senza
     modifiche — altrimenti due cantieri scriverebbero lo stesso default e il
     secondo non saprebbe distinguere «il giocatore l'ha spento» da «nessuno
     l'ha ancora acceso»;
  3. scrive **solo** quello che il giocatore cambia.
Gli offset usati sono quelli del contratto nuovo, verificati uno per uno contro
`sorgenti-v-finale/sgp_chunk.h`: sono gli stessi di prima.
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, indirizzo, IND                              # noqa: E402
from test_blob import frame, tutto_presente, K_SELECT, K_A, K_B      # noqa: E402

STATO_PTR = 0x02240000
C_NPC = 0x07
ASSENTE, VALIDO, RIFIUTATO = 1, 2, 3


def chunk(b):
    return list(b.uc.mem_read(IND["stato_d1"] + 0x10, 16))


def voce_npc(b):
    """Indice reale della voce che comanda il tetto NPC (quale = 3)."""
    tab = list(b.uc.mem_read(IND["tab"], 24))
    for i in range(6):
        if (tab[4 * i + 3] & 0x0F) == 3:
            return i
    raise AssertionError("la voce del tetto NPC non e' nella tabella")


class D1LaPaginaDiceIlVero(unittest.TestCase):
    def test_con_chunk_normalizzato_la_voce_npc_e_accesa(self):
        """Il caso vero dopo il cantiere nativo: chunk ASSENTE ma gia'
        normalizzato da D1 con npc=1. La pagina deve mostrare ACCESO."""
        b = tutto_presente(Banco())
        b.stato_d1(load=ASSENTE, npc=1)
        frame(b, K_SELECT)
        u = b.leggi_ui()
        i = voce_npc(b)
        self.assertEqual(u["val"][i], 1, "la pagina mostra il byte del chunk")
        self.assertEqual(u["val0"][i], 1,
                         "e deve essere anche il valore di partenza, o B lo spegne")

    def test_confermare_senza_toccare_niente_non_cambia_il_chunk(self):
        """La prova che il giocatore faceva: apro, guardo, confermo. Nessun byte
        del chunk deve cambiare: la pagina scrive solo cio' che si e' scelto."""
        b = tutto_presente(Banco())
        b.stato_d1(load=ASSENTE, npc=1)
        prima = chunk(b)
        frame(b, K_SELECT)
        frame(b, K_A)
        self.assertEqual(chunk(b), prima,
                         "confermare senza cambiare niente non tocca il chunk")

    def test_annullare_con_B_non_cambia_il_chunk(self):
        b = tutto_presente(Banco())
        b.stato_d1(load=ASSENTE, npc=1)
        prima = chunk(b)
        frame(b, K_SELECT)
        frame(b, K_B)
        self.assertEqual(chunk(b), prima)

    def test_si_puo_ancora_spegnere_di_proposito(self):
        """Il default acceso non deve diventare un interruttore bloccato."""
        b = tutto_presente(Banco())
        b.stato_d1(load=ASSENTE, npc=1)
        frame(b, K_SELECT)
        i = voce_npc(b)
        riga = b.leggi_ui()["vis"].index(i)
        for _ in range(riga):
            frame(b, 0x080)                     # K_DOWN fino alla voce
        self.assertEqual(b.leggi_ui()["cursore"], riga)
        frame(b, 0x020)                         # K_LEFT: spegni
        self.assertEqual(b.leggi_ui()["val"][i], 0)
        frame(b, K_A)
        self.assertEqual(chunk(b)[C_NPC], 0, "chi lo spegne di proposito lo spegne")


class D2SoloIlByteGiusto(unittest.TestCase):
    def test_aprire_la_pagina_non_scrive_nel_chunk(self):
        """Il cancello che tiene l'inizializzazione FUORI da questa pagina: il
        chunk e' di D1, e aprire una schermata di lettura non deve cambiarlo di
        un bit. Se un domani qualcuno rimettesse un default qui dentro, questo
        test lo ferma."""
        for stato in (ASSENTE, VALIDO):
            for valore in (0, 1):
                b = tutto_presente(Banco())
                b.stato_d1(load=stato, npc=valore)
                prima = chunk(b)
                frame(b, K_SELECT)
                self.assertEqual(chunk(b), prima,
                                 f"load={stato} npc={valore}: aprire non scrive")

    def test_la_pagina_mostra_sempre_il_byte_del_chunk(self):
        for stato in (ASSENTE, VALIDO):
            for valore in (0, 1):
                b = tutto_presente(Banco())
                b.stato_d1(load=stato, npc=valore)
                frame(b, K_SELECT)
                self.assertEqual(b.leggi_ui()["val"][voce_npc(b)], valore,
                                 f"load={stato} npc={valore}")

    def test_con_chunk_rifiutato_non_si_scrive_niente(self):
        b = tutto_presente(Banco())
        b.stato_d1(load=RIFIUTATO, npc=0)
        prima = chunk(b)
        frame(b, K_SELECT)
        self.assertEqual(chunk(b), prima, "REJECT: il gioco resta in modo 1.1")

    def test_senza_la_guardia_di_D1_non_si_scrive_niente(self):
        """Se D1 non e' nella ROM, il chunk non esiste: non si inventa."""
        b = tutto_presente(Banco())
        b.stato_d1(guard=0, load=ASSENTE, npc=0)
        prima = chunk(b)
        frame(b, K_SELECT)
        self.assertEqual(chunk(b), prima)


class D3LaDomandaAlContinua(unittest.TestCase):
    """L'altra porta d'ingresso: chi conferma la domanda al «Continua» e poi
    salva, senza mai aprire la pagina. Anche li' il chunk non si inizializza."""

    def passo(self, b, entrata, stato, tasti=0):
        b.tasti(tasti)
        b.uc.mem_write(STATO_PTR, struct.pack("<i", stato))
        r0, fin = b.chiama(indirizzo(entrata), 0x02250000, STATO_PTR)
        return r0, struct.unpack("<i", b.uc.mem_read(STATO_PTR, 4))[0], fin

    def test_la_domanda_non_tocca_il_chunk_all_apertura(self):
        b = Banco()
        b.stato_d1(load=ASSENTE, npc=1)
        prima = chunk(b)
        self.passo(b, "sgp_cont_init", 0)
        self.assertEqual(chunk(b), prima,
                         "la schermata al Continua legge, non inizializza")

    def test_la_domanda_saltata_non_tocca_il_chunk(self):
        """Chunk gia' valido: la domanda non appare e non deve scrivere niente."""
        b = Banco()
        b.stato_d1(load=VALIDO, npc=1)
        prima = chunk(b)
        self.passo(b, "sgp_cont_init", 0)
        self.assertEqual(chunk(b), prima)

    def test_dopo_la_domanda_la_pagina_e_coerente(self):
        """Il percorso completo con il chunk normalizzato da D1: domanda ->
        conferma -> pagina. La voce del tetto dice ACCESO in tutte e due."""
        b = tutto_presente(Banco())
        b.stato_d1(load=ASSENTE, npc=1)
        self.passo(b, "sgp_cont_init", 0)
        self.assertEqual(chunk(b)[C_NPC], 1)
        frame(b, K_SELECT)
        self.assertEqual(b.leggi_ui()["val"][voce_npc(b)], 1)


if __name__ == "__main__":
    unittest.main()
