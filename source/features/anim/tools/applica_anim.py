#!/usr/bin/env python3
"""APPLICATORE — SGP-1.2-ANIM-B-02 (A1-B fase 2, preparazione).

Scrive il blocco `sgp.anim` (1024 B a 0x023D8B00, riservato in
`source/docs/arm9-reserve-reservations.md`, fine 0x023D8F00) e patcha il gancio
in `ov012` (letterale di 4 B a 0x0226200C, NON un'istruzione: e' il puntatore
a funzione passato a `CreateSysTask` da `ov12_02261FD4`), USANDO
`overlay_patch.py` (copia di `SGP-1.2-OVERLAY-01/tools/overlay_patch.py`:
ricompressione BLZ ottima IN LUOGO, mai riloco — gia' provato su questo
stesso overlay, `SGP-1.2-OVERLAY-01/RAPPORTO.md` §6, corsa `TW2`).

Modello: `SGP-1.2-PRESTAZIONI-NPC-02/tools/applica_npc.py` (applicatore in
luogo, stessa disciplina copia->applica->rilegge->sostituisce) e
`SGP-1.2-PLUS-02/tools/applica_plus.py`. Logica del gancio e del blob:
`SGP-1.2-ANIM-B-01/CONTRATTO-A1B.md` + `PIANO-INIEZIONE.md` (fase 1b).

Differenza dal gancio di NPC/PLUS: qui non c'e' nessuna `BL` da costruire.
Il gancio e' un LETTERALE: la preimmagine `3d202602` (= puntatore al task
vanilla `0x0226203D`) viene sostituita dal puntatore al nostro blob CON IL
BIT THUMB (`codice|1`), in little endian.

L'overlay si sceglie SOLO per guardia (mai per indirizzo: cinque overlay
contengono 0x0226200C — CONTRATTO-A1B.md §1.2, misurato anche da
OVERLAY-01/RAPPORTO.md §1): due guardie, il letterale stesso (4 B) e la firma
del corpo del task vanilla a 0x0226203C (90 B, sha256 identico su EN e IT).

Flag di abilitazione: nello STATO in RAM del blocco (`flags`, offset 0), NON
nel salvataggio (CONTRATTO-A1B.md §7, PIANO-INIEZIONE.md §6: il bit b5
`anim_on` di `SgpExtra.flags` e' della pagina Opzioni, non di questo
pacchetto). **Default SPENTO in questa fase** (`--flags 0` di default): a ROM
applicata il gioco e' byte-identico nei fotogrammi alla 1.1, finche' nessuno
scrive `flags != 0` (dal menu Opzioni, quando esistera', o da uno script di
prova). E' l'INVERSO della convenzione di NPC-02 (default ACCESO): qui la
decisione dell'orchestratore e' l'opposta, scritta in CRITERI.md §0.

Non modifica MAI l'ingresso. Rifiuta (RIFIUTATO, rc=2) tutto quello che non
riconosce: cancelli A0-A4, CRITERI.md §2.

Uso normale (scrive un file NUOVO, l'ingresso resta intatto):
    applica_anim.py --base <sgp-1.2-XX.nds> --out <uscita.nds> --build <dir> \\
                     [--manifest MAPPA-RISERVA-ARM9.json] [--flags 0] [--json log.json]

Uso «in luogo» (NON da usare in questa fase — il lucchetto della ROM di
lavoro condivisa e' di un altro cantiere, questo pacchetto valida solo su
COPIE):
    applica_anim.py --in-luogo <rom.nds> --build <dir> [--manifest ...] [--tmp <scratchpad>]
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
A_GANCIO = 0x0226200C
PRE_GANCIO = bytes.fromhex("3d202602")
A_GUARDIA_CORPO = 0x0226203C
PRE_GUARDIA_CORPO = bytes.fromhex(
    "38b50c1c67218900605a14306052081c625a3438824203d3081c3438101a60"
    "5267208000205abdf5a9fd0622c1179202002390f66cec0a1c0421051c206a"
    "00244b02eb18624112051b0b1343da12120d9a181213a6f588fb38bd")
assert len(PRE_GUARDIA_CORPO) == 90
assert hashlib.sha256(PRE_GUARDIA_CORPO).hexdigest() == \
    "0b247d4c37cd35bd205e6cd51ef496a0ced83064ad58060ccaf473e001c28883"

BLOCK_BASE, BLOCK_N = 0x023D8B00, 0x400          # 1024 B, fine 0x023D8F00
OFF_CODICE, MAX_CODICE = 0x000, 0x2F0            # blob reale: 612 B
OFF_CANARINO, N_CANARINO = 0x2F0, 16             # DENTRO il blocco
OFF_TABELLE = 0x300                              # tab_u 32 B + par 32 B
OFF_STATO, N_STATO = 0x340, 64
OFF_SLOT, N_SLOT = 0x380, 128                    # 4 x 32 B, fino a 0x400
CANARINO_MOTIVO = 0xCA5A1400

ENTRATE_ATTESE = ("sgp_idle_task2",)


class Rifiuto(Exception):
    pass


def no(cancello, msg):
    raise Rifiuto("%s: %s" % (cancello, msg))


def sha(b):
    return hashlib.sha256(bytes(b)).hexdigest()


def carica_build(build_dir):
    build = Path(build_dir)
    man = json.loads((build / "manifesto.json").read_text())
    blob = (build / "blob.bin").read_bytes()
    tab_u = (build / "tab_u.bin").read_bytes()
    par = (build / "par.bin").read_bytes()
    canarino = (build / "canarino.bin").read_bytes()
    if int(man["indirizzi"]["codice"], 16) != BLOCK_BASE + OFF_CODICE:
        no("BUILD", "blob compilato per %s, atteso 0x%08X: ricompila con --base"
           % (man["indirizzi"]["codice"], BLOCK_BASE + OFF_CODICE))
    if int(man["indirizzi"]["stato"], 16) != BLOCK_BASE + OFF_STATO:
        no("BUILD", "indirizzo stato incoerente col blocco sgp.anim")
    if int(man["indirizzi"]["canarino"], 16) != BLOCK_BASE + OFF_CANARINO:
        no("BUILD", "indirizzo canarino incoerente col blocco sgp.anim")
    if len(blob) > MAX_CODICE:
        no("BUILD", "blob %d B non entra nei %d B riservati prima del canarino"
           % (len(blob), MAX_CODICE))
    if len(tab_u) != 32 or len(par) != 32:
        no("BUILD", "tab_u/par devono essere 32+32 B")
    if len(canarino) != N_CANARINO:
        no("BUILD", "canarino.bin deve essere %d B" % N_CANARINO)
    for nome in ENTRATE_ATTESE:
        if nome not in man["simboli"]:
            no("BUILD", "simbolo mancante nel manifesto: %s" % nome)
    return man, blob, tab_u, par, canarino


def verifica_manifest_mappa(manifest_path, log):
    """A4: se una mappa e' data, il blocco sgp.anim non deve sovrapporsi a
    NESSUN blocco gia' registrato (tranne 'libero.1.2', che e' lo spazio
    libero stesso), e se una voce sgp.anim esiste gia' deve combaciare."""
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
            if base != BLOCK_BASE or n != BLOCK_N:
                no("A4/mappa", "voce 'sgp.anim' gia' registrata con base/bytes diversi da quelli attesi")
            continue
        if base < hi and base + n > lo:
            no("A4/mappa", "il blocco sgp.anim [%#x,%#x) si sovrappone a '%s' [%#x,%#x)"
               % (lo, hi, b["nome"], base, base + n))
    log["manifest_controllato"] = True


def voce_mappa(man, canarino_sha, blob_len):
    """Voce PRONTA ma NON scritta (CRITERI.md §1): la scrive solo l'esecuzione
    --in-luogo, mai questa fase di preparazione."""
    return {
        "nome": "sgp.anim",
        "base": hex(BLOCK_BASE),
        "bytes": BLOCK_N,
        "proprietario": "SGP-1.2-ANIM-B-02",
        "tipo": "codice+dati+stato",
        "zona": "1.2",
        "formato": {
            "+0x000": "blob Thumb sgp_idle_task2, fase 1b invariata (%d B su %d)"
                      % (blob_len, MAX_CODICE),
            "+0x2F0": "canarino 16 B, motivo 0x%08X|i" % CANARINO_MOTIVO,
            "+0x300": "tab_u 32 B (seno x 16) + par 32 B",
            "+0x340": "stato 64 B (flags a offset 0: zero = comportamento 1.1)",
            "+0x380": "4 voci per lottatore da 32 B",
        },
        "impronta": {"blob_sha256": man["blob"]["sha256"],
                     "canarino_sha256": canarino_sha},
        "ancore": [
            {"dove": "ov012 0x0226200C", "vale": "<base>|1", "thumb": True,
             "nota": "letterale della funzione passata a CreateSysTask in "
                     "ov12_02261FD4; postimmagine %s per base %s"
                     % (struct.pack("<I", int(man["simboli"]["sgp_idle_task2"], 16)).hex(),
                        hex(BLOCK_BASE))}
        ],
        "pubblico": False,
    }


def applica(ingresso, uscita, build_dir, manifest_path, flags, json_path):
    log = {"strumento": "SGP-1.2-ANIM-B-02/tools/applica_anim.py",
           "ingresso": str(ingresso), "cancelli": []}

    def ok(c, msg=""):
        log["cancelli"].append({"cancello": c, "esito": "passato", "nota": msg})
        print("  %-4s passato  %s" % (c, msg))

    if not (0 <= flags <= 0x3F):
        no("PARAM", "flags fuori da [0, 0x3F] (SGP_F_TUTTI)")

    man, blob, tab_u, par, canarino = carica_build(build_dir)
    verifica_manifest_mappa(manifest_path, log)
    ok("A4", "nessuna sovrapposizione col resto della mappa (o mappa non fornita)")

    dati_in = Path(ingresso).read_bytes()
    log["sha256_ingresso"] = sha(dati_in)
    log["ingresso_bytes"] = len(dati_in)

    # ---------------- scrittura ARM9 (blocco sgp.anim, canarino compreso) --
    with tempfile.TemporaryDirectory() as td:
        arm9_tmp = Path(td) / "arm9-step.nds"
        shutil.copyfile(ingresso, arm9_tmp)
        r = Arm9(arm9_tmp)
        prima = bytes(r.raw)

        # A0: idempotenza — l'intero blocco (1024 B, canarino compreso) deve
        # essere ancora tutto a zero.
        zona = r.leggi(BLOCK_BASE, BLOCK_N)
        if zona != bytes(BLOCK_N):
            primo = next(i for i, x in enumerate(zona) if x)
            no("A0", "il blocco sgp.anim a 0x%08X non e' a zero (primo byte non nullo a +0x%X): "
                     "gia' applicato, o occupato da qualcun altro" % (BLOCK_BASE, primo))
        ok("A0", "1024 B a 0x%08X tutti a zero" % BLOCK_BASE)

        blocco = bytearray(BLOCK_N)
        blocco[OFF_CODICE:OFF_CODICE + len(blob)] = blob
        blocco[OFF_CANARINO:OFF_CANARINO + N_CANARINO] = canarino
        blocco[OFF_TABELLE:OFF_TABELLE + 32] = tab_u
        blocco[OFF_TABELLE + 32:OFF_TABELLE + 64] = par
        stato = bytearray(N_STATO)
        stato[0x00] = flags & 0xFF          # 0 = comportamento 1.1 esatto
        stato[0x01] = 0x5A                  # guardia dell'iniettore
        stato[0x02] = 0                     # diagnostica, a zero all'iniezione
        blocco[OFF_STATO:OFF_STATO + N_STATO] = stato
        # OFF_SLOT..fine: 4 voci per lottatore, a zero (nessuna voce occupata).
        r.scrivi(BLOCK_BASE, bytes(blocco))

        # A2: portata — nessun byte cambiato fuori dal blocco dichiarato
        leciti = set(range(r.off(BLOCK_BASE), r.off(BLOCK_BASE) + BLOCK_N))
        diversi = [i for i in range(len(prima)) if prima[i] != r.raw[i]]
        fuori = [i for i in diversi if i not in leciti]
        if fuori:
            no("A2", "%d byte scritti fuori dal blocco dichiarato, il primo a offset 0x%X"
               % (len(fuori), fuori[0]))
        if len(r.raw) != len(prima):
            no("A2", "la dimensione dell'immagine arm9/riserva e' cambiata")
        ok("A2", "arm9: %d byte scritti (blocco sgp.anim, 1024 B), dimensione invariata" % len(diversi))

        r.salva(arm9_tmp)
        dati_dopo_arm9 = Path(arm9_tmp).read_bytes()

    log["blocco"] = {"base": hex(BLOCK_BASE), "bytes": BLOCK_N, "blob_sha256": sha(blob),
                     "canarino_sha256": sha(canarino), "stato_sha256": sha(stato),
                     "flags": flags}

    # ---------------- patch del letterale in ov012 (in luogo, guardia) -----
    codice_thumb = int(man["simboli"]["sgp_idle_task2"], 16)
    if codice_thumb & 1 == 0:
        no("BUILD", "il simbolo sgp_idle_task2 non ha il bit Thumb: %#x" % codice_thumb)
    post = struct.pack("<I", codice_thumb)
    patch = [{"addr": A_GANCIO, "pre": PRE_GANCIO, "post": post}]
    guardie = [(A_GANCIO, PRE_GANCIO), (A_GUARDIA_CORPO, PRE_GUARDIA_CORPO)]
    try:
        dati_out, ric = ovp.applica(dati_dopo_arm9, None, guardie, patch, strategia="auto")
    except ovp.Rifiuto as e:
        no("A1/overlay", str(e))
    if ric["overlay"]["id"] != OV_CAMPO:
        no("A1", "overlay scelto (%d) diverso da quello atteso (%d)" % (ric["overlay"]["id"], OV_CAMPO))
    if len(ric["cancelli"]["C1_guardia"]["candidati"]) != 1:
        no("A1", "la guardia non individua un overlay solo: candidati %s"
           % ric["cancelli"]["C1_guardia"]["candidati"])
    ok("A1", "overlay 12 scelto SOLO per guardia (candidati=[12]), patchato in luogo: %s"
       % ric["strategia"]["usata"])
    log["overlay_patch"] = ric
    log["ganci"] = {"gancio": hex(A_GANCIO), "bersaglio": hex(codice_thumb), "post": post.hex()}
    log["voce_mappa_pronta"] = voce_mappa(man, sha(canarino), len(blob))

    uscita = Path(uscita)
    uscita.parent.mkdir(parents=True, exist_ok=True)
    uscita.write_bytes(dati_out)
    log["uscita"] = str(uscita)
    log["uscita_sha256"] = sha(dati_out)
    log["uscita_bytes"] = len(dati_out)
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
    ap.add_argument("--base", help="ROM di ingresso (o la ROM di lavoro con --in-luogo)")
    ap.add_argument("--out", help="ROM di uscita (obbligatorio se non --in-luogo)")
    ap.add_argument("--in-luogo", metavar="ROM",
                    help="NON usare in questa fase: applica sulla ROM di lavoro condivisa")
    ap.add_argument("--build", required=True, help="cartella con blob.bin/manifesto.json (tools/compila_anim.py)")
    ap.add_argument("--manifest", help="MAPPA-RISERVA-ARM9.json, per il cancello A4")
    ap.add_argument("--flags", type=lambda x: int(x, 0), default=0,
                    help="default 0 = SPENTO (decisione dell'orchestratore per questa fase, vedi docstring)")
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
                log = applica(tmp_in, tmp_out, a.build, a.manifest, a.flags, None)
                rilettore = QUI / "rileggi_anim.py"
                r = subprocess.run([sys.executable, str(rilettore), str(tmp_in), str(tmp_out),
                                    "--build", a.build] + (["--manifest", a.manifest] if a.manifest else []),
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
            if not (a.base and a.out):
                print("uso: --base e --out (oppure --in-luogo ROM)", file=sys.stderr)
                return 2
            log = applica(a.base, a.out, a.build, a.manifest, a.flags, a.json)
            if not a.niente_registro:
                aggiorna_registro_condiviso(a.out, log)
            return 0
    except Rifiuto as e:
        print("RIFIUTATO — %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
