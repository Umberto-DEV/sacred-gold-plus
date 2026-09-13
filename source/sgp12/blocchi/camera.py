#!/usr/bin/env python3
"""Blocco CAMERA — tabella delle eccezioni camera, da 16 a 24 voci. Porta a
`sgp12` di `SGP-1.2-CAMERA-01/tools/applica_camera.py` + `tabella.py` +
`rileggi_camera.py` (stesse costanti, stessi cancelli G0-G11 / R0-R9).

Due modi, scelti LEGGENDO la base (non da un'opzione): «zona-1.2» se la
riserva estesa (blocco RISERVA di questo pacchetto) e' gia' presente,
«in-luogo» altrimenti (ripiego dentro la sola zona 1.1).

`rileggi()` e' indipendente da `applica()` per costruzione (non importa
`tabella.py` dell'applicatore: qui `_Tabella` e' la STESSA classe, condivisa,
perche' la tabella non e' un'«impronta di verifica» ma un formato dati
pubblico — a differenza del manifest della riserva, vedi `sgp12/riserva.py`).
"""
from __future__ import annotations

import struct

from ..rom import Arm9, Rifiuto, esigi, sha
from ..riserva import canarino

# ---------------------------------------------------------------- tabella

VECCHIE = {2: 4, 4: 4, 5: 4, 135: 1, 176: 0, 221: 3, 226: 4, 239: 10,
           244: 12, 282: 7, 340: 13, 379: 3, 396: 12, 404: 4, 486: 10, 526: 10}
NUOVE = {119: 0, 250: 0, 251: 0, 252: 0, 116: 4, 247: 4, 248: 4, 249: 4}
CANONICA = dict(VECCHIE)
CANONICA.update(NUOVE)
N_MAPPE = 540


def tabella_controlla(t):
    motivi = []
    for k, v in sorted(t.items()):
        if not (0 <= k < N_MAPPE):
            motivi.append("id %d fuori da [0,%d)" % (k, N_MAPPE))
        if not (0 <= v < 16):
            motivi.append("valore %d dell'id %d fuori da [0,16)" % (v, k))
    voci = [(k << 4) | v for k, v in sorted(t.items())]
    if any(voci[i] >= voci[i + 1] for i in range(len(voci) - 1)):
        motivi.append("voci non strettamente crescenti come u16")
    chiavi = sorted(t)
    if any(chiavi[i] == chiavi[i + 1] for i in range(len(chiavi) - 1)):
        motivi.append("id ripetuto")
    for i in range(len(chiavi) - 1):
        if (chiavi[i + 1] << 4) - (chiavi[i] << 4) < 16:
            motivi.append("id %d e %d nello stesso blocco di 16: ricerca ambigua" % (chiavi[i], chiavi[i + 1]))
    if any(x > 0xFFFF for x in voci):
        motivi.append("voce oltre 16 bit")
    return motivi


def tabella_codifica(t):
    voci = sorted((k << 4) | v for k, v in t.items())
    return struct.pack("<%dH" % len(voci), *voci)


def tabella_decodifica(b):
    voci = struct.unpack("<%dH" % (len(b) // 2), b)
    return {x >> 4: x & 15 for x in voci}, list(voci)


# --- zona 1.1, invariante nei due modi
RIS11_BASE, RIS11_N = 0x023DEB40, 5312
RIS11_SHA = "43cdd97ebb48ad43590274ae90d06352bbc5f5a85c8cb65c651d7f8b35e3e2d2"
CAN11, CAN11_N = 0x023DEB40, 32
PAD11, PAD11_N = 0x023DEB60, 12
ECC11, ECC11_N = 0x023DEB6C, 32
COD, COD_N = 0x023DEB8C, 84
COD_SHA = "0832f466100bf990210485f7d43a64d908985802b548709099a0d80d3f7cdd95"
LIT_EXC, LIT_EXC_END = 0x023DEBD4, 0x023DEBD8
POOL = {0x023DEBCC: 0x0203B269, 0x023DEBD0: 0x023DFFFC, LIT_EXC: ECC11,
        LIT_EXC_END: COD, 0x023DEBDC: 0x020F6BE0}
REPEL, REPEL_N = 0x023DEBE0, 160
BORSA, BORSA_N, BSS_N = 0x023DEC80, 4420, 548
LIBERO11, LIBERO11_N = 0x023DFFE8, 20
STATO = 0x023DFFFC
SITO, SITO_BYTE, LIT_SITO = 0x0203B400, bytes.fromhex("054b1847"), 0x0203B418
ARENA_HI_LIT, MAINEX_LIT = 0x020D2BB0, 0x020D2C64
MAPHDR, MAPHDR_N, STRIDE = 0x020F6BE0, 540, 24

# --- zona 1.2 (riserva estesa, blocco RISERVA)
RIS12_BASE, RIS12_N = 0x023D8000, 32768
CAN12, CAN12_N = 0x023D8000, 32
HDR12, HDR12_N = 0x023D8020, 32
ECC12, ECC12_N = 0x023D8040, 48
CAN_ECC12, CAN_ECC12_N = 0x023D8070, 16
LIBERO12_DOPO = CAN_ECC12 + CAN_ECC12_N

ECC11_NUOVA, ECC11_NUOVA_N = 0x023DEB5C, 48
CAN11_RIDOTTO = 28


def applica(rom: bytes, tabella: dict | None = None, diagnostica: bool = False) -> tuple[bytes, dict]:
    import tempfile
    nuova = dict(tabella) if tabella is not None else dict(CANONICA)

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)

    log = {"strumento": "sgp12/blocchi/camera.py:applica", "sha256_ingresso": sha(rom),
           "cancelli": [], "diagnostica": diagnostica, "tabella_esplicita": tabella is not None}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    def no(c, msg):
        raise Rifiuto("%s: %s" % (c, msg))

    sezioni = {s[0]: (s[1], s[2]) for s in r.sezioni}
    if sezioni.get(RIS12_BASE) == (RIS12_N, 0):
        modo, ecc, ecc_n = "zona-1.2", ECC12, ECC12_N
    elif sezioni.get(RIS11_BASE) == (RIS11_N, 0):
        modo, ecc, ecc_n = "in-luogo", ECC11_NUOVA, ECC11_NUOVA_N
    else:
        no("G0", "la base non ha ne' la riserva 1.2 ne' quella 1.1: %s"
           % [("0x%08X" % s[0], s[1], s[2]) for s in r.sezioni])
    log["modo"] = modo

    if r.leggi(ecc, ecc_n) == tabella_codifica(nuova):
        log["esito"] = "gia-applicato"
        return rom, log
    ok("G0", "non e' gia' applicato")

    esigi(r.leggi(SITO, 4) == SITO_BYTE, "G2: i 4 byte a 0x%08X non sono attesi" % SITO)
    esigi(r.u32(LIT_SITO) == (COD | 1), "G2: letterale sito")
    esigi(sha(r.leggi(COD, COD_N)) == COD_SHA, "G2: sha256 del gancio")
    for ind, val in POOL.items():
        esigi(r.u32(ind) == val, "G2: pool 0x%08X" % ind)
    ok("G2", "sito, letterale, gancio (84 B) e pool a 5 voci combaciano")

    esigi(r.leggi(CAN11, CAN11_N) == canarino(0xCA5A0000, 8), "G3: canarino 1.1")
    esigi(set(r.leggi(PAD11, PAD11_N)) == {0}, "G3: padding non a zero")
    ok("G3", "canarino 1.1 + padding")

    vecchia, _ = tabella_decodifica(r.leggi(ECC11, ECC11_N))
    esigi(vecchia == VECCHIE, "G4: tabella vecchia inattesa")
    ok("G4", "16 voci attese")

    esigi(r.u32(STATO) == 1, "G9a: stato camera")
    atteso_arena = RIS12_BASE if modo == "zona-1.2" else RIS11_BASE
    esigi(r.u32(ARENA_HI_LIT) == atteso_arena, "G9a: letterale d'arena")
    esigi(r.u32(MAINEX_LIT) == 0x023E0000, "G9a: estremo alto")
    esigi(set(r.leggi(LIBERO11, LIBERO11_N)) == {0}, "G9a: 20 B liberi")
    ok("G9a", "stato=1, arena, estremo alto, liberi a zero")

    esigi(sha(r.leggi(RIS11_BASE, RIS11_N)) == RIS11_SHA, "G1: sha256 zona 1.1")
    ok("G1", "zona 1.1 intatta")

    if modo == "zona-1.2":
        esigi(r.leggi(CAN12, CAN12_N) == canarino(0xCA5A1000, 8), "G11: canarino basso")
        esigi(r.leggi(HDR12, 4) == b"SGP2", "G11: intestazione magic")
        esigi((r.u32(HDR12 + 8), r.u32(HDR12 + 12)) == (RIS12_BASE, 0x023E0000), "G11: intestazione campi")
        n_libero = RIS11_BASE - ECC12
        esigi(set(r.leggi(ECC12, n_libero)) == {0}, "G11: zona libera 1.2 non a zero")
        ok("G11", "canarino basso, intestazione, zona libera")

    motivi = tabella_controlla(nuova)
    esigi(not motivi, "G5: " + "; ".join(motivi))
    esigi(len(nuova) * 2 == ecc_n, "G5: numero di voci")
    if not diagnostica:
        for k, v in VECCHIE.items():
            esigi(nuova.get(k) == v, "G5: voce vecchia %d->%d persa" % (k, v))
        for k, v in NUOVE.items():
            esigi(nuova.get(k) == v, "G5: voce nuova %d->%d mancante" % (k, v))
    ok("G5", "%d voci, crescenti" % len(nuova))

    if modo == "zona-1.2":
        blocchi = [("canarino.basso", CAN12, CAN12_N), ("intestazione", HDR12, HDR12_N),
                   ("camera.eccezioni.1.2", ECC12, ECC12_N), ("canarino.camera", CAN_ECC12, CAN_ECC12_N),
                   ("libero.1.2", LIBERO12_DOPO, RIS11_BASE - LIBERO12_DOPO),
                   ("canarino.1.1", CAN11, CAN11_N), ("padding", PAD11, PAD11_N),
                   ("camera.eccezioni.dismessa", ECC11, ECC11_N), ("camera.codice", COD, COD_N)]
        primo, totale = RIS12_BASE, RIS12_N
    else:
        blocchi = [("canarino.1.1", CAN11, CAN11_RIDOTTO), ("camera.eccezioni", ECC11_NUOVA, ECC11_NUOVA_N),
                   ("camera.codice", COD, COD_N)]
        primo, totale = RIS11_BASE, RIS11_N
    blocchi += [("repellente", REPEL, REPEL_N), ("borsa.text", BORSA, BORSA_N),
                ("borsa.bss", BORSA + BORSA_N, BSS_N),
                ("libero.1.1", LIBERO11, LIBERO11_N), ("camera.stato", STATO, 4)]
    p = primo
    for nome, b, n in blocchi:
        esigi(b == p, "G10: buco o sovrapposizione prima di '%s'" % nome)
        p = b + n
    esigi(p == primo + totale, "G10: i blocchi non sommano al totale")
    ok("G10", "%d blocchi contigui" % len(blocchi))

    prima = bytes(r.raw)
    scritture = [(ecc, tabella_codifica(nuova)), (LIT_EXC, struct.pack("<I", ecc))]
    if modo == "zona-1.2":
        scritture.append((CAN_ECC12, canarino(0xCA5A1100, CAN_ECC12_N // 4)))
        scritture.append((LIT_EXC_END, struct.pack("<I", ecc + ecc_n)))
    for ram, dati in scritture:
        r.scrivi(ram, dati)

    leciti = set()
    for ram, dati in scritture:
        o = r.off(ram, len(dati))
        leciti |= set(range(o, o + len(dati)))
    diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "G6: %d byte scritti fuori portata" % len(fuori))
    ok("G6", "scritture solo nelle regioni dichiarate")
    esigi(len(r.raw) == len(prima), "G7: dimensione cambiata")
    ok("G7", "dimensione invariata")
    massimo = sum(len(d) for _, d in scritture)
    esigi(len(diversi) <= massimo, "G8: troppi byte diversi")
    ok("G8", "%d byte diversi (<= %d)" % (len(diversi), massimo))

    esigi(r.u32(STATO) == 1, "G9: stato camera cambiato")
    for nome, ram, n in (("repellente", REPEL, REPEL_N), ("borsa.text", BORSA, BORSA_N),
                         ("borsa.bss", BORSA + BORSA_N, BSS_N), ("map header", MAPHDR, MAPHDR_N * STRIDE)):
        o = r.off(ram, n)
        esigi(bytes(r.raw[o:o + n]) == prima[o:o + n], "G9: '%s' e' cambiato" % nome)
    esigi(r.u32(ARENA_HI_LIT) == atteso_arena, "G9: letterale d'arena cambiato")
    parole_can = CAN11_N // 4 if modo == "zona-1.2" else CAN11_RIDOTTO // 4
    esigi(r.leggi(CAN11, parole_can * 4) == canarino(0xCA5A0000, parole_can), "G9: canarino 1.1")
    if modo == "zona-1.2":
        esigi(r.leggi(CAN12, CAN12_N) == canarino(0xCA5A1000, 8), "G9: canarino basso 1.2 cambiato")
        o = r.off(ECC11, ECC11_N)
        esigi(bytes(r.raw[o:o + ECC11_N]) == prima[o:o + ECC11_N], "G9: tabella dismessa 1.1 spostata")
    ok("G9", "invarianti dopo la scrittura")

    log.update(esito="applicato", byte_diversi=len(diversi), byte_scritti=massimo,
               tabella={str(k): v for k, v in sorted(nuova.items())},
               sha256_uscita=sha(r.raw))
    return bytes(r.raw), log


def rileggi(base: bytes, candidata: bytes, attese: dict | None = None) -> dict:
    """Rilettore indipendente: cammina l'ARM9 con la propria routine (non usa
    `sgp12.rom.Arm9`), esattamente come `rileggi_camera.py`."""
    attese = dict(attese) if attese is not None else dict(CANONICA)

    class _Immagine:
        def __init__(self, raw):
            self.raw = raw
            off9 = struct.unpack_from("<I", raw, 0x20)[0]
            ram9 = struct.unpack_from("<I", raw, 0x28)[0]
            self.off9, self.ram9 = off9, ram9
            p = struct.unpack_from("<9I", raw, off9 + 0xBA0)
            tab0, tab1, dati0 = p[0], p[1], p[2]
            self.sez, q = [], off9 + tab0 - ram9
            while q < off9 + tab1 - ram9:
                self.sez.append(struct.unpack_from("<3I", raw, q))
                q += 12
            self.seg, o = [(ram9, off9, dati0 - ram9)], off9 + dati0 - ram9
            for ram, size, _ in self.sez:
                self.seg.append((ram, o, size))
                o += size
            self.fine_arm9 = o

        def b(self, ram, n):
            for base_, o, size in self.seg:
                if base_ <= ram and ram + n <= base_ + size:
                    return self.raw[o + ram - base_: o + ram - base_ + n]
            raise KeyError("0x%08X+%d" % (ram, n))

        def w(self, ram):
            return struct.unpack("<I", self.b(ram, 4))[0]

        def o(self, ram):
            for base_, of, size in self.seg:
                if base_ <= ram < base_ + size:
                    return of + ram - base_
            raise KeyError("0x%08X" % ram)

    b, c = _Immagine(base), _Immagine(candidata)
    esiti, rosso = [], []

    def R(nome, cond, nota):
        esiti.append({"cancello": nome, "esito": "VERDE" if cond else "ROSSO", "nota": nota})
        if not cond:
            rosso.append(nome)

    ecc = c.w(LIT_EXC)
    modo = "zona-1.2" if ecc == ECC12 else ("in-luogo" if ecc == ECC11_NUOVA else "IGNOTO")

    ris = c.sez[-1]
    atteso_ris = (0x023D8000, 32768, 0) if modo == "zona-1.2" else (0x023DEB40, 5312, 0)
    R("R0", len(b.raw) == len(c.raw) and len(c.sez) == 3 and ris == atteso_ris and modo != "IGNOTO",
      "dimensioni/sezioni/riserva")

    esigi_capstone = True
    try:
        from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
    except ImportError:
        esigi_capstone = False

    if esigi_capstone:
        md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
        ist = [(i.mnemonic, i.op_str) for i in md.disasm(c.b(SITO, 4), SITO)]
        R("R1", ist == [("ldr", "r3, [pc, #0x14]"), ("bx", "r3")] and c.w(LIT_SITO) == (COD | 1), "sito+letterale")

        COD_TESTO = 62
        cod_c, cod_b = c.b(COD, COD_N), b.b(COD, COD_N)
        pool = [struct.unpack_from("<I", cod_c, COD_TESTO + 2 + 4 * i)[0] for i in range(5)]
        fine = ecc + (ECC12_N if modo == "zona-1.2" else 48)
        pool_atteso = [0x0203B269, STATO, ecc, fine, MAPHDR]
        n_ist = sum(1 for _ in md.disasm(cod_c[:COD_TESTO], COD))
        dive = [COD + i for i in range(COD_N) if cod_c[i] != cod_b[i]]
        ammessi = set(range(LIT_EXC, LIT_EXC + 4)) | (set(range(LIT_EXC_END, LIT_EXC_END + 4))
                                                       if modo == "zona-1.2" else set())
        R("R2", pool == pool_atteso and n_ist == 31 and bool(dive) and set(dive) <= ammessi, "pool/istruzioni")

        tab = c.b(ecc, fine - ecc)
        dec, voci = tabella_decodifica(tab)
        cresc = all(voci[i] < voci[i + 1] for i in range(len(voci) - 1))
        R("R3", dec == attese and cresc and len(voci) == 24, "tabella")

        testo = list(md.disasm(cod_c[:COD_TESTO], COD))
        prima_del_salto = [i for i in testo if i.address < 0x023DEBBA]
        legge_header = any(i.mnemonic.startswith("ldr") and "#0x14]" in i.op_str for i in prima_del_salto)
        R("R9", not legge_header, "il ramo Plus non legge i map header")
    else:
        fine = ecc + (ECC12_N if modo == "zona-1.2" else 48)
        dec, voci = tabella_decodifica(c.b(ecc, fine - ecc))
        for nome in ("R1", "R2", "R9"):
            esiti.append({"cancello": nome, "esito": "SALTATO", "nota": "capstone non disponibile"})
        R("R3", dec == attese, "tabella (senza controllo del codice: capstone assente)")

    if modo == "zona-1.2":
        ok4 = (c.b(CAN12, CAN12_N) == canarino(0xCA5A1000, 8)
               and c.b(CAN11, 32) == canarino(0xCA5A0000, 8)
               and c.b(CAN_ECC12, CAN_ECC12_N) == canarino(0xCA5A1100, 4))
    else:
        ok4 = c.b(CAN11, 28) == canarino(0xCA5A0000, 7)
    R("R4", ok4, "canarini")

    uguali = all(c.b(x, n) == b.b(x, n) for x, n in
                 ((REPEL, REPEL_N), (BORSA, BORSA_N), (BORSA + BORSA_N, BSS_N), (LIBERO11, LIBERO11_N)))
    dismessa = c.b(ECC11, ECC11_N) == b.b(ECC11, ECC11_N) if modo == "zona-1.2" else True
    R("R5", uguali and dismessa and set(c.b(BORSA + BORSA_N, BSS_N)) == {0}
      and set(c.b(LIBERO11, LIBERO11_N)) == {0} and c.w(STATO) == 1
      and c.w(ARENA_HI_LIT) == b.w(ARENA_HI_LIT), "invarianti pubblici")

    R("R6", c.b(MAPHDR, MAPHDR_N * STRIDE) == b.b(MAPHDR, MAPHDR_N * STRIDE), "map header invariata")
    R("R7", b.raw[:b.off9] + b.raw[b.fine_arm9:] == c.raw[:c.off9] + c.raw[c.fine_arm9:],
      "fuori dall'ARM9 identico alla base")

    diversi = [i for i in range(len(b.raw)) if b.raw[i] != c.raw[i]]
    fine = ecc + (ECC12_N if modo == "zona-1.2" else 48)
    leciti = set(range(c.o(ecc), c.o(ecc) + (fine - ecc))) | set(range(c.o(LIT_EXC), c.o(LIT_EXC) + 4))
    if modo == "zona-1.2":
        leciti |= set(range(c.o(CAN_ECC12), c.o(CAN_ECC12) + CAN_ECC12_N))
        leciti |= set(range(c.o(LIT_EXC_END), c.o(LIT_EXC_END) + 4))
    R("R8", bool(diversi) and set(diversi) <= leciti, "insieme esatto dei byte diversi")

    return {"modo": modo, "sha256_base": sha(b.raw), "sha256_candidata": sha(c.raw),
           "byte_diversi": len(diversi), "cancelli": esiti,
           "esito": "VERDE" if not rosso else "ROSSO (%s)" % ", ".join(rosso)}
