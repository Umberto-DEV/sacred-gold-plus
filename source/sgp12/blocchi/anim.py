#!/usr/bin/env python3
"""Blocco ANIM — moto procedurale delle animazioni (blocco `sgp.anim`, 1024 B
a 0x023D8B00), DUE ganci-letterali in overlay 12. Porta a `sgp12` di
`SGP-1.2-ANIM-B-02/tools/applica_anim.py` (v3, un solo gancio) esteso alla
**v4** (SGP-1.2-ANIM-SOLIDO-01, 13/09/2026, applicata in luogo da
SGP-1.2-INTEGRAZIONE-FINALE-02): il blob passa da 600 a 752 B (scomparto
PIENO) e si aggiunge il secondo gancio G2 in coda a `ov12_02262014`
(0x02262032, `BL sgp_idle_stop`), che ripulisce affine/ombra/voce del
lottatore alla fermata del moto (chiude D1 di ANIM-SOLIDO-01/RAPPORTO.md §2).
`costruisci.py` parte da una base 1.1 vergine (blocco a zero, G1/G2 vanilla):
a differenza di `applica_anim4.py --sostituisci` (che riconosce una v3 gia'
in ROM), qui non serve riconoscimento di stato intermedio — si scrive la v4
direttamente.

`rileggi()` e' scritto QUI, indipendente da `applica()`: ridecodifica blob,
tavola, canarino e i due ganci dalla ROM derivata e li confronta con `build/`.
`verifica.py` chiama questo, non un rilettore esterno.
"""
from __future__ import annotations

import hashlib
import json
import struct
import tempfile
from pathlib import Path

from ..rom import Arm9, Rifiuto, bl_decode, bl_thumb, esigi, esigi_manifesto_descrive, sha
from .. import overlay as ovp

OV_CAMPO = 12
A_GANCIO = 0x0226200C
PRE_GANCIO = bytes.fromhex("3d202602")
A_G2 = 0x02262032
PRE_G2 = bytes.fromhex("206a0421")
A_GUARDIA_CORPO = 0x0226203C
PRE_GUARDIA_CORPO = bytes.fromhex(
    "38b50c1c67218900605a14306052081c625a3438824203d3081c3438101a60"
    "5267208000205abdf5a9fd0622c1179202002390f66cec0a1c0421051c206a"
    "00244b02eb18624112051b0b1343da12120d9a181213a6f588fb38bd")
assert len(PRE_GUARDIA_CORPO) == 90
assert hashlib.sha256(PRE_GUARDIA_CORPO).hexdigest() == \
    "0b247d4c37cd35bd205e6cd51ef496a0ced83064ad58060ccaf473e001c28883"

BLOCK_BASE, BLOCK_N = 0x023D8B00, 0x400
OFF_CODICE, MAX_CODICE = 0x000, 0x2F0
OFF_CANARINO, N_CANARINO = 0x2F0, 16
OFF_TABELLE, N_TABELLE = 0x300, 64          # tab_u (32 B) + par (32 B)
OFF_STATO, N_STATO = 0x340, 64
# M6 della revisione R2: le quattro voci da 32 B con cui il blob tiene lo stato
# per lottatore. Il blob e' compilato con -DSGP_ANIM2_SLOT_ADDR su QUESTO
# indirizzo; non essendo dichiarato da nessuna parte, un blob compilato per un
# altro indirizzo veniva accettato in silenzio e sarebbe andato a leggere e
# scrivere 128 B di qualcun altro dentro la riserva.
OFF_SLOT, N_SLOT = 0x380, 128
# Il canarino di questo blocco arriva da `canarino.bin` (estratto dalla ROM):
# la costante `CANARINO_MOTIVO = 0xCA5A1400` che stava qui non era usata da
# nessuno — codice morto, tolto (M9 della revisione R1). Il motivo vero e'
# documentato in `source/docs/arm9-reserve-map.md` insieme al limite noto che
# lo accompagna: anim e opzioni condividono lo stesso motivo, quindi i due
# canarini non distinguono le due regioni.
ENTRATE_ATTESE = ("sgp_idle_task2", "sgp_idle_stop")


def _carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    tab_u = (build / "tab_u.bin").read_bytes()
    par = (build / "par.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()
    # M6 della revisione R2: si controllano TUTTI e cinque gli indirizzi con cui
    # il blob e' compilato, non tre su cinque. `tabelle` e `slot` sono quelli
    # che il blob usa per leggere e scrivere: se il manifesto li dichiara
    # altrove, il blob scriverebbe dentro il blocco di qualcun altro.
    for chiave, atteso in (("codice", BLOCK_BASE + OFF_CODICE),
                           ("stato", BLOCK_BASE + OFF_STATO),
                           ("canarino", BLOCK_BASE + OFF_CANARINO),
                           ("tabelle", BLOCK_BASE + OFF_TABELLE),
                           ("slot", BLOCK_BASE + OFF_SLOT)):
        esigi(chiave in man["indirizzi"], "BUILD: manifesto senza l'indirizzo '%s'" % chiave)
        esigi(int(man["indirizzi"][chiave], 16) == atteso,
              "BUILD: indirizzo %s = %s, atteso 0x%08x" % (chiave, man["indirizzi"][chiave], atteso))
    # ogni simbolo dichiarato deve cadere dentro il blob che lo contiene
    for nome, valore in man["simboli"].items():
        v = int(valore, 16) & ~1
        esigi(BLOCK_BASE + OFF_CODICE <= v < BLOCK_BASE + OFF_CODICE + len(blob),
              "BUILD: il simbolo '%s' (%s) cade fuori dal blob di sgp.anim" % (nome, valore))
    esigi(len(blob) <= MAX_CODICE, "BUILD: blob non entra prima del canarino")
    # Questo controllo QUI NON C'ERA: `build/anim/manifesto.json` dichiara
    # `blob: {byte, sha256}` e nessuno lo confrontava con `blob.bin`. Regola
    # unica in `sgp12/rom.py`.
    esigi_manifesto_descrive(man, blob, blocco="sgp.anim")
    esigi(len(tab_u) == 32 and len(par) == 32, "BUILD: tab_u/par devono essere 32+32 B")
    esigi(len(canarino) == N_CANARINO, "BUILD: canarino di dimensione sbagliata")
    for nome in ENTRATE_ATTESE:
        esigi(nome in man["simboli"], "BUILD: simbolo mancante: %s" % nome)
    return man, blob, tab_u, par, canarino


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
        if b["nome"] == "sgp.anim":
            esigi(base == BLOCK_BASE and n == BLOCK_N, "A4/mappa: voce 'sgp.anim' diversa da quella attesa")
            continue
        esigi(not (base < hi and base + n > lo), "A4/mappa: sovrapposizione con '%s'" % b["nome"])
    log["manifest_controllato"] = True


def applica(rom: bytes, build, manifest_path=None, flags: int = 0) -> tuple[bytes, dict]:
    log = {"strumento": "sgp12/blocchi/anim.py:applica", "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    esigi(0 <= flags <= 0x3F, "PARAM: flags fuori da [0, 0x3F]")
    man, blob, tab_u, par, canarino = _carica_build(build)
    _verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione")

    log["sha256_ingresso"] = sha(rom)

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
    prima = bytes(r.raw)

    zona = r.leggi(BLOCK_BASE, BLOCK_N)
    esigi(zona == bytes(BLOCK_N), "A0: il blocco sgp.anim non e' a zero")
    ok("A0", "1024 B a zero")

    blocco = bytearray(BLOCK_N)
    blocco[OFF_CODICE:OFF_CODICE + len(blob)] = blob
    blocco[OFF_CANARINO:OFF_CANARINO + N_CANARINO] = canarino
    blocco[OFF_TABELLE:OFF_TABELLE + 32] = tab_u
    blocco[OFF_TABELLE + 32:OFF_TABELLE + 64] = par
    stato = bytearray(N_STATO)
    stato[0x00] = flags & 0xFF
    stato[0x01] = 0x5A
    stato[0x02] = 0
    blocco[OFF_STATO:OFF_STATO + N_STATO] = stato
    r.scrivi(BLOCK_BASE, bytes(blocco))

    leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N))
    diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "A2: byte scritti fuori dal blocco dichiarato")
    esigi(len(r.raw) == len(prima), "A2: dimensione cambiata")
    ok("A2", "%d byte scritti (sgp.anim, 1024 B)" % len(diversi))

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        r.salva(tf2.name)
        dati_dopo_arm9 = Path(tf2.name).read_bytes()

    codice_thumb = int(man["simboli"]["sgp_idle_task2"], 16)
    esigi(codice_thumb & 1 == 1, "BUILD: sgp_idle_task2 senza bit Thumb")
    post_g1 = struct.pack("<I", codice_thumb)

    stop_thumb = int(man["simboli"]["sgp_idle_stop"], 16)
    esigi(stop_thumb & 1 == 1, "BUILD: sgp_idle_stop senza bit Thumb")
    post_g2 = bl_thumb(A_G2, stop_thumb)

    patch = [{"addr": A_GANCIO, "pre": PRE_GANCIO, "post": post_g1},
             {"addr": A_G2, "pre": PRE_G2, "post": post_g2}]
    guardie = [(A_GANCIO, PRE_GANCIO), (A_GUARDIA_CORPO, PRE_GUARDIA_CORPO), (A_G2, PRE_G2)]
    dati_out, ric = ovp.applica(dati_dopo_arm9, None, guardie, patch, strategia="auto")
    esigi(ric["overlay"]["id"] == OV_CAMPO, "A1: overlay scelto diverso da quello atteso")
    esigi(len(ric["cancelli"]["C1_guardia"]["candidati"]) == 1, "A1: la guardia non individua un overlay solo")
    ok("A1", "overlay 12 patchato in luogo (due ganci G1+G2): %s" % ric["strategia"]["usata"])
    log["overlay_patch"] = ric

    log["uscita_sha256"] = sha(dati_out)
    log["esito"] = "applicato"
    return dati_out, log


# ---------------------------------------------------------------- rilettore
def rileggi(ingresso: bytes, derivata: bytes, build) -> dict:
    """Rilettore: ridecodifica blob/tab_u/canarino/gancio da zero, confronta
    col `build/` (che per la v3 di RIFINITURA-01 contiene gia' `tab_u.bin`
    corretto, estratto dalla ROM canonica — vedi `estrai_build.py`)."""
    man, blob, tab_u, par, canarino = _carica_build(build)

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
    esito("L1", d.leggi(BLOCK_BASE + OFF_CODICE, len(blob)) == blob, "blob combacia col build")
    esito("L2", d.leggi(BLOCK_BASE + OFF_CANARINO, N_CANARINO) == canarino, "canarino combacia col build")
    esito("L3", d.leggi(BLOCK_BASE + OFF_TABELLE, 32) == tab_u and
          d.leggi(BLOCK_BASE + OFF_TABELLE + 32, 32) == par, "tab_u/par combaciano col build")

    rom_ovp = ovp.Rom(derivata)
    _, _, img = rom_ovp.immagine_overlay(OV_CAMPO)
    off_g = A_GANCIO - rom_ovp.voce_overlay(OV_CAMPO)["ram"]
    codice_thumb = struct.unpack_from("<I", img, off_g)[0]
    esito("L4", codice_thumb == int(man["simboli"]["sgp_idle_task2"], 16), "gancio G1 -> sgp_idle_task2")

    off_g2 = A_G2 - rom_ovp.voce_overlay(OV_CAMPO)["ram"]
    bersaglio_g2 = bl_decode(A_G2, bytes(img[off_g2:off_g2 + 4]))
    esito("L5", bersaglio_g2 is not None and (bersaglio_g2 | 1) == int(man["simboli"]["sgp_idle_stop"], 16),
          "gancio G2 (BL a 0x%08x) -> sgp_idle_stop" % A_G2)

    return {"esito_finale": "verde" if verde else "ROSSO", "cancelli": esiti}
