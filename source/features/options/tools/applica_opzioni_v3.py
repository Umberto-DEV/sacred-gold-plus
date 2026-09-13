#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""APPLICATORE dell'iniezione — SGP-1.2-OPZIONI-04 (preparazione v2).

Scrive i DUE blocchi della v2 (`PIANO-INIEZIONE.md` §1 di SGP-1.2-OPZIONI-03,
ratificati in `docs/arm9-reserve-reservations.md`):

  sgp.opzioni        0x023D9000  4096 B  codice+risorse+tabella+template+stato,
                                         canarino DENTRO il blocco a +0xFF0
  sgp.opzioni.testi  0x023DA800  1024 B  blob dei testi della lingua della ROM,
                                         canarino DENTRO il blocco a +0x3F0

e patcha i due overlay dei ganci (IDENTICI alla v1, PIANO-INIEZIONE.md §2:
le preimmagini non cambiano fra v1 e v2):

  A  ov054 0x021E6820  04 1c 89 8c -> BL sgp_opz_hook
  B1 ov036 0x021E5A34  puntatore   -> template SGP (Continua)
  B2 ov036 0x021E5998  puntatore   -> template SGP (Nuova partita)

usando `SGP-1.2-OVERLAY-01/tools/overlay_patch.py` (ricompressione BLZ ottima
IN LUOGO, mai riloco) e un lettore/scrittore ARM9 indipendente da ndspy
(`arm9.py`, copiato invariato da SGP-1.2-OPZIONI-02/tools).

PERCHE' RIFIUTA UNA ROM CON LA v1 GIA' APPLICATA, PER COSTRUZIONE: i tre siti
dei ganci (A, B1, B2) sono gli STESSI della v1 (SGP-1.2-OPZIONI-01/02) e le
preimmagini attese (`PRE_A`, `PRE_B1`, `PRE_B2`) sono i byte VANILLA. Una ROM
dove la v1 e' gia' applicata ha in quei siti la BL/i puntatori della v1 (verso
0x023D8DD1 e il suo blocco `0x023D8900..0x23D9900`), che non sono uguali alla
preimmagine vanilla: il cancello A3/A3b rifiuta prima di scrivere un solo byte.
Non serve una lista nera di "impronte v1": basta non riconoscere niente che non
sia la preimmagine vanilla dichiarata.

Non modifica MAI l'ingresso. Rifiuta (RIFIUTATO, rc=2) tutto quello che non
riconosce.

Uso normale (scrive un file NUOVO, l'ingresso resta intatto):
    applica_opzioni_v2.py --rom <sgp-1.2-XX.nds> --out <uscita.nds> --lingua EN|IT \\
                           [--build <dir>] [--manifest MAPPA-RISERVA-ARM9.json] [--json log.json]

Uso «in luogo» (stessa disciplina di SGP-1.2-OPZIONI-02, PLUS-02/03, NPC-02):
    applica_opzioni_v2.py --in-luogo <rom.nds> --lingua EN|IT [--build <dir>] [--tmp <scratchpad>]

QUESTO PACCHETTO NON INVOCA MAI --in-luogo SULLA ROM DI LAVORO CONDIVISA: quel
lucchetto e' di un altro cantiere. Qui si valida solo su COPIE, nella
scratchpad di sessione (RAPPORTO.md).
"""
#
# ===========================================================================
# v3 — SGP-1.2-RIFINITURA-01. Derivato RIGA PER RIGA dall'omonimo strumento di
# SGP-1.2-OPZIONI-04 (che resta invariato e continua ad applicare la v2). Le
# uniche differenze volute:
#   1. la PIANTA del blocco. Il blocco resta lo stesso (0x023D9000, 4096 B) e
#      il canarino resta a +0xFF0: cambia il confine fra il codice e i dati di
#      servizio, perche' il codice della v3 e' 3652 B contro i 3412 della v2 e
#      3584 non bastavano piu'. I 208 B mai usati fra la fine dello stato e il
#      canarino diventano margine del codice:
#          codice +0x000 3776 · ris +0xEC0 96 · tab +0xF20 32
#          tpl    +0xF40   32 · stato +0xF60 96 · libero +0xFC0 48
#   2. `--codice-blob`: il file del blob di codice si puo' indicare a parte,
#      invece di prenderlo sempre da <build>/ui_blob.bin. Serve a provare un
#      blob ricompilato senza rifare tutta la cartella di build; il cancello
#      M1c continua a pretendere che il suo sha256 sia quello dichiarato, o
#      quello passato esplicitamente con --blob-sha.
# Tutto il resto — cancelli, ganci, preimmagini, canarini, --in-luogo — e'
# identico: se diverge, e' un difetto, non una variante.
# ===========================================================================

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
import os
import sys
import tempfile
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI))
OVERLAY01 = QUI.parent.parent / "SGP-1.2-OVERLAY-01" / "tools"
sys.path.insert(0, str(OVERLAY01))
from arm9 import Arm9                    # noqa: E402
import overlay_patch as ovp              # noqa: E402

REPO = Path(__file__).resolve().parents[4]
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))
BUILD_DEFAULT = QUI.parent / "work" / "build"

# --- ganci (PIANO-INIEZIONE.md §2: identici alla v1) -----------------------
OV_A, SITO_A, PRE_A = 54, 0x021E6820, bytes.fromhex("041c898c")
OV_B, SITO_B1, PRE_B1 = 36, 0x021E5A34, struct.pack("<I", 0x020FA16C)
SITO_B2, PRE_B2 = 0x021E5998, struct.pack("<I", 0x020FA15C)
OV054_SHA = "da845099438c42bfa191e8731020da715a3b27b5afe5c48b35518209ec9a49d2"
OV036_SHA = "7d8cb8a0b0d2cb1865ffb09066f20a191eb06f8ae41f250828829c23c5b96acc"

# risorse grafiche vanilla da copiare dal blocco (indirizzo in ov054, lunghezza)
RISORSE = [(0x021E6CD8, 40), (0x021E6C48, 16), (0x021E6E3C, 28)]

# --- blocco sgp.opzioni: 4096 B, canarino DENTRO a +0xFF0 (PRENOTAZIONI-RISERVA.md) --
BLOCK_BASE, BLOCK_N = 0x023D9000, 4096
CANARY_OFF, N_CANARY = 0xFF0, 16
CANARY_MOTIVO = 0xCA5A1400

# --- blocco sgp.opzioni.testi: 1024 B, canarino DENTRO a +0x3F0 ------------
TESTI_BASE, TESTI_N = 0x023DA800, 1024
TESTI_CANARY_OFF = 0x3F0
TESTI_CANARY_MOTIVO = 0xCA5A1500

# scomparti dentro sgp.opzioni (offset relativo a BLOCK_BASE, byte disponibili)
PIANTA = {"codice": (0x000, 0xEC0), "ris": (0xEC0, 0x60), "tab": (0xF20, 0x20),
          "tpl": (0xF40, 0x20), "stato": (0xF60, 0x60)}
# scomparto dentro sgp.opzioni.testi
PIANTA_TESTI = {"testi": (0x000, 0x3F0)}

ENTRATE_ATTESE = ("sgp_ui_frame", "sgp_opz_hook",
                  "sgp_cont_init", "sgp_cont_main", "sgp_cont_exit",
                  "sgp_new_init", "sgp_new_main", "sgp_new_exit")


class Rifiuto(Exception):
    pass


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def bl_thumb(sito, bersaglio):
    delta = (bersaglio & ~1) - (sito + 4)
    if delta % 2 != 0 or not (-0x400000 <= delta < 0x400000):
        raise Rifiuto("BL Thumb fuori portata: %#x -> %#x" % (sito, bersaglio))
    hi = 0xF000 | ((delta >> 12) & 0x7FF)
    lo = 0xF800 | ((delta >> 1) & 0x7FF)
    return struct.pack("<HH", hi, lo)


def bl_decode(sito, quattro_byte):
    hi, lo = struct.unpack("<HH", quattro_byte)
    if hi & 0xF800 != 0xF000 or lo & 0xF800 != 0xF800:
        return None
    addend = ((hi & 0x7FF) << 12) | ((lo & 0x7FF) << 1)
    if addend & 0x400000:
        addend -= 0x800000
    return (sito + 4 + addend) & 0xFFFFFFFE


def carica_build(build_dir, lingua, codice_blob=None, blob_sha=None):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    ind = {k: int(v, 16) for k, v in man["indirizzi"].items()}
    # M1 — la relocazione: il blob deve essere compilato per i due indirizzi
    # DEFINITIVI assegnati da PRENOTAZIONI-RISERVA.md. Misurato (RAPPORTO.md
    # §"relocazione"): il blob di prova di OPZIONI-03 era GIA' compilato per
    # questi indirizzi (0x023D9000 / 0x023DA800): confronto a byte, zero
    # differenze, nessuna vera relocazione necessaria in questa fase.
    if ind["codice"] != BLOCK_BASE:
        no("M1", "manifesto compilato per codice=%#x, il blocco assegnato e' %#x: "
                 "ricompilare con -DSGP_UI_ADDR=%#x" % (ind["codice"], BLOCK_BASE, BLOCK_BASE))
    if ind["testi"] != TESTI_BASE:
        no("M1b", "manifesto compilato per testi=%#x, il blocco assegnato e' %#x: "
                  "ricompilare con -DSGP_UI_TESTI_ADDR=%#x" % (ind["testi"], TESTI_BASE, TESTI_BASE))
    for nome in ENTRATE_ATTESE:
        if nome not in man["simboli"]:
            no("BUILD", "simbolo mancante nel manifesto: %s" % nome)
    # v3: `--codice-blob` indica un file di codice diverso da <build>/ui_blob.bin.
    # Il cancello non sparisce, cambia di riferimento: o il blob e' quello che il
    # manifesto dichiara, o e' quello che chi lancia ha dichiarato lui con
    # --blob-sha. Non esiste il caso «prendi quello che trovi».
    sorgente_blob = Path(codice_blob) if codice_blob else (build / "ui_blob.bin")
    blob = sorgente_blob.read_bytes()
    testi = (build / f"testi-{lingua}.bin").read_bytes()
    tab = (build / f"voci-{lingua}.bin").read_bytes()
    atteso = (blob_sha or man["blob"]["sha256"]).lower()
    if sha(blob) != atteso:
        no("M1c", "%s ha sha256 %s, atteso %s (%s)"
                  % (sorgente_blob.name, sha(blob)[:16], atteso[:16],
                     "--blob-sha" if blob_sha else "manifesto.json"))
    if not blob_sha and len(blob) != man["blob"]["byte"]:
        no("BUILD", "ui_blob.bin non corrisponde al manifesto (dimensione diversa)")
    for nome, dato in (("codice", blob), ("testi", testi), ("tab", tab)):
        cap = (PIANTA[nome][1] if nome in PIANTA else PIANTA_TESTI[nome][1])
        if len(dato) > cap:
            no("BUILD", "%s: %d B su %d riservati" % (nome, len(dato), cap))
    return man, ind, blob, testi, tab


def verifica_manifest_mappa(manifest_path, log):
    """A4: se una mappa e' data, i DUE blocchi non devono sovrapporsi a
    nessun altro blocco gia' registrato (o in prenotazione)."""
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    zone = [(BLOCK_BASE, BLOCK_N, {"sgp.opzioni"}),
            (TESTI_BASE, TESTI_N, {"sgp.opzioni.testi"})]
    for b in mappa["blocchi"]:
        base = int(b["base"], 16)
        n = b.get("bytes", 0)
        if b["nome"].startswith("libero"):
            continue
        for lo, hi_n, nomi in zone:
            hi = lo + hi_n
            if b["nome"] in nomi:
                if base != lo or n != hi_n:
                    no("A4/mappa", "voce '%s' gia' registrata con base/bytes diversi da "
                                   "quelli attesi" % b["nome"])
                continue
            if base < hi and base + n > lo:
                no("A4/mappa", "il blocco [%#x,%#x) si sovrappone a '%s' [%#x,%#x)"
                   % (lo, hi, b["nome"], base, base + n))
    log["manifest_controllato"] = True


def torna_alla_preimmagine(dati, prec_build, lingua, log, ok):
    """v3 — `--sostituisci`: riporta una ROM che ha GIA' la v2 di QUESTA pagina
    alla preimmagine vanilla dei due blocchi e dei tre ganci, cosi' che il
    percorso normale (A0/A0b/A3/A7/A7b) possa poi applicare la v3 con gli STESSI
    cancelli di sempre, senza allentarne nessuno.

    Perche' serve, e perche' non e' un'eccezione alla regola dell'idempotenza.
    La regola del progetto («una sola ROM, applicatori idempotenti che rifiutano
    di riapplicarsi») vale fra blocchi DIVERSI. Qui il blocco e' lo STESSO e
    cambia di versione: senza una via di sostituzione, l'unico modo di portare la
    v3 sulla ROM di lavoro sarebbe ricostruirla da `base-1.1` riapplicando tutti
    gli altri cantieri — cioe' esattamente cio' che «una sola ROM» vuole evitare.
    La via di sostituzione non allenta niente: pretende di RICONOSCERE la v2 byte
    per byte prima di toccarla, e se non la riconosce rifiuta.

    Tre cancelli, tutti di riconoscimento:
      S1  i due blocchi contengono il codice e i testi della v2 dichiarati dalla
          cartella di build precedente (confronto a byte, non «non sono a zero»);
      S2  i tre siti dei ganci contengono ESATTAMENTE i valori che la v2 ci
          avrebbe scritto (BL verso il suo `sgp_opz_hook`, e le due parole verso
          i suoi template);
      S3  tolti quei tre ganci, le immagini decompresse di ov054 e ov036 tornano
          bit per bit quelle vanilla (sha256 dichiarati): la prova che in quegli
          overlay non c'e' nient'altro di nostro.
    """
    prec = json.loads((Path(prec_build) / "manifesto.json").read_text())
    prec_ind = {k: int(v, 16) for k, v in prec["indirizzi"].items()}
    prec_blob = (Path(prec_build) / "ui_blob.bin").read_bytes()
    prec_testi = (Path(prec_build) / f"testi-{lingua}.bin").read_bytes()

    # --- S1: i due blocchi sono quelli della v2 ---------------------------
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "leggi.nds"
        tmp.write_bytes(dati)
        r = Arm9(tmp)
        blocco = bytes(r.leggi(BLOCK_BASE, BLOCK_N))
        blocco_t = bytes(r.leggi(TESTI_BASE, TESTI_N))
    if blocco[:len(prec_blob)] != prec_blob:
        no("S1", "il blocco sgp.opzioni non contiene il codice della versione "
                 "precedente dichiarata in %s: non riconosco che cosa sostituire"
                 % prec_build)
    if blocco_t[:len(prec_testi)] != prec_testi:
        no("S1", "il blocco sgp.opzioni.testi non contiene i testi %s della "
                 "versione precedente" % lingua)
    ok("S1", "i due blocchi contengono la versione precedente (codice %d B, testi %d B)"
             % (len(prec_blob), len(prec_testi)))

    # --- S2: i tre ganci sono quelli della v2 -----------------------------
    prec_a = bl_thumb(SITO_A, int(prec["simboli"]["sgp_opz_hook"], 16))
    prec_b1 = struct.pack("<I", prec_ind["tpl"])
    prec_b2 = struct.pack("<I", prec_ind["tpl"] + 16)
    rom_ro = ovp.Rom(dati)
    v54, _c54, img54 = rom_ro.immagine_overlay(OV_A)
    v36, _c36, img36 = rom_ro.immagine_overlay(OV_B)
    oa = SITO_A - v54["ram"]
    ob1, ob2 = SITO_B1 - v36["ram"], SITO_B2 - v36["ram"]
    if bytes(img54[oa:oa + 4]) != prec_a:
        no("S2", "il gancio A non e' quello della versione precedente (%s, atteso %s)"
                 % (bytes(img54[oa:oa + 4]).hex(), prec_a.hex()))
    if bytes(img36[ob1:ob1 + 4]) != prec_b1 or bytes(img36[ob2:ob2 + 4]) != prec_b2:
        no("S2", "i ganci B1/B2 non sono quelli della versione precedente")
    ok("S2", "i tre ganci sono quelli della versione precedente")

    # --- S3: tolti i ganci, gli overlay tornano vanilla -------------------
    prova54 = bytearray(img54); prova54[oa:oa + 4] = PRE_A
    prova36 = bytearray(img36)
    prova36[ob1:ob1 + 4] = PRE_B1
    prova36[ob2:ob2 + 4] = PRE_B2
    if sha(prova54) != OV054_SHA:
        no("S3", "tolto il gancio A, ov054 non torna vanilla: c'e' dentro altro")
    if sha(prova36) != OV036_SHA:
        no("S3", "tolti i ganci B, ov036 non torna vanilla: c'e' dentro altro")
    ok("S3", "tolti i tre ganci, ov054 e ov036 tornano bit per bit quelli vanilla")

    # --- la sostituzione vera: overlay indietro, blocchi a zero -----------
    dati, _ = ovp.applica(dati, OV_A, [(SITO_A, prec_a)],
                          [{"addr": SITO_A, "pre": prec_a, "post": PRE_A}], strategia="auto")
    dati, _ = ovp.applica(dati, OV_B, [(SITO_B1, prec_b1), (SITO_B2, prec_b2)],
                          [{"addr": SITO_B1, "pre": prec_b1, "post": PRE_B1},
                           {"addr": SITO_B2, "pre": prec_b2, "post": PRE_B2}], strategia="auto")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "azzera.nds"
        tmp.write_bytes(dati)
        r = Arm9(tmp)
        r.scrivi(BLOCK_BASE, bytes(BLOCK_N))
        r.scrivi(TESTI_BASE, bytes(TESTI_N))
        r.salva(tmp)
        dati = tmp.read_bytes()
    log["sostituzione"] = {"build_precedente": str(prec_build),
                           "blob_precedente_sha256": sha(prec_blob),
                           "gancio_A_precedente": prec_a.hex()}
    ok("S4", "preimmagine ripristinata: i cancelli A0/A0b/A3/A7/A7b valgono di nuovo")
    return dati


def applica(ingresso, uscita, build_dir, lingua, manifest_path, json_path,
            codice_blob=None, blob_sha=None, sostituisci=None):
    log = {"strumento": "SGP-1.2-OPZIONI-04/tools/applica_opzioni_v2.py",
           "ingresso": str(ingresso), "lingua": lingua, "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})
        print("  %-4s passato  %s" % (c, msg))

    man, ind, blob, testi, tab = carica_build(build_dir, lingua, codice_blob, blob_sha)
    ok("M1", "manifesto compilato per i blocchi assegnati (%#x / %#x)" % (BLOCK_BASE, TESTI_BASE))
    verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione col resto della mappa (o mappa non fornita)")

    dati_in = Path(ingresso).read_bytes()
    log["sha256_ingresso"] = sha(dati_in)
    log["ingresso_bytes"] = len(dati_in)

    if sostituisci:
        dati_in = torna_alla_preimmagine(dati_in, sostituisci, lingua, log, ok)

    # ---------------- lettura delle risorse DALLA ov054 DELL'INGRESSO -------
    rom_ro = ovp.Rom(dati_in)
    v54, crudo54, img54 = rom_ro.immagine_overlay(OV_A)
    if sha(img54) != OV054_SHA:
        no("A3/ov054", "l'immagine decompressa di ov054 non e' quella attesa (sha256 diverso)")
    v36, crudo36, img36 = rom_ro.immagine_overlay(OV_B)
    if sha(img36) != OV036_SHA:
        no("A3/ov036", "l'immagine decompressa di ov036 non e' quella attesa (sha256 diverso)")

    # ---------------- A7 — rifiuto per costruzione se la v1 (o la v2) e' gia' li' --
    off_a = SITO_A - v54["ram"]
    sito_a_ora = bytes(img54[off_a:off_a + 4])
    if sito_a_ora != PRE_A:
        bersaglio_esistente = bl_decode(SITO_A, sito_a_ora)
        dettaglio = ("il sito del gancio A non ha la preimmagine vanilla (%s, attesa %s): "
                     "una versione della pagina Opzioni (v1 o v2) sembra gia' applicata"
                     % (sito_a_ora.hex(), PRE_A.hex()))
        if bersaglio_esistente is not None:
            dettaglio += "; BL esistente verso %#010x" % bersaglio_esistente
            if bersaglio_esistente == 0x23D8DD1:
                dettaglio += " (e' l'indirizzo di sgp_opz_hook della v1, SGP-1.2-OPZIONI-01/02)"
        no("A7", dettaglio)
    ok("A7", "il sito del gancio A ha ancora la preimmagine vanilla: nessuna v1/v2 presente")

    off_b1, off_b2 = SITO_B1 - v36["ram"], SITO_B2 - v36["ram"]
    if bytes(img36[off_b1:off_b1 + 4]) != PRE_B1 or bytes(img36[off_b2:off_b2 + 4]) != PRE_B2:
        no("A7b", "i siti dei ganci B1/B2 non hanno la preimmagine vanilla: la pagina "
                  "Opzioni sembra gia' applicata (v1 o v2)")
    ok("A7b", "i siti dei ganci B1/B2 hanno ancora la preimmagine vanilla")

    ris = b"".join(bytes(img54[ram - v54["ram"]: ram - v54["ram"] + n]) for ram, n in RISORSE)
    ok("A3", "ov054/ov036 identificati per sha256 dell'immagine decompressa; %d B di risorse letti" % len(ris))

    # ---------------- scrittura ARM9 (due blocchi + due canarini) -----------
    with tempfile.TemporaryDirectory() as td:
        arm9_tmp = Path(td) / "arm9-step.nds"
        Path(arm9_tmp).write_bytes(dati_in)
        r = Arm9(arm9_tmp)
        prima = bytes(r.raw)

        zona = r.leggi(BLOCK_BASE, BLOCK_N)
        if zona != bytes(BLOCK_N):
            primo = next(i for i, x in enumerate(zona) if x)
            no("A0", "il blocco sgp.opzioni a 0x%08X non e' a zero (primo byte non nullo "
                     "a +0x%X): gia' applicato, o occupato da qualcun altro" % (BLOCK_BASE, primo))
        ok("A0", "4096 B a 0x%08X tutti a zero" % BLOCK_BASE)

        zona_t = r.leggi(TESTI_BASE, TESTI_N)
        if zona_t != bytes(TESTI_N):
            primo = next(i for i, x in enumerate(zona_t) if x)
            no("A0b", "il blocco sgp.opzioni.testi a 0x%08X non e' a zero (primo byte non nullo "
                      "a +0x%X)" % (TESTI_BASE, primo))
        ok("A0b", "1024 B a 0x%08X tutti a zero" % TESTI_BASE)

        blocco = bytearray(BLOCK_N)
        blocco_t = bytearray(TESTI_N)

        def metti(nome, dato):
            if nome == "testi":
                o, cap = PIANTA_TESTI[nome]
                if len(dato) > cap:
                    no("BUILD", "%s: %d B su %d" % (nome, len(dato), cap))
                blocco_t[o:o + len(dato)] = dato
                return
            o, cap = PIANTA[nome]
            if len(dato) > cap:
                no("BUILD", "%s: %d B su %d" % (nome, len(dato), cap))
            blocco[o:o + len(dato)] = dato

        metti("codice", blob)
        metti("testi", testi)
        metti("tab", tab)
        # "stato" (+0xEC0, 96 B) resta a zero: e' l'invariante che rende
        # innocuo il guasto piu' probabile (come in v1/D1/NPC).
        metti("tpl", struct.pack("<4I",
                                 int(man["simboli"]["sgp_cont_init"], 16),
                                 int(man["simboli"]["sgp_cont_main"], 16),
                                 int(man["simboli"]["sgp_cont_exit"], 16), 0xFFFFFFFF)
                     + struct.pack("<4I",
                                   int(man["simboli"]["sgp_new_init"], 16),
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
        if fuori:
            no("A2", "%d byte scritti fuori dalle regioni dichiarate, il primo a offset 0x%X"
               % (len(fuori), fuori[0]))
        if len(r.raw) != len(prima):
            no("A2", "la dimensione dell'immagine arm9/riserva e' cambiata")
        ok("A2", "arm9: %d byte scritti (due blocchi con canarino dentro), dimensione invariata" % len(diversi))

        r.salva(arm9_tmp)
        dati_dopo_arm9 = Path(arm9_tmp).read_bytes()

    log["blocco"] = {"base": hex(BLOCK_BASE), "bytes": BLOCK_N, "blob_sha256": sha(blob),
                     "tab_sha256": sha(tab), "ris_sha256": sha(ris),
                     "canarino_off": hex(CANARY_OFF), "canarino_motivo": hex(CANARY_MOTIVO)}
    log["blocco_testi"] = {"base": hex(TESTI_BASE), "bytes": TESTI_N, "testi_sha256": sha(testi),
                           "canarino_off": hex(TESTI_CANARY_OFF), "canarino_motivo": hex(TESTI_CANARY_MOTIVO)}

    # ---------------- patch degli overlay (in luogo, ricompressione ottima) -
    gancio = int(man["simboli"]["sgp_opz_hook"], 16)
    post_a = bl_thumb(SITO_A, gancio)
    patch_a = [{"addr": SITO_A, "pre": PRE_A, "post": post_a}]
    try:
        dati_dopo_a, ric_a = ovp.applica(dati_dopo_arm9, OV_A, [(SITO_A, PRE_A)], patch_a, strategia="auto")
    except ovp.Rifiuto as e:
        no("A5/ov054", str(e))
    ok("A5", "ov054 patchato in luogo: %s" % ric_a["strategia"]["usata"])
    log["overlay_patch_ov054"] = ric_a

    tpl0, tpl1 = ind["tpl"], ind["tpl"] + 16
    post_b1, post_b2 = struct.pack("<I", tpl0), struct.pack("<I", tpl1)
    patch_b = [{"addr": SITO_B1, "pre": PRE_B1, "post": post_b1},
               {"addr": SITO_B2, "pre": PRE_B2, "post": post_b2}]
    try:
        dati_finale, ric_b = ovp.applica(dati_dopo_a, OV_B,
                                         [(SITO_B1, PRE_B1), (SITO_B2, PRE_B2)], patch_b,
                                         strategia="auto")
    except ovp.Rifiuto as e:
        no("A6/ov036", str(e))
    ok("A6", "ov036 patchato in luogo: %s" % ric_b["strategia"]["usata"])
    log["overlay_patch_ov036"] = ric_b
    log["ganci"] = {"A": {"sito": hex(SITO_A), "bersaglio": hex(gancio), "bl": post_a.hex()},
                    "B1": {"sito": hex(SITO_B1), "post": hex(tpl0)},
                    "B2": {"sito": hex(SITO_B2), "post": hex(tpl1)}}

    uscita = Path(uscita)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_bytes(dati_finale)
    log["uscita"] = str(uscita)
    log["uscita_sha256"] = sha(dati_finale)
    log["uscita_bytes"] = len(dati_finale)
    log["esito"] = "applicato"
    if json_path:
        Path(json_path).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: log[k] for k in ("esito", "uscita", "uscita_sha256")}, indent=2))
    return log


def aggiorna_registro_condiviso(rom_path, log):
    rom_path = Path(rom_path).resolve()
    if rom_path.parent != ROM_DIR:
        return False
    sums_path = ROM_DIR / "SHA256SUMS"
    righe = sums_path.read_text().splitlines() if sums_path.exists() else []
    nome = rom_path.name
    nuove = [r for r in righe if not r.endswith("  " + nome)]
    nuove.append("%s  %s" % (log["uscita_sha256"], nome))
    sums_path.write_text("\n".join(nuove) + "\n")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rom", help="ROM di ingresso (o la ROM di lavoro con --in-luogo)")
    ap.add_argument("--out", help="ROM di uscita (obbligatorio se non --in-luogo)")
    ap.add_argument("--in-luogo", metavar="ROM",
                    help="applica sulla ROM di lavoro condivisa IN LUOGO: copia in scratchpad, applica, "
                         "rilegge con rileggi_opzioni_v2.py, sostituisce l'originale SOLO se verde")
    ap.add_argument("--lingua", required=True, choices=("EN", "IT"))
    ap.add_argument("--sostituisci", metavar="BUILD_PRECEDENTE",
                    help="la ROM ha gia' una versione precedente di QUESTA pagina: "
                         "riconoscila con gli artefatti di questa cartella di build "
                         "(cancelli S1-S3) e sostituiscila")
    ap.add_argument("--codice-blob",
                    help="file del blob di codice (predefinito: <build>/ui_blob.bin)")
    ap.add_argument("--blob-sha",
                    help="sha256 atteso del blob indicato da --codice-blob; senza, "
                         "vale quello dichiarato nel manifesto")
    ap.add_argument("--build", default=str(BUILD_DEFAULT),
                    help="cartella con ui_blob.bin/manifesto.json/testi-*.bin/voci-*.bin "
                         "(default: work/build di questo pacchetto)")
    ap.add_argument("--manifest", help="MAPPA-RISERVA-ARM9.json, per il cancello A4")
    ap.add_argument("--tmp", help="cartella scratchpad per --in-luogo")
    ap.add_argument("--json")
    ap.add_argument("--niente-registro", action="store_true")
    a = ap.parse_args()

    try:
        if a.in_luogo:
            rom = Path(a.in_luogo)
            if a.tmp:
                Path(a.tmp).mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=a.tmp) as td:
                tmp_in = Path(td) / ("in-" + rom.name)
                tmp_out = Path(td) / ("out-" + rom.name)
                shutil.copyfile(rom, tmp_in)
                log = applica(tmp_in, tmp_out, a.build, a.lingua, a.manifest, None,
                          a.codice_blob, a.blob_sha, a.sostituisci)
                rilettore = QUI / "rileggi_opzioni_v2.py"
                r = subprocess.run([sys.executable, str(rilettore), str(tmp_in), str(tmp_out),
                                    "--build", a.build, "--lingua", a.lingua] +
                                   (["--manifest", a.manifest] if a.manifest else []),
                                   capture_output=True, text=True)
                log["rilettura_in_luogo"] = {"returncode": r.returncode, "stdout": r.stdout[-4000:], "stderr": r.stderr[-2000:]}
                if r.returncode != 0:
                    print(r.stdout)
                    print(r.stderr, file=sys.stderr)
                    print("RIFIUTATO — la rilettura indipendente non e' verde: NON sostituisco %s" % rom)
                    if a.json:
                        Path(a.json).write_text(json.dumps(log, indent=2) + "\n")
                    return 2
                shutil.copyfile(tmp_out, rom)
                log["uscita"] = str(rom)
            if a.json:
                Path(a.json).write_text(json.dumps(log, indent=2) + "\n")
            if not a.niente_registro:
                aggiorna_registro_condiviso(rom, log)
            print("APPLICATO IN LUOGO %s (verificato prima di sostituire)" % rom)
            return 0
        else:
            if not (a.rom and a.out):
                print("uso: --rom e --out (oppure --in-luogo ROM)", file=sys.stderr)
                return 2
            log = applica(a.rom, a.out, a.build, a.lingua, a.manifest, a.json,
                          a.codice_blob, a.blob_sha, a.sostituisci)
            if not a.niente_registro:
                aggiorna_registro_condiviso(a.out, log)
            return 0
    except Rifiuto as e:
        print("RIFIUTATO — %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
