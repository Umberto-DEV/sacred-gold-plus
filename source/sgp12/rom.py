#!/usr/bin/env python3
"""sgp12.rom — lettura/scrittura sicura di una ROM NDS, senza dipendenze esterne.

Consolida in un solo posto quello che prima viveva, IDENTICO byte per byte, in
12 copie di `tools/arm9.py` (SGP-1.2-CAMERA-01, PLUS-02, WIFI-02/03/04/05,
PRESTAZIONI-NPC-02/03, OPZIONI-02/04, ANIM-B-02/03: `shasum` conferma le 12
copie identiche) e nella classe `Rom` di `SGP-1.2-OVERLAY-01/tools/overlay_patch.py`
(copiata identica in altre 5 cartelle: ANIM-B-02/03, PRESTAZIONI-NPC-02/03,
OPZIONI-02).

Due viste sulla stessa ROM:

  * `Arm9`  — indirizzo RAM -> offset file, dentro il solo ARM9 statico
              (cammina i «module params» a 0xBA0, come fa il caricatore).
              Usata dai blocchi che scrivono byte dentro l'ARM9 (riserva,
              camera, npc, anim, opzioni, wifi, plus).
  * `Rom`   — header/FAT/tabella overlay (y9) della ROM intera. Usata da
              `sgp12.overlay` per leggere/riscrivere gli overlay compressi.

Nessuna delle due stampa mai un byte di ROM: sono librerie.
"""
from __future__ import annotations

import hashlib
import struct
from pathlib import Path


class Rifiuto(Exception):
    """Un cancello non e' superato. Niente viene scritto quando questo vola."""


def esigi(condizione, messaggio):
    if not condizione:
        raise Rifiuto(messaggio)


def sha(dati) -> str:
    """sha256 esadecimale di `dati` (era ridefinita, identica, in oltre 15 file
    del laboratorio 1.2: applica_*.py, rileggi_*.py, overlay_patch.py, ...)."""
    return hashlib.sha256(bytes(dati)).hexdigest()


def esigi_manifesto_descrive(man: dict, corpo, chiave: str = "blob",
                             file: str = "blob.bin", blocco: str = "") -> None:
    """Il manifesto deve descrivere il file che gli sta ACCANTO: `byte` e
    `sha256`, tutti e due, e tutti e due giusti.

    M5 della revisione R2, e poi la revisione della 1.2.1: `build/npc/` aveva un
    manifesto che dichiarava uno sha256 diverso dal `blob.bin` che gli stava
    accanto — e diverso dal `SHA256SUMS` della stessa cartella — e nessuno li
    confrontava. La correzione era stata scritta in `blocchi/npc.py`, e solo li'.
    Le altre sei `_carica_build` erano rimaste com'erano: `anim` e `wifi` non
    guardavano affatto il manifesto, `plus` e `npc` lo guardavano SE il campo
    c'era (`if "blob" in man`), cioe' un manifesto senza quel campo passava per
    buono. Sei copie di una regola, con sei livelli di severita' diversi.

    Qui la regola e' una sola e non ha rami: il campo e' OBBLIGATORIO. Un
    manifesto che non dice quanti byte e quale sha256 non descrive niente, e un
    blob senza manifesto che lo descriva e' esattamente quello che questa
    funzione esiste per impedire."""
    dove = ("%s: " % blocco) if blocco else ""
    d = man.get(chiave)
    esigi(isinstance(d, dict),
          "%sBUILD: il manifesto non ha il campo '%s' che descrive %s "
          "(byte + sha256 sono obbligatori)" % (dove, chiave, file))
    atteso_byte, atteso_sha = d.get("byte"), d.get("sha256")
    esigi(isinstance(atteso_byte, int) and isinstance(atteso_sha, str),
          "%sBUILD: il campo '%s' del manifesto deve avere 'byte' (intero) e "
          "'sha256' (stringa): ha %r" % (dove, chiave, sorted(d)))
    esigi(atteso_byte == len(corpo) and atteso_sha == sha(corpo),
          "%sBUILD: %s (%d B, %s) non corrisponde al manifesto (%s B, %s)"
          % (dove, file, len(corpo), sha(corpo)[:16], atteso_byte, str(atteso_sha)[:16]))


# --------------------------------------------------------------------- CRC16

_TBL_CRC16 = (0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
              0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400)


def crc16(dati, crc=0xFFFF) -> int:
    """CRC16 dell'header di cartuccia DS (gbatek, «Header CRC16»)."""
    for b in dati:
        crc = (crc >> 4) ^ _TBL_CRC16[(crc ^ b) & 0xF]
        crc = (crc >> 4) ^ _TBL_CRC16[(crc ^ (b >> 4)) & 0xF]
    return crc & 0xFFFF


# ---------------------------------------------------------------------- ARM9

class Arm9:
    """Lettore/scrittore dell'ARM9 di una ROM NDS per indirizzo RAM.

    Non importa ndspy: cammina i «module params» a 0xBA0 dell'ARM9 statico per
    ricavare le sezioni di autoload, esattamente come fa il caricatore del
    gioco, e mappa ogni indirizzo RAM sull'offset nel FILE .nds.
    """

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

    # --- traduzione indirizzi -------------------------------------------
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

    # --- ricerca di parole nell'ARM9 statico ------------------------------
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


# ----------------------------------------------------------------- ROM (y9)

class Rom:
    """Vista sui byte di una ROM DS: header, FAT, tabella overlay ARM9 (y9).
    Legge; scrivere e' compito di chi chiama (vedi `sgp12.overlay.applica`)."""

    def __init__(self, dati):
        self.d = bytearray(dati)
        g = lambda o: struct.unpack_from("<I", self.d, o)[0]
        self.arm9_off, self.arm9_ram, self.arm9_len = g(0x20), g(0x28), g(0x2C)
        self.fat_off, self.fat_len = g(0x48), g(0x4C)
        self.ovt9_off, self.ovt9_len = g(0x50), g(0x54)
        self.n_overlay = self.ovt9_len // 32
        self.n_file = self.fat_len // 8

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
        """L'overlay decompresso, con il decodificatore A di `sgp12.blz`."""
        from . import blz
        v = self.voce_overlay(oid)
        crudo = self.file_bytes(v["file_id"])
        if v["compresso"]:
            esigi(v["dim_compressa"] <= len(crudo),
                  "ov%03d: la tabella dichiara %d B compressi ma il file ne ha %d"
                  % (oid, v["dim_compressa"], len(crudo)))
            img = blz.blz_decomprimi(crudo[:v["dim_compressa"]])
        else:
            img = crudo
        return v, crudo, img


# ---------------------------------------------------------- esadecimale CLI

def esa(s: str) -> bytes:
    s = s.strip().replace(" ", "").replace("_", "")
    if s.lower().startswith("0x"):
        s = s[2:]
    esigi(len(s) % 2 == 0, "esadecimale di lunghezza dispari: %r" % s)
    return bytes.fromhex(s)


def analizza_guardia(spec: str):
    esigi(":" in spec, "guardia malformata (serve INDIRIZZO:ESADECIMALE): %r" % spec)
    a, h = spec.split(":", 1)
    return int(a, 0), esa(h)


def analizza_patch(spec: str):
    parti = spec.split(":")
    esigi(len(parti) == 3, "patch malformata (serve INDIRIZZO:PRE:POST): %r" % spec)
    addr = int(parti[0], 0)
    pre, post = esa(parti[1]), esa(parti[2])
    esigi(len(pre) == len(post),
          "patch a %#x: preimmagine %d B e postimmagine %d B non combaciano"
          % (addr, len(pre), len(post)))
    esigi(len(pre) > 0, "patch a %#x: preimmagine vuota" % addr)
    return {"addr": addr, "pre": pre, "post": post}


def bl_decode(sito: int, quattro_byte: bytes):
    """Inversa di `bl_thumb`: decodifica una `BL` Thumb-1 a 4 byte nel suo
    bersaglio (bit Thumb azzerato), o None se non e' una BL Thumb-1. Usata da
    `estrai_build.py` per leggere il bersaglio VERO di un gancio già applicato
    in una ROM (mai per applicarlo: quello resta `bl_thumb`)."""
    hi, lo = struct.unpack("<HH", quattro_byte)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if addend & 0x400000:
        addend -= 0x800000
    return (sito + 4 + addend) & 0xFFFFFFFE


def bl_thumb(sito: int, bersaglio: int) -> bytes:
    """Codifica una `BL` Thumb-1 da `sito` a `bersaglio` (era ridefinita,
    identica nella sostanza, in applica_npc.py/applica_anim.py/applica_wifi.py)."""
    delta = (bersaglio & ~1) - (sito + 4)
    esigi(delta % 2 == 0 and -0x400000 <= delta < 0x400000,
          "BL fuori portata: %#x -> %#x (delta %d)" % (sito, bersaglio, delta))
    hi = 0xF000 | ((delta >> 12) & 0x7FF)
    lo = 0xF800 | ((delta >> 1) & 0x7FF)
    return struct.pack("<HH", hi, lo)
