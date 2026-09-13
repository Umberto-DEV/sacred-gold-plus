#!/usr/bin/env python3
"""Blocco OPZIONI — pagina Opzioni v4 (blocchi `sgp.opzioni` 0x023D9000/4096 B
e `sgp.opzioni.testi` 0x023DA800/1024 B) + ganci in ov054/ov036. Scrive
direttamente la pianta v3 di `SGP-1.2-RIFINITURA-01` (applicata in luogo
12/09/2026: ris/tab/tpl/stato spostati in avanti, canarino invariato a +0xFF0 —
vedi `PIANTA` e MAPPA-RISERVA-ARM9.json). Gli SCOMPARTI non cambiano con la v4:
cambia il blob, che dalla 1.2.1 e' 3632 B (v3 3628, v2 3348) perche'
`opz_presente` applica a ogni voce la precondizione del chunk di D1 (A1 della
revisione R2). Il codice qui dentro non cabla nessuna lunghezza di blob: la
legge dal manifesto e la confronta con lo scomparto.

`rileggi()` e' un adattatore: richiama per sottoprocesso `rileggi_opzioni_v3.py`
originale di SGP-1.2-RIFINITURA-01 (invariato, indipendente da questo
`applica()` — propria Arm9RO, proprio bl_decode, propria BLZ "in avanti").
"""
from __future__ import annotations

import json
import struct
import tempfile
from pathlib import Path

from ..rom import Arm9, Rifiuto, bl_thumb, esigi, esigi_manifesto_descrive, sha
from .. import overlay as ovp

OV_A, SITO_A, PRE_A = 54, 0x021E6820, bytes.fromhex("041c898c")
OV_B, SITO_B1, PRE_B1 = 36, 0x021E5A34, struct.pack("<I", 0x020FA16C)
SITO_B2, PRE_B2 = 0x021E5998, struct.pack("<I", 0x020FA15C)
OV054_SHA = "da845099438c42bfa191e8731020da715a3b27b5afe5c48b35518209ec9a49d2"
OV036_SHA = "7d8cb8a0b0d2cb1865ffb09066f20a191eb06f8ae41f250828829c23c5b96acc"

RISORSE = [(0x021E6CD8, 40), (0x021E6C48, 16), (0x021E6E3C, 28)]

BLOCK_BASE, BLOCK_N = 0x023D9000, 4096
CANARY_OFF, N_CANARY = 0xFF0, 16
CANARY_MOTIVO = 0xCA5A1400

TESTI_BASE, TESTI_N = 0x023DA800, 1024
TESTI_CANARY_OFF = 0x3F0
TESTI_CANARY_MOTIVO = 0xCA5A1500

# v3 (SGP-1.2-RIFINITURA-01, applicata in luogo 12/09/2026): il codice cresce
# da 3348 a 3628 B (tocco dello stilo, righe comandi, default chunk) e sposta
# ris/tab/tpl/stato in avanti; il canarino a +0xFF0 resta DOVE ERA. La v4 della
# 1.2.1 porta il codice a 3632 B e non muove nessuno scomparto. Pianta esatta:
# source/docs/arm9-reserve-map.json, voce "sgp.opzioni".
PIANTA = {"codice": (0x000, 0xEC0), "ris": (0xEC0, 0x60), "tab": (0xF20, 0x20),
          "tpl": (0xF40, 0x20), "stato": (0xF60, 0x60)}
PIANTA_TESTI = {"testi": (0x000, 0x3F0)}

ENTRATE_ATTESE = ("sgp_ui_frame", "sgp_opz_hook",
                  "sgp_cont_init", "sgp_cont_main", "sgp_cont_exit",
                  "sgp_new_init", "sgp_new_main", "sgp_new_exit")


def _bl_decode(sito, quattro_byte):
    hi, lo = struct.unpack("<HH", quattro_byte)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if addend & 0x400000:
        addend -= 0x800000
    return (sito + 4 + addend) & 0xFFFFFFFE


def _carica_build(build_dir, lingua):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    ind = {k: int(v, 16) for k, v in man["indirizzi"].items()}
    esigi(ind["codice"] == BLOCK_BASE, "M1: manifesto compilato per un altro indirizzo di codice")
    esigi(ind["testi"] == TESTI_BASE, "M1b: manifesto compilato per un altro indirizzo di testi")
    # M4 della revisione R1: `tpl` e' l'UNICO valore del manifesto che finisce
    # scritto dentro ov036 (i due letterali SITO_B1/SITO_B2), e non era
    # controllato. Il rilettore `rileggi_opzioni_v3.py` confronta i byte
    # patchati con lo STESSO `ind["tpl"]`: un valore stantio (la v2 aveva
    # +0xEA0) sarebbe stato scritto in ROM e riletto verde. Le altre voci di
    # `indirizzi` in questo manifesto erano davvero rimaste alla v2, quindi
    # l'ipotesi non era teorica.
    esigi(ind["tpl"] == BLOCK_BASE + PIANTA["tpl"][0],
          "M1c: manifesto compilato per un altro indirizzo di template (%#x, atteso %#x)"
          % (ind["tpl"], BLOCK_BASE + PIANTA["tpl"][0]))
    # ris/tab/stato non sono scritti in ROM da qui (la pianta la decide
    # `PIANTA`), ma se il manifesto li dichiara devono dire la stessa cosa:
    # sono gli indirizzi con cui il blob e' compilato.
    for chiave in ("ris", "tab", "stato"):
        if chiave in ind:
            esigi(ind[chiave] == BLOCK_BASE + PIANTA[chiave][0],
                  "M1d: manifesto: '%s' = %#x, la pianta v3 dice %#x"
                  % (chiave, ind[chiave], BLOCK_BASE + PIANTA[chiave][0]))
    for nome in ENTRATE_ATTESE:
        esigi(nome in man["simboli"], "BUILD: simbolo mancante: %s" % nome)
    blob = (build / "ui_blob.bin").read_bytes()
    testi = (build / f"testi-{lingua}.bin").read_bytes()
    tab = (build / f"voci-{lingua}.bin").read_bytes()
    esigi_manifesto_descrive(man, blob, "blob", "ui_blob.bin", "sgp.opzioni")
    for nome, dato in (("codice", blob), ("testi", testi), ("tab", tab)):
        cap = PIANTA[nome][1] if nome in PIANTA else PIANTA_TESTI[nome][1]
        esigi(len(dato) <= cap, "BUILD: %s troppo grande" % nome)
    return man, ind, blob, testi, tab


def _verifica_manifest_mappa(manifest_path, log):
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    zone = [(BLOCK_BASE, BLOCK_N, {"sgp.opzioni"}), (TESTI_BASE, TESTI_N, {"sgp.opzioni.testi"})]
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"].startswith("libero"):
            continue
        for lo, hi_n, nomi in zone:
            hi = lo + hi_n
            if b["nome"] in nomi:
                esigi(base == lo and n == hi_n, "A4/mappa: voce '%s' diversa da quella attesa" % b["nome"])
                continue
            esigi(not (base < hi and base + n > lo), "A4/mappa: sovrapposizione con '%s'" % b["nome"])
    log["manifest_controllato"] = True


def applica(rom: bytes, build, lingua: str, manifest_path=None) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/opzioni.py:applica", "lingua": lingua, "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    man, ind, blob, testi, tab = _carica_build(build, lingua)
    ok("M1", "manifesto compilato per i blocchi assegnati")
    _verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione")

    log["sha256_ingresso"] = sha(rom)

    rom_ro = ovp.Rom(rom)
    v54, crudo54, img54 = rom_ro.immagine_overlay(OV_A)
    esigi(sha(img54) == OV054_SHA, "A3/ov054: immagine decompressa inattesa")
    v36, crudo36, img36 = rom_ro.immagine_overlay(OV_B)
    esigi(sha(img36) == OV036_SHA, "A3/ov036: immagine decompressa inattesa")

    off_a = SITO_A - v54["ram"]
    sito_a_ora = bytes(img54[off_a:off_a + 4])
    esigi(sito_a_ora == PRE_A, "A7: il sito del gancio A non ha la preimmagine vanilla")
    ok("A7", "preimmagine vanilla del gancio A")

    off_b1, off_b2 = SITO_B1 - v36["ram"], SITO_B2 - v36["ram"]
    esigi(bytes(img36[off_b1:off_b1 + 4]) == PRE_B1 and bytes(img36[off_b2:off_b2 + 4]) == PRE_B2,
          "A7b: i siti dei ganci B1/B2 non hanno la preimmagine vanilla")
    ok("A7b", "preimmagine vanilla dei ganci B1/B2")

    ris = b"".join(bytes(img54[ram - v54["ram"]: ram - v54["ram"] + n]) for ram, n in RISORSE)
    ok("A3", "%d B di risorse lette" % len(ris))

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
    prima = bytes(r.raw)

    zona = r.leggi(BLOCK_BASE, BLOCK_N)
    esigi(zona == bytes(BLOCK_N), "A0: il blocco sgp.opzioni non e' a zero")
    ok("A0", "4096 B a zero")
    zona_t = r.leggi(TESTI_BASE, TESTI_N)
    esigi(zona_t == bytes(TESTI_N), "A0b: il blocco sgp.opzioni.testi non e' a zero")
    ok("A0b", "1024 B a zero")

    blocco = bytearray(BLOCK_N)
    blocco_t = bytearray(TESTI_N)

    def metti(nome, dato):
        if nome == "testi":
            o, cap = PIANTA_TESTI[nome]
            esigi(len(dato) <= cap, "BUILD: %s troppo grande" % nome)
            blocco_t[o:o + len(dato)] = dato
            return
        o, cap = PIANTA[nome]
        esigi(len(dato) <= cap, "BUILD: %s troppo grande" % nome)
        blocco[o:o + len(dato)] = dato

    metti("codice", blob)
    metti("testi", testi)
    metti("tab", tab)
    metti("tpl", struct.pack("<4I", int(man["simboli"]["sgp_cont_init"], 16),
                             int(man["simboli"]["sgp_cont_main"], 16),
                             int(man["simboli"]["sgp_cont_exit"], 16), 0xFFFFFFFF)
                 + struct.pack("<4I", int(man["simboli"]["sgp_new_init"], 16),
                               int(man["simboli"]["sgp_new_main"], 16),
                               int(man["simboli"]["sgp_new_exit"], 16), 0xFFFFFFFF))
    metti("ris", ris)

    can1 = b"".join(struct.pack("<I", CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    can2 = b"".join(struct.pack("<I", TESTI_CANARY_MOTIVO | i) for i in range(N_CANARY // 4))
    blocco[CANARY_OFF:CANARY_OFF + N_CANARY] = can1
    blocco_t[TESTI_CANARY_OFF:TESTI_CANARY_OFF + N_CANARY] = can2

    r.scrivi(BLOCK_BASE, bytes(blocco))
    r.scrivi(TESTI_BASE, bytes(blocco_t))

    leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N)) | \
             set(range(r.off(TESTI_BASE), r.off(TESTI_BASE) + TESTI_N))
    diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "A2: byte scritti fuori dalle regioni dichiarate")
    esigi(len(r.raw) == len(prima), "A2: dimensione cambiata")
    ok("A2", "%d byte scritti (due blocchi con canarino dentro)" % len(diversi))

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        r.salva(tf2.name)
        dati_dopo_arm9 = Path(tf2.name).read_bytes()

    gancio = int(man["simboli"]["sgp_opz_hook"], 16)
    post_a = bl_thumb(SITO_A, gancio)
    patch_a = [{"addr": SITO_A, "pre": PRE_A, "post": post_a}]
    dati_dopo_a, ric_a = ovp.applica(dati_dopo_arm9, OV_A, [(SITO_A, PRE_A)], patch_a, strategia="auto")
    ok("A5", "ov054 patchato in luogo: %s" % ric_a["strategia"]["usata"])

    tpl0, tpl1 = ind["tpl"], ind["tpl"] + 16
    post_b1, post_b2 = struct.pack("<I", tpl0), struct.pack("<I", tpl1)
    patch_b = [{"addr": SITO_B1, "pre": PRE_B1, "post": post_b1},
               {"addr": SITO_B2, "pre": PRE_B2, "post": post_b2}]
    dati_finale, ric_b = ovp.applica(dati_dopo_a, OV_B, [(SITO_B1, PRE_B1), (SITO_B2, PRE_B2)],
                                     patch_b, strategia="auto")
    ok("A6", "ov036 patchato in luogo: %s" % ric_b["strategia"]["usata"])

    log["uscita_sha256"] = sha(dati_finale)
    log["esito"] = "applicato"
    return dati_finale, log


# ---------------------------------------------------------------- rilettore
# Adattatore: richiama `rileggi_opzioni_v3.py` di SGP-1.2-RIFINITURA-01
# (indipendente da questo `applica()`: propria Arm9RO, proprio bl_decode,
# propria BLZ "in avanti") per sottoprocesso, senza `--sostituisce` (il
# nostro `applica()` scrive la v3 direttamente da un blocco a zero, non da
# una v2 preesistente: L9 li' verifica appunto "blocco a zero in ingresso").
_SOURCE = Path(__file__).resolve().parents[2]
_RIFINITURA01 = _SOURCE / "features/options/tools"


def rileggi(ingresso: bytes, derivata: bytes, build, lingua: str, manifest_path=None) -> dict:
    import subprocess
    import sys as _sys

    with tempfile.NamedTemporaryFile(suffix=".nds") as ti, \
         tempfile.NamedTemporaryFile(suffix=".nds") as td, \
         tempfile.NamedTemporaryFile(suffix=".json") as tj:
        ti.write(ingresso)
        ti.flush()
        td.write(derivata)
        td.flush()
        cmd = [_sys.executable, str(_RIFINITURA01 / "rileggi_opzioni_v3.py"),
               ti.name, td.name, "--build", str(build), "--lingua", lingua, "--json", tj.name]
        if manifest_path:
            cmd += ["--manifest", str(manifest_path)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        try:
            esito = json.loads(Path(tj.name).read_text())
        except Exception:
            return {"esito_finale": "ROSSO", "cancelli": [],
                   "strumento": "rileggi_opzioni_v3.py (adattatore)",
                   "errore": (r.stdout + r.stderr)[-4000:], "returncode": r.returncode}
    esito["strumento"] = "rileggi_opzioni_v3.py (adattatore)"
    esito["returncode"] = r.returncode
    return esito
