#!/usr/bin/env python3
"""Blocco WIFI — pianta v-finale (SGP-1.2-QUALITA-NATIVO-01, B5/B6/B8,
applicata in luogo il 12/09/2026). Scrive DIRETTAMENTE (non e' piu' un
adattatore verso WIFI-04) il blocco `sgp.wifi` (2048 B a 0x023DA000):

    +0x000  veneer G2 ARM   24 B  (DWCi_BuildApSearchList, +manutenzione cache)
    +0x020  veneer G3 ARM   28 B  (DWC_ConnectInetAsync, +manutenzione cache)
    +0x040  dati di runtime 64 B  -- resta a zero (li scrive il gioco)
    +0x080  riservato      448 B  -- resta a zero
    +0x240  SgpW1Stato      16 B  -- INVARIATO: magic 'W', versione 2, modo 0
                                     (server WFC "Originale", nessun effetto
                                     finche' nessuno scrive wifi_server nel
                                     chunk pubblico)
    +0x250  blob Thumb wifi_slot4  572 B  (era 660 in WIFI-04/05: B6, accessore
                                     unico del chunk, codice morto tolto)
    +0x7F0  canarino       16 B  -- riservato, NON usato da questo blob

Un solo gancio ROM-side: G1 (arm9 statico, epilogo di Overlay_Load,
0x020070A8) -> sgp_wfc_trampolino. G2/G3 non sono mai scritti in ROM: G1 li
installa nella copia RAM di ov000 a ogni caricamento (vedi RAPPORTO
QUALITA-NATIVO-01 §formato blocco sgp.wifi).

`build`: la cartella `wifi/vfinale/` con `blob.bin` (572 B), `veneer-g2.bin`
(24 B), `veneer-g3.bin` (28 B) e `manifesto.json` (simbolo
`sgp_wfc_trampolino`, decodificato dalla ROM canonica da `estrai_build.py`).
"""
from __future__ import annotations

import json
import struct
import tempfile
from pathlib import Path

from ..rom import Arm9, Rifiuto, bl_decode, bl_thumb, esigi, sha

BLOCK_BASE, BLOCK_N = 0x023DA000, 2048
OFF_VENEER2, N_VENEER2 = 0x000, 24
OFF_VENEER3, N_VENEER3 = 0x020, 28
OFF_STATO_W1, N_STATO_W1 = 0x240, 16
OFF_CODICE, MAX_CODICE = 0x250, BLOCK_N - 16 - 0x250

SITO_G1 = 0x020070A8
PRE_G1 = bytes.fromhex("0120f8bd")

MAGIC_W, VERSIONE, MODO = 0x57, 2, 0

ENTRATE_ATTESE = ("sgp_wfc_trampolino",)


def _carica_build(build_dir):
    build = Path(build_dir) / "vfinale"
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    v2 = (build / "veneer-g2.bin").read_bytes()
    v3 = (build / "veneer-g3.bin").read_bytes()
    esigi(len(blob) <= MAX_CODICE, "BUILD: blob non entra nello slot")
    esigi(len(v2) == N_VENEER2, "BUILD: veneer G2 di dimensione sbagliata")
    esigi(len(v3) == N_VENEER3, "BUILD: veneer G3 di dimensione sbagliata")
    for nome in ENTRATE_ATTESE:
        esigi(nome in man["simboli"], "BUILD: simbolo mancante: %s" % nome)
    return man, blob, v2, v3


def _verifica_manifest_mappa(manifest_path, log):
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    lo, hi = BLOCK_BASE, BLOCK_BASE + BLOCK_N
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"] == "libero.1.2":
            continue
        if b["nome"] == "sgp.wifi":
            esigi(base == BLOCK_BASE and n == BLOCK_N, "A4/mappa: voce 'sgp.wifi' diversa da quella attesa")
            continue
        esigi(not (base < hi and base + n > lo), "A4/mappa: sovrapposizione con '%s'" % b["nome"])
    log["manifest_controllato"] = True


def applica(rom: bytes, build, manifest_path=None) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/wifi.py:applica", "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    man, blob, v2, v3 = _carica_build(build)
    _verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione")

    log["sha256_ingresso"] = sha(rom)

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
    prima = bytes(r.raw)

    zona = r.leggi(BLOCK_BASE, BLOCK_N)
    esigi(zona == bytes(BLOCK_N), "A0: il blocco sgp.wifi non e' a zero")
    ok("A0", "2048 B a zero")
    esigi(r.leggi(SITO_G1, 4) == PRE_G1, "A1: G1 non ha la preimmagine vanilla")
    ok("A1", "G1 con preimmagine vanilla")

    blocco = bytearray(BLOCK_N)
    blocco[OFF_VENEER2:OFF_VENEER2 + N_VENEER2] = v2
    blocco[OFF_VENEER3:OFF_VENEER3 + N_VENEER3] = v3
    stato_w1 = bytearray(N_STATO_W1)
    stato_w1[0], stato_w1[1], stato_w1[2] = MAGIC_W, VERSIONE, MODO
    blocco[OFF_STATO_W1:OFF_STATO_W1 + N_STATO_W1] = stato_w1
    blocco[OFF_CODICE:OFF_CODICE + len(blob)] = blob
    r.scrivi(BLOCK_BASE, bytes(blocco))

    gancio = int(man["simboli"]["sgp_wfc_trampolino"], 16)
    r.scrivi(SITO_G1, bl_thumb(SITO_G1, gancio))

    leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N)) | \
             set(range(r.off(SITO_G1), r.off(SITO_G1) + 4))
    diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "A2: byte scritti fuori dalle regioni dichiarate")
    esigi(len(r.raw) == len(prima), "A2: dimensione cambiata")
    ok("A2", "%d byte scritti (sgp.wifi + gancio G1)" % len(diversi))

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        r.salva(tf2.name)
        dati_out = Path(tf2.name).read_bytes()

    log["uscita_sha256"] = sha(dati_out)
    log["esito"] = "applicato"
    return dati_out, log


# ---------------------------------------------------------------- rilettore
def rileggi(ingresso: bytes, derivata: bytes, build) -> dict:
    """Rilettore: ridecodifica G1 e i blob/veneer da zero, confronta con il
    `build/`. Stesso limite dichiarato di `plus_chunk.rileggi`: riusa
    `sgp12.rom`, non e' una famiglia di decoder indipendente."""
    man, blob, v2, v3 = _carica_build(build)

    esiti, verde = [], True

    def esito(nome, ok_, dettaglio=""):
        nonlocal verde
        esiti.append({"cancello": nome, "esito": "verde" if ok_ else "ROSSO", "dettaglio": dettaglio})
        verde = verde and ok_

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(ingresso)
        tf.flush()
        b = Arm9(tf.name)
    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        tf2.write(derivata)
        tf2.flush()
        d = Arm9(tf2.name)

    esito("L0", b.leggi(BLOCK_BASE, BLOCK_N) == bytes(BLOCK_N), "il blocco era a zero nell'ingresso")
    esito("L1", d.leggi(BLOCK_BASE + OFF_VENEER2, N_VENEER2) == v2, "veneer G2 combacia col build")
    esito("L2", d.leggi(BLOCK_BASE + OFF_VENEER3, N_VENEER3) == v3, "veneer G3 combacia col build")
    esito("L3", d.leggi(BLOCK_BASE + OFF_CODICE, len(blob)) == blob, "blob wifi_slot4 combacia col build")

    stato_w1 = d.leggi(BLOCK_BASE + OFF_STATO_W1, N_STATO_W1)
    esito("L4", stato_w1[0] == MAGIC_W and stato_w1[1] == VERSIONE and stato_w1[2] == MODO,
          "SgpW1Stato iniziale: Originale (magic/versione/modo)")

    zero_atteso = (d.leggi(BLOCK_BASE + 0x040, 0x200) == bytes(0x200)
                  and d.leggi(BLOCK_BASE + OFF_CODICE + len(blob), BLOCK_N - 16 - OFF_CODICE - len(blob))
                  == bytes(BLOCK_N - 16 - OFF_CODICE - len(blob)))
    esito("L5", zero_atteso, "dati/riservato e margine dopo il blob a zero")

    t = bl_decode(SITO_G1, d.leggi(SITO_G1, 4))
    esito("L6", t == (int(man["simboli"]["sgp_wfc_trampolino"], 16) & ~1), "G1 -> sgp_wfc_trampolino")

    return {"esito_finale": "verde" if verde else "ROSSO", "cancelli": esiti}
