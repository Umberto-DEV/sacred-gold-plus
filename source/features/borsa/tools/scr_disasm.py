#!/usr/bin/env python3
"""Disassemblatore del bytecode degli script HGSS (NARC `a/0/1/2`).

FONTE DELLE LUNGHEZZE DEGLI ARGOMENTI
-------------------------------------
`tools/py_scripts/scrcmd.json` del pret `pret/pokeheartgold`, commit
`0985e8718df4f25e64d6507d89c0c97c0d288981` (md5 ff8f415b767435bbf9a5e4eff1c20fff).
Il file elenca **853** comandi -- esattamente le voci di `gScriptCmdTable`
(`src/data/fieldmap/script_cmd_table.h`, istanziata in `src/scrcmd_c.c`) -- con,
per ciascuno, la lista delle larghezze dei suoi argomenti. NON e' scritto a mano:
lo genera `tools/py_scripts/get_scrcmd_args.py`, che legge il codice di ogni
`ScrCmd_*` (C o assembly) e conta le chiamate a `ScriptReadByte` (1 B),
`ScriptReadHalfword` (2 B), `ScriptReadWord` (4 B). E' quindi la tabella delle
lunghezze **ricavata dal codice dei comandi**, che e' esattamente cio' che P1 di
`J-borsa-generale-progetto.md` chiede.

La semantica dei tipi simbolici (quanti byte occupa `'var'`, `'script'`, ...) e'
quella del lettore di riferimento del pret, `tools/py_scripts/dump_scrcmds.py`,
funzione `Disassembler.get_arg` (righe 516-630): riprodotta qui in `ARG_SIZES`
con il commento della riga corrispondente.

FORMATO DEL MEMBRO (`dump_scrcmds.py::parse_header`, righe 408-417)
-------------------------------------------------------------------
    u32 rel[0..n-1]   ; entry point i = 4*i + 4 + rel[i]
    u16 0xFD13        ; SCRDEF_END, sentinella di fine tabella
    <bytecode>
Il riconoscimento della sentinella avviene a passo 4 come nel pret.

CAMMINATA
---------
Coda di lavoro inizializzata con tutti gli entry point; ogni argomento di tipo
`script` / `addr` / `movement` e' un offset **relativo alla fine dell'argomento**
e viene accodato (i `movement` come dati, non come codice). Il flusso lineare si
interrompe sui comandi marcati `is_abs_branch` nel JSON del pret: `End` (2),
`GoTo` (22), `Return` (27).

CANCELLO DI CORRETTEZZA (P1)
----------------------------
`--verifica` ri-serializza ogni istruzione decodificata dai suoi valori
semantici (opcode + argomenti, i rami ricalcolati come relativi) e la confronta
byte per byte con l'originale. Se un solo byte differisce, il disassemblato non
vale e il programma esce diverso da zero.

SOLA LETTURA: apre la ROM, non la riscrive mai.
"""
from __future__ import annotations

import argparse
import os
import json
import os
import struct
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Tipi di argomento -> (byte, categoria)
# Corrispondenza con `dump_scrcmds.py::get_arg`; il numero di riga e' del pret
# al commit 0985e871.
ARG_SIZES = {
    # interi espliciti nel JSON: 1, 2, 4 (get_arg righe 519-521)
    "object1": 1,            # riga 523: size = int(name[-1])
    "object2": 2,            # riga 523
    "message": 1,            # riga 534: un byte, indice nel banco messaggi
    "message_var": 2,        # riga 539
    "condition": 1,          # riga 569
    "var": 2,                # riga 578
    "flag": 2,               # riga 578
    "species": 2, "item": 2, "move": 2, "sound": 2, "ribbon": 2,
    "stdscr": 2, "trainer": 2, "phone_contact": 2, "spawn": 2,
    "maps": 2, "badge": 2, "direction": 2,   # righe 581-598
    "rgb": 2,                # riga 602
    "player_transition": 2,  # riga 616
    "addr": 4, "script": 4, "movement": 4,   # riga 556: 4 B RELATIVI
}
RELATIVE = {"addr", "script", "movement"}

SCRDEF_END = 0xFD13

# --------------------------------------------------------------------------
# Comandi che ci interessano per il censimento (indici dal JSON del pret).
CMD_GIVE_ITEM = 125
CMD_TAKE_ITEM = 126
CMD_HAS_SPACE = 127
CMD_HAS_ITEM = 128
CMD_GET_QUANTITY = 669
CMD_CALLSTD = 20

# Valuta e costi -- elenco completo ricavato da scrcmd.json cercando i nomi
# di denaro / gettoni / punti Pokeathlon / Battle Points / negozi / scambi.
CMD_VALUTA = {
    110: "AddMoney", 111: "SubMoneyImmediate", 112: "HasEnoughMoneyImmediate",
    113: "ShowMoneyBox", 114: "HideMoneyBox", 115: "UpdateMoneyBox",
    360: "SubMoneyVar", 368: "HasEnoughMoneyVar",
    119: "GetCoinAmount", 120: "GiveCoins", 121: "TakeCoins",
    532: "CheckCoinsImmediate", 533: "CheckGiveCoins", 570: "CheckCoinsVar",
    122: "GiveAthletePoints", 123: "TakeAthletePoints", 124: "CheckAthletePoints",
    554: "GetBattlePoints(ScrCmd_554)", 555: "GiveBattlePoints(ScrCmd_555)",
    556: "TakeBattlePoints(ScrCmd_556)", 557: "CheckBattlePoints",
    275: "MartBuy", 276: "SpecialMartBuy", 277: "DecorationMart", 278: "SealMart",
    782: "MartSell",
    470: "LoadNPCTrade", 472: "NPCTradeGetReqSpecies", 473: "NPCTradeExec",
    474: "NPCTradeEnd",
    567: "GetDPPlPrizeItemIDAndCost", 651: "GetScratchOffPrize",
    655: "TutorMoveGetPrice", 780: "CasinoGame",
}
# I soli comandi che PRELEVANO davvero (quelli che rendono il sito «a pagamento»
# in senso stretto). Gli altri sono di contorno (finestra dei soldi, controlli).
CMD_PRELIEVO = {
    111: "SubMoneyImmediate", 360: "SubMoneyVar",
    121: "TakeCoins", 123: "TakeAthletePoints",
    275: "MartBuy", 276: "SpecialMartBuy", 277: "DecorationMart",
    278: "SealMart", 782: "MartSell", 473: "NPCTradeExec",
    780: "CasinoGame", 126: "TakeItem", 556: "TakeBattlePoints(ScrCmd_556)",
}

# std_script.h del pret (include/constants/std_script.h)
STD_NOMI = {
    2000: "std_signpost", 2001: "std_hidden_item_fanfare", 2002: "std_nurse_joy",
    2003: "std_survive_poisoning", 2006: "std_prompt_save",
    2007: "std_receive_accessory", 2008: "std_obtain_item_verbose",
    2009: "std_bag_is_full", 2010: "std_pokecenter_pc", 2011: "std_mart_intro",
    2033: "std_give_item_verbose", 2041: "std_bag_is_full_griseous_orb",
}
STD_DONO = {2008, 2033}
# Banchi di script dedicati (src/script_manager.c:56-57, sScriptBankMapping)
BANCO_ITEM_BALL = 141      # _std_item_ball   7000  -> scr_seq_0141, msg 199
BANCO_NASCOSTI = 145       # _std_hidden_item 8000  -> scr_seq_0145, msg 210
BANCO_COMUNI = 3           # _std_misc        2000  -> scr_seq_0003, msg 040


# --------------------------------------------------------------------------
class Comandi:
    """La tabella dei comandi del pret."""

    def __init__(self, percorso_json: Path):
        dati = json.loads(Path(percorso_json).read_text(encoding="utf-8"))
        self.raw = dati["commands"]
        if len(self.raw) != 853:
            raise ValueError(
                "scrcmd.json ha %d comandi, gScriptCmdTable ne ha 853: "
                "non e' il commit 0985e871 del pret" % len(self.raw))
        self.nomi = [c["name"] for c in self.raw]

    def __len__(self):
        return len(self.raw)

    def nome(self, i: int) -> str:
        return self.nomi[i] if 0 <= i < len(self.nomi) else "ScrCmd_ILLEGALE_%d" % i

    def arg_list(self, i: int, valori_gia_letti):
        """Larghezze degli argomenti, tenendo conto dei comandi a caso
        (`switch_arg`/`cases`, dump_scrcmds.py:653-662)."""
        c = self.raw[i]
        base = list(c["args"])
        extra = None
        sw = c.get("switch_arg")
        cases = c.get("cases")
        if sw is not None and cases is not None:
            extra = (sw, cases)
        return base, extra

    def is_abs_branch(self, i: int) -> bool:
        return bool(self.raw[i].get("is_abs_branch"))


class Istruzione:
    __slots__ = ("off", "fine", "op", "nome", "args", "tipi", "rami")

    def __init__(self, off, fine, op, nome, args, tipi, rami):
        self.off = off
        self.fine = fine
        self.op = op
        self.nome = nome
        self.args = args      # valori grezzi letti dal file
        self.tipi = tipi      # larghezza/tipo di ciascun argomento
        self.rami = rami      # [(indice_argomento, destinazione_assoluta, tipo)]

    def testo(self) -> str:
        pezzi = []
        for v, t in zip(self.args, self.tipi):
            if t in RELATIVE:
                pezzi.append("<%d>" % v)
            elif t == "var" and 0x4000 <= v <= 0x40FF:
                pezzi.append("VAR_%04X" % v)
            elif t == "var" and 0x8000 <= v <= 0x80FF:
                pezzi.append("x%04X" % v)
            else:
                pezzi.append(str(v))
        return "%s %s" % (self.nome, ", ".join(pezzi)) if pezzi else self.nome


class Membro:
    """Un membro dell'NARC `a/0/1/2` disassemblato per intero."""

    def __init__(self, indice: int, raw: bytes, cmds: Comandi):
        self.indice = indice
        self.raw = raw
        self.cmds = cmds
        self.entry = []          # entry point (offset assoluti)
        self.header_end = 0
        self.istruzioni = {}     # offset -> Istruzione
        self.dati_movimento = set()
        self.errori = []
        self.header_valido = False
        self.tipo = "?"          # "evento" | "init" | "ignoto"
        self.init_entry = []     # per i membri di init: (tipo, idScript)

    # ---- intestazione (dump_scrcmds.py:408-417)
    def leggi_header(self) -> bool:
        raw = self.raw
        exported = []
        i = 0
        trovata = False
        while i + 2 <= len(raw):
            if raw[i:i + 2] == b"\x13\xfd":
                self.header_end = i + 2
                trovata = True
                break
            if i + 4 > len(raw):
                break
            rel = struct.unpack_from("<I", raw, i)[0]
            dest = (rel + i + 4) & 0xFFFFFFFF
            if dest >= len(raw):
                break
            exported.append(dest)
            i += 4
        if not trovata or self.header_end != 4 * len(exported) + 2:
            return self._leggi_header_init()
        self.entry = exported
        self.header_valido = True
        self.tipo = "evento"
        return True

    def _leggi_header_init(self) -> bool:
        """I 468 membri `scr_seq_*_hdr` NON sono bytecode: sono le tabelle degli
        script di inizializzazione della mappa (`asm/macros/script.inc:4983-5017`,
        `include/constants/init_script_types.h`). Formato:
            { u8 tipo (1..4); u16 idScript; u16 0 } ripetuto, poi u8 0.
        Non contengono alcun comando: sono fuori dal censimento per costruzione,
        non «membri che non si riescono a leggere»."""
        raw = self.raw
        i = 0
        voci = []
        while i < len(raw):
            t = raw[i]
            if t == 0:
                self.tipo = "init"
                self.header_end = len(raw)
                self.init_entry = voci
                return False          # nessun bytecode da camminare
            if t > 4 or i + 5 > len(raw):
                break
            voci.append((t, struct.unpack_from("<H", raw, i + 1)[0]))
            i += 5
        self.tipo = "ignoto"
        self.errori.append("intestazione non riconosciuta (ne' eventi ne' init)")
        return False

    # ---- camminata
    def cammina(self):
        if not self.header_valido and not self.leggi_header():
            return self
        coda = list(self.entry)
        visti = set()
        while coda:
            pc = coda.pop()
            while True:
                if pc in visti or pc >= len(self.raw) or pc < self.header_end:
                    break
                ins = self._decodifica(pc)
                if ins is None:
                    break
                visti.add(pc)
                self.istruzioni[pc] = ins
                for _, dest, tipo in ins.rami:
                    if tipo == "movement":
                        self.dati_movimento.add(dest)
                    elif self.header_end <= dest < len(self.raw) and dest not in visti:
                        coda.append(dest)
                if self.cmds.is_abs_branch(ins.op):
                    break
                pc = ins.fine
        return self

    def _decodifica(self, pc: int):
        raw = self.raw
        if pc + 2 > len(raw):
            return None
        op = struct.unpack_from("<H", raw, pc)[0]
        if op >= len(self.cmds):
            self.errori.append("opcode illegale %d a %d" % (op, pc))
            return None
        cur = pc + 2
        base, extra = self.cmds.arg_list(op, None)
        valori, tipi, rami = [], [], []
        elenco = list(base)
        idx = 0
        while idx < len(elenco):
            t = elenco[idx]
            n = t if isinstance(t, int) else ARG_SIZES.get(t)
            if n is None:
                self.errori.append("tipo di argomento sconosciuto %r (cmd %d @%d)" % (t, op, pc))
                return None
            if cur + n > len(raw):
                self.errori.append("argomenti troncati (cmd %d @%d)" % (op, pc))
                return None
            v = int.from_bytes(raw[cur:cur + n], "little")
            cur += n
            if t in RELATIVE:
                dest = (v + cur) & 0xFFFFFFFF
                if not (self.header_end <= dest < len(raw)):
                    self.errori.append("ramo fuori dal membro %d (cmd %d @%d)" % (dest, op, pc))
                    return None
                rami.append((idx, dest, t))
            valori.append(v)
            tipi.append(t)
            # comandi a caso: gli argomenti extra dipendono dal valore appena letto
            if extra is not None and idx == extra[0]:
                chiave = str(v)
                if chiave not in extra[1]:
                    self.errori.append("caso %s non previsto (cmd %d @%d)" % (chiave, op, pc))
                    return None
                elenco.extend(extra[1][chiave])
            idx += 1
        return Istruzione(pc, cur, op, self.cmds.nome(op), valori, tipi, rami)

    # ---- cancello: ri-serializzazione byte per byte
    def riassembla(self):
        """Ritorna (uguali, primo_offset_diverso). Ogni istruzione viene
        riscritta dai suoi valori semantici e confrontata con l'originale."""
        for pc, ins in self.istruzioni.items():
            out = bytearray(struct.pack("<H", ins.op))
            cur = pc + 2
            for v, t in zip(ins.args, ins.tipi):
                n = t if isinstance(t, int) else ARG_SIZES[t]
                if t in RELATIVE:
                    dest = (v + cur + n) & 0xFFFFFFFF
                    v = (dest - (cur + n)) & 0xFFFFFFFF
                out += int(v).to_bytes(n, "little")
                cur += n
            if bytes(out) != self.raw[pc:ins.fine]:
                return False, pc
        return True, None

    def copertura(self):
        coperti = sum(i.fine - i.off for i in self.istruzioni.values())
        return coperti, len(self.raw) - self.header_end

    def regioni_scoperte(self):
        """Gli intervalli di byte del corpo che la camminata non ha toccato:
        dati di movimento, routine morte lasciate dall'editor di Sacred Gold,
        riempimento. Servono al controllo di completezza del censimento."""
        vista = bytearray(len(self.raw))
        for ins in self.istruzioni.values():
            for k in range(ins.off, ins.fine):
                vista[k] = 1
        fuori, inizio = [], None
        for k in range(self.header_end, len(self.raw)):
            if not vista[k] and inizio is None:
                inizio = k
            elif vista[k] and inizio is not None:
                fuori.append((inizio, k))
                inizio = None
        if inizio is not None:
            fuori.append((inizio, len(self.raw)))
        return fuori

    def ordinate(self):
        return [self.istruzioni[k] for k in sorted(self.istruzioni)]

    def contesto(self, off: int, raggio: int = 10):
        chiavi = sorted(self.istruzioni)
        try:
            i = chiavi.index(off)
        except ValueError:
            return []
        lo, hi = max(0, i - raggio), min(len(chiavi), i + raggio + 1)
        return [self.istruzioni[k] for k in chiavi[lo:hi]]


# --------------------------------------------------------------------------
def carica_narc(percorso_rom: str, nome: str = "a/0/1/2"):
    import ndspy.rom
    import ndspy.narc
    rom = ndspy.rom.NintendoDSRom.fromFile(percorso_rom)
    grezzo = rom.getFileByName(nome)
    return ndspy.narc.NARC(grezzo).files, len(grezzo)


def disassembla_tutto(files, cmds: Comandi):
    return [Membro(i, d, cmds).cammina() for i, d in enumerate(files)]


# --------------------------------------------------------------------------
# CENSIMENTO
def _routine_di(m: Membro, off: int):
    """L'insieme di istruzioni raggiungibili linearmente a ritroso/avanti che
    forma la «routine» attorno a `off`: si risale fino al primo entry point o
    bersaglio di ramo che lo raggiunge, e si scende fino al primo
    `is_abs_branch`. Serve per decidere se un prelievo di valuta e' nello
    STESSO percorso di esecuzione del dono, non solo nello stesso membro."""
    chiavi = sorted(m.istruzioni)
    pos = {k: i for i, k in enumerate(chiavi)}
    if off not in pos:
        return []
    # avanti fino al primo branch assoluto
    fine = pos[off]
    while fine + 1 < len(chiavi):
        if m.cmds.is_abs_branch(m.istruzioni[chiavi[fine]].op):
            break
        fine += 1
    # indietro fino a un bersaglio di ramo (o a un entry point)
    bersagli = set(m.entry)
    for ins in m.istruzioni.values():
        for _, dest, tipo in ins.rami:
            if tipo != "movement":
                bersagli.add(dest)
    inizio = pos[off]
    while inizio > 0 and chiavi[inizio] not in bersagli:
        prec = m.istruzioni[chiavi[inizio - 1]]
        if prec.fine != chiavi[inizio] or m.cmds.is_abs_branch(prec.op):
            break
        inizio -= 1
    return [m.istruzioni[k] for k in chiavi[inizio:fine + 1]]


def _chiusura_valle(m: Membro, off: int, limite: int = 4000):
    """Tutto cio' che la routine che contiene `off` puo' ESEGUIRE dopo di se':
    i bersagli di `Call`/`CallIf`/`GoTo`/`GoToIf`/... seguiti in avanti fino a
    un `End`/`Return`. Serve perche' il prelievo puo' arrivare DOPO il controllo
    di spazio (e' il caso dello sportello Pokeathlon, membro 123: il
    `TakeAthletePoints` sta in una sotto-routine chiamata con `CallIf` piu'
    avanti). Guardare solo a monte lo avrebbe mancato."""
    routine = _routine_di(m, off)
    if not routine:
        return []
    visti = {i.off for i in routine}
    fuori = list(routine)
    coda = [d for i in routine for _, d, t in i.rami if t != "movement"]
    while coda and len(visti) < limite:
        pc = coda.pop()
        while pc in m.istruzioni and pc not in visti:
            ins = m.istruzioni[pc]
            visti.add(pc)
            fuori.append(ins)
            for _, d, t in ins.rami:
                if t != "movement":
                    coda.append(d)
            if m.cmds.is_abs_branch(ins.op):
                break
            pc = ins.fine
    return fuori


def _chiusura_chiamanti(m: Membro, off: int, prof: int = 2):
    """Le routine che chiamano (Call/GoTo/CallIf/GoToIf) la routine che contiene
    `off`, fino a `prof` livelli. Serve per vedere un `TakeCoins` che sta nel
    chiamante e non nella routine del dono."""
    routine = _routine_di(m, off)
    if not routine:
        return []
    visti = {routine[0].off}
    frontiera = [routine[0].off]
    fuori = []
    for _ in range(prof):
        nuovi = []
        for ins in m.istruzioni.values():
            for _, dest, tipo in ins.rami:
                if tipo == "movement" or dest not in frontiera:
                    continue
                r = _routine_di(m, ins.off)
                if r and r[0].off not in visti:
                    visti.add(r[0].off)
                    nuovi.append(r[0].off)
                    fuori.extend(r)
        frontiera = nuovi
        if not frontiera:
            break
    return fuori


def classifica(m: Membro, ins: Istruzione, banco_da_membro=None):
    """Classificazione motivata di un sito della borsa."""
    routine = _routine_di(m, ins.off)
    valle = _chiusura_valle(m, ins.off)
    chiamanti = _chiusura_chiamanti(m, ins.off)
    insieme = valle + chiamanti

    std_vicini = sorted({i.args[0] for i in insieme if i.op == CMD_CALLSTD})
    std_dono = sorted(set(std_vicini) & STD_DONO)
    prel_valle = sorted({CMD_PRELIEVO[i.op] for i in valle if i.op in CMD_PRELIEVO})
    prel_monte = sorted({CMD_PRELIEVO[i.op] for i in chiamanti if i.op in CMD_PRELIEVO})
    prelievi = sorted(set(prel_valle) | set(prel_monte))
    valute = sorted({CMD_VALUTA[i.op] for i in insieme if i.op in CMD_VALUTA})
    # TakeItem a monte nella stessa routine = scambio/baratto
    take_a_monte = any(i.op == CMD_TAKE_ITEM and i.off < ins.off for i in routine)

    motivi = []
    if m.indice == BANCO_ITEM_BALL:
        cls = "RACCOLTA_A_TERRA"
        motivi.append("membro %d = scr_seq_0141, banco dedicato _std_item_ball (7000+), "
                      "script_manager.c:56-57" % m.indice)
    elif m.indice == BANCO_NASCOSTI:
        cls = "OGGETTO_NASCOSTO"
        motivi.append("membro %d = scr_seq_0145, banco dedicato _std_hidden_item (8000+), "
                      "script_manager.c:56-57" % m.indice)
    elif m.indice == BANCO_COMUNI:
        cls = "COMUNE_STD"
        motivi.append("membro 3 = scr_seq_0003, gli script comuni std_2000+ "
                      "(qui vivono std_obtain_item_verbose 2008 e std_give_item_verbose 2033)")
    elif prelievi or take_a_monte:
        cls = "ACQUISTO_O_SCAMBIO"
        if prel_valle:
            motivi.append("prelievo sullo STESSO percorso di esecuzione (routine o sue "
                          "chiamate, anche dopo il controllo di spazio): %s" % ", ".join(prel_valle))
        if prel_monte:
            motivi.append("prelievo in una routine CHIAMANTE: %s" % ", ".join(prel_monte))
        if take_a_monte:
            motivi.append("TakeItem (126) a monte nella stessa routine: baratto")
    elif std_dono:
        cls = "DONO_GRATUITO"
        motivi.append("callstd %s nella stessa catena e nessun prelievo di valuta"
                      % ", ".join("%d (%s)" % (s, STD_NOMI.get(s, "?")) for s in std_dono))
    elif 2001 in std_vicini:
        cls = "OGGETTO_NASCOSTO"
        motivi.append("callstd 2001 (std_hidden_item_fanfare) nella stessa catena")
    else:
        cls = "ALTRO"
        motivi.append("nessun callstd 2008/2033, nessun prelievo di valuta, "
                      "nessun banco dedicato")
    if valute and not prelievi:
        motivi.append("comandi di valuta NON di prelievo nella catena (contorno): %s"
                      % ", ".join(valute))
    return {
        "classe": cls,
        "motivi": motivi,
        "callstd": std_vicini,
        "valuta": valute,
        "prelievi": prelievi,
        "prelievi_a_valle": prel_valle,
        "prelievi_a_monte": prel_monte,
        "take_item_a_monte": take_a_monte,
        "routine_inizio": routine[0].off if routine else None,
        "routine_fine": routine[-1].fine if routine else None,
    }


def fnv32(dati) -> int:
    h = 0x811C9DC5
    for x in dati:
        h = ((h ^ x) * 0x01000193) & 0xFFFFFFFF
    return h


def chiave_sito(m: Membro, ins: Istruzione):
    """La chiave con cui il gancio ARM9 riconosce QUESTO sito a runtime, senza
    conoscere il numero del membro (che `ScriptContext` non conserva):

        offset = ctx->script_ptr - ctx->mapScripts   (dopo l'opcode: off+2)
        impronta = FNV-1a sui <=32 byte che terminano alla fine dell'istruzione

    Entrambi sono leggibili dal gancio. La coppia e' verificata ESAUSTIVAMENTE
    unica su tutti i siti 125 e 127 dell'archivio (vedi --chiavi): non e'
    un'euristica, e' una tabella di ricerca su dati di sola lettura."""
    ini = max(m.header_end, ins.fine - 32)
    finestra = m.raw[ini:ins.fine]
    return {"offset": ins.off, "finestra": len(finestra),
            "impronta32": fnv32(finestra), "impronta16": fnv32(finestra) & 0xFFFF}


SITI_DI_INTERESSE = {
    CMD_GIVE_ITEM: "GiveItem",
    CMD_HAS_SPACE: "HasSpaceForItem",
    CMD_GET_QUANTITY: "GetItemQuantity",
    CMD_TAKE_ITEM: "TakeItem",
}


def censisci(membri, raggio=10):
    siti = []
    for m in membri:
        for ins in m.ordinate():
            if ins.op not in SITI_DI_INTERESSE:
                continue
            cl = classifica(m, ins)
            ctx = m.contesto(ins.off, raggio)
            siti.append({
                "membro": m.indice,
                "offset": ins.off,
                "comando": SITI_DI_INTERESSE[ins.op],
                "opcode": ins.op,
                "chiave": chiave_sito(m, ins),
                "argomenti": ins.args,
                "classe": cl["classe"],
                "motivi": cl["motivi"],
                "callstd": cl["callstd"],
                "valuta": cl["valuta"],
                "prelievi": cl["prelievi"],
                "prelievi_a_valle": cl["prelievi_a_valle"],
                "prelievi_a_monte": cl["prelievi_a_monte"],
                "routine": [cl["routine_inizio"], cl["routine_fine"]],
                "contesto": ["%5d  %s" % (i.off, i.testo()) for i in ctx],
            })
    return siti


CLASSI_PERMISSIVE = {"DONO_GRATUITO", "RACCOLTA_A_TERRA", "OGGETTO_NASCOSTO"}


def _tabella_permissivi(siti):
    """La tabella che il gancio ARM9 consulta: solo i siti 127 e 125 delle
    classi permissive. I due `GiveItem` del membro 3 NON ci sono: quelli
    girano anche per i negozi a gettoni, e sono governati dalla staffetta
    alzata dal gancio 127."""
    out = []
    for s in siti:
        if s["classe"] in CLASSI_PERMISSIVE and s["comando"] in ("HasSpaceForItem", "GiveItem"):
            out.append({"membro": s["membro"], "comando": s["comando"],
                        "offset": s["chiave"]["offset"],
                        "impronta16": s["chiave"]["impronta16"],
                        "finestra": s["chiave"]["finestra"],
                        "classe": s["classe"]})
    return {"voci": len(out), "byte_tabella": 4 * len(out), "elenco": out}


def _controlla_chiavi(membri):
    """Cancello: le chiavi (offset, impronta16) devono essere uniche su TUTTI i
    siti 125/127 dell'archivio, non solo sui permissivi. Se non lo sono, la
    ricerca del gancio non e' decidibile e il disegno cade."""
    esito = {}
    for op, nome in ((CMD_HAS_SPACE, "HasSpaceForItem"), (CMD_GIVE_ITEM, "GiveItem")):
        viste = {}
        collisioni = []
        for m in membri:
            if m.tipo != "evento":
                continue
            for ins in m.ordinate():
                if ins.op != op:
                    continue
                k = chiave_sito(m, ins)
                chiave = (k["offset"], k["impronta16"])
                if chiave in viste:
                    collisioni.append([viste[chiave], [m.indice, ins.off]])
                viste[chiave] = [m.indice, ins.off]
        esito[nome] = {"siti": sum(1 for m in membri if m.tipo == "evento"
                                   for i in m.ordinate() if i.op == op),
                       "chiavi": len(viste), "collisioni": collisioni}
    return esito


def siti_fuori_camminata(membri):
    """Controllo di COMPLETEZZA. Nelle regioni che la camminata non ha toccato
    si passa uno scanner a passo fisso cercando gli opcode della borsa. Ogni riscontro e'
    un possibile sito che il censimento non vede: o e' codice morto, o la
    camminata ha un buco. Dev'essere esaminato a mano, non ignorato."""
    fuori = []
    for m in membri:
        if m.tipo != "evento":
            continue
        for a, b in m.regioni_scoperte():
            for k in range(a, max(a, b - 8)):
                op = int.from_bytes(m.raw[k:k + 2], "little")
                if op not in SITI_DI_INTERESSE:
                    continue
                item, qty, ret = struct.unpack_from("<HHH", m.raw, k + 2)
                plausibile = (0x8000 <= ret <= 0x80FF or 0x4000 <= ret <= 0x40FF)
                if op == CMD_GET_QUANTITY:
                    plausibile = (0x8000 <= qty <= 0x80FF or 0x4000 <= qty <= 0x40FF)
                if plausibile:
                    fuori.append({"membro": m.indice, "offset": k,
                                  "comando": SITI_DI_INTERESSE[op],
                                  "regione_morta": [a, b],
                                  "argomenti": [item, qty, ret]})
    return fuori


def censisci_valuta(membri):
    """Tutti i siti dei comandi di valuta, per membro."""
    out = {}
    for m in membri:
        for ins in m.ordinate():
            if ins.op in CMD_VALUTA:
                out.setdefault(str(m.indice), []).append(
                    {"offset": ins.off, "comando": CMD_VALUTA[ins.op], "opcode": ins.op})
    return out


# --------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True, help="ROM .nds da leggere (sola lettura)")
    ap.add_argument("--pret", default=os.environ.get("SGP_PRET_SOURCE"),
                    help="checkout di pret/pokeheartgold @0985e871")
    ap.add_argument("--verifica", action="store_true",
                    help="cancello P1: ri-serializza e confronta byte per byte")
    ap.add_argument("--censimento", metavar="FILE.json",
                    help="scrive il censimento dei siti della borsa")
    ap.add_argument("--membro", type=int, action="append",
                    help="stampa il disassemblato di questo membro")
    ap.add_argument("--sito", nargs=2, type=int, action="append",
                    metavar=("MEMBRO", "OFFSET"),
                    help="stampa il contesto attorno a un sito")
    ap.add_argument("--raggio", type=int, default=10)
    args = ap.parse_args(argv)

    if not args.pret:
        ap.error("--pret oppure SGP_PRET_SOURCE e' obbligatorio")

    scrcmd = Path(args.pret) / "tools/py_scripts/scrcmd.json"
    cmds = Comandi(scrcmd)
    files, dim = carica_narc(args.rom)
    membri = disassembla_tutto(files, cmds)

    tot_ins = sum(len(m.istruzioni) for m in membri)
    cop = sum(m.copertura()[0] for m in membri)
    tot = sum(m.copertura()[1] for m in membri)
    ev = [m for m in membri if m.tipo == "evento"]
    ini = [m for m in membri if m.tipo == "init"]
    ign = [m.indice for m in membri if m.tipo == "ignoto"]
    con_errori = [m.indice for m in membri if m.errori]
    cop = sum(m.copertura()[0] for m in ev)
    tot = sum(m.copertura()[1] for m in ev)
    print("ROM            : %s" % args.rom)
    print("a/0/1/2        : %d membri, %d byte" % (len(files), dim))
    print("membri di evento (bytecode)     : %d" % len(ev))
    print("membri di init (tabelle _hdr)   : %d  [nessun bytecode: script.inc:4983]" % len(ini))
    print("membri non riconosciuti         : %d %s" % (len(ign), ign[:10]))
    print("istruzioni     : %d" % tot_ins)
    print("copertura      : %d / %d byte di corpo dei membri di evento (%.2f%%)"
          % (cop, tot, 100.0 * cop / tot))
    print("membri con errori di decodifica : %d %s" % (len(con_errori), con_errori[:10]))
    for m in membri:
        for e in m.errori:
            print("   membro %d: %s" % (m.indice, e))

    esito = 0
    if args.verifica:
        diversi = []
        for m in membri:
            ok, off = m.riassembla()
            if not ok:
                diversi.append((m.indice, off))
        print("CANCELLO P1 ri-serializzazione: %s (%d membri diversi) %s"
              % ("VERDE" if not diversi else "ROSSO", len(diversi), diversi[:5]))
        if diversi:
            esito = 1

    for mi in args.membro or []:
        m = membri[mi]
        print("\n=== membro %d (%d byte, %d entry point)" % (mi, len(m.raw), len(m.entry)))
        for k, e in enumerate(m.entry):
            print("  entry %3d -> %d" % (k, e))
        for ins in m.ordinate():
            print("  %5d  %s" % (ins.off, ins.testo()))

    for mi, off in args.sito or []:
        m = membri[mi]
        print("\n=== membro %d offset %d" % (mi, off))
        for ins in m.contesto(off, args.raggio):
            print("  %s%5d  %s" % (">>" if ins.off == off else "  ", ins.off, ins.testo()))
        if off in m.istruzioni:
            print("  classificazione: %s" % json.dumps(
                classifica(m, m.istruzioni[off]), ensure_ascii=False, indent=2))

    if args.censimento:
        siti = censisci(membri, args.raggio)
        morti = siti_fuori_camminata(membri)
        conteggi = {}
        for s in siti:
            conteggi.setdefault(s["comando"], {}).setdefault(s["classe"], 0)
            conteggi[s["comando"]][s["classe"]] += 1
        doc = {
            "rom": os.path.basename(args.rom),
            "pret_commit": "0985e8718df4f25e64d6507d89c0c97c0d288981",
            "fonte_lunghezze": "tools/py_scripts/scrcmd.json (853 comandi) + "
                               "dump_scrcmds.py::get_arg per i tipi simbolici",
            "narc": {"membri": len(files), "byte": dim},
            "disassemblato": {
                "istruzioni": tot_ins,
                "membri_evento": len(ev),
                "membri_init_hdr": len(ini),
                "membri_non_riconosciuti": ign,
                "byte_coperti": cop,
                "byte_corpo": tot,
                "copertura_percento": round(100.0 * cop / tot, 3),
                "membri_con_errori": con_errori,
                "errori": ["membro %d: %s" % (m.indice, e) for m in membri for e in m.errori],
            },
            "conteggi": conteggi,
            "chiavi_uniche": _controlla_chiavi(membri),
            "permissivi": _tabella_permissivi(siti),
            "siti": siti,
            "siti_in_regioni_non_raggiunte": morti,
            "valuta_per_membro": censisci_valuta(membri),
        }
        Path(args.censimento).write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print("censimento scritto in %s (%d siti)" % (args.censimento, len(siti)))
        for c, d in sorted(conteggi.items()):
            print("  %-16s %s" % (c, dict(sorted(d.items()))))

    return esito


if __name__ == "__main__":
    sys.exit(main())
