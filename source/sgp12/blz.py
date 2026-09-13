#!/usr/bin/env python3
"""sgp12.blz — codec BLZ (compressione ARM9/overlay della NitroSDK).

Trascrizione fedele, invariata, di `SGP-1.2-OVERLAY-01/tools/overlay_patch.py`
(la stessa copia, identica byte per byte via `shasum`, viveva anche dentro
ANIM-B-02/03, PRESTAZIONI-NPC-02/03 e OPZIONI-02): qui vive una volta sola.

BLZ si decomprime ALL'INDIETRO e IN LUOGO con `MIi_UncompressBackward`, che
legge gli ultimi 8 byte del flusso:

    word0 = (hdr_len << 24) | enc_len      word1 = inc_len

con, detto `n` la dimensione del flusso compresso e `bottom` il suo indirizzo
finale in RAM:

    dest_fine = bottom + inc_len          (fine dell'immagine decompressa)
    src       = bottom - hdr_len          (primo byte codificato, si scende)
    stop      = bottom - enc_len          (sotto c'e' il prefisso NON codificato)

Il flusso e' un LZ77 «rovesciato»: si comprime la sequenza invertita, e il
risultato si reinverte. Distanze 3..0x1002, lunghezze 3..0x12, soglia 2.
"""
from __future__ import annotations

import struct

from .rom import Rifiuto, esigi

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
    non maggiore della distanza come in `blz.c`: niente sovrapposizioni)."""
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
    letterale 8/8 + 1/8 di bit di bandiera = 9; una coppia 16/8 + 1/8 = 17)."""
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

    Produce sempre uno stream piu' corto di quello prodotto dalla scelta avida
    di `blz.c`: e' cio' che permette di riscrivere l'overlay **in luogo**.

    `bersaglio`: se dato, si cerca un punto di taglio del prefisso grezzo che
    dia ESATTAMENTE quella dimensione, cosi' la voce FAT e la voce y9 non
    cambiano di un byte e nella ROM cambia SOLO il corpo dell'overlay. Se non
    si trova, si ripiega sulla dimensione minima.
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
        k = k_min
        flusso = _confeziona(grezzo, dati, _emetti(dati, scelta, dist_best, k), k)
    return flusso


def blz_comprimi(grezzo):
    """Compressore BLZ AVIDO, l'algoritmo pubblico di `blz.c` di CUE (dominio
    pubblico). Fra piu' riscontri di lunghezza massima vince quello con la
    DISTANZA MAGGIORE (blz.c scorre le distanze dalla piu' grande alla piu'
    piccola aggiornando solo su lunghezza strettamente maggiore)."""
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
