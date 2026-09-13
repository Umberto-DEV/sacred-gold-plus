#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SGP-1.2-OVERLAY-01 — applicatore condiviso di patch di byte dentro gli
overlay ARM9 (compressi BLZ) di HGSS, che lascia la ROM valida.

Libreria + CLI. Nessuna dipendenza esterna: legge e scrive i byte della ROM da
se'. **Non usa `ndspy.rom.save()`**, che e' misurato rompere la ROM anche senza
cambiare niente (SGP-1.2-ANIM-B-01/RAPPORTO.md §8).

Uso tipico:

    overlay_patch.py --rom in.nds --out out.nds --overlay 12 \\
        --guardia 0x0226203C:0bb5... \\
        --patch 0x0226200C:3d206202:51883d02

Ogni `--patch` e' `INDIRIZZO:PREIMMAGINE:POSTIMMAGINE` in esadecimale, con
preimmagine e postimmagine della **stessa** lunghezza. L'indirizzo e' quello in
RAM (lo stesso che si legge nel disassemblato), non un offset di file.

`--overlay auto` sceglie l'overlay per GUARDIA e rifiuta se i candidati non sono
esattamente uno. Con `--overlay N` l'overlay si prende per id, ma la guardia si
verifica lo stesso: una guardia che non combacia e' sempre un rifiuto.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------- eccezioni

class Rifiuto(Exception):
    """Un cancello non e' superato. L'uscita non viene scritta."""


def esigi(condizione, messaggio):
    if not condizione:
        raise Rifiuto(messaggio)


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


# ------------------------------------------------------------------- CRC16

_TBL_CRC16 = (0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
              0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400)


def crc16(dati, crc=0xFFFF):
    """CRC16 dell'header di cartuccia DS (gbatek, «Header CRC16»)."""
    for b in dati:
        crc = (crc >> 4) ^ _TBL_CRC16[(crc ^ b) & 0xF]
        crc = (crc >> 4) ^ _TBL_CRC16[(crc ^ (b >> 4)) & 0xF]
    return crc & 0xFFFF


# --------------------------------------------------------------------- BLZ
#
# BLZ e' il formato con cui la NitroSDK comprime ARM9 e overlay. Si decomprime
# ALL'INDIETRO e IN LUOGO con `MIi_UncompressBackward`, che legge gli ultimi 8
# byte del flusso:
#
#     word0 = (hdr_len << 24) | enc_len      word1 = inc_len
#
# con, detto `n` la dimensione del flusso compresso e `bottom` il suo indirizzo
# finale in RAM:
#
#     dest_fine = bottom + inc_len          (fine dell'immagine decompressa)
#     src       = bottom - hdr_len          (primo byte codificato, si scende)
#     stop      = bottom - enc_len          (sotto c'e' il prefisso NON codificato)
#
# Quindi: dimensione decompressa = n + inc_len; prefisso grezzo = n - enc_len;
# `hdr_len` conta gli 8 byte del trailer piu' il riempimento di allineamento.
#
# Il flusso e' un LZ77 «rovesciato»: si comprime la sequenza invertita, e il
# risultato si reinverte. Distanze 3..0x1002, lunghezze 3..0x12, soglia 2.

BLZ_N = 0x1002
BLZ_F = 0x12
BLZ_SOGLIA = 2


def blz_leggi_trailer(flusso):
    """Ritorna (hdr_len, enc_len, inc_len, prefisso_grezzo, dim_decompressa)."""
    esigi(len(flusso) >= 8, "BLZ: flusso piu' corto di 8 byte")
    w0, w1 = struct.unpack_from("<II", flusso, len(flusso) - 8)
    hdr_len = (w0 >> 24) & 0xFF
    enc_len = w0 & 0xFFFFFF
    inc_len = w1
    esigi(hdr_len >= 8, "BLZ: hdr_len %d < 8" % hdr_len)
    esigi(enc_len >= hdr_len, "BLZ: enc_len %d < hdr_len %d" % (enc_len, hdr_len))
    esigi(enc_len <= len(flusso), "BLZ: enc_len %d oltre il flusso (%d)" % (enc_len, len(flusso)))
    return hdr_len, enc_len, inc_len, len(flusso) - enc_len, len(flusso) + inc_len


def blz_decomprimi(flusso):
    """DECODIFICATORE A — trascrizione fedele di `MIi_UncompressBackward`.

    Lavora IN LUOGO su un buffer lungo quanto l'immagine finale, esattamente
    come fa il gioco: se il flusso fosse costruito male da far scavalcare la
    sorgente alla destinazione, qui si vedrebbe, perche' si vede nel gioco.
    """
    n = len(flusso)
    hdr_len, enc_len, inc_len, grezzo, dim = blz_leggi_trailer(flusso)
    buf = bytearray(dim)
    buf[:n] = flusso
    src = n - hdr_len
    dst = dim
    stop = n - enc_len
    while src > stop:
        src -= 1
        flag = buf[src]
        for _ in range(8):
            if src <= stop:
                break
            if flag & 0x80:
                src -= 1
                b1 = buf[src]
                src -= 1
                b2 = buf[src]
                off = (((b1 & 0x0F) << 8) | b2) + 3
                ln = (b1 >> 4) + 3
                esigi(dst - ln >= 0, "BLZ: scrittura sotto l'inizio del buffer")
                esigi(dst + off <= dim, "BLZ: distanza oltre la fine del buffer")
                for _ in range(ln):
                    dst -= 1
                    buf[dst] = buf[dst + off]
            else:
                src -= 1
                dst -= 1
                buf[dst] = buf[src]
            esigi(dst >= src, "BLZ: la destinazione ha scavalcato la sorgente "
                              "(dst=%d src=%d): il flusso NON e' decomprimibile in luogo" % (dst, src))
            flag = (flag << 1) & 0xFF
    esigi(dst == grezzo, "BLZ: la decompressione finisce a %d invece che a %d" % (dst, grezzo))
    return bytes(buf)


def _riscontri_massimi(dati):
    """Per ogni posizione del dominio ROVESCIATO, la lunghezza massima di un
    riscontro utilizzabile (distanza 3..0x1002, lunghezza 3..0x12, e lunghezza
    non maggiore della distanza come in `blz.c`: niente sovrapposizioni).

    Se a `i` esiste un riscontro di lunghezza `M`, esiste anche per ogni
    lunghezza minore con la STESSA distanza (la distanza e' >= M >= L), quindi
    per la programmazione dinamica basta il massimo."""
    n = len(dati)
    best = bytearray(n)
    dist_best = [0] * n
    catene = {}
    for i in range(n):
        if i + 3 <= n:
            chiave = dati[i:i + 3]
            lista = catene.get(chiave)
            if lista:
                limite = i - BLZ_N
                k = 0
                for k, j in enumerate(lista):
                    if j >= limite:
                        break
                else:
                    k = len(lista)
                if k:
                    del lista[:k]
                m_best = 0
                d_best = 0
                tetto = BLZ_F if n - i >= BLZ_F else n - i
                for j in lista:
                    dist = i - j
                    if dist < 3:
                        break
                    massimo = tetto if tetto < dist else dist
                    if massimo <= m_best:
                        continue
                    if dati[i + m_best] != dati[j + m_best]:
                        continue
                    m = 0
                    while m < massimo and dati[i + m] == dati[j + m]:
                        m += 1
                    if m > m_best:
                        m_best = m
                        d_best = dist
                        if m_best == tetto:
                            break
                if m_best > BLZ_SOGLIA:
                    best[i] = m_best
                    dist_best[i] = d_best
            catene.setdefault(chiave, []).append(i)
    return best, dist_best


def _analisi_ottima(dati, best):
    """Programmazione dinamica: il costo si conta in OTTAVI di byte (un
    letterale 8/8 + 1/8 di bit di bandiera = 9; una coppia 16/8 + 1/8 = 17).

    Ritorna (costo8, lunghezza_scelta, token): `costo8[k]` e' il costo per
    codificare le prime `k` posizioni del dominio rovesciato, `token[k]` quanti
    token ci vogliono, `lunghezza_scelta[k]` la lunghezza dell'ultimo token
    (1 = letterale). Da costo8 e token si ricava la dimensione ESATTA della
    parte codificata, bandiere comprese, senza doverla emettere:

        byte_token = (costo8 - token) // 8        (1 per letterale, 2 per coppia)
        bandiere   = ceil(token / 8)
    """
    n = len(dati)
    INF = 1 << 60
    costo = [INF] * (n + 1)
    token = [0] * (n + 1)
    scelta = bytearray(n + 1)
    costo[0] = 0
    for i in range(n):
        c = costo[i]
        if c >= INF:
            continue
        t = token[i]
        c9 = c + 9
        if c9 < costo[i + 1]:
            costo[i + 1] = c9
            token[i + 1] = t + 1
            scelta[i + 1] = 1
        m = best[i]
        if m:
            c17 = c + 17
            for L in range(3, m + 1):
                if c17 < costo[i + L]:
                    costo[i + L] = c17
                    token[i + L] = t + 1
                    scelta[i + L] = L
    return costo, scelta, token


def _emetti(dati, scelta, dist_best, k):
    """Ricostruisce la sequenza di token che arriva a `k` e la emette nel
    dominio rovesciato (bandiera ogni 8 token, MSB per primo)."""
    percorso = []
    i = k
    while i > 0:
        L = scelta[i]
        percorso.append((i - L, L))
        i -= L
    percorso.reverse()
    pak = bytearray()
    maschera = 0
    pos_flag = -1
    for (p, L) in percorso:
        if maschera == 0:
            pos_flag = len(pak)
            pak.append(0)
            maschera = 0x80
        if L == 1:
            pak.append(dati[p])
        else:
            # la distanza e' quella trovata dall'indicizzazione: vale per la
            # lunghezza massima a quel punto, quindi a maggior ragione per L
            trovata = dist_best[p]
            esigi(trovata >= L and 3 <= trovata <= BLZ_N,
                  "BLZ: distanza %d non valida per un riscontro di %d a %d" % (trovata, L, p))
            esigi(dati[p:p + L] == dati[p - trovata:p - trovata + L],
                  "BLZ: il riscontro (%d,%d) a %d non e' vero" % (trovata, L, p))
            v = L - (BLZ_SOGLIA + 1)
            pak.append(((v << 4) | ((trovata - 3) >> 8)) & 0xFF)
            pak.append((trovata - 3) & 0xFF)
            pak[pos_flag] |= maschera
        maschera >>= 1
    return bytes(pak)


def _confeziona(grezzo, dati, pak, k):
    """Mette insieme prefisso grezzo + coda codificata + riempimento + trailer."""
    raw_len = len(grezzo)
    raw_tmp = raw_len - k
    out = bytearray()
    out += grezzo[:raw_tmp]
    out += bytes(reversed(pak))
    hdr_len = 8
    inc_len = raw_len - len(pak) - raw_tmp
    while len(out) & 3:
        out.append(0xFF)
        hdr_len += 1
    out += struct.pack("<I", ((len(pak) + hdr_len) & 0xFFFFFF) | (hdr_len << 24))
    out += struct.pack("<I", (inc_len - hdr_len) & 0xFFFFFFFF)
    return bytes(out)


def blz_comprimi_ottimo(grezzo, bersaglio=None):
    """Compressore BLZ con **analisi ottima** (cammino minimo sui token).

    Produce sempre uno stream piu' corto di quello prodotto dalla scelta avida di
    `blz.c`, e nella pratica piu' corto anche di quello originale del gioco: e'
    cio' che permette di riscrivere l'overlay **in luogo**, l'unico modo sicuro
    (vedi RAPPORTO §3).

    `bersaglio`: se dato, si cerca un punto di taglio del prefisso grezzo che
    dia ESATTAMENTE quella dimensione, cosi' la voce FAT e la voce y9 non
    cambiano di un byte e nella ROM cambia SOLO il corpo dell'overlay. Se non si
    trova, si ripiega sulla dimensione minima.
    """
    raw_len = len(grezzo)
    esigi(raw_len > 0, "BLZ: niente da comprimere")
    dati = bytes(reversed(grezzo))
    best, dist_best = _riscontri_massimi(dati)
    costo, scelta, token = _analisi_ottima(dati, best)

    def totale(k):
        c, t = costo[k], token[k]
        pak = (c - t) // 8 + (t + 7) // 8
        corpo = (raw_len - k) + pak
        return corpo + (-corpo) % 4 + 8

    tutti = [(totale(k), k) for k in range(1, raw_len + 1)]
    minimo, k_min = min(tutti)
    k = k_min
    if bersaglio is not None and bersaglio != minimo:
        esatti = [kk for (tt, kk) in tutti if tt == bersaglio]
        if esatti:
            k = max(esatti)
    flusso = _confeziona(grezzo, dati, _emetti(dati, scelta, dist_best, k), k)
    if bersaglio is not None and len(flusso) != bersaglio:
        # il bersaglio non e' raggiungibile: si torna al minimo
        k = k_min
        flusso = _confeziona(grezzo, dati, _emetti(dati, scelta, dist_best, k), k)
    return flusso


def blz_comprimi(grezzo):
    """Compressore BLZ AVIDO, l'algoritmo pubblico di `blz.c` di CUE (dominio pubblico).

    Identico per costruzione a `SGP-1.2-ANIM-B-01/tools/blz.c`: stessa finestra,
    stessa soglia, stessa scelta del prefisso grezzo (quello che rende minima la
    somma «prefisso + coda codificata»), stesso riempimento `0xFF` per allineare
    il trailer a 4 byte.

    La ricerca del riscontro e' indicizzata (catene di prefissi da 3 byte) ma
    rispetta l'ordine di `blz.c`: fra piu' riscontri di lunghezza massima vince
    quello con la DISTANZA MAGGIORE, perche' `blz.c` scorre le distanze dalla
    piu' grande alla piu' piccola aggiornando solo su lunghezza strettamente
    maggiore.
    """
    raw_len = len(grezzo)
    if raw_len == 0:
        raise Rifiuto("BLZ: niente da comprimere")
    dati = bytes(reversed(grezzo))

    pak = bytearray()
    catene = {}
    i = 0
    maschera = 0
    pos_flag = -1
    pak_tmp = 0
    raw_tmp = raw_len
    fine = raw_len

    while i < fine:
        if maschera == 0:
            pos_flag = len(pak)
            pak.append(0)
            maschera = 0x80

        len_best = BLZ_SOGLIA
        pos_best = 0
        if i >= 3 and i + 3 <= fine:
            chiave = dati[i:i + 3]
            lista = catene.get(chiave)
            if lista:
                limite = i - BLZ_N
                # le distanze si scorrono dalla piu' grande alla piu' piccola,
                # cioe' i candidati dal piu' vecchio al piu' recente.
                k = 0
                for k, j in enumerate(lista):
                    if j >= limite:
                        break
                else:
                    k = len(lista)
                if k:
                    del lista[:k]
                for j in lista:
                    dist = i - j
                    if dist < 3:
                        break
                    massimo = BLZ_F
                    if fine - i < massimo:
                        massimo = fine - i
                    if dist < massimo:
                        massimo = dist
                    if massimo <= len_best:
                        continue
                    if dati[i + len_best] != dati[j + len_best]:
                        continue
                    m = 0
                    while m < massimo and dati[i + m] == dati[j + m]:
                        m += 1
                    if m > len_best:
                        len_best = m
                        pos_best = dist
                        if m == BLZ_F:
                            break

        if len_best > BLZ_SOGLIA:
            for k in range(len_best):
                if i + k + 3 <= fine:
                    catene.setdefault(dati[i + k:i + k + 3], []).append(i + k)
            i += len_best
            pak[pos_flag] |= maschera
            v = len_best - (BLZ_SOGLIA + 1)
            pak.append(((v << 4) | ((pos_best - 3) >> 8)) & 0xFF)
            pak.append((pos_best - 3) & 0xFF)
        else:
            if i + 3 <= fine:
                catene.setdefault(dati[i:i + 3], []).append(i)
            pak.append(dati[i])
            i += 1

        maschera >>= 1
        if len(pak) + raw_len - i < pak_tmp + raw_tmp:
            pak_tmp = len(pak)
            raw_tmp = raw_len - i

    pak_len = len(pak)
    pak = bytes(reversed(pak))
    # ATTENZIONE: si tengono gli ULTIMI `pak_tmp` byte dell'array INVERTITO
    # (`pak + pak_len - pak_tmp` in `blz.c`), non i primi. Sono i primi `pak_tmp`
    # token prodotti nel dominio rovesciato, rimessi nell'ordine in cui il
    # decodificatore all'indietro li consuma. Prendere i primi produce un flusso
    # che un decodificatore «a buffer separato» decodifica lo stesso ma che
    # referenzia byte MAI SCRITTI: e' il guasto che fa lo schermo nero.
    if pak_tmp == 0 or raw_len + 4 < (((pak_tmp + raw_tmp + 3) & ~3) + 8):
        raise Rifiuto("BLZ: comprimere non conviene (%d B grezzi)" % raw_len)

    out = bytearray()
    out += grezzo[:raw_tmp]
    out += pak[pak_len - pak_tmp:]
    hdr_len = 8
    inc_len = raw_len - pak_tmp - raw_tmp
    while len(out) & 3:
        out.append(0xFF)
        hdr_len += 1
    out += struct.pack("<I", ((pak_tmp + hdr_len) & 0xFFFFFF) | (hdr_len << 24))
    out += struct.pack("<I", (inc_len - hdr_len) & 0xFFFFFFFF)
    return bytes(out)


# --------------------------------------------------------------------- ROM

class Rom:
    """Vista sui byte di una ROM DS. Legge; scrivere e' compito di chi chiama."""

    def __init__(self, dati):
        self.d = bytearray(dati)
        g = lambda o: struct.unpack_from("<I", self.d, o)[0]
        self.arm9_off, self.arm9_ram, self.arm9_len = g(0x20), g(0x28), g(0x2C)
        self.fat_off, self.fat_len = g(0x48), g(0x4C)
        self.ovt9_off, self.ovt9_len = g(0x50), g(0x54)
        self.n_overlay = self.ovt9_len // 32
        self.n_file = self.fat_len // 8

    # -- tabella overlay (32 B per voce, gbatek «ARM9 overlay table») --------
    def voce_overlay(self, oid):
        esigi(0 <= oid < self.n_overlay,
              "overlay %d fuori dalla tabella y9 (%d voci)" % (oid, self.n_overlay))
        off = self.ovt9_off + oid * 32
        (idv, ram, ramsz, bsssz, sis, sie, fid, comp) = struct.unpack_from("<8I", self.d, off)
        return {
            "offset_voce": off, "id": idv, "ram": ram, "ram_size": ramsz,
            "bss_size": bsssz, "static_init_start": sis, "static_init_end": sie,
            "file_id": fid, "parola_comp": comp,
            "dim_compressa": comp & 0xFFFFFF,
            "flag": (comp >> 24) & 0xFF,
            "compresso": bool((comp >> 24) & 1),
            "firmato": bool((comp >> 24) & 2),
        }

    def voce_fat(self, fid):
        esigi(0 <= fid < self.n_file, "file id %d fuori dalla FAT (%d voci)" % (fid, self.n_file))
        off = self.fat_off + fid * 8
        s, e = struct.unpack_from("<II", self.d, off)
        return {"offset_voce": off, "inizio": s, "fine": e, "bytes": e - s}

    def file_bytes(self, fid):
        f = self.voce_fat(fid)
        return bytes(self.d[f["inizio"]:f["fine"]])

    def capienza_slot(self, fid):
        """Byte disponibili per il file `fid` senza spostare nessun altro file:
        dal suo inizio al primo inizio di file successivo (o alla fine della ROM)."""
        f = self.voce_fat(fid)
        prossimo = len(self.d)
        for i in range(self.n_file):
            s, e = struct.unpack_from("<II", self.d, self.fat_off + i * 8)
            if e == 0 and s == 0:
                continue
            if s > f["inizio"] and s < prossimo:
                prossimo = s
        return prossimo - f["inizio"]

    def immagine_overlay(self, oid):
        """L'overlay decompresso, con il decodificatore A."""
        v = self.voce_overlay(oid)
        crudo = self.file_bytes(v["file_id"])
        if v["compresso"]:
            esigi(v["dim_compressa"] <= len(crudo),
                  "ov%03d: la tabella dichiara %d B compressi ma il file ne ha %d"
                  % (oid, v["dim_compressa"], len(crudo)))
            img = blz_decomprimi(crudo[:v["dim_compressa"]])
        else:
            img = crudo
        return v, crudo, img


# ------------------------------------------------------------ patch e guardia

def _esa(s):
    s = s.strip().replace(" ", "").replace("_", "")
    if s.lower().startswith("0x"):
        s = s[2:]
    esigi(len(s) % 2 == 0, "esadecimale di lunghezza dispari: %r" % s)
    return bytes.fromhex(s)


def analizza_guardia(spec):
    esigi(":" in spec, "guardia malformata (serve INDIRIZZO:ESADECIMALE): %r" % spec)
    a, h = spec.split(":", 1)
    return int(a, 0), _esa(h)


def analizza_patch(spec):
    parti = spec.split(":")
    esigi(len(parti) == 3, "patch malformata (serve INDIRIZZO:PRE:POST): %r" % spec)
    addr = int(parti[0], 0)
    pre, post = _esa(parti[1]), _esa(parti[2])
    esigi(len(pre) == len(post),
          "patch a %#x: preimmagine %d B e postimmagine %d B non combaciano"
          % (addr, len(pre), len(post)))
    esigi(len(pre) > 0, "patch a %#x: preimmagine vuota" % addr)
    return {"addr": addr, "pre": pre, "post": post}


def scegli_overlay(rom, guardie, oid=None):
    """Sceglie l'overlay. Con `oid` dato lo verifica; con `oid` None lo cerca.

    In entrambi i casi la guardia DEVE combaciare: e' il contenuto che decide,
    mai l'indirizzo (cinque overlay contengono 0x0226200C, otto 0x02246C94)."""
    esigi(guardie, "serve almeno una --guardia: l'overlay si sceglie per contenuto")
    candidati = []
    for i in range(rom.n_overlay):
        v = rom.voce_overlay(i)
        if not all(v["ram"] <= a and a + len(h) <= v["ram"] + v["ram_size"] for a, h in guardie):
            continue
        try:
            _, _, img = rom.immagine_overlay(i)
        except Rifiuto:
            continue
        if all(img[a - v["ram"]:a - v["ram"] + len(h)] == h for a, h in guardie):
            candidati.append(i)
    if oid is None:
        esigi(len(candidati) == 1,
              "la guardia non individua un overlay solo: candidati %s" % (candidati,))
        return candidati[0], candidati
    esigi(oid in candidati,
          "l'overlay %d NON supera la guardia (la superano: %s)" % (oid, candidati))
    return oid, candidati


# ------------------------------------------------------------- applicazione

def applica(dati_rom, oid, guardie, patch, strategia="auto", ricevuta=None,
            forza_ricompressione=False, consenti_riloco=False):
    """Ritorna (byte della ROM di uscita, ricevuta dict).

    `strategia`:
      * `a`    — ricomprimi BLZ (l'overlay resta compresso);
      * `b`    — scrivi decompresso e spegni il bit 24 nella tabella y9;
      * `auto` — `a` se il flusso ricompresso entra nello spazio disponibile,
                 altrimenti `a` con riloco in coda; `b` solo se richiesta.
    """
    rom = Rom(dati_rom)
    r = ricevuta if ricevuta is not None else {}
    r["strumento"] = "SGP-1.2-OVERLAY-01/tools/overlay_patch.py"
    r["ingresso_sha256"] = sha(dati_rom)
    r["ingresso_bytes"] = len(dati_rom)
    r["cancelli"] = {}

    # -- C1: overlay scelto/verificato per guardia -------------------------
    scelto, candidati = scegli_overlay(rom, guardie, oid)
    v, crudo, img = rom.immagine_overlay(scelto)
    r["cancelli"]["C1_guardia"] = {
        "overlay": scelto, "candidati": candidati,
        "guardie": [{"addr": hex(a), "bytes": len(h), "hex": h.hex()} for a, h in guardie],
    }
    r["overlay"] = {
        "id": scelto, "file_id": v["file_id"], "ram": hex(v["ram"]),
        "ram_size": v["ram_size"], "bss_size": v["bss_size"],
        "compresso_in_ingresso": v["compresso"], "flag_in_ingresso": v["flag"],
        "dim_compressa_dichiarata": v["dim_compressa"],
        "file_bytes_in_ingresso": len(crudo),
        "immagine_bytes": len(img), "immagine_sha256_prima": sha(img),
    }

    # -- C2: coerenza della voce ------------------------------------------
    esigi(v["id"] == scelto, "C2: la voce %d dichiara id %d" % (scelto, v["id"]))
    esigi(len(img) == v["ram_size"],
          "C2: l'immagine decompressa e' %d B ma ram_size dichiara %d"
          % (len(img), v["ram_size"]))
    if v["compresso"]:
        t = blz_leggi_trailer(crudo[:v["dim_compressa"]])
        r["overlay"]["trailer_blz_ingresso"] = {
            "hdr_len": t[0], "enc_len": t[1], "inc_len": t[2],
            "prefisso_grezzo": t[3], "dim_decompressa": t[4]}

    # -- C3: preimmagini ---------------------------------------------------
    nuova = bytearray(img)
    scritture = []
    for p in patch:
        off = p["addr"] - v["ram"]
        esigi(0 <= off and off + len(p["pre"]) <= len(img),
              "C3: la patch a %#x non sta dentro ov%03d [%#x,%#x)"
              % (p["addr"], scelto, v["ram"], v["ram"] + v["ram_size"]))
        trovato = bytes(nuova[off:off + len(p["pre"])])
        esigi(trovato == p["pre"],
              "C3 PREIMMAGINE: a %#x c'e' %s, attesa %s. O la ROM non e' quella, "
              "o la patch e' gia' applicata (idempotenza), o la preimmagine e' sbagliata."
              % (p["addr"], trovato.hex(), p["pre"].hex()))
        nuova[off:off + len(p["post"])] = p["post"]
        scritture.append({"addr": hex(p["addr"]), "offset_nel_modulo": off,
                          "bytes": len(p["pre"]),
                          "prima": p["pre"].hex(), "dopo": p["post"].hex()})
    r["patch"] = scritture
    r["overlay"]["immagine_sha256_dopo"] = sha(nuova)

    # -- costruzione del nuovo corpo del file ------------------------------
    capienza = rom.capienza_slot(v["file_id"])
    fat = rom.voce_fat(v["file_id"])
    r["overlay"]["slot_bytes"] = capienza
    r["overlay"]["fat_in_ingresso"] = [hex(fat["inizio"]), hex(fat["fine"])]

    invariato = bytes(nuova) == bytes(img)
    if strategia in ("a", "auto"):
        if invariato and not forza_ricompressione:
            # niente e' cambiato: non si tocca un byte. E' la regola giusta
            # (idempotenza) ed e' anche cio' che rende il giro a vuoto
            # IDENTICO AL BYTE.
            corpo = bytes(crudo)
            modo = "a-corpo-originale (immagine invariata)"
        else:
            corpo = blz_comprimi_ottimo(bytes(nuova), bersaglio=len(crudo))
            # round-trip con il decodificatore A, in luogo come fa il gioco
            esigi(blz_decomprimi(corpo) == bytes(nuova),
                  "C4: decompresso -> ricompresso -> decompresso NON coincide")
            t = blz_leggi_trailer(corpo)
            r["cancelli"]["C4_roundtrip_blz"] = {
                "compresso_bytes": len(corpo), "hdr_len": t[0], "enc_len": t[1],
                "inc_len": t[2], "prefisso_grezzo": t[3], "dim_decompressa": t[4],
                "identico": True,
                "bersaglio": len(crudo), "bersaglio_centrato": len(corpo) == len(crudo)}
            modo = "a-ricompresso"
        # Il bit «compresso» descrive i BYTE SCRITTI, non la strategia: nel
        # ramo «corpo originale» si riscrive il file com'era, quindi su un
        # overlay non compresso il bit deve restare spento (difetto A1 della
        # revisione R1: accenderlo fa chiamare MIi_UncompressBackward su
        # codice in chiaro).
        nuovo_flag = ((v["flag"] | 1) if (modo == "a-ricompresso" or v["compresso"])
                      else (v["flag"] & ~1)) & 0xFF
    elif strategia == "b":
        corpo = bytes(nuova)
        nuovo_flag = v["flag"] & ~1 & 0xFF
        modo = "b-decompresso"
    else:
        raise Rifiuto("strategia sconosciuta: %r" % strategia)

    esigi(len(corpo) <= 0xFFFFFF,
          "la dimensione da scrivere nella voce y9 (%d) non entra in 24 bit" % len(corpo))

    out = bytearray(rom.d)
    cambiati = []

    if len(corpo) <= capienza:
        inizio = fat["inizio"]
        vecchi = fat["bytes"]
        out[inizio:inizio + len(corpo)] = corpo
        # se il nuovo corpo e' piu' corto del vecchio, i byte liberati tornano al
        # riempimento della ROM (0xFF). Oltre il vecchio corpo non si tocca nulla:
        # cosi' un corpo identico lascia la ROM identica al byte.
        if len(corpo) < vecchi:
            out[inizio + len(corpo):inizio + vecchi] = b"\xFF" * (vecchi - len(corpo))
        toccati_fino = inizio + max(len(corpo), vecchi)
        cambiati.append(("corpo overlay", inizio, toccati_fino))
        collocazione = "in luogo"
    else:
        esigi(consenti_riloco,
              "C6: il corpo nuovo e' %d B e lo slot del file ne tiene %d. Rilocare "
              "l'overlay in coda NON e' sicuro: la NitroSDK tiene la FAT in RAM "
              "(letta a freddo all'avvio), mentre la voce y9 la rilegge dalla "
              "cartuccia a ogni caricamento; misurato il 12/09 (RAPPORTO §3). "
              "Serve un corpo che entri nello slot." % (len(corpo), capienza))
        while len(out) % 512:
            out.append(0xFF)
        inizio = len(out)
        out += corpo
        cambiati.append(("corpo overlay (in coda)", inizio, inizio + len(corpo)))
        collocazione = "rilocato in coda (NON RACCOMANDATO)"

    fine = inizio + len(corpo)
    struct.pack_into("<II", out, fat["offset_voce"], inizio, fine)
    cambiati.append(("voce FAT", fat["offset_voce"], fat["offset_voce"] + 8))
    nuova_parola = (len(corpo) & 0xFFFFFF) | (nuovo_flag << 24)
    if modo != "a-corpo-originale (immagine invariata)":
        struct.pack_into("<I", out, v["offset_voce"] + 28, nuova_parola)
        cambiati.append(("voce y9 (dim+flag)", v["offset_voce"] + 28, v["offset_voce"] + 32))
    # Nel ramo «corpo originale» sopra la parola NON si tocca, nemmeno quando
    # il valore calcolato (`nuova_parola`) differisce da quello gia' in ROM.
    # Su un overlay non compresso i 24 bit bassi di questa parola sono la
    # dimensione compressa: il caricatore li ignora quando il bit «compresso»
    # e' spento (letto sopra da `v["compresso"]`), quindi puo' restare
    # qualunque valore lasci l'utensile che ha prodotto la ROM originale — su
    # ov035 della base 1.1 EN e' 0, non la vera lunghezza. Scriverci la
    # lunghezza vera comunque non e' scorretto per il gioco, ma rompe la
    # promessa sopra ("niente e' cambiato: non si tocca un byte"): un giro a
    # vuoto smetteva di essere identico al byte per un byte che il gioco non
    # legge mai in questo stato. Trovato da TestFlagCompresso su quell'overlay.

    # header: dimensione usata, capienza della cartuccia, CRC
    usato_prima = struct.unpack_from("<I", rom.d, 0x80)[0]
    usato = max(usato_prima, fine)
    if usato != usato_prima:
        struct.pack_into("<I", out, 0x80, usato)
        cambiati.append(("header total_used", 0x80, 0x84))
    cap = rom.d[0x14]
    while len(out) > (0x20000 << cap):
        cap += 1
    esigi(cap <= 12, "l'uscita supera il limite di 512 MiB della cartuccia")
    if cap != rom.d[0x14]:
        out[0x14] = cap
        cambiati.append(("header capienza", 0x14, 0x15))
    nuovo_crc = crc16(bytes(out[:0x15E]))
    if nuovo_crc != struct.unpack_from("<H", rom.d, 0x15E)[0]:
        struct.pack_into("<H", out, 0x15E, nuovo_crc)
        cambiati.append(("header CRC16", 0x15E, 0x160))

    r["strategia"] = {"chiesta": strategia, "usata": modo, "collocazione": collocazione,
                      "corpo_bytes": len(corpo), "flag_y9": nuovo_flag,
                      "parola_y9": hex(nuova_parola)}
    r["regioni_cambiate"] = [{"cosa": c, "da": hex(a), "a": hex(b), "bytes": b - a}
                             for c, a, b in cambiati]

    # -- C5: tutto il resto della ROM e' identico al byte ------------------
    coperto = [(a, b) for _, a, b in cambiati]
    diversi = []
    n = min(len(rom.d), len(out))
    da = 0
    for a, b in sorted(coperto):
        if a > da:
            if rom.d[da:min(a, n)] != out[da:min(a, n)]:
                diversi.append((da, min(a, n)))
        da = max(da, b)
    if da < n and rom.d[da:n] != out[da:n]:
        diversi.append((da, n))
    esigi(not diversi,
          "C5: la ROM cambia FUORI dalle regioni dichiarate: %s" % (diversi,))
    r["cancelli"]["C5_resto_identico"] = {
        "regioni_dichiarate": len(cambiati),
        "byte_aggiunti_in_coda": len(out) - len(rom.d),
        "byte_diversi_fuori": 0}

    r["uscita_bytes"] = len(out)
    r["uscita_sha256"] = sha(out)
    return bytes(out), r


# --------------------------------------------------------------------- CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--overlay", required=True,
                    help="id dell'overlay, oppure `auto` per sceglierlo per guardia")
    ap.add_argument("--guardia", action="append", default=[], metavar="ADDR:HEX",
                    help="byte che l'overlay DEVE avere a quell'indirizzo (ripetibile)")
    ap.add_argument("--patch", action="append", default=[], metavar="ADDR:PRE:POST",
                    help="una patch di byte (ripetibile)")
    ap.add_argument("--strategia", choices=("auto", "a", "b"), default="auto")
    ap.add_argument("--forza-ricompressione", action="store_true",
                    help="ricomprimi anche se le patch non cambiano nessun byte "
                         "(serve ai collaudi, non al lavoro normale)")
    ap.add_argument("--consenti-riloco", action="store_true",
                    help="permetti di rilocare l'overlay in coda se non entra nello "
                         "slot. NON sicuro: vedi RAPPORTO §3")
    ap.add_argument("--json", default=None, help="dove scrivere la ricevuta")
    ap.add_argument("--zitto", action="store_true")
    a = ap.parse_args(argv)

    oid = None if a.overlay.strip().lower() == "auto" else int(a.overlay, 0)
    guardie = [analizza_guardia(s) for s in a.guardia]
    patch = [analizza_patch(s) for s in a.patch]

    dati = Path(a.rom).read_bytes()
    out, r = applica(dati, oid, guardie, patch, a.strategia,
                     forza_ricompressione=a.forza_ricompressione,
                     consenti_riloco=a.consenti_riloco)
    r["ingresso"] = a.rom
    r["uscita"] = a.out
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_bytes(out)
    testo = json.dumps(r, indent=2, ensure_ascii=False) + "\n"
    if a.json:
        Path(a.json).write_text(testo)
    if not a.zitto:
        print(testo)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Rifiuto as e:
        print("RIFIUTO: %s" % e, file=sys.stderr)
        raise SystemExit(2)
