#!/usr/bin/env python3
"""Blocco TYPHLOSION — statistiche base della specie 157 ritoccate.

Dove: NARC `a/0/0/2` (personal data) del NitroFS, NON compresso, 508 membri da
44 byte esatti. L'indice del membro e' il numero del Dex nazionale, quindi il
157 e' Typhlosion. I primi 6 byte di ogni membro sono `struct BaseStats` di
pret/pokeheartgold (`include/pokemon_types_def.h`):

    u8 hp; u8 atk; u8 def; u8 speed; u8 spatk; u8 spdef;   /* 0x00..0x05 */

L'ordine (Velocita' PRIMA di Att.Sp.) e' confermato dai dati stessi: il membro
157 di una ROM non toccata legge dei valori che, in quell'ordine, sono quelli
di Typhlosion, e in nessun altro.

Il membro resta lungo 44 byte: si scrive IN LUOGO dentro la sezione GMIF del
NARC. BTAF, FAT, dimensione del NARC e della ROM restano identiche, nessuna
rilocazione, nessun byte in ARM9/overlay, nessuna voce nella riserva ARM9 —
esattamente come fanno `titolo`/`credito` sul NARC `a/0/4/6`.

**Nessun offset cablato**: il file si risolve per NOME (`a/0/0/2`) camminando
la FNT, e il membro per indice dentro la BTAF del NARC.

**Nessun dato di gioco nel repository**: la pre-immagine non e' scritta in
chiaro, e' riconosciuta per sha256 dei suoi sei byte (stessa strada di
`guida.py` con `ORIGINALE_SHA`). I sei valori scritti sono invece una scelta
di questo progetto e stanno in chiaro.

Non tocca il salvataggio. Le statistiche di un Pokemon gia' in squadra stanno
nel salvataggio, non nella ROM: il gioco le ricalcola (`CalcMonStats`) al
primo fra deposito+prelievo dal PC, salita di livello, vitamina, evoluzione.
Un salvataggio 1.2 resta leggibile e un salvataggio fatto qui resta leggibile
dalla 1.2: nessun campo del chunk cambia.
"""
from __future__ import annotations

import struct

from ..rom import Rifiuto, esigi, sha

NARC_PERSONAL = "a/0/0/2"
SPECIE = 157
TAGLIA_MEMBRO = 44
N_MEMBRI_ATTESI = 508
NOMI = ("ps", "att", "dif", "vel", "att.sp", "dif.sp")

# I sei byte che scriviamo: scelta di questo progetto, quindi in chiaro.
DOPO = (88, 135, 89, 114, 129, 95)         # totale 650
DOPO_SHA = "0adb97c6c3813a3463a751a693b76170f957398b3c44e7b0942351d6f5674ebd"
# La pre-immagine e' dato del gioco originale: solo la sua impronta.
PRIMA_SHA = "f99e776e0dbe43931fde08426cd49d26194652eb1ba45ff30c5406126643bc39"

assert sha(bytes(DOPO)) == DOPO_SHA


# --------------------------------------------------------------- NitroFS
# `applica()` cammina da se' FNT/FAT/NARC, senza ndspy: `rileggi()` ci arriva
# con ndspy, cioe' con una famiglia di decodificatori diversa.

def _u16(d, o):
    return struct.unpack_from("<H", d, o)[0]


def _u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


_BLOCCO = 1 << 20


def posizioni_diverse(a, b) -> list:
    """Tutte le posizioni in cui `a` e `b` differiscono, sull'INTERA immagine.

    Confronto a blocchi da 1 MiB: il confronto di fetta (C) scarta in un colpo
    i blocchi identici e solo dentro un blocco che differisce si scende al
    singolo byte. Il risultato e' lo stesso di un ciclo byte per byte su
    127 MB, ma senza il minuto di attesa che quello costa a ogni chiamata
    (`applica`, `rileggi` e i test lo usano piu' volte per ROM).
    """
    n = min(len(a), len(b))
    fuori = []
    for inizio in range(0, n, _BLOCCO):
        fine = min(inizio + _BLOCCO, n)
        if a[inizio:fine] == b[inizio:fine]:
            continue
        fuori.extend(i for i in range(inizio, fine) if a[i] != b[i])
    fuori.extend(range(n, max(len(a), len(b))))
    return fuori


def _risolvi_id(rom: bytes, percorso: str) -> int:
    """id FAT del file `percorso`, camminando la FNT. Nessun offset cablato."""
    fnt_off = _u32(rom, 0x40)
    dir_id = 0
    parti = percorso.split("/")
    for i, cercato in enumerate(parti):
        base = fnt_off + (dir_id & 0xFFF) * 8
        sotto = _u32(rom, base)
        fid = _u16(rom, base + 4)
        p = fnt_off + sotto
        trovato = None
        while True:
            t = rom[p]
            p += 1
            if t == 0:
                break
            lun = t & 0x7F
            nome = rom[p:p + lun].decode("ascii", "replace")
            p += lun
            if t & 0x80:                       # sottocartella
                sub = _u16(rom, p)
                p += 2
                if nome == cercato:
                    trovato = ("dir", sub)
                    break
            else:
                if nome == cercato:
                    trovato = ("file", fid)
                    break
                fid += 1
        esigi(trovato is not None, "percorso assente nella FNT: " + percorso)
        if trovato[0] == "dir":
            esigi(i < len(parti) - 1, "il percorso finisce su una cartella: " + percorso)
            dir_id = trovato[1]
        else:
            esigi(i == len(parti) - 1, "componente intermedio non e' una cartella: " + percorso)
            return trovato[1]
    raise Rifiuto("percorso non risolto: " + percorso)


def _sezioni_narc(blob: bytes) -> dict:
    esigi(blob[:4] == b"NARC", "non e' un NARC: %r" % blob[:4])
    hdrsize, nsec = struct.unpack_from("<HH", blob, 12)
    out, off = {}, hdrsize
    for _ in range(nsec):
        out[bytes(blob[off:off + 4])] = off
        off += _u32(blob, off + 4)
    return out


def posizione_membro(rom: bytes, percorso: str = NARC_PERSONAL, indice: int = SPECIE):
    """(offset assoluto nel .nds, lunghezza del membro, numero di membri)."""
    fid = _risolvi_id(rom, percorso)
    fat_off, fat_len = struct.unpack_from("<II", rom, 0x48)
    esigi(fid * 8 + 8 <= fat_len, "id FAT fuori tabella: %d" % fid)
    st, en = struct.unpack_from("<II", rom, fat_off + fid * 8)
    blob = rom[st:en]
    sez = _sezioni_narc(blob)
    btaf = sez[b"BTAF"]
    nfiles = _u32(blob, btaf + 8)
    esigi(indice < nfiles, "membro %d fuori dal NARC (%d membri)" % (indice, nfiles))
    m_st, m_en = struct.unpack_from("<II", blob, btaf + 12 + indice * 8)
    return st + sez[b"GMIF"] + 8 + m_st, m_en - m_st, nfiles


# ------------------------------------------------------------------ applica

def applica(rom: bytes) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/typhlosion.py:applica",
           "sha256_ingresso": sha(rom), "cancelli": []}

    def ok(c, nota=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": nota})

    off, lun, nfiles = posizione_membro(rom)
    log["offset_membro"] = "0x%08X" % off

    esigi(nfiles == N_MEMBRI_ATTESI,
          "A0: membri del NARC %s: %d, attesi %d" % (NARC_PERSONAL, nfiles, N_MEMBRI_ATTESI))
    ok("A0", "%s ha %d membri" % (NARC_PERSONAL, nfiles))
    esigi(lun == TAGLIA_MEMBRO,
          "A1: membro %d lungo %d B, attesi %d" % (SPECIE, lun, TAGLIA_MEMBRO))
    ok("A1", "il membro %d e' lungo %d B" % (SPECIE, lun))

    prima = bytes(rom[off:off + 6])
    impronta = sha(prima)
    if impronta == DOPO_SHA:
        log.update(esito="gia-applicato", byte_diversi=0, stato_ingresso="applicato",
                   sha256_uscita=log["sha256_ingresso"])
        ok("A2", "pre-immagine gia' quella finale: niente da scrivere (idempotenza)")
        return rom, log
    esigi(impronta == PRIMA_SHA,
          "A2: la pre-immagine del membro %d non e' quella attesa (impronta %s): la base non e' "
          "una ROM in cui questa specie sia intatta" % (SPECIE, impronta))
    ok("A2", "pre-immagine riconosciuta per impronta")
    log["stato_ingresso"] = "originale"

    esigi(all(1 <= v <= 255 for v in DOPO), "A3: una statistica e' fuori da 1..255")
    ok("A3", "le sei statistiche stanno in 1..255 (massimo %d)" % max(DOPO))

    out = bytearray(rom)
    out[off:off + 6] = bytes(DOPO)

    diversi = posizioni_diverse(rom, out)
    esigi(all(off <= i < off + 6 for i in diversi),
          "A4: %d byte scritti fuori dalle sei statistiche" % len(diversi))
    ok("A4", "%d byte cambiati, tutti dentro i sei dichiarati" % len(diversi))
    esigi(len(out) == len(rom), "A5: la ROM ha cambiato dimensione")
    ok("A5", "dimensione della ROM invariata (%d B)" % len(out))
    esigi(rom[off + 6:off + TAGLIA_MEMBRO] == out[off + 6:off + TAGLIA_MEMBRO],
          "A6: toccati byte oltre le sei statistiche, dentro il membro")
    ok("A6", "i byte 6..43 del membro sono intatti")

    uscita = bytes(out)
    log.update(esito="applicato", byte_diversi=len(diversi), sha256_uscita=sha(uscita))
    return uscita, log


# ------------------------------------------------------------------ rileggi

def rileggi(base: bytes, candidata: bytes) -> dict:
    """Rilettore indipendente: ndspy (`NintendoDSRom` + `narc.NARC`), cioe' una
    famiglia di decodificatori diversa da quella di `applica()`, che cammina
    FNT/FAT/NARC a mano. I valori attesi sono quelli di `DOPO`, ma la
    posizione del membro viene ricavata di nuovo qui."""
    from ndspy import narc as ndsnarc
    from ndspy import rom as ndsrom

    def membri(grezzo):
        immagine = ndsrom.NintendoDSRom(bytes(grezzo))
        archivio = ndsnarc.NARC(immagine.getFileByName(NARC_PERSONAL))
        return [bytes(f) for f in archivio.files]

    mem_a, mem_b = membri(base), membri(candidata)
    off, _lun, _n = posizione_membro(base)
    diversi = posizioni_diverse(base, candidata)

    esiti, rosso = [], []

    def L(nome, cond, nota):
        esiti.append({"cancello": nome, "esito": "VERDE" if cond else "ROSSO", "nota": nota})
        if not cond:
            rosso.append(nome)

    L("L1", len(base) == len(candidata), "lunghezza della ROM invariata")
    L("L2", len(mem_a) == len(mem_b) == N_MEMBRI_ATTESI
      and all(len(m) == TAGLIA_MEMBRO for m in mem_a + mem_b),
      "%s: %d membri da %d B in entrambe" % (NARC_PERSONAL, N_MEMBRI_ATTESI, TAGLIA_MEMBRO))
    L("L3", sha(mem_a[SPECIE][:6]) == PRIMA_SHA, "la base porta la pre-immagine attesa")
    L("L4", tuple(mem_b[SPECIE][:6]) == DOPO, "la candidata porta le sei statistiche attese")
    L("L5", mem_a[SPECIE][6:] == mem_b[SPECIE][6:], "i byte 6..43 del membro sono identici")
    L("L6", all(mem_a[i] == mem_b[i] for i in range(len(mem_a)) if i != SPECIE),
      "gli altri %d membri sono identici" % (N_MEMBRI_ATTESI - 1))
    L("L7", diversi == list(range(off, off + 6)),
      "in TUTTA la ROM cambiano esattamente sei byte consecutivi, a 0x%08X" % off)
    L("L8", all(1 <= v <= 255 for v in mem_b[SPECIE][:6]), "dominio 1..255 rispettato")

    return {"sha256_base": sha(base), "sha256_candidata": sha(candidata),
            "offset_membro": "0x%08X" % off, "byte_diversi": len(diversi),
            "cancelli": esiti,
            "esito": "VERDE" if not rosso else "ROSSO (%s)" % ", ".join(rosso)}
