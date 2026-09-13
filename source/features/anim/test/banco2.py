#!/usr/bin/env python3
"""SGP-1.2-ANIM-B-01 FASE 1b — il banco esteso.

Come `banco.py` della fase 1: un ARM946E-S emulato con dentro il VERO ARM9 e
il VERO overlay 12 della base 1.1, e il blob compilato eseguito davvero.

In piu', e' il punto di questa fase: **si esegue anche il codice di disegno
del gioco**, non una sua parafrasi. Due frammenti rettilinei di
`PokepicManager_DrawAll` (ARM9, 1.1) vengono eseguiti dopo ogni passo del
task, con r4 = Pokepic:

  corpo   0x02008354..0x0200835E  (altezza scalata -> r6)
          0x0200838C..0x020083B2  (Y del corpo -> r1)
                Y = yCenter(+0x26) - altezza/2 + yOffset(+0x2E) - shadowH(+0x6E)

  ombra   0x0200841E..0x02008484  (dimensione dell'ombra -> r3,r1; X; Y)
                shadow.Y(+0x72) = shadow.yOffset(+0x76) + yCenter(+0x26)
                                  + yOffset(+0x2E)          [se bit3 di +0x6C]

L'ultimo passo del disegno dell'ombra (0x020084C4..0x020084EA) dereferenzia
una tabella di celle che qui non esiste; di quel tratto si trascrivono le
QUATTRO istruzioni che servono, ed e' dichiarato:
        r2 = r1 + (r1 >>> 31);  r2 >>= 1;  Ydisegno = s16[+0x72] - r2
cioe' meta' altezza dell'ombra, troncata verso lo zero.

Nessun byte di ROM viene stampato.
"""
import json
import os
from pathlib import Path

from unicorn import UC_HOOK_MEM_WRITE, UC_PROT_ALL, Uc, UC_ARCH_ARM, UC_MODE_THUMB
from unicorn.arm_const import (UC_ARM_REG_LR, UC_ARM_REG_R0, UC_ARM_REG_R1,
                               UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
                               UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
                               UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10,
                               UC_ARM_REG_R11, UC_ARM_REG_SP)

PKG = Path(__file__).resolve().parent.parent
MODULI = Path(os.environ.get("SGP_MODULI", PKG / "work" / "moduli-EN"))

RAM_BASE, RAM_LEN = 0x01F00000, 0x00A00000
OD0 = 0x02300000        # OpponentData sintetico, lottatore 0
OD1 = 0x02301000        # OpponentData sintetico, lottatore 1
PIC0 = 0x02310000
PIC1 = 0x02311000
TASK = 0x02320000
PILA = 0x02340000
SP0 = PILA + 0x8000
RITORNO = 0x023FFF00

OD_POKEPIC, OD_TASK, OD_DEGREES = 0x20, 0x198, 0x19C
PP_XCENTER, PP_YCENTER = 0x24, 0x26
PP_XOFFSET, PP_YOFFSET = 0x2C, 0x2E
PP_AFFINEW, PP_AFFINEH = 0x34, 0x36
PP_ANIMACTIVE, PP_WHICHANIM, PP_STEPDELAY, PP_ANIMSTEP = 0x58, 0x59, 0x5A, 0x5B
PP_LOOPTIMERS, PP_SCRIPT = 0x5C, 0x84
PP_SHADOW_FLAGS, PP_SHADOW_H = 0x6C, 0x6E
PP_SHADOW_X, PP_SHADOW_Y, PP_SHADOW_XOFF, PP_SHADOW_YOFF = 0x70, 0x72, 0x74, 0x76
PP_SIZE = 0xAC

VANILLA_TASK = 0x0226203D
SETATTR = 0x020087A5
START_ANIM = 0x02008551
RUN_ANIM = 0x02009161

# frammenti di PokepicManager_DrawAll, letti dal binario della 1.1
DRAW_H_DA, DRAW_H_A = 0x02008354, 0x0200835E      # altezza scalata -> r6
DRAW_CORPO_DA, DRAW_CORPO_A = 0x0200838C, 0x020083B2
DRAW_OMBRA_DA, DRAW_OMBRA_A = 0x0200841E, 0x02008484

# stato: gli offset del contratto di fase 1b
ST_FLAGS, ST_GUARD, ST_AMP, ST_RR = 0, 1, 2, 3
ST_HITS, ST_HITS_ON, ST_HITS_BUSY = 4, 8, 12
ST_LAST_Y, ST_LAST_STEP, ST_LAST_IDX = 16, 18, 19
ST_BLINKS, ST_RARI, ST_LAST_S76, ST_LAST_CLS, ST_LAST_SLOT = 20, 24, 28, 30, 31
SL_OD, SL_PIC, SL_RNG, SL_BASE76, SL_LAST76 = 0, 4, 8, 12, 14
SL_BLEFT, SL_BWAIT, SL_BCNT, SL_USATO = 16, 17, 18, 19
SL_SIZE = 32

REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]


def _s32(v):
    return v - 0x100000000 if v & 0x80000000 else v


class Banco2:
    def __init__(self, build, codice, tabelle, stato, slot):
        self.codice, self.tabelle, self.stato, self.slot = codice, tabelle, stato, slot
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(RAM_BASE, RAM_LEN, UC_PROT_ALL)
        mods = {m["modulo"]: m for m in json.loads((MODULI / "moduli.json").read_text())}
        for nome in ("arm9", "ov012"):
            m = mods[nome]
            self.uc.mem_write(m["ram"], (MODULI / (nome + ".bin")).read_bytes())
        b = Path(build)
        self.uc.mem_write(codice, (b / "blob2.bin").read_bytes())
        self.uc.mem_write(tabelle, (b / "tab_u.bin").read_bytes())
        self.uc.mem_write(tabelle + 0x20, (b / "par.bin").read_bytes())
        self.uc.mem_write(stato, bytes(64))
        self.uc.mem_write(slot, bytes(SL_SIZE * 4))
        self.uc.mem_write(RITORNO, b"\x00" * 4)
        self.scritture = []
        self._sorveglia = False
        self.istruzioni = 0
        self.uc.hook_add(UC_HOOK_MEM_WRITE, self._on_write)

    # -------------------------------------------------- memoria
    def _on_write(self, uc, access, address, size, value, user):
        if self._sorveglia:
            self.scritture.append((address, size, value))

    def rd(self, a, n):
        return bytes(self.uc.mem_read(a, n))

    def wr(self, a, b):
        self.uc.mem_write(a, bytes(b))

    def u8(self, a):
        return self.rd(a, 1)[0]

    def s16(self, a):
        v = int.from_bytes(self.rd(a, 2), "little")
        return v - 0x10000 if v & 0x8000 else v

    def u16(self, a):
        return int.from_bytes(self.rd(a, 2), "little")

    def u32(self, a):
        return int.from_bytes(self.rd(a, 4), "little")

    def wr16(self, a, v):
        self.uc.mem_write(a, int(v).to_bytes(2, "little", signed=True))

    # -------------------------------------------------- stato sintetico
    def prepara(self, od=OD0, pic=PIC0, degrees=180, animActive=0, anim_step=0,
                affine=0x100, ycentro=96, ombra_yoff=8, ombra_h=0,
                cls=1, adegua_y=True, scala_ombra=True, script=None):
        """Prepara un lottatore. `cls` finisce nei bit 5-6 di +0x6C (taglia
        dell'ombra, attributo 46), `adegua_y` nel bit 3 (DrawAll ricalcola la Y
        dell'ombra), `scala_ombra` nel bit 4 (la dimensione dell'ombra segue
        l'affine). I bit 0-1 restano a 0: sono il LATO del lottatore."""
        self.wr(od, bytes(0x1B0))
        self.wr(pic, bytes(PP_SIZE))
        self.uc.mem_write(od + OD_POKEPIC, int(pic).to_bytes(4, "little"))
        self.uc.mem_write(od + OD_TASK, TASK.to_bytes(4, "little"))
        self.uc.mem_write(od + OD_DEGREES, int(degrees).to_bytes(2, "little"))
        self.uc.mem_write(pic + PP_ANIMACTIVE, bytes([animActive]))
        self.uc.mem_write(pic + PP_ANIMSTEP, bytes([anim_step]))
        self.wr16(pic + PP_AFFINEW, affine)
        self.wr16(pic + PP_AFFINEH, affine)
        self.wr16(pic + PP_YCENTER, ycentro)
        self.wr16(pic + PP_XCENTER, 128)
        self.wr16(pic + PP_SHADOW_YOFF, ombra_yoff)
        self.uc.mem_write(pic + PP_SHADOW_H, int(ombra_h).to_bytes(1, "little", signed=True))
        flags = ((cls & 3) << 5) | 0x04 | (0x08 if adegua_y else 0) \
            | (0x10 if scala_ombra else 0)
        self.wr16(pic + PP_SHADOW_FLAGS, flags)
        if script is not None:
            self.uc.mem_write(pic + PP_SCRIPT, bytes(script) + bytes(40 - len(script)))

    def imposta_stato(self, flags=0, guard=0x5A, amp=3):
        s = bytearray(64)
        s[ST_FLAGS], s[ST_GUARD], s[ST_AMP] = flags, guard, amp
        self.wr(self.stato, s)
        self.wr(self.slot, bytes(SL_SIZE * 4))

    def voce(self, i):
        b = self.slot + i * SL_SIZE
        return {
            "od": self.u32(b + SL_OD), "pic": self.u32(b + SL_PIC),
            "rng": self.u32(b + SL_RNG), "base76": self.s16(b + SL_BASE76),
            "last76": self.s16(b + SL_LAST76), "blink_left": self.u8(b + SL_BLEFT),
            "blink_wait": self.u8(b + SL_BWAIT), "blink_cnt": self.u8(b + SL_BCNT),
            "usato": self.u8(b + SL_USATO),
        }

    def istantanea(self, pic=PIC0, od=OD0):
        """Tutto cio' che il gioco puo' vedere: il Pokepic e l'OpponentData."""
        return self.rd(pic, PP_SIZE) + self.rd(od, 0x1B0)

    # -------------------------------------------------- esecuzione
    def chiama(self, dove, fine=None, r0=0, r1=0, r2=0, r3=0, r4=None,
               sorveglia=False, limite=200000, pulisci=True):
        uc = self.uc
        canarini = [0xA0000000 + i for i in range(len(REGS))]
        if pulisci:
            for reg, v in zip(REGS, canarini):
                uc.reg_write(reg, v)
            uc.reg_write(UC_ARM_REG_R0, r0 & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R1, r1 & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R2, r2 & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_R3, r3 & 0xFFFFFFFF)
            uc.reg_write(UC_ARM_REG_SP, SP0)
            uc.reg_write(UC_ARM_REG_LR, RITORNO | 1)
        if r4 is not None:
            uc.reg_write(UC_ARM_REG_R4, r4 & 0xFFFFFFFF)
        self.scritture = []
        self._sorveglia = sorveglia
        self.istruzioni = 0
        if sorveglia:
            from unicorn import UC_HOOK_CODE
            h = uc.hook_add(UC_HOOK_CODE, self._conta)
        uc.emu_start(dove | 1, RITORNO if fine is None else fine, count=limite)
        if sorveglia:
            uc.hook_del(h)
        self._sorveglia = False
        fuori = {}
        for reg, v, nome in zip(REGS, canarini, [f"r{i}" for i in range(12)]):
            if pulisci and int(nome[1:]) >= 4 and uc.reg_read(reg) != v:
                fuori[nome] = uc.reg_read(reg)
        return {"r0": uc.reg_read(UC_ARM_REG_R0), "r1": uc.reg_read(UC_ARM_REG_R1),
                "r3": uc.reg_read(UC_ARM_REG_R3), "r6": uc.reg_read(UC_ARM_REG_R6),
                "sp": uc.reg_read(UC_ARM_REG_SP),
                "callee_saved_corrotti": fuori, "istruzioni": self.istruzioni}

    def _conta(self, uc, address, size, user):
        self.istruzioni += 1

    # -------------------------------------------------- API del gioco
    def vanilla(self, od=OD0):
        return self.chiama(VANILLA_TASK, r0=TASK, r1=od)

    def nostro(self, od=OD0, **kw):
        return self.chiama(self.codice, r0=TASK, r1=od, **kw)

    def start_anim(self, pic=PIC0):
        return self.chiama(START_ANIM, r0=pic)

    def run_anim(self, pic=PIC0):
        return self.chiama(RUN_ANIM, r0=pic)

    # -------------------------------------------------- il DISEGNO, vero
    def y_corpo(self, pic=PIC0):
        """Esegue i due frammenti di DrawAll che calcolano la Y del corpo."""
        self.uc.reg_write(UC_ARM_REG_SP, SP0)
        self.uc.reg_write(UC_ARM_REG_LR, RITORNO | 1)
        self.uc.reg_write(UC_ARM_REG_R4, pic)
        self.uc.emu_start(DRAW_H_DA | 1, DRAW_H_A, count=64)
        self.uc.emu_start(DRAW_CORPO_DA | 1, DRAW_CORPO_A, count=64)
        return _s32(self.uc.reg_read(UC_ARM_REG_R1))

    def y_ombra(self, pic=PIC0):
        """Esegue il frammento di DrawAll che ricalcola shadow.Y (+0x72) e
        restituisce (Y registrata, Y del disegno, altezza dell'ombra)."""
        self.uc.reg_write(UC_ARM_REG_SP, SP0)
        self.uc.reg_write(UC_ARM_REG_LR, RITORNO | 1)
        self.uc.reg_write(UC_ARM_REG_R4, pic)
        self.uc.emu_start(DRAW_OMBRA_DA | 1, DRAW_OMBRA_A, count=256)
        h = _s32(self.uc.reg_read(UC_ARM_REG_R1))   # altezza dell'ombra
        y72 = self.s16(pic + PP_SHADOW_Y)
        # 0x020084E4..0x020084EA, trascritte: meta' troncata verso lo zero
        meta = int(h / 2) if h >= 0 else -int(-h / 2)
        return y72, y72 - meta, h
