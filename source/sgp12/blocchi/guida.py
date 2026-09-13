#!/usr/bin/env python3
"""Blocco GUIDA — spegne l'etichetta automatica "START Guida"/"START Guide"
nella pagina ABILITA'/Dati del Riepilogo (START e il tocco restano capaci di
aprire i tre pannelli EV/IV). Porta a `sgp12` il lavoro di
`features/guide/tools/applica_guida.py` (+ `rileggi_guida.py`), stesse costanti, stessi cancelli A0-A4/R0-R5.

STORIA (vedi `SGP-1.2-GUIDA-EVIV-02/RAPPORTO.md` §2 per il dettaglio): il
primo tentativo ricompilava `combined_guide.c` con `build_combined_guide.py`.
La prova su `hg_runtime` ha trovato che il clang disponibile in questo
ambiente produce, per questo file, codice che blocca il gioco (eccezione
ARM9) non appena si preme START — riprodotto ANCHE ricompilando il sorgente
SENZA alcun taglio: non e' un bug del taglio, e' la ricompilazione in se' a
essere pericolosa qui. Questo blocco quindi NON ricompila nulla: patcha 96
byte macchina, direttamente sulla ROM spedita (nessun trampolino ne'
template Oak toccato: `guide_main` resta esattamente dov'era). Verificato su
`hg_runtime-gdb`, EN e IT: l'etichetta non compare piu', START apre i tre
pannelli regolarmente, nessun crash, nessun glitch.

Non tocca la riserva ARM9 1.2 (`MAPPA-RISERVA-ARM9.json` non serve qui): la
zona toccata (0x01FF8A1A, dentro l'ITCM statica r5) e' quella storica della
1.1, indipendente dalla riserva 1.2. Non tocca il salvataggio, l'automatismo
di Nuova Partita, i numeri EV/IV, ne' la zona testi della guida.
"""
from __future__ import annotations

import hashlib
import struct
import tempfile
from pathlib import Path

from ..rom import Arm9, Rifiuto, esigi, sha

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


def _spenta_bytes():
    patch = struct.pack("<HHHH", 0x2001, 0x62F8, 0x6338, 0xE07A)
    patch += b"\xC0\x46" * ((PATCH_N - len(patch)) // 2)
    assert hashlib.sha256(patch).hexdigest() == SPENTA_SHA
    return patch


SPENTA_BYTES = _spenta_bytes()


def _stato(regione: bytes) -> str:
    s = sha(regione)
    if s == ORIGINALE_SHA:
        return "originale"
    if s == SPENTA_SHA:
        return "spenta"
    return "ignoto"


def _lingua(a) -> str | None:
    try:
        campione = bytes(a.leggi(TEXT, TEXT_SIGNATURE_N))
    except KeyError:
        return None
    firma = sha(campione)
    for lingua, attesa in LINGUA_FIRMA.items():
        if firma == attesa:
            return lingua
    return None


def applica(rom: bytes) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/guida.py:applica", "sha256_ingresso": sha(rom), "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        a = Arm9(tf.name)
        lingua = _lingua(a)
        regione_ora = bytes(a.leggi(PATCH_ADDR, PATCH_N))

    log["lingua"] = lingua
    stato = _stato(regione_ora)
    log["stato_ingresso"] = stato
    ok("A0", "lingua per il log: %s (la regione patchata non dipende dalla lingua)" % (lingua or "non riconosciuta"))

    if stato == "spenta":
        log["esito"] = "gia-applicato"
        log["byte_diversi"] = 0
        return rom, log
    esigi(stato == "originale", "A1: la regione (0x%08X, %d B) non e' ne' l'originale ne' la 'spenta' "
          "attesa (stato=%s)" % (PATCH_ADDR, PATCH_N, stato))
    ok("A1", "preimmagine originale riconosciuta byte per byte (96 B)")

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
        prima = bytes(r.raw)
        r.scrivi(PATCH_ADDR, SPENTA_BYTES)
        o = r.off(PATCH_ADDR, PATCH_N)
        leciti = set(range(o, o + PATCH_N))
        diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
        fuori = [i for i in diversi if i not in leciti]
        esigi(not fuori, "A2: %d byte scritti fuori dalla regione dichiarata" % len(fuori))
        ok("A2", "scrittura confinata alla sola regione dichiarata (96 B)")
        esigi(0 < len(diversi) <= PATCH_N, "A2b: %d byte diversi, atteso [1,%d]" % (len(diversi), PATCH_N))
        ok("A2b", "%d byte cambiati dentro i 96 B della regione" % len(diversi))
        esigi(len(r.raw) == len(prima), "A3: dimensione della ROM cambiata")
        ok("A3", "dimensione della ROM invariata")
        uscita = bytes(r.raw)

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        tf2.write(uscita)
        tf2.flush()
        a_out = Arm9(tf2.name)
        stato_dopo = _stato(bytes(a_out.leggi(PATCH_ADDR, PATCH_N)))
    esigi(stato_dopo == "spenta", "A4: dopo la scrittura la regione non e' 'spenta' (stato=%s)" % stato_dopo)
    ok("A4", "dopo la scrittura la regione e' riconosciuta come 'spenta'")

    log.update(esito="applicato", byte_diversi=len(diversi), sha256_uscita=sha(uscita))
    return uscita, log


def rileggi(base: bytes, candidata: bytes) -> dict:
    """Rilettore indipendente: cammina l'ARM9 con la propria routine (non usa
    `sgp12.rom.Arm9`), esattamente come `rileggi_guida.py`."""

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

        def b(self, ram, n):
            for base_, o, size in self.seg:
                if base_ <= ram and ram + n <= base_ + size:
                    return self.raw[o + ram - base_: o + ram - base_ + n]
            raise KeyError("0x%08X+%d" % (ram, n))

        def off(self, ram, n):
            for base_, o, size in self.seg:
                if base_ <= ram and ram + n <= base_ + size:
                    return o + ram - base_
            raise KeyError("0x%08X+%d" % (ram, n))

    b, c = _Immagine(base), _Immagine(candidata)

    def stato_di(img):
        lingua_ = None
        try:
            campione = bytes(img.b(TEXT, TEXT_SIGNATURE_N))
            firma = sha(campione)
            for l_, attesa in LINGUA_FIRMA.items():
                if firma == attesa:
                    lingua_ = l_
        except KeyError:
            pass
        regione = bytes(img.b(PATCH_ADDR, PATCH_N))
        return {"lingua": lingua_, "stato": _stato(regione)}

    esiti, rosso = [], []

    def R(nome, cond, nota):
        esiti.append({"cancello": nome, "esito": "VERDE" if cond else "ROSSO", "nota": nota})
        if not cond:
            rosso.append(nome)

    stato_b, stato_c = stato_di(b), stato_di(c)
    R("R0", stato_b["lingua"] is None or stato_c["lingua"] is None or stato_b["lingua"] == stato_c["lingua"],
      "lingua identica se riconosciuta")
    R("R1", stato_b["stato"] == "originale", "la base e' l'originale")
    R("R2", stato_c["stato"] == "spenta", "la candidata e' 'spenta'")

    off = c.off(PATCH_ADDR, PATCH_N)
    leciti = set(range(off, off + PATCH_N))
    R("R3", len(b.raw) == len(c.raw), "dimensione invariata")
    diversi = [i for i in range(min(len(b.raw), len(c.raw))) if b.raw[i] != c.raw[i]]
    R("R4", 0 < len(diversi) <= PATCH_N and set(diversi) <= leciti,
      "%d byte diversi, tutti dentro la regione dichiarata" % len(diversi))
    fine_b = max(o + size for _r, o, size in b.seg)
    fine_c = max(o + size for _r, o, size in c.seg)
    R("R5", b.raw[:b.off9] + b.raw[fine_b:] == c.raw[:c.off9] + c.raw[fine_c:],
      "fuori dall'ARM9 identico")

    return {"sha256_base": sha(b.raw), "sha256_candidata": sha(c.raw), "byte_diversi": len(diversi),
           "cancelli": esiti, "esito": "VERDE" if not rosso else "ROSSO (%s)" % ", ".join(rosso)}
