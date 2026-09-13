#!/usr/bin/env python3
"""SGP-1.2-OPZIONI-03 — cancelli G2/G3/G7: la macchina a stati fa quello che dice.

Il blob viene ESEGUITO su un ARM946E-S emulato (Unicorn). Nessun test legge il
sorgente: tutti guardano lo stato in memoria e la sequenza delle chiamate al
gioco dopo aver premuto dei tasti.

Rispetto alla v1 (`SGP-1.2-OPZIONI-01`) cambiano tre cose, e i test le seguono:
  - non c'e' piu' scorrimento: le voci sono tutte a schermo (G7);
  - le voci sono quelle vere, e ognuna ha un PROPRIETARIO diverso: la sua
    guardia decide se la voce si vede, si vede disattivata, o sparisce;
  - ogni riga e' una finestra sottile, con un tile bianco condiviso fra le
    righe: e' il conto dei tile a essere il cancello, non la forma.
"""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from banco import Banco, indirizzo, CANARINI, APP, IND        # noqa: E402

K_A, K_B, K_SELECT = 1, 2, 4
K_RIGHT, K_LEFT, K_UP, K_DOWN = 0x10, 0x20, 0x40, 0x80

# Geometria dichiarata in sorgenti/sgp_ui.h. Ripetuta qui apposta: se qualcuno la
# cambia nel sorgente, i test devono accorgersene invece di seguirla.
W_TILE, H_TILE, PASSO, RIGHE_MAX = 24, 2, 3, 7
BASETILE, TILE_RIGA = 0x274, 48
TILE_BIANCO = BASETILE + RIGHE_MAX * TILE_RIGA
CORNICE = 0x3DC
TILE_VANILLA_FINE = 0x274        # dove finiscono le 5 finestre del menu
TILE_CELLA_MAX = 1024            # 10 bit di indice di carattere nella cella


def frame(b, tasti, app=APP, touch=0):
    b.tasti(tasti, touch)
    r0, fin = b.chiama(indirizzo("sgp_ui_frame"), app)
    return r0, fin


def tutto_presente(b):
    """Una ROM in cui TUTTI i cantieri sono stati applicati: le 5 voci si vedono."""
    b.stato_npc()
    b.stato_anim()
    b.stato_wifi()
    return b


def apri(**kw):
    b = tutto_presente(Banco())
    for k, v in kw.items():
        getattr(b, k)(**v) if isinstance(v, dict) else None
    frame(b, K_SELECT)
    return b


class G7ContoDeiTile(unittest.TestCase):
    """Il vincolo e' 1024 tile per cella di tilemap, cioe' 396 tile liberi dopo
    le 5 finestre vanilla (0x274) e prima della cornice. Non e' una forma: e'
    un'area. Questi test rifanno il conto **sugli argomenti veri** passati al
    gioco, non sulle costanti del sorgente."""

    def test_le_righe_stanno_tutte_sotto_il_soffitto(self):
        b = apri()
        u = b.leggi_ui()
        self.assertEqual(u["n_vis"], 5, "cinque voci dichiarate dalla 1.2a")
        self.assertEqual(u["n_righe"], 7, "titolo + 5 voci + aiuto")
        self.assertLessEqual(u["n_righe"], RIGHE_MAX)
        # solo le finestre DELLA PAGINA: il suggerimento del menu vanilla riusa
        # di proposito gli stessi tile, perche' non e' mai a schermo insieme.
        finestre = [c for c in b.chiamate if c["f"] == "AddWindowParameterized"
                    and (c["sp"][1] == W_TILE or c["sp"][1] == 1)]
        usati = set()
        for c in finestre:
            base, w, h = c["sp_ext"][0], c["sp"][1], c["sp"][2]
            self.assertGreaterEqual(base, TILE_VANILLA_FINE,
                                    "nessun tile del menu originale viene preso")
            for t in range(base, base + w * h):
                self.assertNotIn(t, usati, f"tile {t:#x} usato da due finestre")
                usati.add(t)
            self.assertLessEqual(base + w * h, CORNICE,
                                 "nessuna finestra entra nei tile della cornice")
        # 7 righe da 24x2 + 1 tile bianco = 337, piu' 36 di cornice = 373 <= 396
        self.assertEqual(len(usati), RIGHE_MAX * W_TILE * H_TILE + 1)
        self.assertLessEqual(max(usati) + 1, CORNICE)
        self.assertLessEqual(CORNICE + 36, TILE_CELLA_MAX)

    def test_passo_verticale_del_gioco(self):
        """24 px, cioe' 3 tile: e' il passo del menu Opzioni che la pagina imita.
        La v1 ne usava 20 perche' aveva una finestra sola alta 12 tile."""
        b = apri()
        righe = [c for c in b.chiamate if c["f"] == "AddWindowParameterized"
                 and c["sp"][1] == W_TILE]
        y = [c["sp"][0] for c in righe]
        self.assertEqual(len(y), 7)
        self.assertEqual(sorted(y), y, "le righe si disegnano dall'alto in basso")
        for a, b_ in zip(y, y[1:]):
            self.assertEqual(b_ - a, PASSO, "passo di 3 tile = 24 px")

    def test_il_pannello_sta_dentro_lo_schermo_ed_e_centrato(self):
        b = apri()
        u = b.leggi_ui()
        # cornice a ycont-1, contenuto alto `altezza`, cornice a ycont+altezza
        self.assertEqual(u["altezza"], PASSO * (u["n_vis"] + 1) + H_TILE)
        self.assertGreaterEqual(u["ycont"], 1, "serve una riga per la cornice sopra")
        self.assertLessEqual(u["ycont"] + u["altezza"] + 1, 24,
                             "la cornice di sotto deve stare nello schermo")
        alto = u["ycont"] - 1
        basso = 24 - (u["ycont"] + u["altezza"] + 1)
        self.assertLessEqual(abs(alto - basso), 1, "pannello centrato in verticale")

    def test_tile_bianco_condiviso(self):
        """Una sola finestra 1x1: il suo tile riempie tutte le celle del pannello,
        comprese quelle fra una riga e l'altra. E' cio' che permette il passo di
        24 px senza pagare 24 tile per ogni riga vuota."""
        b = apri()
        uno = [c for c in b.chiamate if c["f"] == "AddWindowParameterized"
               and c["sp"][1] == 1 and c["sp"][2] == 1]
        self.assertEqual(len(uno), 1)
        self.assertEqual(uno[0]["sp_ext"][0], TILE_BIANCO)
        riempi = [c for c in b.chiamate if c["f"] == "FillBgTilemapRect"]
        self.assertEqual(len(riempi), 1, "una sola FillBgTilemapRect, sul pannello")
        u = b.leggi_ui()
        self.assertEqual(riempi[0]["r"][2], TILE_BIANCO)
        self.assertEqual(riempi[0]["r"][3], 4)               # x del pannello
        self.assertEqual(riempi[0]["sp"][0], u["ycont"])
        self.assertEqual(riempi[0]["sp"][1], W_TILE)
        self.assertEqual(riempi[0]["sp"][2], u["altezza"])
        self.assertEqual(riempi[0]["sp"][3], 13)             # palette


class G3Apertura(unittest.TestCase):
    def test_chiusa_non_consuma_niente(self):
        b = tutto_presente(Banco())
        for k in (K_A, K_B, K_UP, K_DOWN, K_LEFT, K_RIGHT, 0):
            r0, _ = frame(b, k)
            self.assertEqual(r0, 0, f"tasto {k:#x} consumato a pagina chiusa")
            self.assertEqual(b.leggi_ui()["aperta"], 0)

    def test_select_apre_e_consuma(self):
        b = apri()
        u = b.leggi_ui()
        self.assertEqual(u["aperta"], 1)
        self.assertEqual(u["aperture"], 1)
        self.assertEqual(u["guard"], 0x55)
        n = b.nomi_chiamate()
        self.assertIn("LoadUserFrameGfx2", n)
        self.assertIn("DrawFrameAndWindow2", n)
        self.assertLess(n.index("LoadUserFrameGfx2"), n.index("DrawFrameAndWindow2"),
                        "prima si caricano i tile della cornice, poi la si disegna")
        self.assertLess(n.index("FillBgTilemapRect"), n.index("DrawFrameAndWindow2"),
                        "prima il fondo del pannello, poi la cornice intorno")
        self.assertEqual(n[-1], "PlaySE", "il suono di apertura chiude la sequenza")

    def test_select_con_tocco_in_corso_non_apre(self):
        """Se il giocatore sta toccando lo schermo l'evento e' del vanilla."""
        b = tutto_presente(Banco())
        r0, _ = frame(b, K_SELECT, touch=1)
        self.assertEqual(r0, 0)
        self.assertEqual(b.leggi_ui()["aperta"], 0)

    def test_A1_lo_sfondo_del_menu_si_spegne(self):
        """La correzione A1 della revisione. La v1 lo prometteva nei commenti e
        spegneva solo MAIN_0: dietro il pannello restava un menu mezzo cancellato
        (riga blu senza testo, intestazione senza «Opzioni», pillola vuota)."""
        b = apri()
        tog = [(c["r"][0], c["r"][1]) for c in b.chiamate if c["f"] == "ToggleBgLayer"]
        self.assertIn((2, 0), tog, "MAIN_2, lo sfondo del menu, va SPENTO")
        self.assertIn((0, 0), tog, "MAIN_0, la barra di evidenziazione, va spento")
        obj = [(c["r"][0], c["r"][1]) for c in b.chiamate if c["f"] == "TogglePianiA"]
        self.assertEqual(obj, [(0x10, 0)], "il piano OBJ degli sprite va spento")

    def test_A1_alla_chiusura_lo_sfondo_torna(self):
        b = apri()
        frame(b, K_B)
        tog = [(c["r"][0], c["r"][1]) for c in b.chiamate if c["f"] == "ToggleBgLayer"]
        self.assertIn((2, 1), tog, "MAIN_2 si riaccende alla chiusura")
        obj = [(c["r"][0], c["r"][1]) for c in b.chiamate if c["f"] == "TogglePianiA"]
        self.assertEqual(obj, [(0x10, 1)])

    def test_cornice_del_giocatore(self):
        """La cornice e' quella che il giocatore ha scelto nelle Opzioni, non una
        fissa: si legge il campo `frame` del bitfield dell'app."""
        b = tutto_presente(Banco())
        b.uc.mem_write(APP + 0x18, struct.pack("<H", 7 << 10))
        frame(b, K_SELECT)
        c = [x for x in b.chiamate if x["f"] == "LoadUserFrameGfx2"][0]
        self.assertEqual(c["r"][1], 1, "cornice sul BG della pagina")
        self.assertEqual(c["r"][2], CORNICE)
        self.assertEqual(c["r"][3], 15, "palette 15: libera sul BG principale")
        self.assertEqual(c["sp"][0], 7, "numero di cornice del giocatore")


class G3Voci(unittest.TestCase):
    """A6: niente voci segnaposto con un numero di versione. Una voce il cui
    proprietario non e' nella ROM o sparisce o resta disattivata."""

    def test_senza_nessun_proprietario_restano_solo_le_voci_di_D1(self):
        """Stato di oggi sulla ROM di lavoro: D1 c'e', P2/A1-B/W1 no. La voce di
        A1-B si NASCONDE (bit4 del suo `modo`), quelle di P2 e W1 restano visibili
        e disattivate, com'e' stato chiesto dall'orchestratore."""
        b = Banco()                      # tutti gli stati altrui a zero
        frame(b, K_SELECT)
        u = b.leggi_ui()
        self.assertEqual(u["n_vis"], 4, "4 voci: sparisce solo quella di A1-B")
        self.assertEqual(u["vis"][:4], [0, 1, 3, 4])
        self.assertEqual(u["n_righe"], 6)

    def test_con_tutti_i_proprietari_si_vedono_tutte(self):
        b = apri()
        u = b.leggi_ui()
        self.assertEqual(u["n_vis"], 5)
        self.assertEqual(u["vis"][:5], [0, 1, 2, 3, 4])

    def test_una_voce_senza_proprietario_non_cambia_e_non_suona(self):
        b = Banco()                      # W1 assente
        frame(b, K_SELECT)
        u = b.leggi_ui()
        pos = u["vis"][:u["n_vis"]].index(4)     # la voce «Server online»
        for _ in range(pos):
            frame(b, K_DOWN)
        b.chiamate = []
        frame(b, K_RIGHT)
        self.assertEqual(b.leggi_ui()["val"][4], 0, "una voce disattivata non cambia")
        self.assertEqual([c for c in b.chiamate if c["f"] == "PlaySE"], [],
                         "e non produce un suono di conferma")

    def test_niente_giro_in_tondo_sui_valori(self):
        """I cursori del menu vanilla si fermano ai due estremi. Il valore 0 con
        SINISTRA resta 0; l'ultimo con DESTRA resta l'ultimo."""
        b = apri()
        for _ in range(20):
            frame(b, K_LEFT)
        self.assertEqual(b.leggi_ui()["val"][0], 0)
        for _ in range(20):
            frame(b, K_RIGHT)
        self.assertEqual(b.leggi_ui()["val"][0], 1, "la voce di D1 ha due valori")

    def test_la_voce_del_wifi_ha_tre_valori(self):
        """CONTRATTO-W1 §1b.5: «Originale» piu' i soli slot 2 e 3. Lo slot 1 e'
        del Dono Segreto e si sceglie da solo: non e' una voce."""
        b = apri()
        u = b.leggi_ui()
        for _ in range(u["vis"][:u["n_vis"]].index(4)):
            frame(b, K_DOWN)
        for atteso in (1, 2, 2, 2):
            frame(b, K_RIGHT)
            self.assertEqual(b.leggi_ui()["val"][4], atteso)
        for atteso in (1, 0, 0):
            frame(b, K_LEFT)
            self.assertEqual(b.leggi_ui()["val"][4], atteso)

    def test_il_cursore_gira_in_tondo_sulle_voci(self):
        b = apri()
        n = b.leggi_ui()["n_vis"]
        for atteso in list(range(1, n)) + [0]:
            frame(b, K_DOWN)
            self.assertEqual(b.leggi_ui()["cursore"], atteso)
        frame(b, K_UP)
        self.assertEqual(b.leggi_ui()["cursore"], n - 1)

    def test_nessuno_scorrimento(self):
        """La v1 mostrava 3 voci su 6 e faceva scorrere la finestra. Qui il numero
        di righe disegnate non dipende da dove sta il cursore."""
        b = apri()
        conteggi = []
        for _ in range(6):
            b.chiamate = []
            frame(b, K_DOWN)
            conteggi.append(len([c for c in b.chiamate
                                 if c["f"] == "AddWindowParameterized"]))
        self.assertEqual(set(conteggi), {7}, "sempre sette righe, comunque")


class G3Stati(unittest.TestCase):
    """Ogni voce scrive nello stato del SUO proprietario, e solo se c'e'."""

    def test_A_scrive_il_chunk_e_la_copia_operativa(self):
        """CONTRATTO-CHUNK §2: l'opzione sta nel chunk pubblico (`plus` a
        0x023D8713) e chi la accende deve aggiornare anche `active_plus`, il byte
        che il gancio allenatori legge davvero."""
        b = apri()
        frame(b, K_RIGHT)                       # difficolta' Plus = PLUS
        r0, _ = frame(b, K_A)
        self.assertEqual(r0, 1)
        d = b.leggi_d1()
        self.assertEqual(d["plus"], 1)
        self.assertEqual(d["active_plus"], 1)
        self.assertEqual(b.leggi_ui()["aperta"], 0)
        self.assertEqual(b.leggi_ui()["salvataggi"], 1)

    def test_A_scrive_i_byte_di_P2_e_di_A1B_nel_chunk(self):
        """I due cantieri leggono il proprio flag DAL CHUNK: la pagina non entra
        nei loro blocchi, ne legge solo la guardia."""
        b = apri()
        frame(b, K_DOWN); frame(b, K_DOWN)      # voce 2: Pokemon animati
        frame(b, K_RIGHT)
        frame(b, K_DOWN)                        # voce 3: fluidita' NPC
        frame(b, K_RIGHT)
        frame(b, K_A)
        d = b.leggi_d1()
        self.assertEqual(d["anim"], 1)
        self.assertEqual(d["npc"], 1)

    def test_A_scrive_wifi_server_nel_chunk_e_non_nel_blocco_W1(self):
        """`wifi_server` sta nel chunk (dominio 0..3). Il blocco di W1 lo LEGGE:
        la pagina non ci scrive dentro, ne legge solo il magic per sapere se il
        cantiere e' nella ROM."""
        b = apri()
        prima = bytes(b.uc.mem_read(IND["stato_wifi"], 16))
        for _ in range(4):
            frame(b, K_DOWN)                    # voce 4: server online
        frame(b, K_RIGHT)                       # 0 → 1 = slot 2
        frame(b, K_A)
        self.assertEqual(b.leggi_d1()["wifi_server"], 2)
        frame(b, K_SELECT)
        for _ in range(4):
            frame(b, K_DOWN)
        frame(b, K_RIGHT)                       # 1 → 2 = slot 3
        frame(b, K_A)
        self.assertEqual(b.leggi_d1()["wifi_server"], 3)
        frame(b, K_SELECT)
        for _ in range(4):
            frame(b, K_DOWN)
        frame(b, K_LEFT); frame(b, K_LEFT)      # torna a «Originale»
        frame(b, K_A)
        self.assertEqual(b.leggi_d1()["wifi_server"], 0)
        self.assertEqual(bytes(b.uc.mem_read(IND["stato_wifi"], 16)), prima,
                         "il blocco di W1 non viene mai scritto dalla pagina")

    def test_B_annulla_e_non_scrive_da_nessuna_parte(self):
        b = apri()
        frame(b, K_RIGHT)
        frame(b, K_DOWN); frame(b, K_DOWN); frame(b, K_RIGHT)
        r0, _ = frame(b, K_B)
        self.assertEqual(r0, 1)
        d = b.leggi_d1()
        self.assertEqual((d["plus"], d["active_plus"], d["anim"]), (0, 0, 0))
        self.assertEqual(b.leggi_ui()["salvataggi"], 0)

    def test_chunk_rifiutato_non_accende_niente(self):
        b = apri()
        b.stato_d1(load=3)                      # SGP_LOAD_REJECT
        frame(b, K_SELECT)                      # richiude
        frame(b, K_SELECT)                      # riapre con lo stato nuovo
        frame(b, K_RIGHT)
        self.assertEqual(b.leggi_ui()["val"][0], 0)
        frame(b, K_A)
        self.assertEqual(b.leggi_d1()["plus"], 0)

    def test_riaprendo_si_rilegge_lo_stato_vero(self):
        b = apri()
        frame(b, K_RIGHT)
        frame(b, K_A)
        frame(b, K_SELECT)
        u = b.leggi_ui()
        self.assertEqual(u["val"][0], 1)
        self.assertEqual(u["val0"][0], 1, "il valore all'apertura viene dallo stato")


class G3Chiusura(unittest.TestCase):
    def test_SELECT_richiude(self):
        b = apri()
        r0, _ = frame(b, K_SELECT)
        self.assertEqual(r0, 1)
        self.assertEqual(b.leggi_ui()["aperta"], 0)

    def test_chiusura_ripristina_le_cinque_finestre_vanilla(self):
        b = apri()
        frame(b, K_B)
        n = b.nomi_chiamate()
        self.assertEqual(n[0], "PlaySE", "il suono di annullamento parte per primo")
        self.assertEqual(n[1], "BgClearTilemapCommit",
                         "l'intera tilemap si azzera: la cornice scrive celle "
                         "anche fuori dal rettangolo")
        self.assertGreaterEqual(n.count("CopyWindowToVram"), 5,
                                "vanno ristampate tutte e cinque le finestre vanilla")
        self.assertIn("String_Delete", n)
        self.assertEqual(n[-1], "OPZ_EVIDENZIA",
                         "la barra la ripristina la funzione del gioco, per ultima")

    def test_conteggio_alloc_free_pari(self):
        """Ogni String_New ha il suo String_Delete, ogni AddWindowParameterized il
        suo RemoveWindow. Le finestre delle righe vivono il tempo di un disegno:
        il trasferimento in VRAM e' sincrono, quindi si chiudono subito."""
        b = tutto_presente(Banco())
        frame(b, 0)                             # il menu disegna il suggerimento
        alloc = libera = 0
        for _ in range(7):
            for k in (K_SELECT, K_B):
                frame(b, k)
                n = b.nomi_chiamate()
                alloc += n.count("String_New") + n.count("AddWindowParameterized")
                libera += n.count("String_Delete") + n.count("RemoveWindow")
        self.assertEqual(alloc, libera, f"{alloc} allocazioni, {libera} rilasci")
        self.assertEqual(b.leggi_ui()["aperture"], 7)
        self.assertEqual(b.leggi_ui()["aperta"], 0)

    def test_suoni_del_menu_originale(self):
        """Gli id sono quelli letti dai pool dell'app Opzioni: 1500 scorrimento,
        1562 conferma, 2368 annullamento. Non se ne inventano."""
        b = apri()
        self.assertEqual([c["r"][0] for c in b.chiamate if c["f"] == "PlaySE"], [1500])
        frame(b, K_DOWN)
        self.assertEqual([c["r"][0] for c in b.chiamate if c["f"] == "PlaySE"], [1500])
        frame(b, K_B)
        self.assertEqual([c["r"][0] for c in b.chiamate if c["f"] == "PlaySE"], [2368])
        frame(b, K_SELECT)
        frame(b, K_A)
        self.assertEqual([c["r"][0] for c in b.chiamate if c["f"] == "PlaySE"], [1562])


class G3Suggerimento(unittest.TestCase):
    """REVISIONE-QUALITA §6: la funzione non si scopre. Una riga nel menu Opzioni
    vanilla, nella banda libera in basso a sinistra, dice che SELECT la apre."""

    def test_si_disegna_appena_il_menu_e_vivo(self):
        b = tutto_presente(Banco())
        frame(b, 0)
        self.assertEqual(b.leggi_ui()["sugg"], 1)
        c = [x for x in b.chiamate if x["f"] == "AddWindowParameterized"]
        self.assertEqual(len(c), 1)
        self.assertEqual((c[0]["r"][3], c[0]["sp"][0]), (0, 22), "banda in basso a sinistra")
        self.assertEqual(c[0]["sp"][1], 14, "112 px: i pulsanti cominciano a x=117")
        self.assertEqual(c[0]["sp_ext"][0], BASETILE,
                         "riusa i tile della pagina: non coesistono mai")

    def test_non_si_ridisegna_ogni_fotogramma(self):
        b = tutto_presente(Banco())
        frame(b, 0)
        b.chiamate = []
        for _ in range(5):
            frame(b, 0)
        self.assertNotIn("AddWindowParameterized", b.nomi_chiamate())

    def test_sparisce_quando_la_pagina_apre_e_torna_quando_chiude(self):
        b = tutto_presente(Banco())
        frame(b, 0)
        frame(b, K_SELECT)
        self.assertEqual(b.leggi_ui()["sugg"], 0)
        n = b.nomi_chiamate()
        self.assertIn("ClearWindowTilemapAndCopyToVram", n)
        self.assertLess(n.index("ClearWindowTilemapAndCopyToVram"),
                        n.index("FillBgTilemapRect"))
        frame(b, K_B)
        self.assertEqual(b.leggi_ui()["sugg"], 1)


class G3Registri(unittest.TestCase):
    def test_canarini_intatti(self):
        """sgp_ui_frame e' AAPCS: r4-r7 devono tornare come sono entrati.
        E' l'ipotesi su cui la trampolina NON salva r4."""
        b = tutto_presente(Banco())
        for k in (K_SELECT, K_DOWN, K_RIGHT, K_A, 0):
            _, fin = frame(b, k)
            for r, v in CANARINI.items():
                self.assertEqual(fin[r], v, f"registro sporcato dopo tasto {k:#x}")

    def test_proprietario_diverso_cede_senza_liberare(self):
        b = apri()
        r0, _ = frame(b, K_DOWN, app=APP + 0x1000)
        self.assertEqual(r0, 0, "con un'altra app si cede il frame al vanilla")
        self.assertEqual(b.leggi_ui()["aperta"], 0)
        self.assertNotIn("RemoveWindow", b.nomi_chiamate())
        self.assertNotIn("String_Delete", b.nomi_chiamate())


class G3Trampolina(unittest.TestCase):
    """La trampolina e' 4 byte di preimmagine + il salto: si prova eseguendola."""

    def prepara(self, b):
        uc = b.uc
        ritorno = 0x0230E000
        uc.mem_write(ritorno, b"\x00\xbf" * 4)
        sp = 0x023AFF00
        uc.mem_write(sp, struct.pack("<4I", 0, 0, 0, ritorno | 1))
        return sp, ritorno

    def test_non_consumato_riesegue_le_due_istruzioni(self):
        from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_R0,
                                       UC_ARM_REG_R1, UC_ARM_REG_R4, UC_ARM_REG_CPSR)
        b = tutto_presente(Banco())
        sp, _ = self.prepara(b)
        base_lett = 0x02202000
        b.uc.mem_write(base_lett + 0x24, struct.pack("<H", 0x1234))
        b.tasti(0)
        frame(b, 0)                      # il suggerimento e' gia' disegnato
        uc = b.uc
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, APP)
        uc.reg_write(UC_ARM_REG_R1, base_lett)
        from unicorn.arm_const import UC_ARM_REG_R2
        uc.reg_write(UC_ARM_REG_R2, 0xDEADBEEF)
        uc.reg_write(UC_ARM_REG_LR, 0x0230D001)
        uc.mem_write(0x0230D000, b"\x00\xbf" * 4)
        uc.reg_write(UC_ARM_REG_CPSR, 0x33)
        uc.emu_start(indirizzo("sgp_opz_hook") | 1, 0x0230D000, count=200000)
        self.assertEqual(uc.reg_read(UC_ARM_REG_R4), APP, "r4 = app (1a istruzione)")
        self.assertEqual(uc.reg_read(UC_ARM_REG_R1), 0x1234, "r1 = touchNew (2a)")
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP), sp, "la pila deve tornare intatta")
        # IL test che mancava alla v1. Sul ramo dei TASTI l'ospite non ricarica
        # r0: lo porta fino a OptionsApp_HandleKeyInput(r0, r1). Se la trampolina
        # ci lascia il valore di ritorno di sgp_ui_frame (0), il gioco muore al
        # primo tasto non consumato. Misurato sulla ROM: fotogramma 3587.
        self.assertEqual(uc.reg_read(UC_ARM_REG_R0), APP,
                         "r0 deve restare il puntatore all'app: sul ramo dei tasti "
                         "l'ospite non lo ricarica")
        from unicorn.arm_const import UC_ARM_REG_R2
        self.assertEqual(uc.reg_read(UC_ARM_REG_R2), 0xDEADBEEF & 0xFFFFFFFF,
                         "anche r2 torna come l'ospite l'aveva")

    def test_consumato_esegue_l_epilogo_dell_ospite(self):
        from unicorn.arm_const import (UC_ARM_REG_SP, UC_ARM_REG_R0, UC_ARM_REG_R1,
                                       UC_ARM_REG_LR, UC_ARM_REG_CPSR)
        b = tutto_presente(Banco())
        sp, ritorno = self.prepara(b)
        b.tasti(4)                       # SELECT: la pagina apre e consuma
        uc = b.uc
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_R0, APP)
        uc.reg_write(UC_ARM_REG_R1, 0x02202000)
        uc.reg_write(UC_ARM_REG_LR, 0x0230D001)
        uc.mem_write(0x0230D000, b"\x00\xbf" * 4)
        uc.reg_write(UC_ARM_REG_CPSR, 0x33)
        uc.emu_start(indirizzo("sgp_opz_hook") | 1, ritorno, count=200000)
        self.assertEqual(uc.reg_read(UC_ARM_REG_SP), sp + 16,
                         "l'epilogo dell'ospite deve aver tolto i suoi 16 byte")
        self.assertEqual(b.leggi_ui()["aperta"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
