#!/usr/bin/env python3
"""SGP-1.2-ANIM-SOLIDO-01 — i test del blob v4 su Unicorn.

Regola V7 di `CRITERI.md`: **ogni difetto trovato ha prima un test che lo
riproduce**. I test si dividono in tre famiglie e si eseguono **due volte**,
una sul blob **v3** (quello che sta in ROM oggi) e una sul **v4**:

  * `R*` — **riproduzione**: sul v3 devono dimostrare il difetto (il test
    ASSERISCE che il difetto c'è). Sul v4 lo stesso difetto non c'è più, e
    infatti l'asserzione è nel test `V*` corrispondente. I due non sono lo
    stesso test con l'esito girato: `R*` misura il residuo, `V*` misura la
    pulizia, e tutti e due girano sempre.
  * `V*` — **verifica della cura**, solo v4.
  * `G*`/`H*` — **non regressione**: le proprietà della fase 1b/2b che la v4
    non deve avere perso.

Il blob si sceglie con l'ambiente:
    SGP_BUILD=<dir>      cartella di build (blob.bin + manifesto.json)
    SGP_MODULI=<dir>     moduli estratti (arm9.bin, ov012.bin, moduli.json)

Esempio:
    SGP_MODULI=$S/moduli/base-EN SGP_BUILD=$S/build \\
      python3 -m unittest discover -s test -p 'test_blob4.py' -v

GPL-3.0-or-later.
"""
import os
import sys
import unittest
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))

BUILD = Path(os.environ.get("SGP_BUILD", QUI.parent / "work" / "build"))

try:
    from banco4 import (Banco4, OD0, OD1, PIC0, PIC1, PP_AFFINEW, PP_AFFINEH,
                        PP_ANIMSTEP, PP_SHADOW_YOFF, PP_YOFFSET, PP_SHADOW_FLAGS,
                        SL_OD, SL_SIZE, ST_STOP_VISTI, ST_PULITI, OD_DEGREES,
                        LOAD_ABSENT, LOAD_VALID, LOAD_REJECT, LOAD_NONE, GUARD)
    UNICORN = True
except ImportError as e:          # pragma: no cover
    UNICORN = False
    MOTIVO = str(e)

BASE = 0x023D8B00
CODICE = BASE + 0x000
TABELLE = BASE + 0x300
STATO = BASE + 0x340
SLOT = BASE + 0x380

OD2, OD3 = 0x02302000, 0x02303000
PIC2, PIC3 = 0x02312000, 0x02313000


@unittest.skipUnless(UNICORN, "serve unicorn")
class Base(unittest.TestCase):
    def banco(self, blob="blob.bin", build=None):
        return Banco4(build or BUILD, CODICE, TABELLE, STATO, SLOT, blob=blob)

    def setUp(self):
        self.b = self.banco()

    def gira(self, n, od=OD0, pic=PIC0, **kw):
        self.b.prepara(od=od, pic=pic, **kw)
        for _ in range(n):
            self.b.nostro(od=od)


# ===========================================================================
# R — riproduzione dei difetti sulla v3 (il blob che sta in ROM oggi)
# ===========================================================================
@unittest.skipUnless(UNICORN, "serve unicorn")
class RiproduzioneV3(unittest.TestCase):
    """Gira sul blob v3 ricompilato dai sorgenti di `SGP-1.2-ANIM-B-03`
    (sha256 86a4e132…, lo stesso che il rilettore trova in ROM)."""

    @classmethod
    def setUpClass(cls):
        cls.build_v3 = Path(os.environ.get("SGP_BUILD_V3", BUILD.parent / "build-v3"))
        if not (cls.build_v3 / "blob.bin").exists():
            raise unittest.SkipTest("manca la build v3 (SGP_BUILD_V3)")

    def setUp(self):
        self.b = Banco4(self.build_v3, CODICE, TABELLE, STATO, SLOT, blob="blob.bin")

    def test_R1_la_v3_non_ha_la_trampolina(self):
        """Il difetto D1 nasce da qui: nel v3 non esiste `sgp_idle_stop`,
        quindi non c'è nessun posto in cui rimettere a posto le scritture."""
        self.assertFalse(self.b.ha_pulizia)
        self.assertNotIn("sgp_idle_stop", self.b.simboli)

    def test_R2_residuo_di_scala_e_ombra_dopo_la_fermata(self):
        """D1, riprodotto: dopo N esecuzioni il gioco ferma il task e rimette
        SOLO `yOffset` a 0. Scala affine e scostamento dell'ombra restano
        quelli scritti da noi. È la misura fatta in emulazione (257/255 e −1
        per 1235 fotogrammi), qui deterministica."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0, cls=2, ombra_yoff=0)
        for _ in range(4):     # 4 esecuzioni da degrees=180: fase 13, |u| massimo
            self.b.nostro(od=OD0)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)    # solo yOffset = 0
        self.assertEqual(self.b.s16(PIC0 + PP_YOFFSET), 0, "il gioco azzera yOffset")
        residuo_w = self.b.s16(PIC0 + PP_AFFINEW)
        residuo_h = self.b.s16(PIC0 + PP_AFFINEH)
        residuo_s = self.b.s16(PIC0 + PP_SHADOW_YOFF)
        self.assertTrue(residuo_w != 0x100 or residuo_h != 0x100 or residuo_s != 0,
                        "atteso un residuo: affineW=%d affineH=%d shadow.yOff=%d"
                        % (residuo_w, residuo_h, residuo_s))

    def test_R3_residuo_della_posa_a_occhi_chiusi(self):
        """D1, il caso peggiore: se la fermata cade dentro un battito, il
        Pokémon resta con la posa B (occhi chiusi) finché qualcuno non fa
        ripartire un'animazione."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        visto = False
        for _ in range(400):
            self.b.nostro(od=OD0)
            if self.b.u8(PIC0 + PP_ANIMSTEP) == 1:
                visto = True
                break
        self.assertTrue(visto, "il battito deve capitare almeno una volta in 400 giri")
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 1,
                         "la v3 lascia la posa B addosso allo sprite")

    def test_R4_la_voce_del_lottatore_non_viene_mai_liberata(self):
        """D2, riprodotto: `od` resta impresso per sempre."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.u32(SLOT + SL_OD), OD0)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.u32(SLOT + SL_OD), OD0,
                         "la v3 non ha modo di liberare la voce")

    def test_R5_lo_stato_dell_ombra_sopravvive_alla_lotta(self):
        """D2, la conseguenza VERA e misurabile: la voce non viene mai
        liberata, quindi alla lotta dopo — stesso `OpponentData` e stesso
        `Pokepic`, perche' il gioco riusa l'indice del lottatore — il valore a
        riposo dell'ombra della specie PRECEDENTE resta buono. La ri-cattura
        (`cur != last76`) di solito salva la situazione, ma NON quando la nuova
        specie ha per caso il valore a riposo che avevamo scritto noi: allora
        l'ombra resta spostata per tutta la lotta.

        Nota onesta: la conseguenza che si potrebbe temere — quattro voci morte
        che fanno litigare quattro lottatori vivi in lotta doppia — **non si
        riproduce**: lo sfratto a giro converge in un giro. E' scritto nel
        RAPPORTO, non nascosto."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0, cls=2, ombra_yoff=0)
        for _ in range(4):
            self.b.nostro(od=OD0)
        nostro_ultimo = self.b.s16(PIC0 + PP_SHADOW_YOFF)
        self.assertNotEqual(nostro_ultimo, 0)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        # lotta nuova: specie diversa, il cui valore a riposo dell'ombra e'
        # proprio quello che avevamo lasciato scritto noi
        self.b.wr16(PIC0 + PP_SHADOW_YOFF, nostro_ultimo)
        self.b.uc.mem_write(OD0 + OD_DEGREES, (180).to_bytes(2, "little"))
        self.b.nostro(od=OD0)
        base = self.b.s16(SLOT + 0x0C)
        self.assertNotEqual(base, nostro_ultimo,
                            "la v3 non ri-cattura il valore a riposo della specie nuova")

    def test_R6_interruttore_letto_senza_guardia(self):
        """D3 (segnalazione S9 di QUALITA-NATIVO-01): la v3 legge il byte
        `anim` anche con la guardia del blocco di D1 assente e con il chunk
        RIFIUTATO."""
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.accendi(anim=1, guard=0x00, load_status=LOAD_REJECT)
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.u8(STATO + 0x00), 0x3F,
                         "la v3 anima anche senza guardia e con chunk RIFIUTATO")


# ===========================================================================
# V — la cura, sul v4
# ===========================================================================
class CuraV4(Base):
    def test_V1_la_trampolina_esiste_ed_e_thumb(self):
        self.assertTrue(self.b.ha_pulizia)
        self.assertEqual(self.b.simboli["sgp_idle_stop"] & 1, 1)
        self.assertEqual(self.b.simboli["sgp_idle_task2"] & 1, 1)

    def test_V2_scala_e_ombra_tornano_a_riposo(self):
        """D1 chiuso: la stessa corsa di R2, con la trampolina."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0, cls=2, ombra_yoff=0)
        for _ in range(4):     # 4 esecuzioni da degrees=180: fase 13, |u| massimo
            self.b.nostro(od=OD0)
        self.assertNotEqual(self.b.s16(PIC0 + PP_AFFINEW), 0x100,
                            "prima della fermata la scala deve essere fuori da 1.0")
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.s16(PIC0 + PP_YOFFSET), 0)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 0x100)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEH), 0x100)
        self.assertEqual(self.b.s16(PIC0 + PP_SHADOW_YOFF), 0)

    def test_V3_la_posa_torna_a_riposo(self):
        """D1 chiuso anche nel caso peggiore: niente occhi chiusi."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        for _ in range(400):
            self.b.nostro(od=OD0)
            if self.b.u8(PIC0 + PP_ANIMSTEP) == 1:
                break
        self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 1)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 0)

    def test_V4_ombra_a_riposo_non_nulla_si_ricostruisce(self):
        """Il valore a riposo dell'ombra dipende dalla specie (misurato: 14 sul
        lottatore avversario della corsa reale). La pulizia deve rimettere
        QUELLO, non zero."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0, ombra_yoff=14, cls=1)
        for _ in range(4):
            self.b.nostro(od=OD0)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.s16(PIC0 + PP_SHADOW_YOFF), 14)

    def test_V5_contratto_dei_registri_col_sito(self):
        """La trampolina deve tornare con esattamente quello che le due
        istruzioni sostituite avrebbero lasciato: r0 = pokepic, r1 = 4
        (POKEPIC_YOFFSET), r2 = 0; e non deve spostare la pila."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        for _ in range(5):
            self.b.nostro(od=OD0)
        r = self.b.ferma(od=OD0)
        self.assertEqual(r["r0"], PIC0)
        self.assertEqual(r["r1"], 4)
        self.assertEqual(r["r2"], 0)
        self.assertEqual(r["r4"], OD0)
        self.assertTrue(r["sp_invariato"])
        self.assertEqual(r["callee_saved_corrotti"], {})

    def test_V6_voce_liberata(self):
        """D2 chiuso."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.u32(SLOT + SL_OD), OD0)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.u32(SLOT + SL_OD), 0)
        self.assertEqual(self.b.voci_occupate(), [])
        self.assertEqual(self.b.stato_u32(ST_PULITI), 1)

    def test_V7_lo_stato_dell_ombra_non_sopravvive_alla_lotta(self):
        """D2 chiuso: la stessa scena di R5. La voce viene liberata alla
        fermata, quindi alla lotta dopo il valore a riposo si ri-cattura anche
        nel caso limite in cui coincide con quello che avevamo scritto noi."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0, cls=2, ombra_yoff=0)
        for _ in range(4):
            self.b.nostro(od=OD0)
        nostro_ultimo = self.b.s16(PIC0 + PP_SHADOW_YOFF)
        self.assertNotEqual(nostro_ultimo, 0)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.voci_occupate(), [])
        self.b.wr16(PIC0 + PP_SHADOW_YOFF, nostro_ultimo)
        self.b.uc.mem_write(OD0 + OD_DEGREES, (180).to_bytes(2, "little"))
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.s16(SLOT + 0x0C), nostro_ultimo)

    def test_V7b_quattro_lottatori_quattro_voci(self):
        """Quattro lottatori vivi insieme (lotta doppia) hanno una voce
        ciascuno, anche dopo che una lotta precedente ne ha occupate quattro:
        le voci vengono liberate alla fermata."""
        self.b.accendi()
        morti = [(0x02330000 + i * 0x1000, 0x02360000 + i * 0x1000) for i in range(4)]
        for od, pic in morti:
            self.b.prepara(od=od, pic=pic)
            self.b.nostro(od=od)
        for od, pic in morti:
            self.b.ferma_come_il_gioco(od=od, pic=pic)
        self.assertEqual(self.b.voci_occupate(), [])
        vivi = [(OD0, PIC0), (OD1, PIC1), (OD2, PIC2), (OD3, PIC3)]
        for od, pic in vivi:
            self.b.prepara(od=od, pic=pic)
        for _ in range(6):
            for od, _pic in vivi:
                self.b.nostro(od=od)
        occupati = {self.b.u32(SLOT + i * SL_SIZE + SL_OD) for i in range(4)}
        self.assertEqual(occupati, {od for od, _ in vivi})

    def test_V8_la_pulizia_non_strappa_la_scala_a_un_altro(self):
        """Se nel frattempo qualcun altro ha preso il canale della scala (fuori
        dalla finestra stretta), la pulizia non gliela strappa."""
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        for _ in range(5):
            self.b.nostro(od=OD0)
        self.b.wr16(PIC0 + PP_AFFINEW, 0x80)
        self.b.wr16(PIC0 + PP_AFFINEH, 0x80)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEW), 0x80)
        self.assertEqual(self.b.s16(PIC0 + PP_AFFINEH), 0x80)

    def test_V9_la_pulizia_non_strappa_l_ombra_a_un_altro(self):
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0, ombra_yoff=0)
        for _ in range(5):
            self.b.nostro(od=OD0)
        self.b.wr16(PIC0 + PP_SHADOW_YOFF, 99)
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.s16(PIC0 + PP_SHADOW_YOFF), 99)

    def test_V10_la_pulizia_non_tocca_la_posa_se_l_interprete_lavora(self):
        self.b.accendi()
        self.b.prepara(od=OD0, pic=PIC0)
        for _ in range(5):
            self.b.nostro(od=OD0)
        self.b.uc.mem_write(PIC0 + 0x58, bytes([1]))   # animActive
        self.b.uc.mem_write(PIC0 + PP_ANIMSTEP, bytes([1]))
        self.b.ferma_come_il_gioco(od=OD0, pic=PIC0)
        self.assertEqual(self.b.u8(PIC0 + PP_ANIMSTEP), 1)

    def test_V11_a_interruttore_spento_la_pulizia_non_scrive_nel_gioco(self):
        """Il gancio G2 è installato anche a funzione spenta: deve essere
        inerte sulla memoria del gioco. È la condizione di M9/V5 di CRITERI."""
        self.b.spegni()
        self.b.prepara(od=OD0, pic=PIC0, ombra_yoff=7, affine=0x100, anim_step=1)
        for _ in range(20):
            self.b.nostro(od=OD0)
        prima = self.b.istantanea(pic=PIC0, od=OD0)
        r = self.b.ferma(od=OD0, sorveglia=True)
        dopo = self.b.istantanea(pic=PIC0, od=OD0)
        self.assertEqual(prima, dopo, "a spento la pulizia non deve toccare il Pokepic")
        self.assertEqual(r["r0"], PIC0)
        self.assertEqual(r["r1"], 4)
        self.assertEqual(r["r2"], 0)
        fuori = [(a, s, v) for (a, s, v) in self.b.scritture
                 if not (STATO <= a < STATO + 64 or SLOT <= a < SLOT + 128
                         or 0x02340000 <= a < 0x02350000)]
        self.assertEqual(fuori, [], "scritture fuori dal nostro blocco e dalla pila")

    def test_V12_il_contatore_stop_conta_anche_a_spento(self):
        """`stop_visti` è la prova che il gancio G2 è vivo anche quando non
        c'è niente da ripulire: senza quel contatore una corsa verde a spento
        non distinguerebbe «gancio inerte» da «gancio mai chiamato»."""
        self.b.spegni()
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.ferma(od=OD0)
        self.b.ferma(od=OD0)
        self.assertEqual(self.b.stato_u32(ST_STOP_VISTI), 2)
        self.assertEqual(self.b.stato_u32(ST_PULITI), 0)

    def test_V13_guardia_del_chunk_assente_spegne(self):
        """D3 chiuso: senza la guardia 0x5A del blocco di D1 non si anima."""
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.accendi(anim=1, guard=0x00, load_status=LOAD_VALID)
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.u8(STATO + 0x00), 0x00)

    def test_V14_chunk_rifiutato_spegne(self):
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.accendi(anim=1, guard=GUARD, load_status=LOAD_REJECT)
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.u8(STATO + 0x00), 0x00)

    def test_V15_chunk_non_letto_spegne(self):
        self.b.prepara(od=OD0, pic=PIC0)
        self.b.accendi(anim=1, guard=GUARD, load_status=LOAD_NONE)
        self.b.nostro(od=OD0)
        self.assertEqual(self.b.u8(STATO + 0x00), 0x00)

    def test_V16_assente_e_valido_accendono(self):
        for ls in (LOAD_ABSENT, LOAD_VALID):
            with self.subTest(load_status=ls):
                b = self.banco()
                b.prepara(od=OD0, pic=PIC0)
                b.accendi(anim=1, guard=GUARD, load_status=ls)
                b.nostro(od=OD0)
                self.assertEqual(b.u8(STATO + 0x00), 0x3F)


# ===========================================================================
# G/H — non regressione: quello che la fase 1b/2b aveva già e non si perde
# ===========================================================================
class NonRegressione(Base):
    def test_G2_spento_memoria_del_gioco_identica_al_vanilla(self):
        a = self.banco()
        a.spegni()
        a.prepara(od=OD0, pic=PIC0)
        for _ in range(36):
            a.nostro(od=OD0)
        mia = a.istantanea(pic=PIC0, od=OD0)
        v = self.banco()
        v.prepara(od=OD0, pic=PIC0)
        for _ in range(36):
            v.vanilla(od=OD0)
        self.assertEqual(mia, v.istantanea(pic=PIC0, od=OD0))

    def test_G3_animActive_astensione_totale(self):
        a = self.banco()
        a.accendi()
        a.prepara(od=OD0, pic=PIC0, animActive=3)
        for _ in range(36):
            a.nostro(od=OD0)
        mia = a.istantanea(pic=PIC0, od=OD0)
        v = self.banco()
        v.prepara(od=OD0, pic=PIC0, animActive=3)
        for _ in range(36):
            v.vanilla(od=OD0)
        self.assertEqual(mia, v.istantanea(pic=PIC0, od=OD0))
        self.assertEqual(a.stato_u32(0x0C), 36)      # hits_busy

    def test_G4_yoffset_segue_la_tavola_e_non_salta_mai_piu_di_1px(self):
        for cls in range(4):
            with self.subTest(cls=cls):
                b = self.banco()
                b.accendi()
                b.prepara(od=OD0, pic=PIC0, cls=cls)
                serie = []
                for _ in range(72):
                    b.nostro(od=OD0)
                    serie.append(b.s16(PIC0 + PP_YOFFSET))
                salti = [abs(serie[i + 1] - serie[i]) for i in range(len(serie) - 1)]
                self.assertLessEqual(max(salti), 1,
                                     "classe %d: salto massimo %d px" % (cls, max(salti)))
                amp = (max(serie) - min(serie)) / 2
                self.assertGreaterEqual(amp, 2)

    def test_G10b_nessuna_scrittura_in_IO_o_VRAM(self):
        b = self.banco()
        b.accendi()
        b.prepara(od=OD0, pic=PIC0)
        for _ in range(40):
            b.nostro(od=OD0, sorveglia=True)
            for a, _s, _v in b.scritture:
                self.assertFalse(0x04000000 <= a < 0x05000000, "scrittura in I/O")
                self.assertFalse(0x06000000 <= a < 0x07000000, "scrittura in VRAM")
        b.ferma(od=OD0, sorveglia=True)
        for a, _s, _v in b.scritture:
            self.assertFalse(0x04000000 <= a < 0x05000000)
            self.assertFalse(0x06000000 <= a < 0x07000000)

    def test_G9_callee_saved_intatti(self):
        b = self.banco()
        b.accendi()
        b.prepara(od=OD0, pic=PIC0)
        for _ in range(10):
            r = b.nostro(od=OD0)
            self.assertEqual(r["callee_saved_corrotti"], {})

    def test_H1_ombra_ferma_su_tutte_e_quattro_le_classi(self):
        for cls in range(4):
            with self.subTest(cls=cls):
                b = self.banco()
                b.accendi()
                b.prepara(od=OD0, pic=PIC0, cls=cls, ombra_yoff=8, adegua_y=True)
                ys, yc = [], []
                for _ in range(72):
                    b.nostro(od=OD0)
                    yc.append(b.y_corpo(pic=PIC0))
                    ys.append(b.y_ombra(pic=PIC0)[1])
                esc_ombra = max(ys) - min(ys)
                esc_corpo = max(yc) - min(yc)
                self.assertLessEqual(esc_ombra, 1,
                                     "classe %d: ombra %d px" % (cls, esc_ombra))
                self.assertGreaterEqual(esc_corpo, 4)

    def test_H4_due_lottatori_sfasati(self):
        b = self.banco()
        b.accendi()
        b.prepara(od=OD0, pic=PIC0)
        b.prepara(od=OD1, pic=PIC1)
        s0, s1 = [], []
        for _ in range(72):
            b.nostro(od=OD0)
            s0.append(b.s16(PIC0 + PP_YOFFSET))
            b.nostro(od=OD1)
            s1.append(b.s16(PIC1 + PP_YOFFSET))
        self.assertNotEqual(s0, s1, "i due lottatori devono essere sfasati")
        self.assertEqual(len(b.voci_occupate()), 2)

    def test_H5_ampiezza_per_classe(self):
        amp = {}
        for cls in range(4):
            b = self.banco()
            b.accendi()
            b.prepara(od=OD0, pic=PIC0, cls=cls)
            serie = []
            for _ in range(72):
                b.nostro(od=OD0)
                serie.append(b.s16(PIC0 + PP_YOFFSET))
            amp[cls] = (max(serie) - min(serie)) // 2
        # l'atteso NON e' scritto a mano: viene dal manifesto della build, cosi'
        # il test non puo' dire una taratura diversa da quella compilata.
        atteso = self.b.man["tabelle_bin"]["par"]["amp"]
        self.assertEqual([amp[c] for c in range(4)], atteso)

    def test_G11_costo_in_istruzioni(self):
        """Criterio 8 di `10c` §4 e M7 della matrice: il sovrapprezzo per
        esecuzione rispetto al task vanilla. Scrive il numero in
        `prove/costo-v4.json` quando la cartella esiste."""
        import json as _json
        v = self.banco()
        v.prepara(od=OD0, pic=PIC0)
        van = [v.vanilla(od=OD0) for _ in range(36)]
        v2 = self.banco()
        v2.prepara(od=OD0, pic=PIC0)
        van_i = sum(v2.chiama(0x0226203C, r0=0x02320000, r1=OD0,
                              sorveglia=True)["istruzioni"] for _ in range(36)) / 36.0
        a = self.banco()
        a.accendi()
        a.prepara(od=OD0, pic=PIC0)
        acc = sum(a.nostro(od=OD0, sorveglia=True)["istruzioni"] for _ in range(36)) / 36.0
        s = self.banco()
        s.spegni()
        s.prepara(od=OD0, pic=PIC0)
        spe = sum(s.nostro(od=OD0, sorveglia=True)["istruzioni"] for _ in range(36)) / 36.0
        p = self.banco()
        p.accendi()
        p.prepara(od=OD0, pic=PIC0)
        for _ in range(4):
            p.nostro(od=OD0)
        pul = p.ferma(od=OD0, sorveglia=True)["istruzioni"]
        fuori = {"vanilla": round(van_i, 1), "v4_acceso": round(acc, 1),
                 "v4_spento": round(spe, 1),
                 "sovrapprezzo_acceso": round(acc - van_i, 1),
                 "sovrapprezzo_spento": round(spe - van_i, 1),
                 "pulizia_una_tantum": pul, "soglia_mandato": 250}
        prove = Path(os.environ.get("SGP_PROVE", QUI.parent / "prove"))
        if prove.exists():
            (prove / "costo-v4.json").write_text(_json.dumps(fuori, indent=2) + "\n")
        self.assertLessEqual(acc - van_i, 250,
                             "sovrapprezzo %.1f istruzioni > 250: %s" % (acc - van_i, fuori))
        self.assertLessEqual(spe - van_i, 40, str(fuori))
        self.assertTrue(van)


if __name__ == "__main__":
    unittest.main(verbosity=2)
