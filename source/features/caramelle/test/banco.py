#!/usr/bin/env python3
"""SGP-1.2-CARAMELLE-01 — banco Unicorn.

Il codice si ESEGUE, non si legge: si carica l'ARM9 **vero** della ROM patchata
(tutti i suoi segmenti, statico e autoload), si costruiscono un `PartyMenu` e un
`PartyMenuArgs` finti in RAM, e si parte dal **sito del gancio** 0x02081E96, non
dal blob: così la prova copre anche la codifica della `BL` e il `pop` che la
segue, cioè proprio i 6 byte che l'applicatore scrive.

Le funzioni del gioco non possono girare (vogliono heap, VRAM, printer): ognuna
è intercettata da un hook che registra la chiamata con i suoi argomenti, scrive
il valore di ritorno che il caso di prova ha deciso, e salta il corpo. È la
stessa impostazione di `source/features/options/test/banco.py`.

Modellato su `source/features/options/test/banco.py` e
`source/features/native-core/test/banco.py`. GPL-3.0-or-later.
"""
import json
import os
import struct
from pathlib import Path

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_PROT_ALL
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4,
    UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
    UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

PAC = Path(__file__).resolve().parent.parent          # source/features/caramelle
# Il blob SPEDITO. `tools/mutanti.py` punta SGP_CAR_BUILD su una copia mutata:
# e' l'unica differenza fra la corsa normale e quella dei mutanti.
BUILD = Path(os.environ.get("SGP_CAR_BUILD",
                            PAC.parents[1] / "sgp12" / "build" / "caramelle"))

RAM, RAM_N = 0x02000000, 0x00400000
PILA = 0x023B0000
FINE = 0x02390000          # indirizzo sentinella: emu_start si ferma qui

PM = 0x02300000            # PartyMenu finto  (0xCA8 B)
ARGS = 0x02320000          # PartyMenuArgs finto
BAG = 0x02330000
PARTY = 0x02340000
SPRITE = 0x02350000

GANCIO = 0x02081E96
BLOCCO = 0x023DAC00

# Offset (pret include/party_menu.h, tutti riverificati sui byte: RAPPORTO §3)
PM_ARGS = 0x654
PM_WIN34 = 0x224
PM_SPR_CURSOR = 0x678
PM_SLOT = 0xC65
A_PARTY, A_BAG, A_CONTEXT, A_ACTION = 0x00, 0x04, 0x24, 0x27
A_ITEMID, A_SEARCH, A_SPECIES = 0x28, 0x38, 0x3C

# Le sei funzioni native, indirizzi PARI.
NATIVE = {
    0x02078550: "Bag_GetItemQuantity",
    0x0207463C: "Party_GetCount",
    0x02074640: "Party_GetCapacity",
    0x0200E9BC: "ClearFrameAndWindow2",
    0x0207DAC4: "PartyMenu_PrintMessageOnWindow32",
    0x0200DD08: "thunk_Sprite_SetPaletteOverride",
}

CALLEE = {UC_ARM_REG_R4: 0xC4C4C4C4, UC_ARM_REG_R5: 0xC5C5C5C5,
          UC_ARM_REG_R6: 0xC6C6C6C6, UC_ARM_REG_R7: 0xC7C7C7C7,
          UC_ARM_REG_R8: 0xC8C8C8C8, UC_ARM_REG_R9: 0xC9C9C9C9,
          UC_ARM_REG_R10: 0xCACACACA, UC_ARM_REG_R11: 0xCBCBCBCB}


# Nome della ROM dentro $SGP_ROM_DIR. Di norma e' la ROM SPEDITA, che il blocco
# `sgp12/blocchi/caramelle.py` ha gia' patchato: cosi' la suite gira sui byte
# che il giocatore riceve, non su una copia di comodo. `tools/mutanti.py`, che
# deve costruirsi le proprie ROM con un blob guasto, lo cambia con
# SGP_CAR_ROM_NOME (un modello con un solo `%s`, la lingua).
ROM_NOME = os.environ.get("SGP_CAR_ROM_NOME", "sgp-1.2.1-%s.nds")


def rom_dir():
    d = os.environ.get("SGP_ROM_DIR")
    if not d:
        raise RuntimeError("SGP_ROM_DIR non impostata: serve la cartella con le "
                           "ROM " + ROM_NOME % "{EN,IT}")
    return Path(d)


def rom_presenti():
    """Classe B: senza le ROM la suite SALTA con un motivo, non esplode."""
    d = os.environ.get("SGP_ROM_DIR")
    if not d:
        return False
    return all((Path(d) / (ROM_NOME % L)).is_file() for L in ("EN", "IT"))


def segmenti_arm9(path):
    """Segmenti (ram, bytes) dell'ARM9 di una .nds. Lettore proprio: il banco
    non dipende da sgp12.rom, così una prova verde non può venire da un bug
    condiviso col laboratorio."""
    d = Path(path).read_bytes()
    o9 = struct.unpack_from("<I", d, 0x20)[0]
    r9 = struct.unpack_from("<I", d, 0x28)[0]
    t0, t1, d0 = struct.unpack_from("<3I", d, o9 + 0xBA0)
    fuori = [(r9, d[o9:o9 + (d0 - r9)])]
    p = o9 + (t0 - r9)
    fine = o9 + (t1 - r9)
    o = o9 + (d0 - r9)
    while p < fine:
        ram, n, _bss = struct.unpack_from("<3I", d, p)
        fuori.append((ram, d[o:o + n]))
        o += n
        p += 12
    return fuori


class Banco:
    def __init__(self, rom):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(RAM, RAM_N, UC_PROT_ALL)
        for ram, dati in segmenti_arm9(rom):
            if RAM <= ram and ram + len(dati) <= RAM + RAM_N:
                self.uc.mem_write(ram, dati)
        self.chiamate = []
        # risposte programmabili degli stub
        self.quantita = 1
        self.conteggio = 6
        self.capienza = 6
        for a in NATIVE:
            self.uc.hook_add(UC_HOOK_CODE, self._stub, begin=a, end=a)

    # ------------------------------------------------------------- stub ---
    def _stub(self, uc, address, size, _):
        nome = NATIVE[address]
        r = [uc.reg_read(x) for x in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                      UC_ARM_REG_R2, UC_ARM_REG_R3)]
        self.chiamate.append((nome, r[0], r[1], r[2]))
        if nome == "Bag_GetItemQuantity":
            uc.reg_write(UC_ARM_REG_R0, self.quantita)
        elif nome == "Party_GetCount":
            uc.reg_write(UC_ARM_REG_R0, self.conteggio)
        elif nome == "Party_GetCapacity":
            uc.reg_write(UC_ARM_REG_R0, self.capienza)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    # ------------------------------------------------------------ stato ---
    def prepara(self, species=0, item=50, context=5, slot=0, azione=0xEE,
                search=0x7777, args_nullo=False, pm_nullo=False):
        u = self.uc
        u.mem_write(PM, bytes(0xD00))
        u.mem_write(ARGS, bytes(0x50))
        u.mem_write(PM + PM_ARGS, struct.pack("<I", 0 if args_nullo else ARGS))
        u.mem_write(PM + PM_SPR_CURSOR, struct.pack("<I", SPRITE))
        u.mem_write(PM + PM_SLOT, bytes([slot]))
        u.mem_write(ARGS + A_PARTY, struct.pack("<I", PARTY))
        u.mem_write(ARGS + A_BAG, struct.pack("<I", BAG))
        u.mem_write(ARGS + A_CONTEXT, bytes([context]))
        u.mem_write(ARGS + A_ACTION, bytes([azione]))
        u.mem_write(ARGS + A_ITEMID, struct.pack("<H", item))
        u.mem_write(ARGS + A_SEARCH, struct.pack("<I", search))
        u.mem_write(ARGS + A_SPECIES, struct.pack("<H", species))
        self.args_nullo = args_nullo
        self.pm_nullo = pm_nullo
        self.species = species

    def esegui(self):
        """Parte dal SITO del gancio, con i registri che il gioco ha davvero
        in quel punto: r0 = args->species, r1 = args, r4 = PartyMenu. La pila
        porta le quattro parole che `pop {r3,r4,r5,pc}` consumerà."""
        u = self.uc
        self.chiamate = []
        sp = PILA - 16
        u.mem_write(sp, struct.pack("<4I", 0x33333333, 0xC4C4C4C4,
                                    0xC5C5C5C5, FINE | 1))
        u.reg_write(UC_ARM_REG_SP, sp)
        u.reg_write(UC_ARM_REG_R0, self.species)
        u.reg_write(UC_ARM_REG_R1, 0 if self.args_nullo else ARGS)
        u.reg_write(UC_ARM_REG_R2, 0xDEADBEEF)
        u.reg_write(UC_ARM_REG_R3, 0xDEADBEEF)
        for reg, val in CALLEE.items():
            u.reg_write(reg, val)
        u.reg_write(UC_ARM_REG_R4, 0 if self.pm_nullo else PM)
        u.reg_write(UC_ARM_REG_LR, 0xFFFFFFFF)
        u.emu_start(GANCIO | 1, FINE, count=20000)
        return {
            "stato": u.reg_read(UC_ARM_REG_R0),
            "azione": u.mem_read(ARGS + A_ACTION, 1)[0],
            "search": struct.unpack("<I", u.mem_read(ARGS + A_SEARCH, 4))[0],
            "chiamate": list(self.chiamate),
            "callee": {r: u.reg_read(r) for r in CALLEE},
            "sp": u.reg_read(UC_ARM_REG_SP),
        }


    def esegui_blob(self):
        """Come `esegui`, ma entra direttamente in `sgp_caramelle_gancio` e
        torna a `lr`: serve per guardare i registri callee-saved COME LI LASCIA
        il nostro codice. Passando dal sito, il `pop {r3,r4,r5,pc}` del gioco
        li rimetterebbe a posto dalla propria pila e la prova non proverebbe
        niente."""
        u = self.uc
        self.chiamate = []
        u.reg_write(UC_ARM_REG_SP, PILA - 64)
        u.reg_write(UC_ARM_REG_R0, self.species)
        u.reg_write(UC_ARM_REG_R1, 0 if self.args_nullo else ARGS)
        u.reg_write(UC_ARM_REG_R2, 0xDEADBEEF)
        u.reg_write(UC_ARM_REG_R3, 0xDEADBEEF)
        for reg, val in CALLEE.items():
            u.reg_write(reg, val)
        u.reg_write(UC_ARM_REG_R4, 0 if self.pm_nullo else PM)
        u.reg_write(UC_ARM_REG_LR, FINE | 1)
        u.emu_start(BLOCCO | 1, FINE, count=20000)
        callee = {r: u.reg_read(r) for r in CALLEE}
        callee[UC_ARM_REG_R4] = u.reg_read(UC_ARM_REG_R4)
        return {
            "stato": u.reg_read(UC_ARM_REG_R0),
            "azione": u.mem_read(ARGS + A_ACTION, 1)[0],
            "callee": callee,
            "r4": u.reg_read(UC_ARM_REG_R4),
            "sp": u.reg_read(UC_ARM_REG_SP),
            "chiamate": list(self.chiamate),
        }


def manifesto():
    return json.loads((BUILD / "manifesto.json").read_text())
