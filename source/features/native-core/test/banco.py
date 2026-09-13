#!/usr/bin/env python3
"""Banco Unicorn condiviso: un ARM946E-S con la riserva 1.2, una pila, un'area
dati e gli stub delle funzioni del gioco chiamate dai blob.

I blob si ESEGUONO. Nessun test di questo pacchetto legge il sorgente C per
dedurre un comportamento: si carica il codice macchina (quello estratto dalla ROM
o quello appena compilato) e lo si fa girare.
"""
import struct

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_PROT_ALL, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
    UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_PC, UC_ARM_REG_CPSR)

REG = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
       UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7]

RISERVA, RISERVA_N = 0x023D0000, 0x00010000
ARM9, ARM9_N = 0x02000000, 0x001E0000          # arm9 statico: stub delle funzioni
OV, OV_N = 0x021E0000, 0x00040000              # copia RAM degli overlay
DATI, DATI_N = 0x02300000, 0x00020000
PILA, PILA_N = 0x02700000, 0x00010000
RITORNO = 0x023DFFF0
SP0 = PILA + 0x8000

# funzioni del gioco (sgp_salva.h / wifi_slot4.h), indirizzi PARI
WRITE_BACKUP = 0x02028758
READ_BACKUP = 0x0202877C
CRC16 = 0x0201FF98
ORIG_LOAD = 0x020277D4
ORIG_SAVE = 0x02027DB4
DC_FLUSH = 0x020D2894
IC_INVAL = 0x020D28D0


def crc16_ccitt(data):
    """MATH_CalcCRC16CCITT della NitroSDK: tabella riflessa, seme 0xFFFF."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return crc & 0xFFFF


class Banco:
    def __init__(self):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        for base, ln in ((RISERVA, RISERVA_N), (ARM9, ARM9_N), (OV, OV_N),
                         (DATI, DATI_N), (PILA, PILA_N)):
            self.uc.mem_map(base, ln, UC_PROT_ALL)
        self.uc.mem_write(RITORNO, b"\x70\x47")          # bx lr
        self.settori = {}          # offset -> 32 byte
        self.lettura_ok = True
        self.scrittura_ok = True
        self.chiamate = []         # traccia degli stub chiamati
        self.orig_load_ret = 0
        self.orig_save_ret = 2
        # stub ARM «bx lr» per DC_FlushRange / IC_InvalidateRange
        for a in (DC_FLUSH, IC_INVAL):
            self.uc.mem_write(a, struct.pack("<I", 0xE12FFF1E))
        # stub Thumb: il gancio Python li intercetta prima di eseguirli
        for a in (WRITE_BACKUP, READ_BACKUP, CRC16, ORIG_LOAD, ORIG_SAVE):
            self.uc.mem_write(a, b"\x70\x47")
        self.uc.hook_add(UC_HOOK_CODE, self._stub)

    # ---------------------------------------------------------------- stub
    def _stub(self, uc, address, size, _):
        a = address & ~1
        if a in (DC_FLUSH, IC_INVAL):
            self.chiamate.append((a, uc.reg_read(UC_ARM_REG_R0),
                                  uc.reg_read(UC_ARM_REG_R1)))
            return
        if a not in (WRITE_BACKUP, READ_BACKUP, CRC16, ORIG_LOAD, ORIG_SAVE):
            return
        r0, r1, r2 = (uc.reg_read(r) for r in REG[:3])
        self.chiamate.append((a, r0, r1))
        if a == CRC16:
            uc.reg_write(UC_ARM_REG_R0, crc16_ccitt(bytes(uc.mem_read(r0, r1))))
        elif a == READ_BACKUP:
            if self.lettura_ok:
                uc.mem_write(r1, self.settori.get(r0, b"\xFF" * r2)[:r2])
            uc.reg_write(UC_ARM_REG_R0, 0 if self.lettura_ok else 1)
        elif a == WRITE_BACKUP:
            if self.scrittura_ok:
                self.settori[r0] = bytes(uc.mem_read(r1, r2))
            uc.reg_write(UC_ARM_REG_R0, 0 if self.scrittura_ok else 1)
        elif a == ORIG_LOAD:
            uc.reg_write(UC_ARM_REG_R0, self.orig_load_ret)
        else:
            uc.reg_write(UC_ARM_REG_R0, self.orig_save_ret)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    # ------------------------------------------------------------ servizi
    def carica(self, indirizzo, byte):
        self.uc.mem_write(indirizzo, bytes(byte))

    def leggi(self, indirizzo, n):
        return bytes(self.uc.mem_read(indirizzo, n))

    def scrivi(self, indirizzo, byte):
        self.uc.mem_write(indirizzo, bytes(byte))

    def chiama(self, entrata, argomenti=(), canarini=None, sp=SP0):
        """Esegue una funzione Thumb. `entrata` ha già il bit 0 acceso.
        Ritorna (r0, registri r0..r7 all'uscita)."""
        uc = self.uc
        vals = list(canarini) if canarini else [0] * 8
        for i, v in enumerate(argomenti):
            vals[i] = v
        for r, v in zip(REG, vals):
            uc.reg_write(r, v & 0xFFFFFFFF)
        uc.reg_write(UC_ARM_REG_SP, sp)
        uc.reg_write(UC_ARM_REG_LR, RITORNO | 1)
        uc.reg_write(UC_ARM_REG_CPSR, uc.reg_read(UC_ARM_REG_CPSR) | (1 << 5))
        self.chiamate = []
        uc.emu_start(entrata | 1, RITORNO, count=2_000_000)
        fuori = [uc.reg_read(r) for r in REG]
        return fuori[0], fuori
