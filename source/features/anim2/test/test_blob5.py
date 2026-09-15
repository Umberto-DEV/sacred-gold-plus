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
    from banco4 import (OD0, OD1, PIC0, PIC1, PP_ANIMACTIVE, PP_YOFFSET,
                        PP_AFFINEW, PP_AFFINEH, PP_SHADOW_YOFF, OD_POKEPIC,
                        SL_OD, SL_PIC, SL_SIZE)
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


if __name__ == "__main__":
    unittest.main()
