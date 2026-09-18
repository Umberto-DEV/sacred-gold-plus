#!/usr/bin/env python3
"""Prove v5 sul codice ARM reale: multi-lottatore, politica e sospensione."""
import os
import sys
import unittest
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))

try:
    from banco5 import Banco5, BS, ANIMSYS
    from banco4 import (OD0, OD1, PIC0, PIC1, PP_ANIMACTIVE, PP_ANIMSTEP,
                        PP_YOFFSET, PP_AFFINEW, PP_AFFINEH, PP_SHADOW_YOFF,
                        OD_POKEPIC, SL_OD, SL_PIC, SL_SIZE)
    from unicorn import UC_HOOK_CODE
    from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0,
                                   UC_ARM_REG_R1, UC_ARM_REG_R2)
    UNICORN = True
except ImportError:
    UNICORN = False

REPO = QUI.parents[3]
BUILD = Path(os.environ.get("SGP_BUILD", REPO / "source/sgp12/build/anim2"))
MODULI = Path(os.environ.get("SGP_MODULI", ""))
OD2, OD3 = 0x02302000, 0x02303000
PIC2, PIC3, PIC4 = 0x02312000, 0x02313000, 0x02314000
LRS = [0x02258E9D, 0x0225933D, 0x0225959B, 0x0225DFC3, 0x0225E00F,
       0x0225E0B7, 0x0225E3A3, 0x0225E675, 0x0225FC0F]
# offset di `par.bin` (sgp_anim5.h) e dello stato, usati dalle prove dell'accento
PAR_BLINK_MIN, PAR_BLINK_MASK, PAR_BLINK_DUR = 0x0C, 0x0D, 0x0E
PAR_RARO_OGNI, PAR_RARO_PIU = 0x0F, 0x10
ST_LAST_STEP, ST_LAST_IDX = 0x12, 0x13
SL_RNG, SL_BLEFT, SL_BWAIT = 0x08, 0x10, 0x11
SL_FASE, SL_INVILUPPO = 0x16, 0x17   # fase privata in ottavi, inviluppo 0..16
SL_CODA0 = 0x18            # v5d: il BattleSystem che ha creato la voce (M2)
PAR_PASSO = 0x17           # par.bin: stesso numero di SL_INVILUPPO, tabella diversa
SETATTR = 0x020087A4       # Pokepic_SetAttr, indirizzo pari
PICCO = (4, 5)             # indici in cui `tab_u` vale il massimo (16)


@unittest.skipUnless(UNICORN, "serve unicorn")
@unittest.skipUnless((BUILD / "blob.bin").is_file(), "serve la build v5")
@unittest.skipUnless((MODULI / "moduli.json").is_file(),
                     "serve SGP_MODULI con ARM9 e ov012 estratti")
class Blob5Test(unittest.TestCase):
    def setUp(self):
        self.b = Banco5(BUILD)
        self.b.accendi()
        self.b.prepara(OD0, PIC0, ombra_yoff=7)

    def test_spento_e_byte_identico_al_task_vanilla(self):
        a, v = Banco5(BUILD), Banco5(BUILD)
        a.spegni()
        a.prepara(OD0, PIC0)
        v.prepara(OD0, PIC0)
        a.nostro(OD0)
        v.vanilla(OD0)
        self.assertEqual(a.istantanea(PIC0, OD0), v.istantanea(PIC0, OD0))

    def test_quattro_lottatori_occupano_quattro_voci(self):
        coppie = [(OD0, PIC0), (OD1, PIC1), (OD2, PIC2), (OD3, PIC3)]
        self.b.prepara_bs([x[0] for x in coppie])
        for od, pic in coppie:
            self.b.prepara(od, pic)
            self.b.nostro(od)
        self.assertEqual(
            {self.b.u32(self.b.slot + i * SL_SIZE + SL_OD) for i in range(4)},
            {OD0, OD1, OD2, OD3},
        )

    def test_stub_avvia_una_volta_ognuno_dei_quattro(self):
        battlers = [OD0, OD1, OD2, OD3]
        self.b.prepara_bs(battlers)
        visti = []

        def intercetta(uc, address, size, user):
            visti.append((uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)))
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        h = self.b.uc.hook_add(UC_HOOK_CODE, intercetta, begin=0x02261FD4, end=0x02261FD4)
        try:
            self.b.chiama(self.b.avvia_tutti, r0=OD0, r1=BS)
        finally:
            self.b.uc.hook_del(h)
        self.assertEqual(visti, [(od, BS) for od in battlers])

    def test_i_nove_lr_hanno_la_politica_dichiarata(self):
        soppressi = {LRS[i] for i in (1, 2, 3, 4, 6, 7, 8)}
        for lr in LRS:
            self.b.prepara(OD0, PIC0)
            got = self.b.politica(OD0, lr)["r0"]
            self.assertEqual(got, 1 if lr in soppressi else 0, hex(lr))

    def test_sospensione_scrive_riposo_una_volta_poi_tace_e_riprende(self):
        self.b.nostro(OD0)
        self.b.mossa(True)
        self.b.nostro(OD0)
        self.assertEqual(self.b.s16(PIC0 + PP_YOFFSET), 0)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 0x100)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEH), 0x100)
        self.b.nostro(OD0, sorveglia=True)
        scritte_pic = [x for x in self.b.scritture if PIC0 <= x[0] < PIC0 + 0xAC]
        self.assertEqual(scritte_pic, [])
        self.b.mossa(False)
        prima = self.b.u32(self.b.stato + 8)
        self.b.nostro(OD0)
        self.assertGreater(self.b.u32(self.b.stato + 8), prima)

    def test_tutti_e_tre_i_cancelli_sospendono(self):
        for cancello in ("mossa", "ingresso", "animActive"):
            b = Banco5(BUILD)
            b.accendi()
            b.prepara(OD0, PIC0)
            if cancello == "mossa":
                b.mossa(True)
            elif cancello == "ingresso":
                b.ingresso(0, True)
            else:
                b.wr(PIC0 + PP_ANIMACTIVE, b"\x01")
            b.nostro(OD0)
            self.assertEqual(b.u32(b.stato + 0x0C), 1, cancello)

    def test_cambio_pic_riazzera_la_voce(self):
        self.b.nostro(OD0)
        self.b.mossa(True)
        self.b.nostro(OD0)
        self.b.mossa(False)
        self.b.prepara(OD0, PIC4)
        self.b.nostro(OD0)
        self.assertEqual(self.b.u32(self.b.slot + SL_PIC), PIC4)
        self.assertEqual(self.b.u8(self.b.slot + 0x15), 0)

    def test_ombra_resta_ancorata_entro_un_pixel(self):
        ys = []
        for _ in range(36):
            self.b.nostro(OD0)
            ys.append(self.b.y_ombra(PIC0)[1])
        self.assertLessEqual(max(ys) - min(ys), 1)

    def test_respiro_rallentato_senza_salti_di_pixel(self):
        # Il vecchio ciclo di 18 tick deve durare da 36 a 72 tick (0.5–0.25x).
        # Misuriamo gli attributi realmente scritti dal blob, non la sua fase.
        campioni = []
        for _ in range(240):
            self.b.nostro(OD0)
            campioni.append((self.b.s16(PIC0 + PP_YOFFSET),
                             self.b.s16(PIC0 + PP_AFFINEW)))
        campioni = campioni[80:]  # lascia terminare l'ingresso a riposo
        periodo = next((p for p in range(1, 73)
                        if all(a == b for a, b in zip(campioni, campioni[p:]))), None)
        self.assertIsNotNone(periodo)
        self.assertGreaterEqual(periodo, 36)
        self.assertGreater(max(y for y, _ in campioni), min(y for y, _ in campioni))
        self.assertLessEqual(max(abs(a[0] - b[0]) for a, b in
                                 zip(campioni, campioni[1:])), 1)

    def test_ripresa_dopo_mossa_parte_da_riposo(self):
        self.b.prepara_bs([OD0, OD1, OD2, OD3])
        for od, pic in ((OD0, PIC0), (OD1, PIC1), (OD2, PIC2), (OD3, PIC3)):
            self.b.prepara(od, pic)
            for _ in range(13):
                self.b.nostro(od)
        self.b.mossa(True)
        for od in (OD0, OD1, OD2, OD3):
            self.b.nostro(od)
        self.b.mossa(False)
        for od, pic in ((OD0, PIC0), (OD1, PIC1), (OD2, PIC2), (OD3, PIC3)):
            self.b.nostro(od)
            self.assertLessEqual(abs(self.b.s16(pic + PP_YOFFSET)), 1)

    def test_sprite_cancellato_non_viene_animato_e_libera_slot(self):
        self.b.nostro(OD0)
        self.b.wr(PIC0, bytes(4))  # Pokepic_Delete: active = FALSE
        self.b.nostro(OD0, sorveglia=True)
        self.assertEqual([x for x in self.b.scritture
                          if PIC0 <= x[0] < PIC0 + 0xAC], [])
        self.assertEqual(self.b.u32(self.b.slot + SL_OD), 0)

    def test_scala_nativa_sospende_anche_posa_respiro_e_ombra(self):
        self.b.nostro(OD0)
        self.b.wr16(PIC0 + PP_AFFINEW, 128)
        self.b.wr16(PIC0 + PP_AFFINEH, 128)
        self.b.nostro(OD0)
        self.b.nostro(OD0, sorveglia=True)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 128)
        self.assertEqual([x for x in self.b.scritture
                          if PIC0 <= x[0] < PIC0 + 0xAC], [])

    def test_avvio_rimette_ferma_la_barra_hp(self):
        self.b.wr16(OD0 + 0x28 + 0x54, 160)  # fase del bounce HUD

        def sistema_creazione(uc, address, size, user):
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        # La sola creazione OS è esclusa; il reset della barra e il renderer
        # sono quelli originali. La prova pixel runtime copre il task vivo.
        h = self.b.uc.hook_add(UC_HOOK_CODE, sistema_creazione,
                              begin=0x02261FD4, end=0x02261FD4)
        try:
            self.b.chiama(self.b.avvia_tutti, r0=OD0, r1=BS)
        finally:
            self.b.uc.hook_del(h)
        self.assertEqual(self.b.u16(OD0 + 0x28 + 0x54), 0)

    def test_tutti_i_menu_conservano_il_task_fino_alla_mossa(self):
        for i in (1, 2, 3, 4, 6, 7, 8):
            with self.subTest(sito=hex(LRS[i])):
                self.assertEqual(self.b.politica(OD0, LRS[i])["r0"], 1)

    def test_cattura_ferma_tutti_prima_di_creare_il_task_nativo(self):
        self.b.prepara_bs([OD0, OD1])
        self.b.prepara(OD1, PIC1)
        for od in (OD0, OD1):
            self.b.nostro(od)
        work = 0x02358000
        self.b.wr(work, BS.to_bytes(4, "little"))
        visti = []

        def scheduler(uc, address, size, user):
            if address == 0x0200E320:
                visti.append((uc.reg_read(UC_ARM_REG_R0),
                              uc.reg_read(UC_ARM_REG_R1),
                              uc.reg_read(UC_ARM_REG_R2),
                              self.b.voci_occupate(),
                              [self.b.u32(od + 0x198) for od in (OD0, OD1)]))
                uc.reg_write(UC_ARM_REG_R0, 0x42)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        hooks = [self.b.uc.hook_add(UC_HOOK_CODE, scheduler, begin=a, end=a)
                 for a in (0x0200E320, 0x0200E390)]
        try:
            # La build precedente raggiungeva direttamente CreateOnMainQueue.
            fn = self.b.simboli.get("sgp_avvia_cattura", 0x0200E321) & ~1
            r = self.b.chiama(fn, r0=0x022465A9, r1=work, r2=0)
        finally:
            for h in hooks:
                self.b.uc.hook_del(h)
        self.assertEqual(visti, [(0x022465A9, work, 0, [], [0, 0])])
        self.assertEqual(r["r0"], 0x42)

    def test_ko_ritagliato_sospende_senza_cambiare_scala(self):
        self.b.nostro(OD0)
        # Funzione originale che il KO chiama prima di abbassare il corpo.
        self.b.chiama(0x0200908C, r0=PIC0, r1=0, r2=0, r3=80)
        self.assertEqual(self.b.u32(PIC0 + 0x54) & 2, 2)
        self.b.nostro(OD0)
        self.b.nostro(OD0, sorveglia=True)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 256)
        self.assertEqual([x for x in self.b.scritture
                          if PIC0 <= x[0] < PIC0 + 0xAC], [])

    def test_riuso_stesso_indirizzo_riparte_con_nuova_ombra(self):
        for _ in range(24):
            self.b.nostro(OD0)
        nuova_base = self.b.s16(PIC0 + PP_SHADOW_YOFF)
        self.b.wr(PIC0, bytes(4))
        self.b.nostro(OD0)
        self.b.prepara(OD0, PIC0, ombra_yoff=nuova_base)
        self.b.nostro(OD0)
        self.assertLessEqual(abs(self.b.s16(PIC0 + PP_YOFFSET)), 1)
        self.assertEqual(self.b.s16(PIC0 + PP_SHADOW_YOFF)
                         + self.b.s16(PIC0 + PP_YOFFSET), nuova_base)

    def test_pulizia_non_scrive_sul_vecchio_puntatore(self):
        for _ in range(24):
            self.b.nostro(OD0)
        self.b.wr(OD0 + OD_POKEPIC, PIC4.to_bytes(4, "little"))
        prima = self.b.rd(PIC0, 0xAC)
        self.b.politica(OD0, 0)
        self.assertEqual(self.b.rd(PIC0, 0xAC), prima)

    def test_distruzione_non_legge_altri_lottatori_gia_liberati(self):
        self.b.prepara_bs([OD0, 0xDEAD0000])
        self.b.nostro(OD0)
        self.assertEqual(self.b.politica(OD0, LRS[0])["r0"], 0)
        self.assertEqual(self.b.voci_occupate(), [])

    def test_cattura_spenta_conserva_argomenti_e_ritorno(self):
        self.b.spegni()
        work = 0x02358000
        visti = []

        def scheduler(uc, address, size, user):
            visti.append((uc.reg_read(UC_ARM_REG_R0),
                          uc.reg_read(UC_ARM_REG_R1), uc.reg_read(UC_ARM_REG_R2)))
            uc.reg_write(UC_ARM_REG_R0, 0x42)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

        h = self.b.uc.hook_add(UC_HOOK_CODE, scheduler,
                              begin=0x0200E320, end=0x0200E320)
        try:
            r = self.b.chiama(self.b.simboli["sgp_avvia_cattura"] & ~1,
                              r0=0x022465A9, r1=work, r2=0)
        finally:
            self.b.uc.hook_del(h)
        self.assertEqual(visti, [(0x022465A9, work, 0)])
        self.assertEqual(r["r0"], 0x42)
        self.assertEqual(self.b.u32(OD0 + 0x198), 0x02320000)


    # ------------------------------------------------------------------ v5d
    def _porta_dentro_la_posa_b(self, od=OD0, limite=4000):
        """Fa girare il task finche' la voce non e' dentro una posa B con
        almeno un tick residuo. Rende il numero di tick consumati."""
        for i in range(limite):
            self.b.nostro(od)
            if self.b.u8(self.b.slot + SL_BLEFT) != 0:
                return i + 1
        self.fail("in %d tick la posa B non e' mai iniziata" % limite)

    def test_cancello_dentro_la_posa_b_annulla_il_residuo(self):
        """B3 (A1 §3.2, misurato sul banco in A2 §6.2): oggi il residuo di
        `blink_left` si congela e la posa B riappare appena il cancello cade —
        un lampo fisso alla fine di ogni mossa. Dopo la correzione la posa e'
        annullata e l'attesa riparte da un valore pieno."""
        blink_min = self.b.par(PAR_BLINK_MIN)
        self._porta_dentro_la_posa_b()
        self.b.mossa(True)
        self.b.nostro(OD0)                     # riposo + sospensione
        self.assertEqual(self.b.u8(self.b.slot + SL_BLEFT), 0,
                         "il residuo della posa B non e' stato annullato")
        self.assertGreaterEqual(self.b.u8(self.b.slot + SL_BWAIT), blink_min,
                                "l'attesa non e' ripartita da un valore pieno")
        self.b.mossa(False)
        for i in range(blink_min):
            self.b.nostro(OD0)
            self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 0,
                             "posa B al tick %d dopo il rilascio" % i)

    def test_ogni_accento_comincia_al_picco_del_respiro(self):
        """S3 (A1 §3.3, confermato in A2 §3: il cambio di posa e' oggi
        indipendente dalla fase, chi-quadro compatibile con l'uniforme). In
        v5d l'accento parte solo nel punto di quiete del respiro, dove
        `tab_u` e' al massimo, cosi' non si sommano due moti."""
        inizi, prec = [], self.b.u8(PIC0 + PP_ANIMSTEP)
        for _ in range(400):
            self.b.nostro(OD0)
            p = self.b.u8(PIC0 + PP_ANIMSTEP)
            if p == 1 and prec == 0:
                inizi.append(self.b.u8(self.b.stato + ST_LAST_IDX))
            prec = p
        self.assertTrue(inizi, "nessun accento in 400 tick")
        self.assertEqual(sorted(set(inizi) - set(PICCO)), [],
                         "accenti fuori dal picco, indici visti: %s" % inizi)

    def test_prima_attesa_casuale_per_ogni_lottatore(self):
        """S2 (A1 §3.3): in v5c la prima attesa e' `BLINK_MIN` nuda, uguale per
        tutti, e quattro lottatori creati nello stesso tick fanno il primo
        accento all'unisono. In v5d la prima attesa e' sorteggiata come ogni
        altra."""
        b = Banco5(BUILD)
        b.accendi()
        b.prepara_bs([OD0, OD1])
        minimo, maschera = b.par(PAR_BLINK_MIN), b.par(PAR_BLINK_MASK)
        for od, pic in ((OD0, PIC0), (OD1, PIC1)):
            b.prepara(od, pic)
        b.nostro(OD0)
        b.nostro(OD1)
        attese = [b.u8(b.slot + i * SL_SIZE + SL_BWAIT) for i in (0, 1)]
        for a in attese:   # un tick e' gia' stato scalato dal primo giro
            self.assertGreaterEqual(a + 1, minimo)
            self.assertLessEqual(a + 1, minimo + maschera)
        self.assertNotEqual(attese[0], attese[1],
                            "i due lottatori hanno la STESSA prima attesa (%s)" % attese)

    def test_primo_accento_in_tick_diversi_per_i_due_lottatori(self):
        """M4 (A8b, riesaminato in review): QUESTO test misura l'effetto
        visibile combinato di S2 (prima attesa sorteggiata) **e** dello
        sfasamento statico `--fase` spedito (0,9,5,14) — non S2 da solo. Con
        `--fase` spedito i due lottatori raggiungono il picco del respiro
        (SGP_PICCO_IDX) su tick assoluti gia' diversi, quindi resterebbe
        verde anche con un S2 rotto (`blink_wait` identico per tutti).

        La prova diretta e deterministica di S2 e'
        `test_prima_attesa_casuale_per_ogni_lottatore`, che legge `blink_wait`
        dalla voce invece di dedurlo dal primo accento visibile.

        Si e' provato ad azzerare i quattro byte di `PAR_FASE` nella RAM del
        banco per isolare S2: con OD0/OD1 e la sequenza di chiamate di questo
        test il risultato e' PEGGIORE, non migliore — i due lottatori restano
        allo stesso tick (250 == 250) pur avendo `blink_wait` diversi (vedi
        l'altro test), perche' l'accento e' quantizzato sulle finestre di
        picco del respiro (una ogni 48 tick, larga 4 tick): due attese
        diverse possono arrotondare sulla STESSA finestra per coincidenza.
        Isolare `--fase` scambia un falso positivo (questo test, con S2
        rotto) con un falso negativo (con S2 funzionante): non e' stato
        tenuto. Questo test resta quello che il pacchetto spedito garantisce
        davvero: coi parametri di consegna, il primo accento dei due
        lottatori NON e' all'unisono."""
        b = Banco5(BUILD)
        b.accendi()
        b.prepara_bs([OD0, OD1])
        for od, pic in ((OD0, PIC0), (OD1, PIC1)):
            b.prepara(od, pic)
        primo = {}
        for t in range(600):
            for od, pic in ((OD0, PIC0), (OD1, PIC1)):
                b.nostro(od)
                if od not in primo and b.u8(pic + PP_ANIMSTEP) == 1:
                    primo[od] = t
            if len(primo) == 2:
                break
        self.assertEqual(len(primo), 2, "un lottatore non ha mai fatto l'accento")
        self.assertNotEqual(primo[OD0], primo[OD1], primo)

    def test_spegnere_a_lotta_in_corso_ripulisce_e_libera(self):
        """A8b-A1: le due uscite «opzione spenta» ritornavano senza
        `sgp_pulisci`, e affineW/H (+-6), shadow.yOffset e posa B restavano
        impressi sullo sprite — D1+D2 della v4, reintrodotti."""
        for _ in range(120):   # fino a trovare lo sprite davvero spostato
            self.b.nostro(OD0)
            if self.b.s16(PIC0 + PP_AFFINEW) != 256:
                break
        base = self.b.s16(self.b.slot + 0x0C)          # base76 catturata
        self.assertNotEqual(self.b.s16(PIC0 + PP_AFFINEW), 256,
                            "la scala non e' stata toccata: prova non probante")
        self.b.spegni()
        self.b.politica(OD0, LRS[0])
        self.assertEqual(self.b.voci_occupate(), [])
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 256)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEH), 256)
        self.assertEqual(self.b.s16(PIC0 + PP_SHADOW_YOFF), base)
        self.assertEqual(self.b.s16(PIC0 + PP_YOFFSET), 0)
        self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 0)

    def test_spegnere_dal_task_ripulisce_prima_del_task_vanilla(self):
        """L'altra uscita «opzione spenta»: quella del task idle."""
        for _ in range(24):
            self.b.nostro(OD0)
        self.b.spegni()
        self.b.nostro(OD0)
        self.assertEqual(self.b.voci_occupate(), [])
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 256)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEH), 256)
        self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 0)

    def test_opzione_mai_accesa_non_scrive_un_byte_in_piu(self):
        """La byte-identita' a interruttore spento: le stesse Pokepic_SetAttr,
        nello stesso ordine, e la politica che non tocca il Pokepic."""
        a, v = Banco5(BUILD), Banco5(BUILD)
        a.spegni()
        v.spegni()
        a.prepara(OD0, PIC0, ombra_yoff=7)
        v.prepara(OD0, PIC0, ombra_yoff=7)
        conta = {"a": 0, "v": 0}

        def fai(banco, chiave):
            def visto(uc, address, size, user):
                conta[chiave] += 1
            h = banco.uc.hook_add(UC_HOOK_CODE, visto,
                                  begin=SETATTR, end=SETATTR)
            try:
                if chiave == "a":
                    banco.nostro(OD0, sorveglia=True)
                else:
                    banco.vanilla(OD0)
            finally:
                banco.uc.hook_del(h)

        fai(a, "a")
        fai(v, "v")
        self.assertEqual(conta["a"], conta["v"], conta)
        self.assertEqual(a.istantanea(PIC0, OD0), v.istantanea(PIC0, OD0))
        prima = a.rd(PIC0, 0xAC)
        a.politica(OD0, LRS[0])
        self.assertEqual(a.rd(PIC0, 0xAC), prima,
                         "la politica a opzione spenta ha scritto nel Pokepic")

    def test_seconda_lotta_con_stessi_indirizzi_ricrea_la_voce(self):
        """M2 (A8b): `s->idx`, inviluppo, fase e rng sopravvivevano a una
        seconda lotta che riusa gli stessi indirizzi. La voce porta ora il
        `BattleSystem` che l'ha creata e si riazzera quando cambia."""
        BS2 = 0x02354000
        for _ in range(24):
            self.b.nostro(OD0)
        rng = self.b.u32(self.b.slot + SL_RNG)
        fase = self.b.u8(self.b.slot + 0x16)
        self.assertNotEqual(fase, 0, "fase gia' a zero: prova non probante")
        self.b.wr(BS2, self.b.rd(BS, 0x220))          # seconda lotta, stessi od
        self.b.wr(self.b.stato + 0x28, BS2.to_bytes(4, "little"))
        self.b.nostro(OD0)
        self.assertEqual(self.b.u32(self.b.slot + SL_CODA0), BS2)
        self.assertNotEqual(self.b.u32(self.b.slot + SL_RNG), rng)
        # M3 (A8b): `yOffset == 0` al tick 25 non e' probante, perche' vale
        # anche col bug (idx sopravvissuto puo' dare y=0 per coincidenza
        # della tavola). Si legge direttamente la voce: inviluppo == 1 (era
        # 0, un solo tick e' passato da quando slot_per l'ha azzerato) e
        # fase == passo (era 0, +PASSO in un tick), non la loro proiezione
        # sullo schermo.
        self.assertEqual(self.b.u8(self.b.slot + SL_INVILUPPO), 1,
                         "l'inviluppo non e' ripartito da zero")
        self.assertEqual(self.b.u8(self.b.slot + SL_FASE), self.b.par(PAR_PASSO),
                         "la fase non e' ripartita da zero")

    def test_durata_della_posa_b_segue_i_parametri(self):
        """A1 §1.2 / A2 §3.2: l'intervallo con ANIM_STEP=1 dura `dur` o
        `dur+1` tick, e uno su `raro_ogni` dura `raro_piu` tick in piu'."""
        dur = self.b.par(PAR_BLINK_DUR)
        piu = self.b.par(PAR_RARO_PIU)
        attese = {dur, dur + 1, dur + piu, dur + piu + 1}
        durate, corsa, prec = [], 0, 0
        for _ in range(3000):
            self.b.nostro(OD0)
            p = self.b.u8(PIC0 + PP_ANIMSTEP)
            if p == 1:
                corsa += 1
            elif prec == 1:
                durate.append(corsa)
                corsa = 0
            prec = p
        self.assertGreaterEqual(len(durate), 3, durate)
        self.assertEqual(sorted(set(durate) - attese), [],
                         "durate fuori dai parametri %s: %s" % (sorted(attese), durate))

if __name__ == "__main__":
    unittest.main()
