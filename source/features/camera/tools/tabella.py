#!/usr/bin/env python3
"""La tabella delle eccezioni camera: definizione unica, codifica e decodifica.

Un solo posto definisce le 68 voci (16 della 1.1 + 8 della 1.2 + 44 della 1.2.3).  L'applicatore e il rilettore la usano, ma il
rilettore ricontrolla comunque la forma sui byte letti dalla ROM d'uscita.
"""
import struct

# le 16 voci gia' presenti nella 1.1 spedita (lette dai byte, non copiate)
VECCHIE = {2: 4, 4: 4, 5: 4, 135: 1, 176: 0, 221: 3, 226: 4, 239: 10,
           244: 12, 282: 7, 340: 13, 379: 3, 396: 12, 404: 4, 486: 10, 526: 10}

# le 8 di C1 (1.2): Monte Scodella -> profilo 0, negozio/covo di Mogania -> profilo 4
NUOVE_1_2 = {119: 0, 250: 0, 251: 0, 252: 0, 116: 4, 247: 4, 248: 4, 249: 4}

# le 44 della 1.2.3 (perimetro B): grotte fra Johto e Kanto, grotte di Kanto e
# grotte «vere» di Johto, tutte riportate al loro cameraType NATIVO (0).
NUOVE_1_2_3 = {
    99: 0, 106: 0, 107: 0, 108: 0, 114: 0, 120: 0, 121: 0, 122: 0,
    123: 0, 124: 0, 125: 0, 126: 0, 145: 0, 146: 0, 153: 0, 154: 0,
    177: 0, 178: 0, 179: 0, 181: 0, 237: 0, 238: 0, 242: 0, 243: 0,
    253: 0, 298: 0, 342: 0, 448: 0, 450: 0, 451: 0, 452: 0, 453: 0,
    454: 0, 455: 0, 456: 0, 457: 0, 458: 0, 459: 0, 460: 0, 461: 0,
    462: 0, 463: 0, 464: 0, 465: 0,
}

NUOVE = dict(NUOVE_1_2)
NUOVE.update(NUOVE_1_2_3)

NOMI = {
    99: 'MAP_UNION_CAVE_1F',
    106: 'MAP_DIGLETT_CAVE',
    107: 'MAP_MOUNT_MOON',
    108: 'MAP_ROCK_TUNNEL_1F',
    114: 'MAP_SLOWPOKE_WELL_ENTRANCE',
    116: 'MAP_MAHOGANY_SOUVENIR_SHOP',
    119: 'MAP_MOUNT_MORTAR_1F_ENTRANCE',
    120: 'MAP_ICE_PATH_1F',
    121: 'MAP_WHIRL_ISLANDS_1F',
    122: 'MAP_MOUNT_SILVER_CAVE_1F',
    123: 'MAP_DARK_CAVE_ROUTE_45_SIDE',
    124: 'MAP_VICTORY_ROAD_1F',
    125: 'MAP_DRAGONS_DEN_ENTRANCE',
    126: 'MAP_TOHJO_FALLS',
    145: 'MAP_CERULEAN_CAVE_1F',
    146: 'MAP_SEAFOAM_ISLANDS_1F',
    153: 'MAP_UNION_CAVE_B1F',
    154: 'MAP_UNION_CAVE_B2F',
    177: 'MAP_SLOWPOKE_WELL_B1F',
    178: 'MAP_VICTORY_ROAD_2F',
    179: 'MAP_VICTORY_ROAD_3F',
    181: 'MAP_SLOWPOKE_WELL_B2F',
    237: 'MAP_ICE_PATH_B1F',
    238: 'MAP_ICE_PATH_B2F',
    242: 'MAP_WHIRL_ISLANDS_B1F',
    243: 'MAP_WHIRL_ISLANDS_B2F',
    247: 'MAP_TEAM_ROCKET_HEADQUARTERS_B1F',
    248: 'MAP_TEAM_ROCKET_HEADQUARTERS_B2F',
    249: 'MAP_TEAM_ROCKET_HEADQUARTERS_B3F',
    250: 'MAP_MOUNT_MORTAR_1F_BACK',
    251: 'MAP_MOUNT_MORTAR_2F',
    252: 'MAP_MOUNT_MORTAR_B1F',
    253: 'MAP_DRAGONS_DEN',
    298: 'MAP_TOHJO_FALLS_HIDDEN_ROOM',
    342: 'MAP_CLIFF_CAVE',
    448: 'MAP_MOUNT_MOON_SQUARE_ENTRANCE',
    450: 'MAP_CERULEAN_CAVE_2F',
    451: 'MAP_CERULEAN_CAVE_B1F',
    452: 'MAP_ROCK_TUNNEL_B1F',
    453: 'MAP_SEAFOAM_ISLANDS_B1F',
    454: 'MAP_SEAFOAM_ISLANDS_B2F',
    455: 'MAP_SEAFOAM_ISLANDS_B3F',
    456: 'MAP_SEAFOAM_ISLANDS_B4F',
    457: 'MAP_SEAFOAM_ISLANDS_CINNABAR_GYM',
    458: 'MAP_SEAFOAM_ISLANDS_UNUSED',
    459: 'MAP_MOUNT_SILVER_CAVE_UPPER_MOUNTAINSIDE',
    460: 'MAP_MOUNT_SILVER_CAVE_LOWER_MOUNTAINSIDE',
    461: 'MAP_MOUNT_SILVER_CAVE_EXPERT_BELT_CHAMBER',
    462: 'MAP_MOUNT_SILVER_CAVE_MOLTRES_CHAMBER',
    463: 'MAP_MOUNT_SILVER_CAVE_2F',
    464: 'MAP_MOUNT_SILVER_CAVE_3F',
    465: 'MAP_MOUNT_SILVER_CAVE_SUMMIT',
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
