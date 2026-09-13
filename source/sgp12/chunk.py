#!/usr/bin/env python3
"""sgp12.chunk — il chunk di salvataggio pubblico 1.2 (CONTRATTO-CHUNK.md,
`SGP-1.2-PLUS-03/CONTRATTO-CHUNK.md`, cantiere D1).

Un solo posto per gli offset che OPZIONI-03, NPC-02, ANIM-B e WIFI-01 leggono e
scrivono (prima ogni cantiere li aveva ricopiati a mano nei propri commenti,
mai in un formato verificabile). Qui vive **solo il formato dei dati**: la
copia in RAM a 0x023D8710 e il footer su disco a settore 47/111. Nessuna
logica ARM9/overlay: quella resta nei singoli blocchi.

Layout dei 16 byte a 0x023D8710 (CONTRATTO-CHUNK.md §2):

    +0x0  magic       u16 LE   0x5347 ('SG')
    +0x2  versione    u8       1..2 (oggi 2)
    +0x3  plus        u8       0/1   (D1)
    +0x4  selvatici   u8       0/1   (D1)
    +0x5  oltre100    u8       0/1   (D1, riservato 1.2b)
    +0x6  anim        u8       0/1   (A1-B)
    +0x7  npc         u8       0/1   (P2)
    +0x8  wifi_server u8       0..3  (W1)
    +0x9  picco       u8       1..100 (1..150 se oltre100)
    +0xA  riservato0  u8       0
    +0xB  riservato1  u8       0
    +0xC  riservato2  u32 LE   0
"""
from __future__ import annotations

import struct
from dataclasses import dataclass

from .rom import crc16

# --- indirizzi RAM (CONTRATTO-CHUNK.md §1) ---------------------------------
STATO_BASE = 0x023D8700         # sgp.plus +0x600, 32 B
CHUNK_RAM = 0x023D8710          # copia in RAM del chunk, 16 B
CHUNK_RAM_BYTES = 16
CODICE_BASE = 0x023D8730        # 460 B
BUFFER_BASE = 0x023D8F00        # sgp.salvataggio, 32 B
CANARINO_SALVATAGGIO = 0x023D8FF0

MAGIC = 0x5347
VERSIONE_CORRENTE = 2
FOOTER_MAGIC = 0x32504753        # 'SGP2' (diverso dal magic 0x20060623 del gioco)

_STRUCT = struct.Struct("<HBBBBBBBBBBI")   # magic,versione,plus,selvatici,oltre100,
                                            # anim,npc,wifi_server,picco,ris0,ris1,ris2
assert _STRUCT.size == CHUNK_RAM_BYTES


class ChunkNonValido(Exception):
    pass


@dataclass
class Chunk:
    magic: int = MAGIC
    versione: int = VERSIONE_CORRENTE
    plus: int = 0
    selvatici: int = 0
    oltre100: int = 0
    anim: int = 0
    npc: int = 0
    wifi_server: int = 0
    picco: int = 1
    riservato0: int = 0
    riservato1: int = 0
    riservato2: int = 0

    def pack(self) -> bytes:
        return _STRUCT.pack(self.magic, self.versione, self.plus, self.selvatici,
                            self.oltre100, self.anim, self.npc, self.wifi_server,
                            self.picco, self.riservato0, self.riservato1, self.riservato2)

    @classmethod
    def unpack(cls, dati: bytes) -> "Chunk":
        if len(dati) != CHUNK_RAM_BYTES:
            raise ChunkNonValido("il chunk misura %d B, attesi %d" % (len(dati), CHUNK_RAM_BYTES))
        return cls(*_STRUCT.unpack(dati))

    def invarianti(self):
        """Le regole di CONTRATTO-CHUNK.md §6. Ritorna la lista dei motivi di rifiuto
        (vuota se il chunk e' valido)."""
        motivi = []
        if self.magic != MAGIC:
            motivi.append("magic 0x%04X, atteso 0x%04X" % (self.magic, MAGIC))
        if not (1 <= self.versione <= 2):
            motivi.append("versione %d fuori da 1..2" % self.versione)
        for nome in ("plus", "selvatici", "oltre100", "anim", "npc"):
            v = getattr(self, nome)
            if v not in (0, 1):
                motivi.append("%s=%d non e' 0/1" % (nome, v))
        if not (0 <= self.wifi_server <= 3):
            motivi.append("wifi_server=%d fuori da 0..3" % self.wifi_server)
        if self.riservato0 != 0 or self.riservato1 != 0 or self.riservato2 != 0:
            motivi.append("un campo riservato non e' zero")
        tetto = 150 if self.oltre100 else 100
        if not (1 <= self.picco <= tetto):
            motivi.append("picco=%d fuori da 1..%d" % (self.picco, tetto))
        return motivi

    def valido(self) -> bool:
        return not self.invarianti()


def chunk_assente() -> Chunk:
    """CONTRATTO-CHUNK.md §4: chunk assente = tutti i campi a 0 tranne `picco=1`,
    cioe' byte-identico al comportamento 1.1."""
    return Chunk(picco=1)


# --------------------------------------------------------- footer su disco

_FOOTER = struct.Struct("<IIIHH")   # magic, saveno, size, idx, crc


def calcola_crc_gioco(dati: bytes) -> int:
    """`GF_CalcCRC16` (0x0201FF98): stesso CRC16 dell'header di cartuccia DS
    (tabella a nibble, polinomio 0x8408), su un seme 0xFFFF — vedi `sgp12.rom.crc16`."""
    return crc16(dati)


def pack_footer(payload: bytes, saveno: int, idx: int) -> bytes:
    if len(payload) != CHUNK_RAM_BYTES:
        raise ChunkNonValido("payload di %d B, attesi %d" % (len(payload), CHUNK_RAM_BYTES))
    size = len(payload)
    corpo = payload + struct.pack("<II", FOOTER_MAGIC, saveno) + struct.pack("<I", size)
    # il CRC copre size+14 byte: payload(16) + magic(4) + saveno(4) + size(4) + idx(2) = 30
    coperto = corpo + struct.pack("<H", idx)
    crc = calcola_crc_gioco(coperto)
    return coperto + struct.pack("<H", crc)


def unpack_footer(settore: bytes) -> Chunk:
    """Decodifica i 32 byte di un settore (16 payload + 16 footer, CONTRATTO-CHUNK.md
    §5) e SOLLEVA `ChunkNonValido` se magic/CRC/invarianti non tornano — non prova
    a "riparare" niente: il chiamante decide se e' `load_status=REJECT`."""
    if len(settore) != 32:
        raise ChunkNonValido("settore di %d B, attesi 32" % len(settore))
    payload = settore[:16]
    magic, saveno, size, idx, crc = _FOOTER.unpack(settore[16:])
    if magic != FOOTER_MAGIC:
        raise ChunkNonValido("footer.magic 0x%08X, atteso 0x%08X" % (magic, FOOTER_MAGIC))
    coperto = payload + struct.pack("<II", magic, saveno) + struct.pack("<IH", size, idx)
    atteso = calcola_crc_gioco(coperto)
    if crc != atteso:
        raise ChunkNonValido("footer.crc 0x%04X, atteso 0x%04X" % (crc, atteso))
    chunk = Chunk.unpack(payload)
    motivi = chunk.invarianti()
    if motivi:
        raise ChunkNonValido("; ".join(motivi))
    return chunk


# --- settori del salvataggio (CONTRATTO-CHUNK.md §5) -----------------------
# Settore 47 e la sua copia al 111, 32 byte ciascuno (16 payload + 16 footer).
SETTORE_PRIMARIO = 47
SETTORE_COPIA = 111
SETTORE_BYTES = 32
SETTORE_OFFSET_PRIMARIO = 0x2F000
SETTORE_OFFSET_COPIA = 0x6F000
