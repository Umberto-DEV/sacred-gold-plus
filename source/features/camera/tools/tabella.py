#!/usr/bin/env python3
"""La tabella delle eccezioni camera: definizione unica, codifica e decodifica.

Un solo posto definisce le 24 voci.  L'applicatore e il rilettore la usano, ma il
rilettore ricontrolla comunque la forma sui byte letti dalla ROM d'uscita.
"""
import struct

# le 16 voci gia' presenti nella 1.1 spedita (lette dai byte, non copiate)
VECCHIE = {2: 4, 4: 4, 5: 4, 135: 1, 176: 0, 221: 3, 226: 4, 239: 10,
           244: 12, 282: 7, 340: 13, 379: 3, 396: 12, 404: 4, 486: 10, 526: 10}

# le 8 nuove di C1: Monte Scodella -> profilo 0, negozio/covo di Mogania -> profilo 4
NUOVE = {119: 0, 250: 0, 251: 0, 252: 0, 116: 4, 247: 4, 248: 4, 249: 4}

NOMI = {
    119: 'MAP_MOUNT_MORTAR_1F_ENTRANCE', 250: 'MAP_MOUNT_MORTAR_1F_BACK',
    251: 'MAP_MOUNT_MORTAR_2F', 252: 'MAP_MOUNT_MORTAR_B1F',
    116: 'MAP_MAHOGANY_SOUVENIR_SHOP', 247: 'MAP_TEAM_ROCKET_HEADQUARTERS_B1F',
    248: 'MAP_TEAM_ROCKET_HEADQUARTERS_B2F', 249: 'MAP_TEAM_ROCKET_HEADQUARTERS_B3F',
}

CANONICA = dict(VECCHIE)
CANONICA.update(NUOVE)
PLUS_DEFAULT = 11
N_MAPPE = 540


def controlla(t):
    """Forma della tabella (G5 / R3).  Ritorna la lista di motivi di rifiuto."""
    motivi = []
    for k, v in sorted(t.items()):
        if not (0 <= k < N_MAPPE):
            motivi.append('id %d fuori da [0,%d)' % (k, N_MAPPE))
        if not (0 <= v < 16):
            motivi.append('valore %d dell\'id %d fuori da [0,16)' % (v, k))
    voci = [(k << 4) | v for k, v in sorted(t.items())]
    if any(voci[i] >= voci[i + 1] for i in range(len(voci) - 1)):
        motivi.append('voci non strettamente crescenti come u16')
    chiavi = sorted(t)
    if any(chiavi[i] == chiavi[i + 1] for i in range(len(chiavi) - 1)):
        motivi.append('id ripetuto')
    for i in range(len(chiavi) - 1):
        if (chiavi[i + 1] << 4) - (chiavi[i] << 4) < 16:
            motivi.append('id %d e %d nello stesso blocco di 16: ricerca ambigua'
                          % (chiavi[i], chiavi[i + 1]))
    if any(x > 0xFFFF for x in voci):
        motivi.append('voce oltre 16 bit')
    return motivi


def codifica(t):
    voci = sorted((k << 4) | v for k, v in t.items())
    return struct.pack('<%dH' % len(voci), *voci)


def decodifica(b):
    voci = struct.unpack('<%dH' % (len(b) // 2), b)
    return {x >> 4: x & 15 for x in voci}, list(voci)
