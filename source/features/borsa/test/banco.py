#!/usr/bin/env python3
"""SGP-1.2-BORSA-GEN-03 — banco Unicorn per `sgp.borsa`.

Il codice si ESEGUE, non si legge: si carica l'ARM9 **vero** di una ROM 1.2.1,
si scrive il nostro blob nella riserva a 0x023DAD00 insieme alla tabella
permissiva di prova, si fabbrica in memoria emulata un **membro di script vero**
(intestazione + bytecode) e un `ScriptContext` che ci punta dentro, e si parte
dal trampolino — cioe' dall'indirizzo che l'applicatore scrivera' in
`gScriptCmdTable[125]`/`[127]`.

Tre cose girano PER DAVVERO, e sono quelle su cui il disegno si gioca:

1. `ScriptReadHalfword` (0x0203FE2C), che e' pura aritmetica su `ctx->script_ptr`:
   cosi' la prova che il puntatore avanza di 6 byte esatti e' una misura, non
   una dichiarazione;
2. **gli originali** `ScrCmd_HasSpaceForItem` (0x0204EA89) e `ScrCmd_GiveItem`
   (0x0204E9D9): la via non permissiva non e' confrontata con un'imitazione
   del vanilla, e' il vanilla;
3. il membro di script, percio' `script_ptr - mapScripts` e l'impronta FNV sono
   calcolati sui byte, non forniti dal banco.

Le funzioni della Borsa e delle variabili non possono girare (vogliono heap,
NARC, salvataggio): ognuna e' intercettata da un hook che registra la chiamata
con i suoi argomenti, scrive il valore di ritorno che il caso di prova ha
deciso, e salta il corpo — la stessa impostazione di
`source/features/caramelle/test/banco.py`.

Modellato su `source/features/caramelle/test/banco.py`. GPL-3.0-or-later.
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

PAC = Path(__file__).resolve().parent.parent      # .../source/features/borsa
# Il blob spedito. `tools/mutanti.py` punta SGP_BORSA_BUILD su una copia mutata:
# e' l'unica differenza fra la corsa normale e quella dei mutanti.
REPO = PAC.parents[2]
BUILD = Path(os.environ.get(
    "SGP_BORSA_BUILD", REPO / "source" / "sgp12" / "build" / "borsa"))

RAM, RAM_N = 0x02000000, 0x00400000
PILA = 0x023B0000
FINE = 0x02390000          # indirizzo sentinella: emu_start si ferma qui

CTX = 0x02300000
FS = 0x02310000
SAVE = 0x02320000
BAG = 0x02330000
MEMBRO = 0x02340000        # il membro di script finto
VARS = 0x02350000          # area delle variabili (la rende GetVarPointer)
SLOTS = 0x02360000

# --- il blocco `sgp.borsa` (sorgenti/sgp_borsa.h) --------------------------
BLOCCO = 0x023DAD00
BLOCCO_N = 0x800
OFF_ORIG = 0x5E0
OFF_STAFFETTA = 0x5F0
OFF_TABELLA = 0x600
N_TABELLA = 120
OFF_CANARINO = 0x7F0
ST_ARMATA, ST_ITEM, ST_CHIESTE, ST_ENTRATE = 0x0, 0x2, 0x4, 0x6

CMD127 = BLOCCO + 0x000    # sgp_borsa_cmd127
CMD125 = BLOCCO + 0x008    # sgp_borsa_cmd125

# --- ScriptContext (pret include/script.h; RAPPORTO §3) -------------------
CTX_SCRIPT_PTR = 0x08
CTX_MAP_SCRIPTS = 0x7C
CTX_FIELD_SYSTEM = 0x80
FS_SAVEDATA = 0x0C

# --- indirizzi nativi, PARI ------------------------------------------------
VAN127 = 0x0204EA88
VAN125 = 0x0204E9D8
NATIVE = {
    0x020403AC: "ScriptGetVar",
    0x02040374: "GetVarPointer",
    0x0207879C: "Save_Bag_Get",
    0x02078240: "Bag_GetItemPocket",
    0x02078550: "Bag_GetItemQuantity",
    0x02078384: "Bag_HasSpaceForItem",
    0x02078398: "Bag_AddItem",
}

# Tasche (pret include/constants/items.h)
POCKET_ITEMS, POCKET_MEDICINE, POCKET_BALLS, POCKET_TMHMS = 0, 1, 2, 3
POCKET_BERRIES, POCKET_MAIL, POCKET_BATTLE_ITEMS, POCKET_KEY_ITEMS = 4, 5, 6, 7

CALLEE = {UC_ARM_REG_R4: 0xC4C4C4C4, UC_ARM_REG_R5: 0xC5C5C5C5,
          UC_ARM_REG_R6: 0xC6C6C6C6, UC_ARM_REG_R7: 0xC7C7C7C7,
          UC_ARM_REG_R8: 0xC8C8C8C8, UC_ARM_REG_R9: 0xC9C9C9C9,
          UC_ARM_REG_R10: 0xCACACACA, UC_ARM_REG_R11: 0xCBCBCBCB}

ROM_NOME = os.environ.get("SGP_BORSA_ROM_NOME", "sgp-1.2.1-%s.nds")
LINGUE = ("EN", "IT")


def rom_dir():
    valore = os.environ.get("SGP_ROM_DIR")
    return Path(valore) if valore else None


def rom_presenti():
    """Classe B: senza le ROM la suite SALTA con un motivo, non esplode."""
    d = rom_dir()
    return d is not None and all((d / (ROM_NOME % L)).is_file() for L in LINGUE)


def rom(lingua):
    return rom_dir() / (ROM_NOME % lingua)


def fnv16(dati):
    """FNV-1a a 32 bit troncato a 16, identico al `sgp_fnv` del blob. Qui e'
    riscritto in Python di proposito: se il C sbagliasse, il confronto fallirebbe
    invece di sbagliare insieme."""
    h = 0x811C9DC5
    for b in dati:
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h & 0xFFFF


def segmenti_arm9(path):
    """Segmenti (ram, bytes) dell'ARM9 di una .nds. Lettore proprio: il banco non
    dipende da `sgp12.rom`, cosi' una prova verde non puo' venire da un errore
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


class Membro:
    """Un membro di script finto ma ben formato: intestazione `u32 rel[1]`,
    sentinella 0xFD13, riempimento deterministico, e l'istruzione ganciata a un
    offset scelto. Serve perche' l'offset e l'impronta li calcoli il BLOB dai
    byte, non il banco."""

    def __init__(self, off, opcode, args, n=256, seme=0x5A):
        assert off + 8 <= n
        b = bytearray(((seme + 7 * i) & 0xFF) for i in range(n))
        struct.pack_into("<I", b, 0, 0x00000000)     # rel[0]
        struct.pack_into("<H", b, 4, 0xFD13)         # sentinella
        struct.pack_into("<H", b, off, opcode)
        for k, v in enumerate(args):
            struct.pack_into("<H", b, off + 2 + 2 * k, v)
        self.byte = bytes(b)
        self.off = off

    def chiave(self):
        """(offset << 16) | impronta, calcolata come la calcola il blob:
        finestra di al piu' 32 byte che TERMINA con l'istruzione (8 B)."""
        disp = self.off + 8
        n = min(32, disp)
        return ((self.off & 0xFFFF) << 16) | fnv16(self.byte[disp - n:disp])


class Banco:
    def __init__(self, rom_path, tabella=(), orig_da_blocco=True):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(RAM, RAM_N, UC_PROT_ALL)
        for ram, dati in segmenti_arm9(rom_path):
            if RAM <= ram and ram + len(dati) <= RAM + RAM_N:
                self.uc.mem_write(ram, dati)

        # il blocco: blob + puntatori agli originali + tabella + canarino
        blob = (BUILD / "blob.bin").read_bytes()
        can = (BUILD / "canarino.bin").read_bytes()
        self.uc.mem_write(BLOCCO, bytes(BLOCCO_N))
        self.uc.mem_write(BLOCCO, blob)
        self.uc.mem_write(BLOCCO + OFF_CANARINO, can)
        if orig_da_blocco:
            self.uc.mem_write(BLOCCO + OFF_ORIG,
                              struct.pack("<2I", VAN127 | 1, VAN125 | 1))
        self.scrivi_tabella(tabella)

        self.chiamate = []
        # risposte programmabili degli stub
        self.tasca = POCKET_ITEMS
        self.quantita = 0
        self.spazio = 1
        self.aggiunta = 1
        self.vars = {}
        for a in NATIVE:
            self.uc.hook_add(UC_HOOK_CODE, self._stub, begin=a, end=a)

    # -------------------------------------------------------------- blocco ---
    def scrivi_tabella(self, chiavi):
        chiavi = list(chiavi)
        assert len(chiavi) <= N_TABELLA
        dati = b"".join(struct.pack("<I", k) for k in chiavi)
        self.uc.mem_write(BLOCCO + OFF_TABELLA, bytes(N_TABELLA * 4))
        if dati:
            self.uc.mem_write(BLOCCO + OFF_TABELLA, dati)

    def staffetta(self):
        b = self.uc.mem_read(BLOCCO + OFF_STAFFETTA, 8)
        a, i, c, e = struct.unpack("<4H", bytes(b))
        return {"armata": a, "item": i, "chieste": c, "entrate": e}

    def arma(self, item, chieste, entrate=0):
        self.uc.mem_write(BLOCCO + OFF_STAFFETTA,
                          struct.pack("<4H", 1, item, chieste, entrate))

    def canarino_intatto(self):
        atteso = (BUILD / "canarino.bin").read_bytes()
        return bytes(self.uc.mem_read(BLOCCO + OFF_CANARINO, len(atteso))) == atteso

    # ---------------------------------------------------------------- stub ---
    def _stub(self, uc, address, size, _):
        nome = NATIVE[address]
        r = [uc.reg_read(x) for x in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                      UC_ARM_REG_R2, UC_ARM_REG_R3)]
        sp = uc.reg_read(UC_ARM_REG_SP)
        quinto = struct.unpack("<I", bytes(uc.mem_read(sp, 4)))[0]
        if nome == "ScriptGetVar":
            # un id < 0x4000 e' un letterale: il gioco lo rende tale e quale
            val = self.vars.get(r[1], r[1])
            uc.reg_write(UC_ARM_REG_R0, val & 0xFFFF)
            self.chiamate.append((nome, r[1], val, 0))
        elif nome == "GetVarPointer":
            p = VARS + (r[1] & 0x0FFF) * 2
            uc.reg_write(UC_ARM_REG_R0, p)
            self.chiamate.append((nome, r[1], p, 0))
        elif nome == "Save_Bag_Get":
            uc.reg_write(UC_ARM_REG_R0, BAG)
            self.chiamate.append((nome, r[0], 0, 0))
        elif nome == "Bag_GetItemPocket":
            uc.mem_write(r[2], struct.pack("<I", SLOTS))
            uc.mem_write(r[3], struct.pack("<I", 50))
            uc.reg_write(UC_ARM_REG_R0, self.tasca)
            self.chiamate.append((nome, r[0], r[1], quinto))
        elif nome == "Bag_GetItemQuantity":
            uc.reg_write(UC_ARM_REG_R0, self.quantita)
            self.chiamate.append((nome, r[0], r[1], r[2]))
        elif nome == "Bag_HasSpaceForItem":
            uc.reg_write(UC_ARM_REG_R0, self.spazio)
            self.chiamate.append((nome, r[0], r[1], r[2]))
        elif nome == "Bag_AddItem":
            uc.reg_write(UC_ARM_REG_R0, self.aggiunta)
            self.chiamate.append((nome, r[0], r[1], r[2]))
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    # --------------------------------------------------------------- stato ---
    def prepara(self, membro, fs_nullo=False):
        """Scrive il membro e il ScriptContext. `script_ptr` punta SUBITO DOPO
        l'opcode, come lo lascia `RunScriptCommand` (script.c:75)."""
        u = self.uc
        u.mem_write(MEMBRO, membro.byte)
        u.mem_write(VARS, bytes(0x2000))
        u.mem_write(CTX, bytes(0x90))
        u.mem_write(FS, bytes(0x20))
        u.mem_write(CTX + CTX_SCRIPT_PTR,
                    struct.pack("<I", MEMBRO + membro.off + 2))
        u.mem_write(CTX + CTX_MAP_SCRIPTS, struct.pack("<I", MEMBRO))
        u.mem_write(CTX + CTX_FIELD_SYSTEM,
                    struct.pack("<I", 0 if fs_nullo else FS))
        u.mem_write(FS + FS_SAVEDATA, struct.pack("<I", SAVE))
        self.membro = membro

    def var(self, vid):
        return struct.unpack("<H", bytes(self.uc.mem_read(
            VARS + (vid & 0x0FFF) * 2, 2)))[0]

    def scrivi_var(self, vid, valore):
        self.uc.mem_write(VARS + (vid & 0x0FFF) * 2, struct.pack("<H", valore))

    # ------------------------------------------------------------- esegui ---
    def esegui(self, quale):
        """Parte dal TRAMPOLINO — l'indirizzo che finira' in gScriptCmdTable —
        con `ctx` in r0, come fa `RunScriptCommand` (`ctx->cmdTable[cmd](ctx)`)."""
        u = self.uc
        self.chiamate = []
        sp = PILA - 64
        u.reg_write(UC_ARM_REG_SP, sp)
        u.reg_write(UC_ARM_REG_R0, CTX)
        for reg, val in CALLEE.items():
            u.reg_write(reg, val)
        for reg in (UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3):
            u.reg_write(reg, 0xDEADBEEF)
        u.reg_write(UC_ARM_REG_LR, FINE | 1)
        u.emu_start((CMD127 if quale == 127 else CMD125) | 1, FINE, count=200000)
        pc_dopo = struct.unpack("<I", bytes(
            u.mem_read(CTX + CTX_SCRIPT_PTR, 4)))[0]
        return {
            "reso": u.reg_read(UC_ARM_REG_R0),
            "avanzamento": pc_dopo - (MEMBRO + self.membro.off + 2),
            "chiamate": list(self.chiamate),
            "staffetta": self.staffetta(),
            "callee": {r: u.reg_read(r) for r in CALLEE},
            "sp": u.reg_read(UC_ARM_REG_SP),
            "canarino": self.canarino_intatto(),
        }

    def nomi(self, esito):
        return [c[0] for c in esito["chiamate"]]


def manifesto():
    return json.loads((BUILD / "manifesto.json").read_text())
