#!/usr/bin/env python3
"""APPLICATORE — SGP-1.2-ANIM-SOLIDO-01: il blocco `sgp.anim` **v4**.

Fa due cose che l'applicatore della v2b/v3 non faceva:

1. **sostituisce una versione già applicata** (`--sostituisci`), riconoscendola
   byte per byte, invece di pretendere il blocco vergine. È la stessa via
   aperta da `SGP-1.2-RIFINITURA-01` per la pagina Opzioni (`--sostituisci`),
   con i tre cancelli di riconoscimento S1/S2/S3;
2. installa **due** ganci in `ov012`, non uno:

   | gancio | indirizzo | vanilla | v3 | v4 |
   |---|---|---|---|---|
   | G1, letterale del task | `0x0226200C` | `3d202602` | `018b3d02` | `<sgp_idle_task2>` |
   | G2, coda di `ov12_02262014` | `0x02262032` | `206a0421` | `206a0421` | `BL sgp_idle_stop` |

   G2 sostituisce `ldr r0,[r4,#0x20]` + `movs r1,#4` con una `BL` alla nostra
   trampolina, che rimette quelle due istruzioni (e `movs r2,#0`) prima di
   tornare: le due istruzioni che seguono nel gioco girano identiche. Serve a
   togliere lo **stato sporco** che il gioco non ripulisce quando ferma il
   moto (scala affine, scostamento dell'ombra, posa del battito) — misurato:
   257/255 e −1 per 1235 fotogrammi dopo la fermata.

L'overlay si sceglie SOLO per guardia (mai per indirizzo: cinque overlay
contengono `0x0226200C`), con TRE guardie: il letterale G1 (nella forma attesa
per il modo scelto), la firma di 90 B del corpo del task vanilla a
`0x0226203C`, e i 4 byte vanilla del sito G2.

`ov012` è **byte-identico fra EN e IT** (sha256 del modulo decompresso
`d32c3d9e…` su entrambe le basi 1.1): lo stesso artefatto vale per le due
lingue.

Uso:
  applica_anim4.py --base ROM --out ROM --build DIR [--manifest M] [--flags 0]
                   [--sostituisci] [--json F]
  applica_anim4.py --in-luogo ROM --build DIR [--sostituisci] [--tmp D] [--json F]
  applica_anim4.py --rilegge ROM   (dice soltanto in che stato è: vanilla/v3/v4)

rc: 0 applicato · 2 RIFIUTATO.
GPL-3.0-or-later.
"""
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
from arm9 import Arm9                    # noqa: E402
import overlay_patch as ovp              # noqa: E402

REPO = Path(__file__).resolve().parents[4]
ROM_DIR = Path(os.environ.get("SGP_ROM_DIR", "rom-dir-not-set"))

OV_CAMPO = 12
A_G1 = 0x0226200C
PRE_G1_VANILLA = bytes.fromhex("3d202602")       # il task vanilla, 0x0226203D
A_G2 = 0x02262032
PRE_G2_VANILLA = bytes.fromhex("206a0421")       # ldr r0,[r4,#0x20] ; movs r1,#4
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
OFF_TABELLE = 0x300
OFF_STATO, N_STATO = 0x340, 64
OFF_SLOT, N_SLOT = 0x380, 128
CANARINO_MOTIVO = 0xCA5A1400

ENTRATE_ATTESE = ("sgp_idle_task2", "sgp_idle_stop")

# --- l'immagine v3 che ci si aspetta di trovare in ROM, per S1 --------------
# Sono i numeri dichiarati da SGP-1.2-ANIM-B-03/RESULT.json (blob) e da
# SGP-1.2-RIFINITURA-01/RESULT.json (tavola lisciata). Non si ricompila la v3:
# la si riconosce per impronta, che è più forte.
V3_BLOB_SHA = "86a4e1323f3046403b1267d2ad92383c1f59c654447154d1f0ed54ef55248f83"
V3_BLOB_N = 600
V3_TAB_U = bytes((x & 0xFF) for x in
                 (0, 5, 9, 13, 16, 16, 13, 9, 5, 0, -5, -9, -13, -16, -16, -13, -9, -5)) \
    + bytes(32 - 18)
V3_PAR = (bytes((2, 3, 4, 4)) + bytes((4, 6, 6, 6)) + bytes((0, 9, 5, 14))
          + bytes((70, 63, 2, 3)) + bytes((3,)) + bytes(15))
assert len(V3_PAR) == 32
V3_GANCIO = struct.pack("<I", BLOCK_BASE | 1)    # 018b3d02


class Rifiuto(Exception):
    pass


def img_ov(dati, oid=OV_CAMPO):
    """L'immagine decompressa dell'overlay `oid` e il suo indirizzo RAM.
    `overlay_patch.Rom.immagine_overlay` rende (voce, corpo grezzo, immagine)."""
    v, _crudo, img = ovp.Rom(dati).immagine_overlay(oid)
    return {"ram": v["ram"], "immagine": img, "voce": v}


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def canarino_atteso():
    return b"".join((CANARINO_MOTIVO | i).to_bytes(4, "little")
                    for i in range(N_CANARINO // 4))


def bl_thumb(sito, bersaglio_thumb):
    """Le due halfword di una `BL` Thumb-1 da `sito` a `bersaglio_thumb`.
    ARMv5TE non ha `B.W`: la `BL` è l'unico salto Thumb a ±4 MB, e al sito G2
    `lr` è morto (la funzione l'ha già salvato con `push {r4,lr}`)."""
    delta = (bersaglio_thumb & ~1) - (sito + 4)
    if delta & 1:
        no("G2", "delta dispari: %#x" % delta)
    if not (-0x400000 <= delta < 0x400000):
        no("G2", "delta %#x fuori dalla portata di una BL Thumb (+-4 MB)" % delta)
    hi = 0xF000 | ((delta >> 12) & 0x7FF)
    lo = 0xF800 | ((delta >> 1) & 0x7FF)
    return struct.pack("<HH", hi, lo)


def carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    tab_u = (build / "tab_u.bin").read_bytes()
    par = (build / "par.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()
    if int(man["indirizzi"]["codice"], 16) != BLOCK_BASE + OFF_CODICE:
        no("BUILD", "blob compilato per %s, atteso 0x%08X" %
           (man["indirizzi"]["codice"], BLOCK_BASE + OFF_CODICE))
    if int(man["indirizzi"]["stato"], 16) != BLOCK_BASE + OFF_STATO:
        no("BUILD", "indirizzo stato incoerente col blocco sgp.anim")
    if int(man["indirizzi"]["canarino"], 16) != BLOCK_BASE + OFF_CANARINO:
        no("BUILD", "indirizzo canarino incoerente col blocco sgp.anim")
    if len(blob) > MAX_CODICE:
        no("BUILD", "blob %d B non entra nei %d B prima del canarino"
           % (len(blob), MAX_CODICE))
    if len(tab_u) != 32 or len(par) != 32:
        no("BUILD", "tab_u/par devono essere 32+32 B")
    if len(canarino) != N_CANARINO or canarino != canarino_atteso():
        no("BUILD", "canarino.bin non è il motivo 0x%08X|i" % CANARINO_MOTIVO)
    for nome in ENTRATE_ATTESE:
        if nome not in man["simboli"]:
            no("BUILD", "simbolo mancante nel manifesto: %s" % nome)
        if int(man["simboli"][nome], 16) & 1 == 0:
            no("BUILD", "%s senza bit Thumb: %s" % (nome, man["simboli"][nome]))
    if man.get("M_MONO", {}).get("esito") != "verde":
        no("BUILD", "il manifesto non porta M-MONO verde")
    return man, blob, tab_u, par, canarino


def blocco_atteso(blob, tab_u, par, canarino, flags):
    b = bytearray(BLOCK_N)
    b[OFF_CODICE:OFF_CODICE + len(blob)] = blob
    b[OFF_CANARINO:OFF_CANARINO + N_CANARINO] = canarino
    b[OFF_TABELLE:OFF_TABELLE + 32] = tab_u
    b[OFF_TABELLE + 32:OFF_TABELLE + 64] = par
    st = bytearray(N_STATO)
    st[0x00] = flags & 0xFF
    st[0x01] = 0x5A
    b[OFF_STATO:OFF_STATO + N_STATO] = st
    return bytes(b)


def riconosci(zona, ov012_g1, ov012_g2=None):
    """Che cosa c'è oggi nel blocco e nel gancio G1: 'vergine', 'v3' o 'v4'.

    Il riconoscimento è per CONTENUTO, non per un numero di versione scritto
    da qualche parte: un numero si può scrivere per sbaglio, 600 byte con
    quello sha no.
    """
    if zona == bytes(BLOCK_N) and ov012_g1 == PRE_G1_VANILLA:
        return "vergine"
    blob = bytes(zona[OFF_CODICE:OFF_CODICE + V3_BLOB_N])
    if (sha(blob) == V3_BLOB_SHA
            and zona[V3_BLOB_N:OFF_CANARINO] == bytes(OFF_CANARINO - V3_BLOB_N)
            and zona[OFF_CANARINO:OFF_CANARINO + N_CANARINO] == canarino_atteso()
            and zona[OFF_TABELLE:OFF_TABELLE + 32] == V3_TAB_U
            and zona[OFF_TABELLE + 32:OFF_TABELLE + 64] == V3_PAR
            and zona[OFF_STATO + 1] == 0x5A
            and ov012_g1 == V3_GANCIO):
        return "v3"
    # v4: il blocco ha il canarino al suo posto, il gancio G1 punta DENTRO il
    # blocco e G2 non e' piu' vanilla (c'e' la BL alla trampolina).
    g1 = struct.unpack("<I", bytes(ov012_g1))[0] if len(ov012_g1) == 4 else 0
    if (zona[OFF_CANARINO:OFF_CANARINO + N_CANARINO] == canarino_atteso()
            and BLOCK_BASE < (g1 & ~1) < BLOCK_BASE + OFF_CANARINO
            and ov012_g2 is not None and bytes(ov012_g2) != PRE_G2_VANILLA):
        return "v4"
    return "ignoto"


def applica(ingresso, uscita, build_dir, manifest_path, flags, sostituisci, json_path):
    log = {"strumento": "SGP-1.2-ANIM-SOLIDO-01/tools/applica_anim4.py",
           "ingresso": str(ingresso), "cancelli": [], "sostituisci": bool(sostituisci)}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})
        print("  %-6s passato  %s" % (c, msg))

    if not (0 <= flags <= 0x3F):
        no("PARAM", "flags fuori da [0, 0x3F]")

    man, blob, tab_u, par, canarino = carica_build(build_dir)
    ok("BUILD", "blob %d B, simboli %s, M-MONO verde"
       % (len(blob), ",".join(ENTRATE_ATTESE)))

    if manifest_path:
        mappa = json.loads(Path(manifest_path).read_text())
        lo, hi = BLOCK_BASE, BLOCK_BASE + BLOCK_N
        for b in mappa["blocchi"]:
            base, n = int(b["base"], 16), b.get("bytes", 0)
            if b["nome"] in ("libero.1.2",):
                continue
            if b["nome"] == "sgp.anim":
                if base != BLOCK_BASE or n != BLOCK_N:
                    no("A4", "voce 'sgp.anim' con base/bytes diversi dagli attesi")
                continue
            if base < hi and base + n > lo:
                no("A4", "sovrapposizione con '%s' [%#x,%#x)" % (b["nome"], base, base + n))
    log["manifest_controllato"] = bool(manifest_path)
    ok("A4", "nessuna sovrapposizione nella mappa della riserva"
       if manifest_path else "mappa non fornita")

    dati_in = Path(ingresso).read_bytes()
    log["sha256_ingresso"] = sha(dati_in)
    log["ingresso_bytes"] = len(dati_in)

    # --- che cosa c'è oggi ------------------------------------------------
    ov_in = img_ov(dati_in)
    g1_ora = ov_in["immagine"][A_G1 - ov_in["ram"]:A_G1 - ov_in["ram"] + 4]
    g2_ora = ov_in["immagine"][A_G2 - ov_in["ram"]:A_G2 - ov_in["ram"] + 4]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "arm9-lettura.nds"
        shutil.copyfile(ingresso, tmp)
        try:
            zona_ora = bytes(Arm9(tmp).leggi(BLOCK_BASE, BLOCK_N))
        except KeyError:
            no("A0", "l'indirizzo %#x non esiste in questa ROM: manca l'arena "
                     "della riserva ARM9 1.2 (SGP-1.2-RISERVA-01). La v4 si "
                     "applica su una ROM 1.2, non sulla base 1.1." % BLOCK_BASE)
    stato_ora = riconosci(zona_ora, bytes(g1_ora), bytes(g2_ora))
    log["stato_ingresso"] = stato_ora
    atteso_v4 = blocco_atteso(blob, tab_u, par, canarino, flags)
    g1_v4 = struct.pack("<I", int(man["simboli"]["sgp_idle_task2"], 16))
    g2_v4 = bl_thumb(A_G2, int(man["simboli"]["sgp_idle_stop"], 16))

    if zona_ora == atteso_v4 and bytes(g1_ora) == g1_v4 and bytes(g2_ora) == g2_v4:
        no("A0", "la v4 è già applicata (blocco e ganci identici agli attesi): "
                 "idempotenza, non riscrivo")
    if stato_ora == "vergine":
        if sostituisci:
            no("A0", "--sostituisci chiesto ma il blocco è vergine: "
                     "usa l'applicazione normale")
        pre_g1 = PRE_G1_VANILLA
        ok("A0", "blocco vergine (1024 B a zero) e gancio G1 vanilla")
    elif stato_ora == "v3":
        if not sostituisci:
            no("A0", "il blocco contiene la v3 (blob %s…): serve --sostituisci"
               % V3_BLOB_SHA[:12])
        pre_g1 = V3_GANCIO
        ok("S1", "v3 riconosciuta byte per byte: blob 600 B %s…, margine a zero, "
                 "canarino, tavola v3 e parametri attesi" % V3_BLOB_SHA[:12])
    else:
        no("A0", "il blocco non è né vergine né la v3 riconosciuta: non tocco niente")
    if bytes(g2_ora) != PRE_G2_VANILLA:
        no("S2", "il sito G2 (%#x) non ha i 4 byte vanilla %s ma %s: "
                 "qualcuno ci ha già messo qualcosa"
           % (A_G2, PRE_G2_VANILLA.hex(), bytes(g2_ora).hex()))
    ok("S2", "G1 riconosciuto (%s), G2 ancora vanilla (%s)"
       % (bytes(g1_ora).hex(), PRE_G2_VANILLA.hex()))

    # --- scrittura del blocco in ARM9 -------------------------------------
    with tempfile.TemporaryDirectory() as td:
        arm9_tmp = Path(td) / "arm9-step.nds"
        shutil.copyfile(ingresso, arm9_tmp)
        r = Arm9(arm9_tmp)
        prima = bytes(r.raw)
        r.scrivi(BLOCK_BASE, atteso_v4)
        leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N))
        diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
        fuori = [i for i in diversi if i not in leciti]
        if fuori:
            no("A2", "%d byte scritti fuori dal blocco, il primo a 0x%X"
               % (len(fuori), fuori[0]))
        if len(r.raw) != len(prima):
            no("A2", "dimensione dell'immagine arm9/riserva cambiata")
        ok("A2", "arm9: %d byte cambiati, tutti dentro i 1024 B del blocco" % len(diversi))
        ok("A5", "canarino %s a +0x%X" % (sha(canarino)[:12], OFF_CANARINO))
        r.salva(arm9_tmp)
        dati_dopo = Path(arm9_tmp).read_bytes()

    # --- i due ganci in ov012 ---------------------------------------------
    patch = [{"addr": A_G1, "pre": pre_g1, "post": g1_v4},
             {"addr": A_G2, "pre": PRE_G2_VANILLA, "post": g2_v4}]
    guardie = [(A_G1, pre_g1), (A_GUARDIA_CORPO, PRE_GUARDIA_CORPO),
               (A_G2, PRE_G2_VANILLA)]
    try:
        dati_out, ric = ovp.applica(dati_dopo, None, guardie, patch, strategia="auto")
    except ovp.Rifiuto as e:
        no("A1", str(e))
    if ric["overlay"]["id"] != OV_CAMPO:
        no("A1", "overlay %d invece di %d" % (ric["overlay"]["id"], OV_CAMPO))
    if len(ric["cancelli"]["C1_guardia"]["candidati"]) != 1:
        no("A1", "le guardie non individuano un overlay solo: %s"
           % ric["cancelli"]["C1_guardia"]["candidati"])
    ok("A1", "overlay 12 scelto per guardia, due ganci scritti in luogo (%s)"
       % ric["strategia"]["usata"])

    # S3: l'overlay, tolti i ganci, torna identico al vanilla di questa ROM.
    ov_out = img_ov(dati_out)
    img = bytearray(ov_out["immagine"])
    img[A_G1 - ov_out["ram"]:A_G1 - ov_out["ram"] + 4] = PRE_G1_VANILLA
    img[A_G2 - ov_out["ram"]:A_G2 - ov_out["ram"] + 4] = PRE_G2_VANILLA
    base_img = bytearray(ov_in["immagine"])
    base_img[A_G1 - ov_in["ram"]:A_G1 - ov_in["ram"] + 4] = PRE_G1_VANILLA
    base_img[A_G2 - ov_in["ram"]:A_G2 - ov_in["ram"] + 4] = PRE_G2_VANILLA
    if bytes(img) != bytes(base_img):
        n = sum(1 for a, b in zip(img, base_img) if a != b)
        no("S3", "l'overlay differisce dall'ingresso in %d byte oltre i ganci" % n)
    ok("S3", "overlay 12: tolti i due ganci, identico al byte all'ingresso "
             "(%d B decompressi)" % len(img))

    log["ganci"] = {
        "G1": {"addr": hex(A_G1), "pre": pre_g1.hex(), "post": g1_v4.hex(),
               "bersaglio": man["simboli"]["sgp_idle_task2"]},
        "G2": {"addr": hex(A_G2), "pre": PRE_G2_VANILLA.hex(), "post": g2_v4.hex(),
               "bersaglio": man["simboli"]["sgp_idle_stop"],
               "istruzione": "BL"},
    }
    log["blocco"] = {"base": hex(BLOCK_BASE), "bytes": BLOCK_N,
                     "blob_sha256": sha(blob), "blob_bytes": len(blob),
                     "canarino_sha256": sha(canarino),
                     "blocco_sha256": sha(atteso_v4), "flags": flags}
    log["overlay_patch"] = ric
    log["voce_mappa_pronta"] = voce_mappa(man, sha(canarino), len(blob), atteso_v4, g2_v4)

    uscita = Path(uscita)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_bytes(dati_out)
    log["uscita"] = str(uscita)
    log["uscita_sha256"] = sha(dati_out)
    log["uscita_bytes"] = len(dati_out)
    if len(dati_out) != len(dati_in):
        no("A2", "la dimensione della ROM è cambiata")
    log["esito"] = "applicato"
    if json_path:
        Path(json_path).write_text(json.dumps(log, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: log[k] for k in
                      ("esito", "stato_ingresso", "uscita", "uscita_sha256")}, indent=2))
    return log


def voce_mappa(man, canarino_sha, blob_len, blocco, g2_post):
    return {
        "nome": "sgp.anim",
        "base": hex(BLOCK_BASE),
        "bytes": BLOCK_N,
        "proprietario": "SGP-1.2-ANIM-SOLIDO-01 (v4)",
        "tipo": "codice+dati+stato",
        "zona": "1.2",
        "formato": {
            "+0x000": "blob Thumb v4: sgp_pulisci, scala_nostra, sgp_idle_stop, "
                      "sgp_idle_task2 (%d B su %d, scomparto PIENO)" % (blob_len, MAX_CODICE),
            "+0x2F0": "canarino 16 B, motivo 0x%08X|i" % CANARINO_MOTIVO,
            "+0x300": "tab_u 32 B (tavola v3 lisciata) + par 32 B",
            "+0x340": "stato 64 B (flags a offset 0: zero = comportamento 1.1; "
                      "+0x20 stop_visti, +0x24 puliti)",
            "+0x380": "4 voci per lottatore da 32 B, liberate da sgp_pulisci",
        },
        "impronta": {
            "blob_sha256": man["blob"]["sha256"],
            "canarino_sha256": canarino_sha,
            "tabella_sha256": sha(blocco[OFF_TABELLE:OFF_TABELLE + 64]),
            "blocco_sha256": sha(blocco),
        },
        "patch_overlay": [
            {"modulo": "ov012", "dove": hex(A_G1), "bytes": 4,
             "pre": PRE_G1_VANILLA.hex(),
             "post": struct.pack("<I", int(man["simboli"]["sgp_idle_task2"], 16)).hex(),
             "nota": "letterale del task passato a CreateSysTask da ov12_02261FD4"},
            {"modulo": "ov012", "dove": hex(A_G2), "bytes": 4,
             "pre": PRE_G2_VANILLA.hex(), "post": g2_post.hex(),
             "nota": "coda di ov12_02262014: BL sgp_idle_stop, che ripete le due "
                     "istruzioni sostituite prima di tornare"},
        ],
        "guardia": {"corpo_task_vanilla": hex(A_GUARDIA_CORPO),
                    "sha256": hashlib.sha256(PRE_GUARDIA_CORPO).hexdigest()},
        "pubblico": False,
    }


def aggiorna_registro_condiviso(rom_path, log):
    rom_path = Path(rom_path).resolve()
    if rom_path.parent != ROM_DIR:
        return False
    sums_path = ROM_DIR / "SHA256SUMS"
    righe = sums_path.read_text().splitlines() if sums_path.exists() else []
    nome = rom_path.name
    nuove = [r for r in righe if not r.endswith("  " + nome)]
    nuove.append("%s  %s" % (log["uscita_sha256"], nome))
    nuove.sort(key=lambda r: r.split("  ")[-1])
    sums_path.write_text("\n".join(nuove) + "\n")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base")
    ap.add_argument("--out")
    ap.add_argument("--in-luogo", metavar="ROM")
    ap.add_argument("--rilegge", metavar="ROM")
    ap.add_argument("--build")
    ap.add_argument("--manifest")
    ap.add_argument("--flags", type=lambda x: int(x, 0), default=0)
    ap.add_argument("--sostituisci", action="store_true")
    ap.add_argument("--tmp")
    ap.add_argument("--json")
    ap.add_argument("--niente-registro", action="store_true")
    a = ap.parse_args()

    try:
        if a.rilegge:
            dati = Path(a.rilegge).read_bytes()
            ov = img_ov(dati)
            g1 = bytes(ov["immagine"][A_G1 - ov["ram"]:A_G1 - ov["ram"] + 4])
            g2 = bytes(ov["immagine"][A_G2 - ov["ram"]:A_G2 - ov["ram"] + 4])
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / "x.nds"
                shutil.copyfile(a.rilegge, tmp)
                try:
                    zona = bytes(Arm9(tmp).leggi(BLOCK_BASE, BLOCK_N))
                except KeyError:
                    print(json.dumps({"rom": a.rilegge, "stato_blocco":
                                      "arena della riserva 1.2 assente (base 1.1)"},
                                     indent=2))
                    return 0
            fuori = {"rom": a.rilegge, "sha256": sha(dati),
                     "stato_blocco": riconosci(zona, g1, g2),
                     "G1": g1.hex(), "G2": g2.hex(),
                     "G2_vanilla": g2 == PRE_G2_VANILLA,
                     "blob_sha256_primi600": sha(zona[:600]),
                     "blocco_sha256": sha(zona)}
            print(json.dumps(fuori, indent=2))
            return 0
        if not a.build:
            print("uso: --build è obbligatorio (tranne con --rilegge)", file=sys.stderr)
            return 2
        if a.in_luogo:
            rom = Path(a.in_luogo)
            if a.tmp:
                Path(a.tmp).mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=a.tmp) as td:
                tmp_in = Path(td) / ("in-" + rom.name)
                tmp_out = Path(td) / ("out-" + rom.name)
                shutil.copyfile(rom, tmp_in)
                log = applica(tmp_in, tmp_out, a.build, a.manifest, a.flags,
                              a.sostituisci, None)
                rilettore = QUI / "rileggi_anim4.py"
                r = subprocess.run([sys.executable, str(rilettore), str(tmp_in),
                                    str(tmp_out), "--build", a.build]
                                   + (["--manifest", a.manifest] if a.manifest else []),
                                   capture_output=True, text=True)
                log["rilettura_in_luogo"] = {"returncode": r.returncode,
                                             "stdout": r.stdout[-6000:],
                                             "stderr": r.stderr[-3000:]}
                if r.returncode != 0:
                    print(r.stdout)
                    print(r.stderr, file=sys.stderr)
                    print("RIFIUTATO — rilettura non verde: NON sostituisco %s" % rom)
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
        if not (a.base and a.out):
            print("uso: --base e --out (oppure --in-luogo ROM)", file=sys.stderr)
            return 2
        log = applica(a.base, a.out, a.build, a.manifest, a.flags, a.sostituisci, a.json)
        if not a.niente_registro:
            aggiorna_registro_condiviso(a.out, log)
        return 0
    except Rifiuto as e:
        print("RIFIUTATO — %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
