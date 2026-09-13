#!/usr/bin/env python3
"""Blocco PLUS+CHUNK — pianta DEFINITIVA (SGP-1.2-QUALITA-NATIVO-01, v-finale,
applicata in luogo il 12/09/2026). Scrive DIRETTAMENTE (non e' piu' un
adattatore verso PLUS-02/PLUS-03) il blocco `sgp.plus` (2048 B a 0x023D8100):

    +0x000  blob Thumb PLUS         256 B  (sgp_trainer_hook/sgp_wild_hook)
    +0x120  blob Thumb SALVATAGGIO  500 B  (sgp_gancio_carica/sgp_gancio_salva)
    +0x314..+0x400  a zero (margine)
    +0x400  tab_trainer  256 B  -- INVARIATA
    +0x500  tab_wild     256 B  -- INVARIATA
    +0x600  stato         32 B  -- INVARIATO
    +0x620  canarino      16 B  -- INVARIATO
    +0x630..+0x800  a zero (464 B liberi: qui viveva il blob salvataggio v2)

e il blocco DATI `sgp.salvataggio` (256 B a 0x023D8F00): SOLO il buffer del
chunk (32 B, resta a zero: lo riempie il gioco) + il canarino a +0xF0. Il
codice che prima viveva li' (PLUS-03) e' dentro `sgp.plus` ora.

Sette ganci, tutti scritti IN LUOGO su bytes vanilla (nessuna rilocazione,
nessuna catena a due passi come la vecchia PLUS-02->PLUS-03):
  arm9   4x 0x02073718/0x02073802/0x0207390C/0x02073A0C -> sgp_trainer_hook
  ov002  0x02247D3A (guardia 0x02246C94) -> sgp_wild_hook
  arm9   0x020271F8 -> sgp_gancio_carica (dentro SaveData_Init)
  arm9   0x02027456 -> sgp_gancio_salva  (in coda a SaveData_Save)

Le preimmagini vanilla (PREIMG_TRAINER/PREIMG_WILD/PRE_L0/PRE_S0) sono le
stesse gia' verificate da `SGP-1.2-PLUS-02/tools/applica_plus.py` e
`SGP-1.2-PLUS-03/tools/applica_salvataggio.py`: non sono state re-inventate
qui, sono le costanti misurate su base-1.1 vanilla.

`build`: una cartella `plus/` con `blob.bin` (256 B), `salva_blob.bin`
(500 B), `tab_trainer.bin`/`tab_wild.bin` (256 B, INVARIATI), `stato.bin`/
`canarino.bin` (32/16 B, INVARIATI) e `manifesto.json` (simboli
sgp_trainer_hook/sgp_wild_hook/sgp_gancio_carica/sgp_gancio_salva, decodificati
dalla ROM canonica da `estrai_build.py`) — e una cartella `salvataggio/` con
`canarino.bin` (16 B) per il blocco dati.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..rom import Arm9, Rifiuto, bl_decode, bl_thumb, esigi, esigi_manifesto_descrive, sha
from .. import overlay as ovp

# --- pianta sgp.plus ---------------------------------------------------
PLUS_BASE, PLUS_N = 0x023D8100, 2048
OFF_BLOB_PLUS, OFF_BLOB_SALVA, FINE_CODICE = 0x000, 0x120, 0x400
N_BLOB_PLUS_CAP, N_BLOB_SALVA_CAP = OFF_BLOB_SALVA - OFF_BLOB_PLUS, FINE_CODICE - OFF_BLOB_SALVA
OFF_TAB_TRN, OFF_TAB_WLD, OFF_STATO, OFF_CANARY = 0x400, 0x500, 0x600, 0x620
N_STATO, N_CANARY = 32, 16

# --- pianta sgp.salvataggio (dati) --------------------------------------
SALVA_BASE, SALVA_N = 0x023D8F00, 256
SALVA_OFF_CANARY, SALVA_N_CANARY = 0xF0, 16

# --- ganci: siti vanilla + preimmagini vanilla (misurate da PLUS-02/03) --
SITI_TRAINER = (0x02073718, 0x02073802, 0x0207390C, 0x02073A0C)
PREIMG_TRAINER = bytes.fromhex("5288301c")

SITO_WILD = 0x02247D3A
PREIMG_WILD = bytes.fromhex("04a80078")
GUARDIA_ADDR, PREIMG_GUARDIA = 0x02246C94, bytes.fromhex("00880328")

SITO_L0, PRE_L0 = 0x020271F8, bytes.fromhex("00f0ecfa")
SITO_S0, PRE_S0 = 0x02027456, bytes.fromhex("00f0adfc")

ENTRATE_ATTESE = ("sgp_trainer_hook", "sgp_wild_hook", "sgp_gancio_carica", "sgp_gancio_salva")


def _carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob_plus = (build / "blob.bin").read_bytes()
    blob_salva = (build / "salva_blob.bin").read_bytes()
    tab_trainer = (build / "tab_trainer.bin").read_bytes()
    tab_wild = (build / "tab_wild.bin").read_bytes()
    stato = (build / "stato.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()
    esigi(len(blob_plus) <= N_BLOB_PLUS_CAP, "BUILD: blob PLUS non entra nello slot (%d > %d)"
          % (len(blob_plus), N_BLOB_PLUS_CAP))
    esigi(len(blob_salva) <= N_BLOB_SALVA_CAP, "BUILD: blob SALVATAGGIO non entra nello slot (%d > %d)"
          % (len(blob_salva), N_BLOB_SALVA_CAP))
    esigi(len(tab_trainer) == 256 and len(tab_wild) == 256, "BUILD: tabelle di dimensione sbagliata")
    esigi(len(stato) == N_STATO, "BUILD: stato di dimensione sbagliata")
    esigi(len(canarino) == N_CANARY, "BUILD: canarino di dimensione sbagliata")
    # Regola unica (`sgp12/rom.py`): il manifesto descrive i due blob che gli
    # stanno accanto, byte e sha256, e i due campi sono OBBLIGATORI. Prima erano
    # due `if ... in man`: un manifesto che non li dichiarava passava.
    esigi_manifesto_descrive(man, blob_plus, "blob", "blob.bin", "sgp.plus")
    esigi_manifesto_descrive(man, blob_salva, "blob_salva", "salva_blob.bin", "sgp.plus")
    for nome in ENTRATE_ATTESE:
        esigi(nome in man["simboli"], "BUILD: simbolo mancante: %s" % nome)
    _verifica_simboli(man, blob_plus, blob_salva)
    return man, blob_plus, blob_salva, tab_trainer, tab_wild, stato, canarino


# A quale dei due blob appartiene ciascuna entrata.
PROPRIETARIO = {"sgp_trainer_hook": "plus", "sgp_wild_hook": "plus",
                "sgp_gancio_carica": "salva", "sgp_gancio_salva": "salva"}


def _verifica_simboli(man, blob_plus, blob_salva):
    """M4 della revisione R2: `_carica_build` verificava solo che il NOME del
    simbolo esistesse, mai il valore — e `applica()` scrive quel valore dentro
    sette BL, mentre `rileggi()` L7-L10 lo riverifica leggendo LO STESSO
    numero. Una BL sbagliata e la sua verifica sbagliata si annullavano a
    vicenda. Qui si controllano indirizzo e contenuto:

      * bit Thumb acceso (tutte e cinque le entrate sono Thumb);
      * l'indirizzo cade dentro il blob che lo possiede — non genericamente
        «dentro sgp.plus», dove c'e' anche la riserva azzerata e le tabelle;
      * i byte a quell'indirizzo non sono nulli (non e' riempimento);
      * `sgp_wild_hook` porta come PRIMA istruzione quella che il gancio
        sostituisce in ov002 (`PREIMG_WILD`): e' la trampolina che la
        riesegue, quindi e' un controllo sul CONTENUTO, non solo sul posto.
    """
    zone = {"plus": (PLUS_BASE + OFF_BLOB_PLUS, blob_plus),
            "salva": (PLUS_BASE + OFF_BLOB_SALVA, blob_salva)}
    for nome, valore in man["simboli"].items():
        v = int(valore, 16)
        dentro = [(base, blob) for base, blob in zone.values() if base <= (v & ~1) < base + len(blob)]
        esigi(dentro, "BUILD: il simbolo '%s' (%s) non cade dentro nessuno dei due blob "
                      "spediti di sgp.plus" % (nome, valore))
    for nome in ENTRATE_ATTESE:
        v = int(man["simboli"][nome], 16)
        esigi(v & 1, "BUILD: '%s' (%s) senza bit Thumb" % (nome, man["simboli"][nome]))
        base, blob = zone[PROPRIETARIO[nome]]
        off = (v & ~1) - base
        esigi(0 <= off <= len(blob) - 4,
              "BUILD: '%s' (%s) fuori dal blob '%s' [%#x, %#x)"
              % (nome, man["simboli"][nome], PROPRIETARIO[nome], base, base + len(blob)))
        esigi(blob[off:off + 4] != b"\x00\x00\x00\x00",
              "BUILD: '%s' (%s) punta a byte nulli: e' riempimento, non codice"
              % (nome, man["simboli"][nome]))
    v = int(man["simboli"]["sgp_wild_hook"], 16) & ~1
    off = v - (PLUS_BASE + OFF_BLOB_PLUS)
    esigi(blob_plus[off:off + 4] == PREIMG_WILD,
          "BUILD: sgp_wild_hook non comincia con l'istruzione che il gancio sostituisce "
          "(%s, attesa %s): o l'indirizzo e' sbagliato, o la trampolina non e' quella"
          % (blob_plus[off:off + 4].hex(), PREIMG_WILD.hex()))


def _carica_build_salvataggio(build_salvataggio_dir):
    build = Path(build_salvataggio_dir)
    canarino = (build / "canarino.bin").read_bytes()
    esigi(len(canarino) == SALVA_N_CANARY, "BUILD: canarino sgp.salvataggio di dimensione sbagliata")
    return canarino


def _verifica_manifest_mappa(manifest_path, log):
    if not manifest_path:
        log["manifest_controllato"] = False
        return
    mappa = json.loads(Path(manifest_path).read_text())
    zone = [(PLUS_BASE, PLUS_N, {"sgp.plus"}), (SALVA_BASE, SALVA_N, {"sgp.salvataggio"})]
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


def applica(rom: bytes, build_dir, manifest_path=None) -> tuple[bytes, dict]:
    """`build_dir`: la cartella `sgp12/build/` (contiene `plus/` e
    `salvataggio/`), come per gli altri blocchi in `costruisci.py`."""
    build_dir = Path(build_dir)
    log = {"strumento": "sgp12/blocchi/plus_chunk.py:applica", "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})

    man, blob_plus, blob_salva, tab_trainer, tab_wild, stato, canarino = _carica_build(build_dir / "plus")
    canarino_salva = _carica_build_salvataggio(build_dir / "salvataggio")
    _verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione")

    log["sha256_ingresso"] = sha(rom)

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf:
        tf.write(rom)
        tf.flush()
        r = Arm9(tf.name)
    prima = bytes(r.raw)

    zona = r.leggi(PLUS_BASE, PLUS_N)
    esigi(zona == bytes(PLUS_N), "A0: il blocco sgp.plus non e' a zero")
    ok("A0", "2048 B a zero")
    zona_s = r.leggi(SALVA_BASE, SALVA_N)
    esigi(zona_s == bytes(SALVA_N), "A0b: il blocco sgp.salvataggio non e' a zero")
    ok("A0b", "256 B a zero")

    for s in SITI_TRAINER:
        esigi(r.leggi(s, 4) == PREIMG_TRAINER, "A1: 0x%08X non ha la preimmagine vanilla" % s)
    ok("A1", "quattro siti trainer con preimmagine vanilla")
    esigi(r.leggi(SITO_L0, 4) == PRE_L0, "A1b: L0 non ha la preimmagine vanilla")
    esigi(r.leggi(SITO_S0, 4) == PRE_S0, "A1c: S0 non ha la preimmagine vanilla")
    ok("A1bc", "L0/S0 con preimmagine vanilla")

    blocco = bytearray(PLUS_N)
    blocco[OFF_BLOB_PLUS:OFF_BLOB_PLUS + len(blob_plus)] = blob_plus
    blocco[OFF_BLOB_SALVA:OFF_BLOB_SALVA + len(blob_salva)] = blob_salva
    blocco[OFF_TAB_TRN:OFF_TAB_TRN + 256] = tab_trainer
    blocco[OFF_TAB_WLD:OFF_TAB_WLD + 256] = tab_wild
    blocco[OFF_STATO:OFF_STATO + N_STATO] = stato
    blocco[OFF_CANARY:OFF_CANARY + N_CANARY] = canarino
    r.scrivi(PLUS_BASE, bytes(blocco))

    blocco_s = bytearray(SALVA_N)
    blocco_s[SALVA_OFF_CANARY:SALVA_OFF_CANARY + SALVA_N_CANARY] = canarino_salva
    r.scrivi(SALVA_BASE, bytes(blocco_s))

    gancio_trainer = int(man["simboli"]["sgp_trainer_hook"], 16)
    for s in SITI_TRAINER:
        r.scrivi(s, bl_thumb(s, gancio_trainer))
    r.scrivi(SITO_L0, bl_thumb(SITO_L0, int(man["simboli"]["sgp_gancio_carica"], 16)))
    r.scrivi(SITO_S0, bl_thumb(SITO_S0, int(man["simboli"]["sgp_gancio_salva"], 16)))

    leciti = set(range(r.off(PLUS_BASE), r.off(PLUS_BASE) + PLUS_N)) | \
             set(range(r.off(SALVA_BASE), r.off(SALVA_BASE) + SALVA_N)) | \
             set(range(r.off(SITI_TRAINER[0]), r.off(SITI_TRAINER[0]) + 4)) | \
             set(range(r.off(SITI_TRAINER[1]), r.off(SITI_TRAINER[1]) + 4)) | \
             set(range(r.off(SITI_TRAINER[2]), r.off(SITI_TRAINER[2]) + 4)) | \
             set(range(r.off(SITI_TRAINER[3]), r.off(SITI_TRAINER[3]) + 4)) | \
             set(range(r.off(SITO_L0), r.off(SITO_L0) + 4)) | \
             set(range(r.off(SITO_S0), r.off(SITO_S0) + 4))
    diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
    fuori = [i for i in diversi if i not in leciti]
    esigi(not fuori, "A2: byte scritti fuori dalle regioni dichiarate")
    esigi(len(r.raw) == len(prima), "A2: dimensione cambiata")
    ok("A2", "%d byte scritti (due blocchi + sei ganci arm9)" % len(diversi))

    with tempfile.NamedTemporaryFile(suffix=".nds") as tf2:
        r.salva(tf2.name)
        dati_dopo_arm9 = Path(tf2.name).read_bytes()

    gancio_wild = int(man["simboli"]["sgp_wild_hook"], 16)
    post_wild = bl_thumb(SITO_WILD, gancio_wild)
    guardie = [(GUARDIA_ADDR, PREIMG_GUARDIA), (SITO_WILD, PREIMG_WILD)]
    patch = [{"addr": SITO_WILD, "pre": PREIMG_WILD, "post": post_wild}]
    dati_finale, ric = ovp.applica(dati_dopo_arm9, None, guardie, patch, strategia="auto")
    ok("A3", "overlay selvatici (scelto per guardia, id %d) patchato in luogo: %s"
       % (ric["overlay"]["id"], ric["strategia"]["usata"]))
    log["overlay_patch"] = ric

    log["uscita_sha256"] = sha(dati_finale)
    log["esito"] = "applicato"
    return dati_finale, log


# ---------------------------------------------------------------- rilettore
def rileggi(ingresso: bytes, derivata: bytes, build_dir) -> dict:
    """Rilettore: ridecodifica i sette ganci e i due blocchi da zero
    (`sgp12.rom.Arm9`/`bl_decode`, NON riusa nessuno stato di `applica()`
    sopra) e confronta con quello che il `build/` dichiara. Non e' una
    famiglia di decoder indipendente come in `npc.py` (qui si riusa
    `sgp12.rom`): un limite dichiarato, non nascosto — vedi RAPPORTO."""
    build_dir = Path(build_dir)
    man, blob_plus, blob_salva, tab_trainer, tab_wild, stato, canarino = _carica_build(build_dir / "plus")
    canarino_salva = _carica_build_salvataggio(build_dir / "salvataggio")

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

    esito("L0", b.leggi(PLUS_BASE, PLUS_N) == bytes(PLUS_N) and b.leggi(SALVA_BASE, SALVA_N) == bytes(SALVA_N),
          "i due blocchi erano a zero nell'ingresso")

    codice_plus = d.leggi(PLUS_BASE + OFF_BLOB_PLUS, len(blob_plus))
    codice_salva = d.leggi(PLUS_BASE + OFF_BLOB_SALVA, len(blob_salva))
    esito("L1", sha(codice_plus) == sha(blob_plus) and sha(codice_salva) == sha(blob_salva),
          "blob PLUS/SALVATAGGIO combaciano col build")

    padding_ok = (d.leggi(PLUS_BASE + OFF_BLOB_PLUS + len(blob_plus), OFF_BLOB_SALVA - OFF_BLOB_PLUS - len(blob_plus))
                  == bytes(OFF_BLOB_SALVA - OFF_BLOB_PLUS - len(blob_plus))
                  and d.leggi(PLUS_BASE + OFF_BLOB_SALVA + len(blob_salva),
                             FINE_CODICE - OFF_BLOB_SALVA - len(blob_salva))
                  == bytes(FINE_CODICE - OFF_BLOB_SALVA - len(blob_salva))
                  and d.leggi(PLUS_BASE + FINE_CODICE + N_STATO * 0, OFF_TAB_TRN - FINE_CODICE)
                  == bytes(OFF_TAB_TRN - FINE_CODICE)
                  and d.leggi(PLUS_BASE + OFF_CANARY + N_CANARY, PLUS_N - OFF_CANARY - N_CANARY)
                  == bytes(PLUS_N - OFF_CANARY - N_CANARY))
    esito("L2", padding_ok, "margini (+0x314..+0x400, +0x630..+0x800) a zero")

    esito("L3", d.leggi(PLUS_BASE + OFF_TAB_TRN, 256) == tab_trainer and
          d.leggi(PLUS_BASE + OFF_TAB_WLD, 256) == tab_wild, "tab_trainer/tab_wild INVARIATE")
    esito("L4", d.leggi(PLUS_BASE + OFF_STATO, N_STATO) == stato, "stato INVARIATO")
    esito("L5", d.leggi(PLUS_BASE + OFF_CANARY, N_CANARY) == canarino, "canarino sgp.plus INVARIATO")
    esito("L6", d.leggi(SALVA_BASE, SALVA_N)[:32] == bytes(32) and
          d.leggi(SALVA_BASE + SALVA_OFF_CANARY, SALVA_N_CANARY) == canarino_salva,
          "sgp.salvataggio: buffer a zero, canarino INVARIATO")

    bersaglio_atteso = int(man["simboli"]["sgp_trainer_hook"], 16) & ~1
    for i, s in enumerate(SITI_TRAINER):
        t = bl_decode(s, d.leggi(s, 4))
        esito("L7.%d" % i, t == bersaglio_atteso, "trainer[%d] -> %s" % (i, hex(t) if t else t))
    esito("L8", bl_decode(SITO_L0, d.leggi(SITO_L0, 4)) == (int(man["simboli"]["sgp_gancio_carica"], 16) & ~1),
          "L0 -> sgp_gancio_carica")
    esito("L9", bl_decode(SITO_S0, d.leggi(SITO_S0, 4)) == (int(man["simboli"]["sgp_gancio_salva"], 16) & ~1),
          "S0 -> sgp_gancio_salva")

    rom_ovp_b, rom_ovp_d = ovp.Rom(ingresso), ovp.Rom(derivata)
    trovati = []
    for i in range(rom_ovp_d.n_overlay):
        v = rom_ovp_d.voce_overlay(i)
        if not (v["ram"] <= SITO_WILD < v["ram"] + v["ram_size"]):
            continue
        try:
            _, _, img = rom_ovp_d.immagine_overlay(i)
        except Exception:
            continue
        off_w = SITO_WILD - v["ram"]
        t = bl_decode(SITO_WILD, bytes(img[off_w:off_w + 4]))
        if t is not None:
            trovati.append((i, t))
    bersaglio_wild_atteso = int(man["simboli"]["sgp_wild_hook"], 16) & ~1
    esito("L10", any(t == bersaglio_wild_atteso for _, t in trovati),
          "almeno un overlay decodifica il gancio selvatici sul bersaglio atteso: %s" % trovati)

    return {"esito_finale": "verde" if verde else "ROSSO", "cancelli": esiti}
