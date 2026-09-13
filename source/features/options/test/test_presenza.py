#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A1 della revisione R2 — la precondizione del chunk vale per OGNI voce.

IL DIFETTO. Fino alla 1.2 `opz_presente()` applicava la regola dell'accessore
unico (`sgp_chunk_opzione`: guardia di D1 **e** `load_status` ASSENTE o VALIDO)
solo alle due voci di D1. Le altre tre — animazioni, fluidita' NPC, Wi-Fi —
guardavano la sola guardia del PROPRIETARIO, un byte che scrive l'iniettore e
che vale sempre 0x5A/0x57: quindi «presente» sempre.

Con `load_status = 3 RIFIUTATO` (chunk trovato ma con un'invariante violata) o
`= 0` (gancio L0 mai eseguito) i consumatori leggono 0 e `sgp_chunk_scrivi`
rifiuta di scrivere — ma la pagina mostrava lo stesso le tre voci attive. Il
giocatore spostava il cursore, premeva A, sentiva il suono di conferma, vedeva
il valore nuovo disegnato, e non succedeva niente: ne' allora ne' mai. La
mitigazione esisteva solo per il pennino (il tocco sulla riga dei comandi era
gia' disabilitato); A e B restavano attivi.

QUESTI TEST. Non leggono il sorgente: **eseguono** `opz_presente` sul blob, un
`quale` alla volta, e poi guardano la pagina intera. L'ultimo costruisce un
MUTANTE — una copia dei sorgenti con le tre righe di prima rimesse al loro
posto — lo compila davvero e pretende che questa suite diventi rossa: un test
che non sa morire non prova niente.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, indirizzo                                   # noqa: E402
from test_blob import frame, tutto_presente, K_SELECT, K_A           # noqa: E402

PAC = Path(__file__).resolve().parent.parent
SORGENTI = PAC / "sorgenti"
COMPILA = PAC / "tools" / "compila.py"

# sgp_ui.h: Q_D1_PLUS 0, Q_D1_WILD 1, Q_ANIM 2, Q_NPC 3, Q_WIFI 4
Q_D1_PLUS, Q_D1_WILD, Q_ANIM, Q_NPC, Q_WIFI = 0, 1, 2, 3, 4
QUALI = (Q_D1_PLUS, Q_D1_WILD, Q_ANIM, Q_NPC, Q_WIFI)
ALTRUI = (Q_ANIM, Q_NPC, Q_WIFI)
NONE, ASSENTE, VALIDO, RIFIUTATO = 0, 1, 2, 3
# sgp_ui.h: enum dei testi
T_TITOLO, T_AIUTO_A, T_AIUTO_B, T_BLOCCATO, T_RIFIUTATO = 0, 1, 2, 3, 4


def presente(b, quale):
    """Esegue `opz_presente(quale)` e rende il valore u32 di ritorno."""
    r0, _fine = b.chiama(indirizzo("opz_presente"), quale)
    return r0


def banco_con(load, guard=0x5A):
    b = tutto_presente(Banco())
    b.stato_d1(guard=guard, load=load, npc=1, anim=1, wifi=1, plus=1, wild=1)
    return b


class A1Precondizione(unittest.TestCase):
    """Il cuore della correzione, voce per voce."""

    def test_con_chunk_utilizzabile_le_cinque_voci_sono_presenti(self):
        """Il controllo positivo: senza di lui «tutto assente» passerebbe."""
        for load in (ASSENTE, VALIDO):
            b = banco_con(load)
            for quale in QUALI:
                with self.subTest(load=load, quale=quale):
                    self.assertEqual(presente(b, quale), 1,
                                     "load=%d: la voce %d deve essere presente" % (load, quale))

    def test_con_chunk_rifiutato_nessuna_voce_e_presente(self):
        """load = 3 REJECT: il chunk c'e' ma non e' utilizzabile. Prima di A1
        le tre voci altrui rispondevano 1 lo stesso."""
        b = banco_con(RIFIUTATO)
        for quale in QUALI:
            with self.subTest(quale=quale):
                self.assertEqual(presente(b, quale), 0,
                                 "load=3 RIFIUTATO: la voce %d non e' presente" % quale)

    def test_con_load_zero_nessuna_voce_e_presente(self):
        """load = 0: il gancio L0 non e' mai passato, la copia in RAM non e'
        ancora normalizzata. Mostrare i suoi zeri come scelte e' una bugia."""
        b = banco_con(NONE)
        for quale in QUALI:
            with self.subTest(quale=quale):
                self.assertEqual(presente(b, quale), 0,
                                 "load=0: la voce %d non e' presente" % quale)

    def test_senza_la_guardia_di_D1_nessuna_voce_e_presente(self):
        for load in (NONE, ASSENTE, VALIDO, RIFIUTATO):
            b = banco_con(load, guard=0)
            for quale in QUALI:
                with self.subTest(load=load, quale=quale):
                    self.assertEqual(presente(b, quale), 0)

    def test_la_guardia_del_proprietario_resta_necessaria(self):
        """La precondizione si AGGIUNGE, non sostituisce: con il chunk buono ma
        senza il blocco del proprietario nella ROM, la voce non c'e'."""
        for load in (ASSENTE, VALIDO):
            b = Banco()                       # stati altrui azzerati
            b.stato_d1(guard=0x5A, load=load, npc=1, anim=1, wifi=1)
            for quale in ALTRUI:
                with self.subTest(load=load, quale=quale):
                    self.assertEqual(presente(b, quale), 0)


class A1LaPagina(unittest.TestCase):
    """La conseguenza visibile: con un chunk inutilizzabile ogni voce e'
    disattivata, il valore mostrato e' 0, la riga di aiuto lo dice e A non
    conferma niente."""

    def test_con_chunk_rifiutato_nessuna_voce_e_attiva(self):
        """Le voci che non si nascondono restano a schermo ma DISATTIVATE, e il
        valore mostrato e' 0 per tutte: e' la forma che la pagina ha sempre
        avuto per «il proprietario non c'e'», applicata ora anche qui. La riga
        di aiuto lo dice: T_RIFIUTATO con load=3, T_BLOCCATO con load=0."""
        for load, aiuto in ((RIFIUTATO, T_RIFIUTATO), (NONE, T_BLOCCATO)):
            b = banco_con(load)
            frame(b, K_SELECT)
            u = b.leggi_ui()
            with self.subTest(load=load):
                self.assertEqual(u["val"][:5], [0, 0, 0, 0, 0],
                                 "load=%d: nessun valore dev'essere mostrato acceso" % load)
                r0, _ = b.chiama(indirizzo("opz_aiuto_id"))
                self.assertEqual(r0, aiuto,
                                 "load=%d: la riga di aiuto deve dirlo" % load)
                for quale in QUALI:
                    self.assertEqual(presente(b, quale), 0)

    def test_con_chunk_rifiutato_A_non_scrive_nel_chunk(self):
        from banco import IND
        for load in (NONE, RIFIUTATO):
            b = banco_con(load)
            prima = list(b.uc.mem_read(IND["stato_d1"] + 0x10, 16))
            frame(b, K_SELECT)
            frame(b, K_A)
            with self.subTest(load=load):
                self.assertEqual(list(b.uc.mem_read(IND["stato_d1"] + 0x10, 16)), prima,
                                 "load=%d: confermare non deve cambiare un bit" % load)

    def test_con_chunk_utilizzabile_le_voci_si_vedono(self):
        """Il controprova della precedente: la pagina non e' rotta, e' la
        precondizione a spegnerla quando deve."""
        b = banco_con(VALIDO)
        frame(b, K_SELECT)
        self.assertEqual(b.leggi_ui()["n_vis"], 5)


# --------------------------------------------------------------------------
# Il mutante: rimette le tre righe di prima e ricompila davvero.
MUTANTE_PRIMA = """    if (SGP_D1_GUARDIA != SGP_D1_GUARD
        || (SGP_D1_LOAD != SGP_LOAD_ABSENT && SGP_D1_LOAD != SGP_LOAD_VALID)) {
        return 0u;
    }
    if (quale == Q_D1_PLUS || quale == Q_D1_WILD) {
        return 1u;
    }
"""
MUTANTE_DOPO = """    if (quale == Q_D1_PLUS || quale == Q_D1_WILD) {
        return (SGP_D1_GUARDIA == SGP_D1_GUARD
                && (SGP_D1_LOAD == SGP_LOAD_ABSENT
                    || SGP_D1_LOAD == SGP_LOAD_VALID)) ? 1u : 0u;
    }
"""


def _compilatore_c_e():
    r = subprocess.run(["clang", "--target=armv5te-none-eabi", "-mcpu=arm946e-s",
                        "-mthumb", "-ffreestanding", "-c", "-x", "c", os.devnull,
                        "-o", os.devnull], capture_output=True)
    return r.returncode == 0


@unittest.skipUnless(_compilatore_c_e(), "serve clang con il bersaglio armv5te-none-eabi")
class A1Mutante(unittest.TestCase):
    """M1 — si toglie la precondizione dai sorgenti, si ricompila il blob e si
    rigira QUESTA STESSA suite contro il blob mutato: dev'essere rossa. Senza
    questo, i test sopra potrebbero essere veri per costruzione."""

    def test_senza_la_precondizione_la_suite_diventa_rossa(self):
        with tempfile.TemporaryDirectory(prefix="sgp-a1-mut-") as d:
            d = Path(d)
            sorg = d / "sorgenti"
            shutil.copytree(SORGENTI, sorg)
            pagina = sorg / "opzioni_pagina.c"
            testo = pagina.read_text()
            self.assertIn(MUTANTE_PRIMA, testo,
                          "il sorgente non ha piu' la forma che questo mutante conosce")
            pagina.write_text(testo.replace(MUTANTE_PRIMA, MUTANTE_DOPO))

            build = d / "build"
            amb = dict(os.environ, SGP_UI_SORGENTI=str(sorg))
            r = subprocess.run([sys.executable, str(COMPILA), "--uscita", str(build)],
                               capture_output=True, text=True, env=amb)
            self.assertEqual(r.returncode, 0, "il mutante non compila: %s" % r.stderr[-800:])
            for f in sorted((PAC / "prove/testi").iterdir()):
                if f.is_file():
                    shutil.copy2(f, build / f.name)

            amb2 = dict(os.environ, SGP_UI_BUILD=str(build), PYTHONDONTWRITEBYTECODE="1")
            r2 = subprocess.run([sys.executable, "-m", "unittest",
                                 "test_presenza.A1Precondizione",
                                 "test_presenza.A1LaPagina"],
                                cwd=str(Path(__file__).resolve().parent),
                                capture_output=True, text=True, env=amb2)
            # Rossa non basta: dev'essere rossa AVENDO ESEGUITO dei test. Una
            # suite che non parte esce rossa e passerebbe per un mutante
            # ucciso da un cancello che non ha girato.
            self.assertRegex(r2.stderr, r"Ran [1-9]\d* tests?",
                             "la suite figlia non ha eseguito nessun test: il mutante "
                             "non e' valutabile\n" + r2.stderr[-2000:])
            self.assertNotEqual(r2.returncode, 0,
                                "il mutante e' SOPRAVVISSUTO: senza la precondizione i "
                                "test restano verdi, quindi non provano niente\n"
                                + r2.stderr[-2000:])
            self.assertIn("load=3 RIFIUTATO", r2.stderr,
                          "il mutante e' morto, ma non per il motivo giusto")


if __name__ == "__main__":
    unittest.main()
