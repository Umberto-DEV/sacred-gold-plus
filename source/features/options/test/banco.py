#!/usr/bin/env python3
"""SGP-1.2-OPZIONI-03 — banco di prova: esegue il blob su un ARM946E-S emulato.

Non si legge il codice: lo si **esegue**. Le funzioni del gioco non esistono qui,
quindi ogni indirizzo del gioco e' intercettato da un hook che registra la
chiamata (pc, r0..r3 e i primi 4 argomenti sulla pila) e salta il corpo tornando
a `lr`. Cosi' la macchina a stati e' provata per davvero, e ogni disegno diventa
una traccia confrontabile.

E' la stessa impostazione di `SGP-1.2-PLUS-01/test/test_blob.py`, con in piu' la
tabella delle chiamate: qui l'esito da provare non e' un numero, e' una sequenza.
"""
import atexit
import hashlib
import json
import os
import shutil
import struct
import tempfile
from pathlib import Path

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_PROT_ALL)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_SP,
                               UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_CPSR)

PAC = Path(__file__).resolve().parent.parent
# La cartella di costruzione e' scambiabile: i mutanti ne producono una
# propria e riusano ESATTAMENTE questa suite, senza copiarne una riga.
# M8 della revisione R2: il default era `options/work/build`, una cartella di
# cantiere che non esiste in questo repository — cosi' le cinque suite della
# pagina Opzioni davano 76 errori e non esercitavano nulla. Il default e' ora
# il blob SPEDITO, `source/sgp12/build/opzioni/`, che porta `ui_blob.bin`,
# `manifesto.json`, `testi-{EN,IT}.bin` e `voci-{EN,IT}.bin`. `run_tests.py`
# continua a passare `SGP_UI_BUILD` con il blob appena ricompilato, che e' il
# confronto piu' stretto quando un compilatore ARM c'e'.
def _build_predefinita():
    """Mette insieme il blob spedito (`sgp12/build/opzioni/ui_blob.bin` +
    `manifesto.json`) e i testi in forma GREZZA (`options/prove/testi/`), che e'
    la stessa coppia che `run_tests.py` prepara quando un compilatore ARM c'e'.
    I `testi-*.bin`/`voci-*.bin` sotto `sgp12/build/` sono gli stessi contenuti
    riempiti di zeri fino alla misura dello scomparto in ROM: qui servono
    grezzi, perche' i test ne contano le voci."""
    tmp = Path(tempfile.mkdtemp(prefix="sgp-ui-build-"))
    atexit.register(shutil.rmtree, tmp, True)
    for f in ("ui_blob.bin", "manifesto.json"):
        shutil.copy2(PAC.parents[1] / "sgp12/build/opzioni" / f, tmp / f)
    for f in sorted((PAC / "prove/testi").iterdir()):
        if f.is_file():
            shutil.copy2(f, tmp / f.name)
    return tmp


BUILD = Path(os.environ["SGP_UI_BUILD"]) if os.environ.get("SGP_UI_BUILD") else _build_predefinita()

BASE_RAM, DIM_RAM = 0x02000000, 0x00400000
SP0 = 0x023B0000

IND = json.loads((BUILD / "manifesto.json").read_text())["indirizzi"] \
    if (BUILD / "manifesto.json").is_file() else {}
IND = {k: int(v, 16) for k, v in IND.items()}
GSYS = 0x021D110C
NEWKEYS = GSYS + 0x48
TOUCHX = GSYS + 0x60            # v3: struct System, include/system.h di pret
TOUCHY = GSYS + 0x62
TOUCHNEW = GSYS + 0x64

# finta app Opzioni: heapID, unk10, bgConfig, 5 Window
APP = 0x02200000
BGCONFIG = 0x02201000
FINTO_PIXEL = 0x02210000        # cio' che AddWindowParameterized "alloca"
FINTA_STRINGA = 0x02220000
# v5 (19/09/2026): il BgConfig finto ha una TILEMAP vera per il layer MAIN_1,
# 32x32 celle u16 (2 KiB, layer testo 256x256 come i cinque dell'app Opzioni),
# e gli stub di CopyWindowToVram / ClearWindowTilemapAndCopyToVram /
# BgClearTilemapCommit / FillBgTilemapRect la scrivono come fa il gioco
# (`PutWindowTilemap_TextMode`: cella = tile | palette << 12). Pianta di
# BgConfig letta dal disassemblato di AddWindowParameterized (0x0201D40C):
# heapID u32 + due u16 = 8 B, poi Background[8] da 0x2C B con `tilemapBuffer`
# a +0 (`muls r7, #0x2c` ... `ldr r0, [r1, #8]`). E' la verita' di terreno che
# la pagina interroga per sapere se il suggerimento e' a schermo: senza questa
# tilemap il banco non poteva riprodurre il difetto del rientro nel menu.
TILEMAP1 = 0x02240000
TILEMAP_BYTE = 0x800
BG_OFF_BGS, BG_STRIDE = 8, 0x2C
CELLE_RIGA = 32

FUNZIONI = {
    0x0201D40C: "AddWindowParameterized", 0x0201D520: "RemoveWindow",
    0x0201D578: "CopyWindowToVram", 0x0201D8C8: "ClearWindowTilemapAndCopyToVram",
    0x0201D978: "FillWindowPixelBuffer", 0x020200FC: "AddTextPrinterWithColor",
    0x02002F30: "FontID_String_GetWidth", 0x02026354: "String_New",
    0x02026380: "String_Delete", 0x0201BC28: "ToggleBgLayer",
    0x0201A9C4: "Heap_Destroy", 0x02000EF4: "RegisterMainOverlay",
    0x0200604C: "PlaySE", 0x021E69D4: "OPZ_EVIDENZIA",
    0x0201A910: "Heap_Create", 0x02022BE8: "GfGfx_SetBanks",
    0x0201ACB0: "SetScreenModesDisable", 0x0201AC88: "BgConfig_Alloc",
    0x0201B1E4: "InitBgFromTemplate", 0x0201CAE0: "BgClearTilemapCommit",
    0x0201BB4C: "FreeBgTilemapBuffer", 0x0201C1C4: "BG_ClearCharDataRange",
    0x02003030: "LoadFontPal0", 0x0200FA24: "PaletteFadeBegin",
    0x0200FB5C: "PaletteFadeFinished", 0x0200FBF4: "SchermoNero",
    0x0200E644: "LoadUserFrameGfx2", 0x0200E998: "DrawFrameAndWindow2",
    0x0200E9BC: "ClearFrameAndWindow2", 0x0201CAE0: "BgClearTilemapCommit",
    0x02022C60: "TogglePianiA", 0x0201C8C4: "FillBgTilemapRect",
}

# Guardie degli altri cantieri: la pagina e' un consumatore e ogni voce si
# accende solo se il suo proprietario ha scritto la propria guardia.
G_D1, G_ANIM, G_NPC, G_WIFI = 0, 2, 3, 4

CANARINI = {UC_ARM_REG_R4: 0xC4C4C4C4, UC_ARM_REG_R5: 0xC5C5C5C5,
            UC_ARM_REG_R6: 0xC6C6C6C6, UC_ARM_REG_R7: 0xC7C7C7C7}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def simboli():
    return json.loads((BUILD / "manifesto.json").read_text())["simboli"]


def indirizzo(nome):
    return int(simboli()[nome], 16)


class Banco:
    """Una macchina con il blob caricato e le funzioni del gioco intercettate."""

    def __init__(self, palette_finita=True):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(BASE_RAM, DIM_RAM, UC_PROT_ALL)
        self.chiamate = []
        self.palette_finita = palette_finita

        blob = (BUILD / "ui_blob.bin").read_bytes()
        self.uc.mem_write(IND["codice"], blob)
        for lingua in ("IT",):
            self.uc.mem_write(IND["testi"], (BUILD / f"testi-{lingua}.bin").read_bytes())
            self.uc.mem_write(IND["tab"], (BUILD / f"voci-{lingua}.bin").read_bytes())
        self.uc.mem_write(IND["ris"], bytes(96))

        # BgConfig finto: heapID 38 e la tilemap del layer MAIN_1 (gli altri
        # layer restano senza: come nel gioco, AddWindowParameterized su un
        # layer senza tilemap non fa nulla).
        self.uc.mem_write(BGCONFIG, struct.pack("<I", 38))
        self.uc.mem_write(BGCONFIG + BG_OFF_BGS + BG_STRIDE * 1,
                          struct.pack("<I", TILEMAP1))
        self.uc.mem_write(TILEMAP1, bytes(TILEMAP_BYTE))

        # finta app: heapID 38, unk10 con cursore 0, bgConfig, 5 Window "in uso"
        self.uc.mem_write(APP, struct.pack("<I", 38))
        self.uc.mem_write(APP + 0x10, struct.pack("<I", 0))
        self.uc.mem_write(APP + 0x14, struct.pack("<I", BGCONFIG))
        for i in range(5):
            self.uc.mem_write(APP + 0x34 + 16 * i,
                              struct.pack("<IBBBBBBHI", BGCONFIG, 1, 1, 0, 12, 3, 13,
                                          0x00A, 0x02230000 + 0x1000 * i))

        # stato D1: guard 0x5A, cap 100, load_status 1 (chunk assente), tutto spento
        self.stato_d1(guard=0x5A, cap=100, load=1, plus=0, wild=0)
        self.uc.mem_write(IND["stato"], bytes(96))
        # Gli stati altrui partono AZZERATI: e' la condizione reale di una ROM
        # dove quei cantieri non sono ancora stati applicati.
        for k in ("stato_npc", "stato_anim", "stato_wifi"):
            self.uc.mem_write(IND[k], bytes(32))

        for a in FUNZIONI:
            self.uc.hook_add(UC_HOOK_CODE, self._stub, begin=a & ~1, end=a & ~1)

    # --- stato -----------------------------------------------------------
    def stato_d1(self, guard=0x5A, cap=100, load=1, plus=0, wild=0, peak=1,
                 anim=0, npc=0, wifi=0, versione=2, magic=0x5347):
        """Stato D1 (32 B) + copia in RAM del chunk pubblico a +0x10.
        CONTRATTO-CHUNK §1-§2: magic u16, versione, plus, selvatici, oltre100,
        anim, npc, wifi_server, picco."""
        b = struct.pack("<BBBBBBBBII", plus, wild, cap, load, guard, 0, 0, 0, 0, 0)
        b += struct.pack("<HBBBBBBBB", magic, versione, plus, wild, 0,
                         anim, npc, wifi, peak)
        b += bytes(6)
        self.uc.mem_write(IND["stato_d1"], b[:32])

    def leggi_d1(self):
        b = self.uc.mem_read(IND["stato_d1"], 32)
        (ap, aw, cap, load, guard) = struct.unpack_from("<5B", b, 0)
        (magic, ver, plus, selv, oltre, anim, npc, wifi, peak) = \
            struct.unpack_from("<HBBBBBBBB", b, 16)
        return {"active_plus": ap, "active_wild": aw, "cap": cap,
                "load_status": load, "guard": guard, "magic": magic,
                "versione": ver, "plus": plus, "selvatici": selv,
                "oltre100": oltre, "anim": anim, "npc": npc,
                "wifi_server": wifi, "picco": peak}

    # --- stati degli altri cantieri (P2, A1-B, W1) -----------------------
    def stato_npc(self, attivo=0, guardia=0x5A, tetto=4):
        """sgp.npc: guardia a +2 (CONTRATTO-P2 §3). Il flag vero e' `npc` nel
        chunk; qui serve solo a dire che il cantiere e' nella ROM."""
        self.uc.mem_write(IND["stato_npc"],
                          struct.pack("<BBBB", attivo, tetto, guardia, 0))

    def stato_anim(self, flags=0, guardia=0x5A):
        """sgp.anim: flags a +0, guard a +1 (CONTRATTO-A1B §4.1)."""
        self.uc.mem_write(IND["stato_anim"], struct.pack("<BB", flags, guardia))

    def stato_wifi(self, magic=0x57, versione=1, modo=0, slot_gts=0, slot_dono=0,
                   flag=0):
        """SgpW1Stato, 16 B (CONTRATTO-W1 §4.2): magic 'W' a +0, versione +1,
        modo +2, slot_gts +3, slot_dono +4, flag +5."""
        self.uc.mem_write(IND["stato_wifi"],
                          struct.pack("<6B", magic, versione, modo, slot_gts,
                                      slot_dono, flag))

    def leggi_wifi(self):
        """Il blocco W1 non viene piu' SCRITTO dalla pagina: il valore sta nel
        chunk (`wifi_server`) e W1 lo legge da li'. Qui resta solo la guardia."""
        b = self.uc.mem_read(IND["stato_wifi"], 6)
        return {"magic": b[0], "modo": b[2], "slot_gts": b[3]}

    def leggi_ui(self):
        b = self.uc.mem_read(IND["stato"], 96)
        (ap, cur, nvis, gu) = struct.unpack_from("<4B", b, 0)
        vis = list(struct.unpack_from("<6B", b, 4))
        val = list(struct.unpack_from("<6B", b, 0x0A))
        val0 = list(struct.unpack_from("<6B", b, 0x10))
        (sugg, ycont, altezza, nrighe) = struct.unpack_from("<4B", b, 0x16)
        (aperture, eventi, salv, esito) = struct.unpack_from("<4I", b, 0x1C)
        pixels = struct.unpack_from("<I", b, 0x3C + 12)[0]
        return {"aperta": ap, "cursore": cur, "n_vis": nvis, "guard": gu,
                "vis": vis, "val": val, "val0": val0, "sugg": sugg,
                "ycont": ycont, "altezza": altezza, "n_righe": nrighe,
                "aperture": aperture, "eventi": eventi, "salvataggi": salv,
                "esito": esito, "pixels": pixels}

    # --- la tilemap di MAIN_1 ----------------------------------------------
    def _tilemap_di(self, bgconfig, bgid):
        if bgconfig != BGCONFIG:
            return 0
        return struct.unpack("<I", self.uc.mem_read(
            bgconfig + BG_OFF_BGS + BG_STRIDE * bgid, 4))[0]

    def cella(self, x, y):
        """La cella (x, y) della tilemap di MAIN_1: tile nei 10 bit bassi,
        palette nei 4 alti, esattamente come la scrive il gioco."""
        return struct.unpack("<H", self.uc.mem_read(
            TILEMAP1 + 2 * (y * CELLE_RIGA + x), 2))[0]

    def _finestra(self, w):
        """Legge una `Window` del gioco (bg_window.h:68-79, 16 B)."""
        b = self.uc.mem_read(w, 16)
        bg, bgid, x, y, wid, hei, pal, base, pix = struct.unpack("<IBBBBBBHI", b)
        return {"bg": bg, "bgid": bgid, "x": x, "y": y, "w": wid, "h": hei,
                "pal": pal, "base": base, "pixels": pix}

    def _scrivi_rett(self, tm, x, y, w, h, primo, pal, incrementa):
        for r in range(h):
            for c in range(w):
                tile = (primo + r * w + c) if incrementa else primo
                v = 0 if primo is None else ((tile | (pal << 12)) & 0xFFFF)
                self.uc.mem_write(tm + 2 * ((y + r) * CELLE_RIGA + (x + c)),
                                  struct.pack("<H", v))

    def ospite_rinasce(self):
        """L'app Opzioni esce e rientra. Misurato sul banco melonDS il
        19/09/2026 (ROM 1.2.2 IT, fixture 708b317a...): la nuova istanza nasce
        allo STESSO indirizzo di heap della precedente (0x022C0264 entrambe le
        volte), quindi `u->app == app`; il suo init vanilla azzera la tilemap di
        ogni layer (`BgClearTilemapBufferAndCommit`, options_app.c:633). Lo stato
        dell'interfaccia NON si tocca: e' quello che il gioco lascia davvero."""
        self.uc.mem_write(TILEMAP1, bytes(TILEMAP_BYTE))

    def tasti(self, k, touch=0):
        self.uc.mem_write(NEWKEYS, struct.pack("<I", k))
        self.uc.mem_write(TOUCHNEW, struct.pack("<H", touch))

    def tocco(self, x, y):
        """v3: un tocco NUOVO alle coordinate date, senza alcun tasto. E' cosi'
        che il gioco lo presenta: touchNew alzato e le coordinate nei due campi
        che lo precedono nella stessa struttura."""
        self.uc.mem_write(NEWKEYS, struct.pack("<I", 0))
        self.uc.mem_write(TOUCHX, struct.pack("<HH", x, y))
        self.uc.mem_write(TOUCHNEW, struct.pack("<H", 1))

    # --- intercettazione delle funzioni del gioco -------------------------
    def _stub(self, uc, address, size, _):
        sp = uc.reg_read(UC_ARM_REG_SP)
        pila = list(struct.unpack("<4I", uc.mem_read(sp, 16)))
        pila_ext = list(struct.unpack("<4I", uc.mem_read(sp + 16, 16)))
        regs = [uc.reg_read(r) for r in (UC_ARM_REG_R0, UC_ARM_REG_R1,
                                         UC_ARM_REG_R2, UC_ARM_REG_R3)]
        nome = FUNZIONI[address]
        self.chiamate.append({"f": nome, "r": regs, "sp": pila, "sp_ext": pila_ext})
        if nome == "String_New":
            uc.reg_write(UC_ARM_REG_R0, FINTA_STRINGA)
            uc.mem_write(FINTA_STRINGA, struct.pack("<HHI", regs[0], 0, 0xB6F8D2EC))
        elif nome == "AddWindowParameterized":
            # bg_window.c:1560: senza tilemap del layer la finestra NON viene
            # scritta (nemmeno `pixels`); altrimenti si compilano i campi
            # come fa il gioco, cosi' gli stub sotto possono rileggerli.
            if self._tilemap_di(regs[0], regs[2]):
                uc.mem_write(regs[1], struct.pack("<IBBBBBBHI", regs[0], regs[2],
                                                  regs[3], pila[0], pila[1], pila[2],
                                                  pila[3], pila_ext[0], FINTO_PIXEL))
        elif nome == "CopyWindowToVram":
            f = self._finestra(regs[0])
            tm = self._tilemap_di(f["bg"], f["bgid"])
            if tm:                                  # PutWindowTilemap_TextMode
                self._scrivi_rett(tm, f["x"], f["y"], f["w"], f["h"],
                                  f["base"], f["pal"], True)
        elif nome == "ClearWindowTilemapAndCopyToVram":
            f = self._finestra(regs[0])
            tm = self._tilemap_di(f["bg"], f["bgid"])
            if tm:                                  # ClearWindowTilemapText
                self._scrivi_rett(tm, f["x"], f["y"], f["w"], f["h"], None, 0, False)
        elif nome == "BgClearTilemapCommit":
            tm = self._tilemap_di(regs[0], regs[1])
            if tm:
                uc.mem_write(tm, bytes(TILEMAP_BYTE))
        elif nome == "FillBgTilemapRect":
            tm = self._tilemap_di(regs[0], regs[1])
            if tm:                                  # r2 = tile, r3 = x; pila: y, w, h, pal
                self._scrivi_rett(tm, regs[3], pila[0], pila[1], pila[2],
                                  regs[2], pila[3], False)
        elif nome == "BgConfig_Alloc":
            uc.reg_write(UC_ARM_REG_R0, BGCONFIG)
        elif nome == "PaletteFadeFinished":
            uc.reg_write(UC_ARM_REG_R0, 1 if self.palette_finita else 0)
        elif nome == "FontID_String_GetWidth":
            uc.reg_write(UC_ARM_REG_R0, 40)
        else:
            uc.reg_write(UC_ARM_REG_R0, 0)
        uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR) | 1)

    # --- esecuzione -------------------------------------------------------
    def chiama(self, funzione, *args, canarini=True):
        """Esegue una funzione del blob e ritorna (r0, registri_finali)."""
        uc = self.uc
        fine = 0x0230F000
        uc.mem_write(fine, b"\x00\xbf" * 4)
        uc.reg_write(UC_ARM_REG_SP, SP0)
        uc.reg_write(UC_ARM_REG_LR, fine | 1)
        uc.reg_write(UC_ARM_REG_CPSR, 0x33)
        for i, v in enumerate(args):
            uc.reg_write((UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                          UC_ARM_REG_R3)[i], v)
        if canarini:
            for r, v in CANARINI.items():
                uc.reg_write(r, v)
        self.chiamate = []
        uc.emu_start(funzione | 1, fine, count=200000)
        finali = {r: uc.reg_read(r) for r in CANARINI}
        return uc.reg_read(UC_ARM_REG_R0), finali

    def nomi_chiamate(self):
        return [c["f"] for c in self.chiamate]
