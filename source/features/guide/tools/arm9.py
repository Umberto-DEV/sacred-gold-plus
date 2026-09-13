#!/usr/bin/env python3
"""Copia verbatim di source/features/camera/tools/arm9.py (13/09/2026),
riusata qui (lettura e scrittura, come in ANIM-SOLIDO-01/CAMERA-01) per SGP-1.2-GUIDA-EVIV-02.
Nessuna modifica al file originale.

Lettore/scrittore dell'ARM9 di una ROM NDS per indirizzo RAM.

Scritto da zero per questo pacchetto: non importa ndspy, non importa nessuno
strumento della 1.1.  Cammina i «module params» a 0xBA0 dell'ARM9 statico per
ricavare le sezioni di autoload, esattamente come fa il caricatore del gioco,
e mappa ogni indirizzo RAM sull'offset nel FILE .nds.

Nessun byte di ROM viene mai stampato da questo modulo: e' una libreria.
"""
import struct
from pathlib import Path


class Arm9:
    def __init__(self, path):
        self.path = Path(path)
        self.raw = bytearray(self.path.read_bytes())
        self.off9 = struct.unpack_from('<I', self.raw, 0x20)[0]
        self.ram9 = struct.unpack_from('<I', self.raw, 0x28)[0]
        self.siz9 = struct.unpack_from('<I', self.raw, 0x2C)[0]
        # parametri di modulo: 9 parole a 0xBA0 dentro l'ARM9 statico
        f = struct.unpack_from('<9I', self.raw, self.off9 + 0xBA0)
        self.tab0, self.tab1, self.dati0 = f[0], f[1], f[2]
        self.sezioni = []
        p = self.off9 + (self.tab0 - self.ram9)
        fine = self.off9 + (self.tab1 - self.ram9)
        while p < fine:
            self.sezioni.append(struct.unpack_from('<3I', self.raw, p))  # ram, size, bss
            p += 12
        # segmenti (ram, offset_file, bytes)
        self.segmenti = [(self.ram9, self.off9, self.dati0 - self.ram9)]
        off = self.off9 + (self.dati0 - self.ram9)
        for ram, size, _bss in self.sezioni:
            self.segmenti.append((ram, off, size))
            off += size

    # --- traduzione indirizzi -------------------------------------------------
    def off(self, ram, n=1):
        for base, o, size in self.segmenti:
            if base <= ram and ram + n <= base + size:
                return o + (ram - base)
        raise KeyError('0x%08X+%d non e\' dentro nessun segmento ARM9' % (ram, n))

    def leggi(self, ram, n):
        o = self.off(ram, n)
        return bytes(self.raw[o:o + n])

    def scrivi(self, ram, dati):
        o = self.off(ram, len(dati))
        self.raw[o:o + len(dati)] = dati

    def u32(self, ram):
        return struct.unpack('<I', self.leggi(ram, 4))[0]

    def u16(self, ram):
        return struct.unpack('<H', self.leggi(ram, 2))[0]

    def salva(self, path):
        Path(path).write_bytes(bytes(self.raw))

    # --- ricerca di parole nell'ARM9 statico ----------------------------------
    def cerca_parola(self, valore):
        """Ritorna gli indirizzi RAM dell'ARM9 STATICO che contengono `valore`."""
        ago = struct.pack('<I', valore)
        base, o, size = self.segmenti[0]
        blob = self.raw[o:o + size]
        fuori, i = [], 0
        while True:
            i = blob.find(ago, i)
            if i < 0:
                break
            if i % 4 == 0:
                fuori.append(base + i)
            i += 1
        return fuori
