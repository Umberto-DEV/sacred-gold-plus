#!/usr/bin/env python3
"""FASE 1b — cancelli G (i venti della fase 1, riportati sul blob nuovo) e
cancelli H (i nuovi invarianti: ombra ferma, battito mai durante animActive,
sfasamento fra i lottatori, scala entro 0x100+-6, ampiezza per taglia).

Il BLOB COMPILATO viene ESEGUITO su un ARM946E-S emulato che contiene il VERO
ARM9 e il VERO overlay 12 della base 1.1. In piu', per i cancelli sull'ombra,
si esegue anche il codice di disegno del gioco (vedi banco2.py).

Se `unicorn` manca, i cancelli NON sono superati: i test si dichiarano
saltati, non sostituiti con una prova piu' debole.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PKG = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PKG / "test"))

try:
    import banco2 as B
    UNICORN = True
except ImportError:                                            # pragma: no cover
    UNICORN = False

BASE = 0x023D8900
CODICE = BASE + 0x000
TABELLE = BASE + 0x300
STATO = BASE + 0x340
SLOT = BASE + 0x380

F_RESPIRO, F_POSA, F_SCALA, F_OMBRA, F_FASE, F_TAGLIA = 1, 2, 4, 8, 16, 32
F_TUTTI = 0x3F


def costruisci(dest):
    r = subprocess.run([sys.executable, str(PKG / "tools" / "compila2.py"),
                        "--uscita", str(dest), "--base", hex(BASE)],
                       text=True, capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(r.stdout + r.stderr)
    return json.loads((dest / "manifesto2.json").read_text())


@unittest.skipUnless(UNICORN, "unicorn assente: i cancelli NON sono superati")
class Fase1b(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dest = Path(cls.tmp.name) / "build"
        cls.man = costruisci(cls.dest)
        cls.tab_u = cls.man["tabelle_bin"]["tab_u"]["valori"]
        cls.par = cls.man["tabelle_bin"]["par"]
        cls.serie = cls.man["serie_y_per_classe"]
        cls.serie_s = cls.man["serie_scala_per_classe"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)

    def y_attesa(self, cls_, deg):
        return self.serie[str(cls_)][(deg * 205) >> 12]

    # ================================================================ G
    def test_G1_dimensioni(self):
        """Il blob entra nei 768 B riservati al codice dentro il blocco."""
        self.assertLessEqual(self.man["blob"]["byte"], 0x300)
        self.assertLessEqual(self.man["occupazione_totale_byte"], 1024)
        self.assertIn("sgp_idle_task2", self.man["simboli"])

    def test_G1b_fase_uguale_al_vanilla(self):
        """La forma d'onda unitaria ha la stessa fase e lo stesso segno del
        task vanilla, e con ampiezza 3 riproduce ESATTAMENTE la tabella della
        fase 1: il movimento amplifica quello che il gioco gia' fa."""
        self.b.prepara(degrees=180)
        vanilla, nostra = [], []
        for _ in range(18):
            self.b.vanilla()
            deg = self.b.u16(B.OD0 + B.OD_DEGREES)
            vanilla.append(self.b.s16(B.PIC0 + B.PP_YOFFSET))
            nostra.append(self.serie["1"][(deg * 205) >> 12])
        self.assertEqual(vanilla, [0, 0, -1, -1, -1, -1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0],
                         "il task vanilla emulato non riproduce la serie di 10b")
        self.assertTrue(self.man["continuita_fase_1"]["uguale_a_classe_1"],
                        "la classe 1 non riproduce piu' la tab_y della fase 1")
        for v, n in zip(vanilla, nostra):
            if v != 0:
                self.assertEqual(v > 0, n > 0, f"segno discorde: vanilla {v}, nostro {n}")

    def test_G2_spento_identico_al_vanilla(self):
        """A flag spento la memoria del gioco e' IDENTICA AL BYTE a quella che
        lascia il task vanilla, su 36 esecuzioni."""
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=0)
        a = []
        for _ in range(36):
            self.b.nostro()
            a.append(self.b.istantanea())
        self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
        self.b.prepara(degrees=180)
        v = []
        for _ in range(36):
            self.b.vanilla()
            v.append(self.b.istantanea())
        self.assertEqual(a, v, "a flag spento qualcosa cambia rispetto alla 1.1")

    def test_G2b_spento_registri_e_voci(self):
        self.b.prepara()
        self.b.imposta_stato(flags=0)
        r = self.b.nostro()
        self.assertEqual(r["callee_saved_corrotti"], {})
        self.assertEqual(r["sp"], B.SP0)
        self.assertEqual(self.b.rd(SLOT, 128), bytes(128),
                         "a flag spento non deve nascere nemmeno una voce")

    def test_G3_anim_attiva_non_si_tocca(self):
        for flags in (F_RESPIRO, F_POSA, F_SCALA, F_OMBRA, F_TUTTI):
            with self.subTest(flags=flags):
                self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
                self.b.prepara(degrees=180, animActive=1, anim_step=1)
                self.b.imposta_stato(flags=flags)
                a = [self.b.istantanea()]
                for _ in range(18):
                    self.b.nostro()
                    a.append(self.b.istantanea())
                self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
                self.b.prepara(degrees=180, animActive=1, anim_step=1)
                v = [self.b.istantanea()]
                for _ in range(18):
                    self.b.vanilla()
                    v.append(self.b.istantanea())
                self.assertEqual(a, v)

    def test_G3b_contatori(self):
        self.b.prepara(degrees=180, animActive=1)
        self.b.imposta_stato(flags=F_TUTTI)
        for _ in range(5):
            self.b.nostro()
        self.assertEqual(self.b.u32(STATO + B.ST_HITS), 5)
        self.assertEqual(self.b.u32(STATO + B.ST_HITS_BUSY), 5)
        self.assertEqual(self.b.u32(STATO + B.ST_HITS_ON), 0)

    def test_G4_respiro_segue_la_tabella(self):
        self.b.prepara(degrees=180, cls=1)
        self.b.imposta_stato(flags=F_RESPIRO | F_TAGLIA)
        visti = []
        for _ in range(36):
            self.b.nostro()
            deg = self.b.u16(B.OD0 + B.OD_DEGREES)
            y = self.b.s16(B.PIC0 + B.PP_YOFFSET)
            self.assertEqual(y, self.y_attesa(1, deg), f"deg={deg}")
            visti.append((deg * 205) >> 12)
        self.assertEqual(sorted(set(visti)), list(range(18)))

    def test_G4b_respiro_cambia_solo_yoffset(self):
        """Rispetto al vanilla, col solo respiro, cambia SOLO pokepic+0x2E.
        Il confronto e' su tutte e 18 le fasi (e' cosi' che nella fase 1 era
        sopravvissuto il mutante M7)."""
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_RESPIRO | F_TAGLIA)
        a = [bytearray(self.b.istantanea()) for _ in range(0)]
        for _ in range(36):
            self.b.nostro()
            a.append(bytearray(self.b.istantanea()))
        self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
        self.b.prepara(degrees=180)
        v = []
        for _ in range(36):
            self.b.vanilla()
            v.append(bytearray(self.b.istantanea()))
        diversi = set()
        for x, y in zip(a, v):
            diversi |= {i for i in range(len(x)) if x[i] != y[i]}
        self.assertTrue(diversi <= {B.PP_YOFFSET, B.PP_YOFFSET + 1},
                        f"cambiati anche: {sorted(hex(i) for i in diversi)}")
        self.assertTrue(diversi, "il respiro non sta scrivendo")

    def test_G5_posa_solo_A_o_B(self):
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_POSA)
        pose = set()
        for _ in range(600):
            self.b.nostro()
            p = self.b.u8(B.PIC0 + B.PP_ANIMSTEP)
            self.assertIn(p, (0, 1), "posa fuori dalle due caselle UV")
            pose.add(p)
        self.assertEqual(pose, {0, 1}, "la posa non alterna mai")

    def test_G5b_posa_non_tocca_lo_stato_interprete(self):
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_POSA)
        for _ in range(200):
            self.b.nostro()
        for off, nome in ((B.PP_ANIMACTIVE, "animActive"), (B.PP_WHICHANIM, "whichAnim"),
                          (B.PP_STEPDELAY, "animStepDelay")):
            self.assertEqual(self.b.u8(B.PIC0 + off), 0, nome)
        self.assertEqual(self.b.rd(B.PIC0 + B.PP_LOOPTIMERS, 10), bytes(10))
        self.assertEqual(self.b.rd(B.PIC0 + B.PP_XOFFSET, 2), bytes(2),
                         "xOffset toccato: e' il campo conteso con l'interprete")

    def test_G6_interprete_riparte_identico(self):
        """Se scriviamo la posa fuori dall'interprete, quando riparte
        un'animazione VERA lo stato non si corrompe."""
        copione = bytes([1, 3, 0, 0, 0, 4, 2, 0, 1, 2, 0, 0,
                         0xFE, 3, 0, 0, 0xFF, 0, 0, 0])

        def corsa(sporca):
            b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
            b.prepara(degrees=180, script=copione)
            if sporca:
                b.imposta_stato(flags=F_POSA)
                for _ in range(200):
                    b.nostro()
            b.start_anim()
            passi = []
            for _ in range(80):
                passi.append((b.u8(B.PIC0 + B.PP_ANIMACTIVE), b.u8(B.PIC0 + B.PP_ANIMSTEP),
                              b.u8(B.PIC0 + B.PP_WHICHANIM), b.u8(B.PIC0 + B.PP_STEPDELAY),
                              b.s16(B.PIC0 + B.PP_XOFFSET)))
                b.run_anim()
            return passi, b.rd(B.PIC0 + B.PP_ANIMACTIVE, 0xAC - B.PP_ANIMACTIVE)

        sporca, fine_s = corsa(True)
        pulita, fine_p = corsa(False)
        self.assertEqual(sporca, pulita)
        self.assertEqual(fine_s, fine_p)
        self.assertEqual(sporca[-1][0], 0)
        self.assertEqual(sporca[-1][1], 0)

    def test_G6b_start_anim_riscrive_la_posa(self):
        self.b.prepara(degrees=180, script=bytes([0, 5, 0, 0, 0xFF, 0, 0, 0]))
        self.b.wr(B.PIC0 + B.PP_ANIMSTEP, bytes([1]))
        self.b.start_anim()
        self.assertEqual(self.b.u8(B.PIC0 + B.PP_ANIMSTEP), 0)
        self.assertEqual(self.b.u8(B.PIC0 + B.PP_ANIMACTIVE), 1)

    def test_G7_scala_in_controfase(self):
        """Squash & stretch: affineW e affineH si muovono in VERSI OPPOSTI, e
        il verso e' legato a quello di y (in basso = piu' largo e piu' basso)."""
        self.b.prepara(degrees=180, affine=0x100, cls=1)
        self.b.imposta_stato(flags=F_RESPIRO | F_SCALA | F_TAGLIA)
        for _ in range(36):
            self.b.nostro()
            deg = self.b.u16(B.OD0 + B.OD_DEGREES)
            d = self.serie_s["1"][(deg * 205) >> 12]
            w = self.b.s16(B.PIC0 + B.PP_AFFINEW)
            h = self.b.s16(B.PIC0 + B.PP_AFFINEH)
            self.assertEqual(w, 0x100 + d)
            self.assertEqual(h, 0x100 - d)
            self.assertEqual((w - 0x100) + (h - 0x100), 0, "non e' controfase")
            y = self.b.s16(B.PIC0 + B.PP_YOFFSET)
            if y > 0:
                self.assertGreaterEqual(w, 0x100, "in basso deve essere piu' largo")

    def test_G7b_scala_fuori_finestra_si_astiene(self):
        self.b.prepara(degrees=180, affine=0x80)
        self.b.imposta_stato(flags=F_SCALA | F_TAGLIA)
        for _ in range(18):
            self.b.nostro()
            self.assertEqual(self.b.s16(B.PIC0 + B.PP_AFFINEW), 0x80)
            self.assertEqual(self.b.s16(B.PIC0 + B.PP_AFFINEH), 0x80)

    def test_G8_pokepic_nullo_non_e_una_esposizione_nuova(self):
        from unicorn import UcError
        self.b.prepara(degrees=180)
        self.b.uc.mem_write(B.OD0 + B.OD_POKEPIC, (0).to_bytes(4, "little"))
        with self.assertRaises(UcError,
                               msg="il vanilla regge un Pokepic nullo: allora la "
                                   "nostra guardia va spostata PRIMA della chiamata"):
            self.b.vanilla()

    def test_G9_disciplina_registri(self):
        for flags in (0, F_RESPIRO, F_POSA, F_SCALA, F_OMBRA, F_TUTTI):
            with self.subTest(flags=flags):
                self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
                self.b.prepara(degrees=180)
                self.b.imposta_stato(flags=flags)
                for _ in range(18):
                    r = self.b.nostro()
                    self.assertEqual(r["callee_saved_corrotti"], {}, "r4-r11 corrotti")
                    self.assertEqual(r["sp"], B.SP0, "pila sbilanciata")

    def test_G10_scritture_confinate(self):
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_TUTTI)
        fuori = []
        for _ in range(36):
            self.b.nostro(sorveglia=True)
            for a, n, v in self.b.scritture:
                if B.PIC0 <= a < B.PIC0 + B.PP_SIZE:
                    continue
                if B.OD0 + B.OD_DEGREES <= a < B.OD0 + B.OD_DEGREES + 2:
                    continue
                if STATO <= a < STATO + 64 or SLOT <= a < SLOT + 128:
                    continue
                if B.PILA <= a < B.PILA + 0x10000:
                    continue
                fuori.append((hex(a), n, hex(v)))
        self.assertEqual(fuori, [], "scritture fuori dai confini dichiarati")

    def test_G10b_niente_scritture_in_vram_o_registri(self):
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_TUTTI)
        for _ in range(18):
            self.b.nostro(sorveglia=True)
            for a, n, v in self.b.scritture:
                self.assertFalse(0x04000000 <= a < 0x05000000, "registro I/O")
                self.assertFalse(0x06000000 <= a < 0x07000000, "VRAM")

    def test_G11_costo(self):
        self.b.prepara(degrees=180)
        v = sum(self.b.chiama(B.VANILLA_TASK, r0=B.TASK, r1=B.OD0,
                              sorveglia=True)["istruzioni"] for _ in range(18)) / 18
        self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=0)
        off = sum(self.b.nostro(sorveglia=True)["istruzioni"] for _ in range(18)) / 18
        self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_TUTTI)
        on = sum(self.b.nostro(sorveglia=True)["istruzioni"] for _ in range(36)) / 36
        print(f"\n  costo medio 1b: vanilla {v:.1f}, spento {off:.1f} (+{off - v:.1f}), "
              f"acceso {on:.1f} (+{on - v:.1f})")
        (PKG / "prove" / "costo-1b.json").write_text(json.dumps(
            {"istruzioni_per_esecuzione": {"vanilla": v, "spento": off, "acceso": on},
             "fase": "1b",
             "confronto_fase_1": {"vanilla": 299.9, "spento": 313.9, "acceso": 444.0},
             "nota": "conteggio di istruzioni eseguite su Unicorn, non cicli di clock"},
            indent=2) + "\n")
        self.assertLess(on - v, v, "il sovrapprezzo acceso supera il task che gira gia'")
        self.assertLess(off - v, 40, "a flag spento il sovrapprezzo deve essere minimo")

    def test_G12_indipendente_dalla_lingua(self):
        vecchio = os.environ.get("SGP_MODULI")
        risultati = {}
        import importlib
        for lingua in ("EN", "IT"):
            d = PKG / "work" / f"moduli-{lingua}"
            if not d.exists():
                self.skipTest(f"moduli-{lingua} non estratti")
            os.environ["SGP_MODULI"] = str(d)
            importlib.reload(B)
            b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
            b.prepara(degrees=180)
            b.imposta_stato(flags=F_TUTTI)
            serie = []
            for _ in range(72):
                b.nostro()
                serie.append((b.s16(B.PIC0 + B.PP_YOFFSET), b.u8(B.PIC0 + B.PP_ANIMSTEP),
                              b.s16(B.PIC0 + B.PP_AFFINEH), b.s16(B.PIC0 + B.PP_SHADOW_YOFF)))
            risultati[lingua] = serie
        if vecchio:
            os.environ["SGP_MODULI"] = vecchio
        else:
            os.environ.pop("SGP_MODULI", None)
        importlib.reload(B)
        self.assertEqual(risultati["EN"], risultati["IT"])

    # ================================================================ H
    def test_H1_ombra_ferma_corpo_in_movimento(self):
        """IL CANCELLO DELLA FASE 1b. Eseguendo il codice di disegno VERO:
        la Y dell'ombra non si muove di piu' di 1 px mentre il corpo oscilla."""
        for cls_ in range(4):
            with self.subTest(classe=cls_):
                self.b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
                self.b.prepara(degrees=180, cls=cls_, ombra_yoff=8)
                self.b.imposta_stato(flags=F_TUTTI)
                corpi, ombre72, ombre = [], [], []
                for _ in range(72):
                    self.b.nostro()
                    corpi.append(self.b.y_corpo())
                    y72, ydis, _h = self.b.y_ombra()
                    ombre72.append(y72)
                    ombre.append(ydis)
                esc_corpo = max(corpi) - min(corpi)
                esc_72 = max(ombre72) - min(ombre72)
                esc_ombra = max(ombre) - min(ombre)
                amp = self.par["amp"][cls_]
                # il corpo oscilla di 2*ampiezza, piu' al massimo 2 px dovuti
                # allo stretch: DrawAll sottrae alla Y anche meta' dell'altezza
                # scalata (0x02008354: h = affineH*0x50>>8), e l'altezza cambia
                # con affineH. E' l'effetto voluto, non un errore.
                self.assertGreaterEqual(esc_corpo, 2 * amp,
                                        f"il corpo oscilla meno del dichiarato "
                                        f"({esc_corpo} invece di {2 * amp})")
                self.assertLessEqual(esc_corpo, 2 * amp + 2,
                                     f"il corpo oscilla piu' del dichiarato "
                                     f"({esc_corpo} contro {2 * amp} + 2 di stretch)")
                self.assertEqual(esc_72, 0,
                                 f"shadow.Y registrata oscilla di {esc_72} px")
                self.assertLessEqual(esc_ombra, 1,
                                     f"l'ombra disegnata oscilla di {esc_ombra} px")

    def test_H1b_senza_la_riparazione_l_ombra_seguirebbe(self):
        """Il controfattuale: con l'ombra NON ancorata (bit 3 dei flag spento)
        l'ombra oscilla quanto il corpo. Serve a dimostrare che il cancello H1
        misura qualcosa."""
        self.b.prepara(degrees=180, cls=1)
        self.b.imposta_stato(flags=F_TUTTI & ~F_OMBRA)
        ombre = []
        for _ in range(36):
            self.b.nostro()
            ombre.append(self.b.y_ombra()[0])
        self.assertGreaterEqual(max(ombre) - min(ombre), 6,
                                "senza riparazione l'ombra deve oscillare di 6 px")

    def test_H1c_valore_a_riposo_ripreso_dal_gioco(self):
        """Se il gioco riscrive shadow.yOffset (allestimento del lottatore),
        il valore a riposo viene ri-catturato e l'ombra resta ferma al NUOVO
        posto: nessuna deriva accumulata."""
        self.b.prepara(degrees=180, cls=1, ombra_yoff=8)
        self.b.imposta_stato(flags=F_TUTTI)
        for _ in range(20):
            self.b.nostro()
            self.b.y_ombra()
        self.assertEqual(self.b.voce(0)["base76"], 8)
        self.b.wr16(B.PIC0 + B.PP_SHADOW_YOFF, 20)   # il gioco riscrive
        ombre = []
        for _ in range(36):
            self.b.nostro()
            ombre.append(self.b.y_ombra()[0])
        self.assertEqual(self.b.voce(0)["base76"], 20, "valore a riposo non ripreso")
        self.assertEqual(max(ombre) - min(ombre), 0, "deriva dopo la ricattura")

    def test_H2_blink_mai_durante_anim_attiva(self):
        """La posa non viene MAI scritta mentre animActive != 0, nemmeno a
        meta' di un battito gia' cominciato."""
        self.b.prepara(degrees=180, cls=1)
        self.b.imposta_stato(flags=F_TUTTI)
        acceso = 0
        for i in range(600):
            if self.b.voce(0)["blink_left"] != 0 and acceso == 0:
                acceso = i   # accendiamo l'interprete proprio dentro un battito
                self.b.wr(B.PIC0 + B.PP_ANIMACTIVE, bytes([1]))
            self.b.wr(B.PIC0 + B.PP_ANIMSTEP, bytes([9]))  # sentinella
            self.b.nostro()
            if self.b.u8(B.PIC0 + B.PP_ANIMACTIVE) != 0:
                self.assertEqual(self.b.u8(B.PIC0 + B.PP_ANIMSTEP), 9,
                                 "posa scritta mentre animActive != 0")
        self.assertGreater(acceso, 0, "non e' mai partito un battito: prova inutile")

    def test_H3_battito_pseudo_casuale(self):
        """Durata 2-3 esecuzioni (i 'rari' di piu'), cadenza non periodica."""
        self.b.prepara(degrees=180, cls=1)
        self.b.imposta_stato(flags=F_TUTTI)
        serie = []
        for _ in range(3000):
            self.b.nostro()
            serie.append(self.b.u8(B.PIC0 + B.PP_ANIMSTEP))
        # lunghezze dei tratti a posa B e degli intervalli fra un battito e l'altro
        tratti, intervalli, cur, gap = [], [], 0, 0
        for p in serie:
            if p:
                if gap:
                    intervalli.append(gap)
                    gap = 0
                cur += 1
            else:
                if cur:
                    tratti.append(cur)
                    cur = 0
                gap += 1
        base = self.par["blink_dur"]
        raro = base + self.par["raro_piu"]
        self.assertTrue(tratti, "nessun battito")
        for t in tratti:
            self.assertIn(t, (base, base + 1, raro, raro + 1),
                          f"durata del battito fuori contratto: {t}")
        comuni = [t for t in tratti if t <= base + 1]
        rari = [t for t in tratti if t >= raro]
        self.assertTrue(comuni and rari, "manca la cadenza comune/rara")
        self.assertAlmostEqual(len(comuni) / max(len(rari), 1),
                               self.par["raro_ogni"] - 1, delta=1.0)
        self.assertGreaterEqual(len(set(intervalli)), 5,
                                "gli intervalli sono periodici: non e' un battito")
        mn, mx = min(intervalli), max(intervalli)
        self.assertGreaterEqual(mn, self.par["blink_min"] - 1)
        self.assertLessEqual(mx, self.par["blink_min"] + self.par["blink_mask"] + 2)
        print(f"\n  battiti: {len(tratti)} ({len(rari)} rari), durate {sorted(set(tratti))}, "
              f"intervalli {mn}..{mx} esecuzioni ({mn / 30:.1f}..{mx / 30:.1f} s)")

    def test_H3b_lcg_deterministico(self):
        """Stesso seme, stessa serie: il battito e' riproducibile."""
        def corsa():
            b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
            b.prepara(degrees=180)
            b.imposta_stato(flags=F_TUTTI)
            return [b.u8(B.PIC0 + B.PP_ANIMSTEP) for _ in
                    [b.nostro() for _ in range(400)]] if False else \
                   [(_ , b.nostro(), b.u8(B.PIC0 + B.PP_ANIMSTEP))[2] for _ in range(400)]
        self.assertEqual(corsa(), corsa())

    def test_H4_sfasamento_fra_i_due_slot(self):
        """I due lottatori NON respirano all'unisono: lo sfasamento e' quello
        dichiarato e vale almeno un quarto di periodo."""
        self.b.prepara(od=B.OD0, pic=B.PIC0, degrees=180, cls=1)
        self.b.prepara(od=B.OD1, pic=B.PIC1, degrees=180, cls=1)
        self.b.imposta_stato(flags=F_TUTTI)
        s0, s1 = [], []
        for _ in range(36):
            self.b.nostro(od=B.OD0)
            self.b.nostro(od=B.OD1)
            s0.append(self.b.s16(B.PIC0 + B.PP_YOFFSET))
            s1.append(self.b.s16(B.PIC1 + B.PP_YOFFSET))
        self.assertNotEqual(s0, s1, "i due lottatori sono in fase")
        atteso = self.par["fase"][1] - self.par["fase"][0]
        self.assertEqual(s1, s0[atteso:] + s0[:atteso],
                         "lo sfasamento non e' quello dichiarato")
        self.assertGreaterEqual(min(atteso, 18 - atteso), 18 // 4,
                                "sfasamento sotto un quarto di periodo")
        self.assertEqual(self.b.voce(0)["od"], B.OD0)
        self.assertEqual(self.b.voce(1)["od"], B.OD1)

    def test_H4b_senza_sfasamento_sono_identici(self):
        self.b.prepara(od=B.OD0, pic=B.PIC0, degrees=180, cls=1)
        self.b.prepara(od=B.OD1, pic=B.PIC1, degrees=180, cls=1)
        self.b.imposta_stato(flags=F_RESPIRO | F_TAGLIA)
        s0, s1 = [], []
        for _ in range(36):
            self.b.nostro(od=B.OD0)
            self.b.nostro(od=B.OD1)
            s0.append(self.b.s16(B.PIC0 + B.PP_YOFFSET))
            s1.append(self.b.s16(B.PIC1 + B.PP_YOFFSET))
        self.assertEqual(s0, s1, "senza il bit di sfasamento devono essere in fase")

    def test_H5_ampiezza_per_taglia(self):
        """L'ampiezza segue la classe di taglia letta dal Pokepic."""
        escursioni = {}
        for cls_ in range(4):
            b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
            b.prepara(degrees=180, cls=cls_)
            b.imposta_stato(flags=F_RESPIRO | F_TAGLIA)
            ys = []
            for _ in range(36):
                b.nostro()
                ys.append(b.s16(B.PIC0 + B.PP_YOFFSET))
            escursioni[cls_] = (min(ys), max(ys))
            self.assertEqual(b.u8(STATO + B.ST_LAST_CLS), cls_,
                             "la classe letta non e' quella del Pokepic")
            self.assertEqual(max(ys), self.par["amp"][cls_])
            self.assertEqual(min(ys), -self.par["amp"][cls_])
        self.assertLess(escursioni[0][1], escursioni[2][1],
                        "un Pokemon piccolo deve oscillare meno di uno grande")

    def test_H5b_senza_il_bit_taglia_la_classe_e_una(self):
        for cls_ in (0, 3):
            b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
            b.prepara(degrees=180, cls=cls_)
            b.imposta_stato(flags=F_RESPIRO)
            ys = []
            for _ in range(36):
                b.nostro()
                ys.append(b.s16(B.PIC0 + B.PP_YOFFSET))
            self.assertEqual(max(ys), self.par["amp"][1])

    def test_H6_scala_entro_0x100_piu_o_meno_6(self):
        for cls_ in range(4):
            b = B.Banco2(self.dest, CODICE, TABELLE, STATO, SLOT)
            b.prepara(degrees=180, cls=cls_)
            b.imposta_stato(flags=F_TUTTI)
            for _ in range(36):
                b.nostro()
                for off in (B.PP_AFFINEW, B.PP_AFFINEH):
                    v = b.s16(B.PIC0 + off)
                    self.assertLessEqual(abs(v - 0x100), 6,
                                         f"scala fuori da 0x100+-6: {v:#x}")

    def test_H7_quattro_lottatori_indipendenti(self):
        """Quattro voci, quattro fasi, nessuno scrive nella voce di un altro."""
        ods = [B.OD0, B.OD1, B.OD0 + 0x2000, B.OD0 + 0x3000]
        pics = [B.PIC0, B.PIC1, B.PIC0 + 0x2000, B.PIC0 + 0x3000]
        for od, pic in zip(ods, pics):
            self.b.prepara(od=od, pic=pic, degrees=180, cls=1)
        self.b.imposta_stato(flags=F_TUTTI)
        for _ in range(36):
            for od in ods:
                self.b.nostro(od=od)
        visti = [self.b.voce(i)["od"] for i in range(4)]
        self.assertEqual(sorted(visti), sorted(ods), "le quattro voci non sono distinte")
        serie = [self.b.s16(p + B.PP_YOFFSET) for p in pics]
        self.assertGreaterEqual(len(set(serie)), 3, "le fasi non sono indipendenti")

    def test_H8_niente_rotazione(self):
        """Nessuna scrittura sugli attributi di rotazione (10c §3.1 idea 5:
        sconsigliata). Gli attributi 7,8,9 stanno a +0x38,+0x3A,+0x3C."""
        self.b.prepara(degrees=180)
        self.b.imposta_stato(flags=F_TUTTI)
        for _ in range(36):
            self.b.nostro()
        self.assertEqual(self.b.rd(B.PIC0 + 0x38, 6), bytes(6),
                         "qualcuno ha scritto una rotazione")


if __name__ == "__main__":
    unittest.main()
