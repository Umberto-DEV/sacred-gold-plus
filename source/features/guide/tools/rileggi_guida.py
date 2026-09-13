#!/usr/bin/env python3
"""RILETTORE INDIPENDENTE — SGP-1.2-GUIDA-EVIV-02.

Non importa `applica_guida.py` ne' `arm9.py`: cammina l'ARM9 con la propria
routine (copiata qui, non condivisa) ed e' l'unico giudice usato dalla
modalita' `--in-luogo` dell'applicatore prima di sostituire la ROM.

La patch e' chirurgica: 96 B a 0x01FF8A1A (dentro `guide_main`, fusa con
`badge_create`), nessun trampolino ne' template Oak toccato (vedi
`applica_guida.py` per la storia completa: la prima versione ricompilava e
rompeva START, questa versione patcha solo 96 byte macchina sulla ROM
spedita, verificato su hg_runtime).

Due usi:
  rileggi_guida.py ROM                    -> stampa solo lo stato: originale|spenta|ignoto
  rileggi_guida.py ROM_BASE ROM_CANDIDATA -> confronta le due, cancelli R0-R4, VERDE/ROSSO

rc: 0 VERDE (o stato singolo stampato) - 2 ROSSO.
GPL-3.0-or-later.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path

PATCH_ADDR = 0x01FF8A1A
PATCH_N = 96
TEXT = 0x01FF9B10
TEXT_SIGNATURE_N = 1098

ORIGINALE_SHA = "9ffbcb8c920f67d2343e16cde7426b57f5a639ebddee956cfe2b240dc6bf9aa9"
SPENTA_SHA = "e9c85f702347a58698951876d43662f5f6690f5dbff0290465a435892e46bf08"
LINGUA_FIRMA = {
    "EN": "5b2061b68b6b471c6043def4e222c893c4b977de4a5389518f8f9f2f77b18188",
    "IT": "c7b977a19f50135526e35fc89ea968f855c652395a923b77d708c2c1187f21cd",
}


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


class _Immagine:
    """Cammina l'autoload ARM9 dall'header .nds, indipendente da arm9.py."""

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
        self.seg = [(ram9, off9, dati0 - ram9)]
        o = off9 + dati0 - ram9
        for ram, size, _bss in self.sez:
            self.seg.append((ram, o, size))
            o += size

    def b(self, ram, n):
        for base, o, size in self.seg:
            if base <= ram and ram + n <= base + size:
                return self.raw[o + ram - base: o + ram - base + n]
        raise KeyError("0x%08X+%d" % (ram, n))

    def off(self, ram, n):
        for base, o, size in self.seg:
            if base <= ram and ram + n <= base + size:
                return o + ram - base
        raise KeyError("0x%08X+%d" % (ram, n))


def riconosci_lingua(img):
    try:
        campione = bytes(img.b(TEXT, TEXT_SIGNATURE_N))
    except KeyError:
        return None
    firma = sha(campione)
    for lingua, attesa in LINGUA_FIRMA.items():
        if firma == attesa:
            return lingua
    return None


def stato_di(img):
    lingua = riconosci_lingua(img)
    regione = bytes(img.b(PATCH_ADDR, PATCH_N))
    s = sha(regione)
    if s == ORIGINALE_SHA:
        stato = "originale"
    elif s == SPENTA_SHA:
        stato = "spenta"
    else:
        stato = "ignoto"
    return {"lingua": lingua, "stato": stato, "regione_sha256": s}


def confronta(base_raw, cand_raw):
    b, c = _Immagine(base_raw), _Immagine(cand_raw)
    esiti, rosso = [], []

    def R(nome, cond, nota):
        esiti.append({"cancello": nome, "esito": "VERDE" if cond else "ROSSO", "nota": nota})
        if not cond:
            rosso.append(nome)

    stato_b, stato_c = stato_di(b), stato_di(c)
    R("R0", stato_b["lingua"] is None or stato_c["lingua"] is None or stato_b["lingua"] == stato_c["lingua"],
      "lingua identica se riconosciuta (la regione patchata non dipende dalla lingua): %s / %s"
      % (stato_b["lingua"], stato_c["lingua"]))
    R("R1", stato_b["stato"] == "originale", "la base e' l'originale spedito (non gia' spenta)")
    R("R2", stato_c["stato"] == "spenta", "la candidata e' riconosciuta come 'spenta'")

    off = c.off(PATCH_ADDR, PATCH_N)
    leciti = set(range(off, off + PATCH_N))
    R("R3", len(b.raw) == len(c.raw), "dimensione della ROM invariata (%d B)" % len(c.raw))
    diversi = [i for i in range(min(len(b.raw), len(c.raw))) if b.raw[i] != c.raw[i]]
    R("R4", 0 < len(diversi) <= PATCH_N and set(diversi) <= leciti,
      "%d byte diversi, tutti dentro la regione dichiarata (%d B)" % (len(diversi), PATCH_N))

    # R5: fuori dall'ARM9 (banner, overlay, filesystem, header) identico.
    fine_b = max(o + size for _r, o, size in b.seg)
    fine_c = max(o + size for _r, o, size in c.seg)
    R("R5", b.raw[:b.off9] + b.raw[fine_b:] == c.raw[:c.off9] + c.raw[fine_c:],
      "fuori dall'ARM9 identico fra base e candidata")

    return {"base": {"sha256": sha(b.raw), **stato_b}, "candidata": {"sha256": sha(c.raw), **stato_c},
            "byte_diversi": len(diversi), "cancelli": esiti,
            "esito": "VERDE" if not rosso else "ROSSO (%s)" % ", ".join(rosso)}


def main():
    if len(sys.argv) == 2:
        raw = Path(sys.argv[1]).read_bytes()
        img = _Immagine(raw)
        stato = stato_di(img)
        print(json.dumps({"rom": sys.argv[1], "sha256": sha(raw), **stato}, indent=2))
        return 0
    if len(sys.argv) == 3:
        base_raw = Path(sys.argv[1]).read_bytes()
        cand_raw = Path(sys.argv[2]).read_bytes()
        esito = confronta(base_raw, cand_raw)
        print(json.dumps(esito, indent=2))
        return 0 if esito["esito"] == "VERDE" else 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
