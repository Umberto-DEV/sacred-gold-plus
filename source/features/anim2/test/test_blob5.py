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
    from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_R1
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
        soppressi = {LRS[1], LRS[3], LRS[4]}
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


if __name__ == "__main__":
    unittest.main()
