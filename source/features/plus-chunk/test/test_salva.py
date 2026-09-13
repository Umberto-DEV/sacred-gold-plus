#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-PLUS-03 — test host del blob `sgp.salvataggio`.

Prova il blob STORICO di PLUS-03 (`prove/build/salva_blob.bin`, 460 B). Quello
spedito nella 1.2 e' `sgp12/build/plus/salva_blob.bin` (500 B), applicato da
`sgp12/blocchi/plus_chunk.py` e verificato da `sgp12/test_lib.py`.

Il blob viene ESEGUITO (Unicorn, ARMv5 Thumb), non letto: le cinque funzioni del
gioco che chiama (lettura/scrittura della memoria di backup, CRC16, e le due
chiamate originali dei siti di gancio) sono sostituite da moncherini scritti
qui, e la memoria di backup e' un `bytearray` di 512 KiB. Cosi' i cancelli
possono davvero fallire: un chunk malformato che il blob accettasse si vede
subito, senza toccare una ROM.

Nota onesta sul CRC. Il moncherino NON e' il CRC della NitroSDK: e' un CRC-16
qualunque, uguale in scrittura e in lettura. Prova quindi che il blob *usa* il
CRC e che un byte cambiato lo fa cadere, non che il polinomio sia quello giusto
— quello si vede solo a runtime, ed e' la corsa B4 del rapporto.

Uso:  python3 -m unittest discover -s test -p 'test_*.py'
"""
import json
import struct
import unittest
from pathlib import Path

from unicorn import (Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE, UC_PROT_ALL)
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2,
                               UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC)

QUI = Path(__file__).resolve().parent
BUILD = QUI.parent / "prove" / "build"

# --- geometria, la stessa del manifesto ------------------------------------
MANIFESTO = json.loads((BUILD / "manifesto.json").read_text())
CODICE = int(MANIFESTO["indirizzi"]["codice"], 16)
STATO = int(MANIFESTO["indirizzi"]["stato"], 16)
BUF = int(MANIFESTO["indirizzi"]["buffer"], 16)
GANCIO_CARICA = int(MANIFESTO["simboli"]["sgp_gancio_carica"], 16)
GANCIO_SALVA = int(MANIFESTO["simboli"]["sgp_gancio_salva"], 16)

# --- funzioni del gioco sostituite -----------------------------------------
RB = 0x0202877C
WB = 0x02028758
CRC = 0x0201FF98
ORIG_LOAD = 0x020277D4
ORIG_SAVE = 0x02027DB4
STUBS = (RB, WB, CRC, ORIG_LOAD, ORIG_SAVE)

RESERVE = 0x023D8000
RESERVE_LEN = 0x8000
GIOCO = 0x02000000
GIOCO_LEN = 0x00200000
PILA = 0x02800000
PILA_LEN = 0x10000
FINE = 0x02900000          # indirizzo esca: il ritorno si ferma qui

SETT_A = 0x0002F000
SETT_B = 0x0006F000
PAY = 16
MAGIC_CHUNK = 0x5347
MAGIC_FOOTER = 0x32504753
VERSIONE = 2
GUARD = 0x5A
ABSENT, VALID, REJECT = 1, 2, 3


def crc16(dati):
    """CRC-16/CCITT (poli 0x1021, init 0xFFFF). Non e' quello della NitroSDK:
    e' UN crc, uguale per chi scrive e per chi legge (vedi il docstring)."""
    c = 0xFFFF
    for b in dati:
        c ^= b << 8
        for _ in range(8):
            c = ((c << 1) ^ 0x1021) & 0xFFFF if c & 0x8000 else (c << 1) & 0xFFFF
    return c


class Banco:
    """Un blob caricato, una memoria di backup, uno stato."""

    def __init__(self):
        self.blob = (BUILD / "salva_blob.bin").read_bytes()
        self.backup = bytearray(b"\xFF" * 0x80000)
        self.ritorno_load = 0
        self.ritorno_save = 2
        self.chiamate = {"rb": 0, "wb": 0, "crc": 0, "orig_load": 0, "orig_save": 0}
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
        self.uc.mem_map(GIOCO, GIOCO_LEN, UC_PROT_ALL)
        self.uc.mem_map(RESERVE, RESERVE_LEN, UC_PROT_ALL)
        self.uc.mem_map(PILA, PILA_LEN, UC_PROT_ALL)
        self.uc.mem_map(FINE & ~0xFFF, 0x1000, UC_PROT_ALL)
        self.uc.mem_write(RESERVE, b"\x00" * RESERVE_LEN)
        self.uc.mem_write(CODICE, self.blob)
        for a in STUBS:                      # `bx lr` come corpo: il gancio fa il resto
            self.uc.mem_write(a & ~1, b"\x70\x47")
        self.uc.hook_add(UC_HOOK_CODE, self._stub, begin=GIOCO, end=GIOCO + GIOCO_LEN)

    # -- moncherini ---------------------------------------------------------
    def _stub(self, uc, address, size, _user):
        if address == (RB & ~1):
            off = uc.reg_read(UC_ARM_REG_R0)
            dst = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            uc.mem_write(dst, bytes(self.backup[off:off + n]))
            uc.reg_write(UC_ARM_REG_R0, 1)
            self.chiamate["rb"] += 1
        elif address == (WB & ~1):
            off = uc.reg_read(UC_ARM_REG_R0)
            src = uc.reg_read(UC_ARM_REG_R1)
            n = uc.reg_read(UC_ARM_REG_R2)
            self.backup[off:off + n] = uc.mem_read(src, n)
            uc.reg_write(UC_ARM_REG_R0, 1)
            self.chiamate["wb"] += 1
        elif address == (CRC & ~1):
            p = uc.reg_read(UC_ARM_REG_R0)
            n = uc.reg_read(UC_ARM_REG_R1)
            uc.reg_write(UC_ARM_REG_R0, crc16(bytes(uc.mem_read(p, n))))
            self.chiamate["crc"] += 1
        elif address == (ORIG_LOAD & ~1):
            uc.reg_write(UC_ARM_REG_R0, self.ritorno_load)
            self.chiamate["orig_load"] += 1
        elif address == (ORIG_SAVE & ~1):
            uc.reg_write(UC_ARM_REG_R0, self.ritorno_save)
            self.chiamate["orig_save"] += 1

    # -- stato --------------------------------------------------------------
    def stato(self):
        b = bytes(self.uc.mem_read(STATO, 32))
        return {
            "active_plus": b[0], "active_wild": b[1], "cap": b[2],
            "load_status": b[3], "guard": b[4],
            "hits_trainer": struct.unpack_from("<I", b, 8)[0],
            "hits_wild": struct.unpack_from("<I", b, 12)[0],
            "chunk": b[16:32],
        }

    def scrivi_stato(self, **kw):
        b = bytearray(self.uc.mem_read(STATO, 32))
        for k, v in kw.items():
            if k == "active_plus":
                b[0] = v
            elif k == "active_wild":
                b[1] = v
            elif k == "cap":
                b[2] = v
            elif k == "load_status":
                b[3] = v
            elif k == "guard":
                b[4] = v
            elif k == "hits_trainer":
                struct.pack_into("<I", b, 8, v)
            elif k == "hits_wild":
                struct.pack_into("<I", b, 12, v)
            elif k == "chunk":
                b[16:32] = v
            else:
                raise KeyError(k)
        self.uc.mem_write(STATO, bytes(b))

    # -- esecuzione ---------------------------------------------------------
    def chiama(self, funzione, r0=0):
        uc = self.uc
        uc.reg_write(UC_ARM_REG_SP, PILA + PILA_LEN - 0x100)
        uc.reg_write(UC_ARM_REG_LR, FINE | 1)
        uc.reg_write(UC_ARM_REG_R0, r0)
        uc.emu_start(funzione | 1, FINE, timeout=5_000_000, count=200000)
        return uc.reg_read(UC_ARM_REG_R0)

    def carica(self):
        return self.chiama(GANCIO_CARICA, 0x02100000)

    def salva(self):
        return self.chiama(GANCIO_SALVA, 0x02100000)

    # -- utilita' -----------------------------------------------------------
    def metti_chunk(self, settore, payload, *, saveno=1, size=PAY, idx=6, crc=None,
                    magic=MAGIC_FOOTER):
        blocco = bytearray(payload) + bytearray(16)
        struct.pack_into("<IIIH", blocco, PAY, magic, saveno, size, idx)
        c = crc16(bytes(blocco[:PAY + 14])) if crc is None else crc
        struct.pack_into("<H", blocco, PAY + 14, c)
        self.backup[settore:settore + len(blocco)] = blocco
        return bytes(blocco)


def chunk(plus=0, selvatici=0, oltre100=0, anim=0, npc=0, wifi=0, picco=1,
          magic=MAGIC_CHUNK, versione=VERSIONE, r0=0, r1=0, r2=0):
    return struct.pack("<HBBBBBBBBBBI", magic, versione, plus, selvatici,
                       oltre100, anim, npc, wifi, picco, r0, r1, r2)


class TestChunk(unittest.TestCase):

    # --- B2.1 assente ------------------------------------------------------
    def test_chunk_assente_e_comportamento_1_1(self):
        b = Banco()
        b.ritorno_load = 7
        self.assertEqual(b.carica(), 7, "il gancio deve restituire il valore dell'originale")
        s = b.stato()
        self.assertEqual(s["load_status"], ABSENT)
        self.assertEqual(s["active_plus"], 0)
        self.assertEqual(s["active_wild"], 0)
        self.assertEqual(s["cap"], 100)
        self.assertEqual(s["guard"], GUARD)
        self.assertEqual(b.chiamate["rb"], 2, "deve provare tutte e due le copie")

    # --- B2.2 andata e ritorno --------------------------------------------
    def test_scrivi_poi_leggi(self):
        b = Banco()
        b.carica()
        b.scrivi_stato(active_plus=1, active_wild=1,
                       chunk=chunk(oltre100=1, anim=1, npc=1, wifi=3, picco=57))
        self.assertEqual(b.salva(), 2)
        self.assertEqual(b.chiamate["wb"], 2, "due copie, 47 e 111")
        self.assertEqual(bytes(b.backup[SETT_A:SETT_A + 32]),
                         bytes(b.backup[SETT_B:SETT_B + 32]),
                         "le due copie devono essere identiche")
        b2 = Banco()
        b2.backup = b.backup
        b2.carica()
        s = b2.stato()
        self.assertEqual(s["load_status"], VALID)
        self.assertEqual(s["active_plus"], 1)
        self.assertEqual(s["active_wild"], 1)
        self.assertEqual(s["chunk"][2], VERSIONE)
        self.assertEqual(s["chunk"][5], 1, "oltre100 conservato")
        self.assertEqual(s["chunk"][6], 1, "anim conservato")
        self.assertEqual(s["chunk"][7], 1, "npc conservato")
        self.assertEqual(s["chunk"][8], 3, "wifi_server conservato")
        self.assertEqual(s["chunk"][9], 57, "picco conservato")

    # --- B2.3 gli undici chunk malformati ---------------------------------
    def test_chunk_malformati_rifiutati(self):
        casi = {
            "magic del chunk sbagliato": dict(payload=chunk(magic=0x5348)),
            "versione 0": dict(payload=chunk(versione=0)),
            "versione 3 (futura)": dict(payload=chunk(versione=3)),
            "plus = 2": dict(payload=chunk(plus=2)),
            "selvatici = 5": dict(payload=chunk(selvatici=5)),
            "anim = 2": dict(payload=chunk(anim=2)),
            "npc = 0xFF": dict(payload=chunk(npc=0xFF)),
            "wifi_server = 4": dict(payload=chunk(wifi=4)),
            "picco = 0": dict(payload=chunk(picco=0)),
            "picco = 101 senza oltre100": dict(payload=chunk(picco=101)),
            "riservato0 != 0": dict(payload=chunk(r0=1)),
            "riservato2 != 0": dict(payload=chunk(r2=0xDEAD)),
            "CRC sbagliato": dict(payload=chunk(), crc=0x1234),
        }
        for nome, kw in casi.items():
            with self.subTest(nome):
                b = Banco()
                b.metti_chunk(SETT_A, **kw)
                b.metti_chunk(SETT_B, **kw)
                b.carica()
                s = b.stato()
                self.assertEqual(s["load_status"], REJECT,
                                 "%s: doveva essere rifiutato" % nome)
                self.assertEqual(s["active_plus"], 0, "%s: PLUS non deve accendersi" % nome)
                self.assertEqual(s["active_wild"], 0)

    # --- B2.4 un chunk rifiutato NON viene riscritto -----------------------
    def test_chunk_rifiutato_non_viene_riscritto(self):
        b = Banco()
        rotto = b.metti_chunk(SETT_A, payload=chunk(plus=2))
        b.metti_chunk(SETT_B, payload=chunk(plus=2))
        b.carica()
        self.assertEqual(b.stato()["load_status"], REJECT)
        prima = b.chiamate["wb"]
        self.assertEqual(b.salva(), 2, "il gancio restituisce comunque l'esito del gioco")
        self.assertEqual(b.chiamate["wb"], prima, "non deve scrivere un solo byte")
        self.assertEqual(bytes(b.backup[SETT_A:SETT_A + 32]), rotto)

    # --- B2.5 stato mai inizializzato --------------------------------------
    def test_stato_senza_guardia_non_scrive(self):
        b = Banco()
        b.scrivi_stato(guard=0, load_status=VALID)
        prima = b.chiamate["wb"]
        b.salva()
        self.assertEqual(b.chiamate["wb"], prima)

    # --- B2.6 salvataggio del gioco fallito: non si scrive -----------------
    def test_salvataggio_fallito_non_scrive(self):
        b = Banco()
        b.carica()
        b.ritorno_save = 3
        prima = b.chiamate["wb"]
        self.assertEqual(b.salva(), 3)
        self.assertEqual(b.chiamate["wb"], prima)

    # --- B2.7 copia rotta: regge il mirror ---------------------------------
    def test_copia_A_rotta_si_usa_la_B(self):
        b = Banco()
        b.metti_chunk(SETT_A, payload=chunk(plus=1), crc=0x0000)   # CRC rotto
        b.metti_chunk(SETT_B, payload=chunk(plus=1))
        b.carica()
        s = b.stato()
        self.assertEqual(s["load_status"], VALID)
        self.assertEqual(s["active_plus"], 1)

    # --- B2.8 i contatori diagnostici sopravvivono -------------------------
    def test_hits_non_azzerati(self):
        b = Banco()
        b.scrivi_stato(hits_trainer=6, hits_wild=3)
        b.carica()
        s = b.stato()
        self.assertEqual(s["hits_trainer"], 6)
        self.assertEqual(s["hits_wild"], 3)

    # --- B2.9 saveno cresce ------------------------------------------------
    def test_saveno_cresce(self):
        b = Banco()
        b.carica()
        b.salva()
        n1 = struct.unpack_from("<I", bytes(b.backup[SETT_A:SETT_A + 32]), PAY + 4)[0]
        b.salva()
        n2 = struct.unpack_from("<I", bytes(b.backup[SETT_A:SETT_A + 32]), PAY + 4)[0]
        self.assertEqual(n2, n1 + 1)

    # --- B2.10 un settore con magic altrui resta «assente» -----------------
    def test_magic_del_gioco_non_e_nostro(self):
        b = Banco()
        b.metti_chunk(SETT_A, payload=chunk(), magic=0x20060623)
        b.metti_chunk(SETT_B, payload=chunk(), magic=0x20060623)
        b.carica()
        self.assertEqual(b.stato()["load_status"], ABSENT,
                         "un chunk del gioco non e' un nostro chunk rotto")


if __name__ == "__main__":
    unittest.main()
